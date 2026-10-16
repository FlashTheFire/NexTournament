package com.nextournament.app.data.network

import com.nextournament.app.data.security.AppSecurityGatekeeper
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
        val path = originalRequest.url.encodedPath

        // Generate 3-Tier Security Tokens
        val appKey = AppSecurityGatekeeper.getStaticAppKey()
        val timeNonce = AppSecurityGatekeeper.generateReversedTimingNonce()
        val signature = AppSecurityGatekeeper.computeHmacSignature(originalRequest.method, path, timeNonce)
        val token = sessionManager.getAccessToken()

        val requestBuilder = originalRequest.newBuilder()
            .header("X-Nex-App-Key", appKey)
            .header("X-Nex-Time-Nonce", timeNonce)
            .header("X-Nex-Signature", signature)
            .header("X-Device-ID", sessionManager.getOrCreateDeviceId())

        if (!token.isNullOrBlank()) {
            requestBuilder.header("Authorization", "Bearer $token")
        }

        return chain.proceed(requestBuilder.build())
    }
}
