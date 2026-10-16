package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class GoogleAuthRequest(
    @SerialName("email") val email: String,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    @SerialName("id_token") val idToken: String? = null,
    @SerialName("device_id") val deviceId: String? = null
)

@Serializable
data class TelegramSyncRequest(
    @SerialName("sync_code") val syncCode: String,
    @SerialName("device_id") val deviceId: String? = null
)

@Serializable
data class TokenRefreshRequest(
    @SerialName("refresh_token") val refreshToken: String
)

@Serializable
data class QuickLoginRequest(
    @SerialName("user_id") val userId: Long
)

@Serializable
data class AuthResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "Bearer",
    @SerialName("expires_in") val expiresIn: Long = 2592000L,
    @SerialName("user") val user: UserProfileDto
)
