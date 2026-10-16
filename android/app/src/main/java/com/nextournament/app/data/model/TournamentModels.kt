package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TournamentDto(
    @SerialName("id") val id: Long,
    @SerialName("title") val title: String,
    @SerialName("game_id") val gameId: String = "free_fire",
    @SerialName("match_type") val matchType: String = "battle_royale",
    @SerialName("team_format") val teamFormat: String = "squad", // "solo", "duo", "squad", "6v6"
    @SerialName("map_name") val mapName: String = "Bermuda",
    @SerialName("entry_fee") val entryFee: Double = 0.0,
    @SerialName("prize_pool") val prizePool: Double = 0.0,
    @SerialName("per_kill_bounty") val perKillBounty: Double = 0.0,
    @SerialName("total_slots") val totalSlots: Int = 48,
    @SerialName("filled_slots") val filledSlots: Int = 0,
    @SerialName("status") val status: String = "open", // "open", "full", "credentials_sent", "in_progress", "completed", "cancelled"
    @SerialName("start_time") val startTime: String,
    @SerialName("gun_attributes") val gunAttributes: Boolean = false,
    @SerialName("allows_emulator") val allowsEmulator: Boolean = false
)

@Serializable
data class TournamentDetailDto(
    @SerialName("tournament") val tournament: TournamentDto,
    @SerialName("first_prize") val firstPrize: Double = 0.0,
    @SerialName("second_prize") val secondPrize: Double = 0.0,
    @SerialName("third_prize") val thirdPrize: Double = 0.0,
    @SerialName("rules") val rules: String = "1. Mobile devices only.\n2. No teaming up.\n3. Room ID released at T-15m.",
    @SerialName("seats") val seats: List<SeatStateDto> = emptyList(),
    @SerialName("room_id") val roomId: String? = null,
    @SerialName("room_password") val roomPassword: String? = null
)

@Serializable
data class SeatStateDto(
    @SerialName("slot_number") val slotNumber: Int,
    @SerialName("status") val status: String, // "available", "locked", "booked"
    @SerialName("user_id") val userId: Long? = null,
    @SerialName("in_game_name") val inGameName: String? = null,
    @SerialName("lock_expires_in_seconds") val lockExpiresInSeconds: Int? = null
)

@Serializable
data class LockSeatRequest(
    @SerialName("slot_number") val slotNumber: Int
)

@Serializable
data class LockSeatResponse(
    @SerialName("success") val success: Boolean,
    @SerialName("slot_number") val slotNumber: Int,
    @SerialName("lock_ttl_seconds") val lockTtlSeconds: Int = 120,
    @SerialName("message") val message: String? = null
)

@Serializable
data class JoinTournamentRequest(
    @SerialName("slot_number") val slotNumber: Int,
    @SerialName("game_id") val gameId: String,
    @SerialName("in_game_id") val inGameId: String,
    @SerialName("in_game_name") val inGameName: String
)

@Serializable
data class JoinTournamentResponse(
    @SerialName("success") val success: Boolean,
    @SerialName("slot_number") val slotNumber: Int,
    @SerialName("new_game_balance") val newGameBalance: Double,
    @SerialName("message") val message: String
)
