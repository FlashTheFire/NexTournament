package com.nextournament.app.data.network

import com.nextournament.app.data.security.SessionManager
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val sessionManager: SessionManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()

        // Skip auth header for open endpoints like login, OTP, version check
        val path = originalRequest.url.encodedPath
        if (path.contains("/auth/phone/") || path.contains("/auth/refresh") || path.contains("/app/version-check")) {
            return chain.proceed(originalRequest)
        }

        val token = sessionManager.getAccessToken()
        val requestBuilder = originalRequest.newBuilder()
            .header("X-Device-ID", sessionManager.getOrCreateDeviceId())

        if (!token.isNullOrBlank()) {
            requestBuilder.header("Authorization", "Bearer $token")
        }

        return chain.proceed(requestBuilder.build())
    }
}
