package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserProfileDto(
    @SerialName("user_id") val userId: Long,
    @SerialName("telegram_id") val telegramId: Long? = null,
    @SerialName("username") val username: String? = null,
    @SerialName("first_name") val firstName: String,
    @SerialName("role") val role: String = "user",
    @SerialName("game_balance") val gameBalance: Double = 0.0,
    @SerialName("win_balance") val winBalance: Double = 0.0,
    @SerialName("game_profiles") val gameProfiles: List<GameAccountDto> = emptyList(),
    @SerialName("created_at") val createdAt: String? = null
)

@Serializable
data class GameAccountDto(
    @SerialName("game_id") val gameId: String, // "free_fire", "bgmi", "codm", "valorant"
    @SerialName("in_game_id") val inGameId: String,
    @SerialName("in_game_name") val inGameName: String,
    @SerialName("level") val level: Int = 1,
    @SerialName("is_verified") val isVerified: Boolean = false
)

@Serializable
data class UpdateGameProfileRequest(
    @SerialName("game_id") val gameId: String,
    @SerialName("in_game_id") val inGameId: String,
    @SerialName("in_game_name") val inGameName: String
)
