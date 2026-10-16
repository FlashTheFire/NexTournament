package com.nextournament.app.data.network

import com.nextournament.app.data.model.AuthResponse
import com.nextournament.app.data.model.TokenRefreshRequest
import com.nextournament.app.data.security.SessionManager
import kotlinx.serialization.json.Json
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenAuthenticator @Inject constructor(
    private val sessionManager: SessionManager,
    private val json: Json
) : Authenticator {

    private val lock = Any()

    override fun authenticate(route: Route?, response: Response): Request? {
        // Prevent infinite loops if refresh fails
        if (responseCount(response) >= 2) {
            return null
        }

        synchronized(lock) {
            val currentToken = sessionManager.getAccessToken()
            val requestToken = response.request.header("Authorization")?.replace("Bearer ", "")

            // If another thread already refreshed the token, retry with new token
            if (currentToken != null && currentToken != requestToken) {
                return response.request.newBuilder()
                    .header("Authorization", "Bearer $currentToken")
                    .build()
            }

            val refreshToken = sessionManager.getRefreshToken() ?: return null

            // Direct OkHttp call to prevent circular Retrofit dependency
            val refreshPayload = json.encodeToString(TokenRefreshRequest.serializer(), TokenRefreshRequest(refreshToken))
            val refreshRequest = Request.Builder()
                .url(response.request.url.newBuilder().encodedPath("/api/v1/auth/refresh").build())
                .post(refreshPayload.toRequestBody("application/json".toMediaType()))
                .build()

            val client = OkHttpClient()
            try {
                val refreshResponse = client.newCall(refreshRequest).execute()
                if (refreshResponse.isSuccessful) {
                    val bodyString = refreshResponse.body?.string() ?: return null
                    val authResponse = json.decodeFromString(AuthResponse.serializer(), bodyString)

                    sessionManager.saveTokens(authResponse.accessToken, authResponse.refreshToken)

                    return response.request.newBuilder()
                        .header("Authorization", "Bearer ${authResponse.accessToken}")
                        .build()
                } else {
                    // Refresh token expired or revoked - clear session
                    sessionManager.clearSession()
                    return null
                }
            } catch (e: Exception) {
                return null
            }
        }
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }
}
