package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SendOtpRequest(
    @SerialName("phone_number") val phoneNumber: String,
    @SerialName("method") val method: String = "sms" // "sms" or "whatsapp"
)

@Serializable
data class VerifyOtpRequest(
    @SerialName("phone_number") val phoneNumber: String,
    @SerialName("otp_code") val otpCode: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("device_model") val deviceModel: String
)

@Serializable
data class TelegramSyncRequest(
    @SerialName("sync_code") val syncCode: String,
    @SerialName("device_id") val deviceId: String
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
    @SerialName("expires_in") val expiresIn: Long,
    @SerialName("user") val user: UserProfileDto
)
