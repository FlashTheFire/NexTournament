package com.nextournament.app.data.model

import kotlinx.serialization.Serializable

enum class SeatSlotStatus {
    AVAILABLE,
    LOCKING_MUTEX,
    BOOKED,
    SELECTED_BY_ME
}

@Serializable
data class SeatSlot(
    val slotNumber: Int,
    val teamNumber: Int = 1,
    val role: String = "MEMBER", // "LEADER", "MEMBER"
    val status: SeatSlotStatus = SeatSlotStatus.AVAILABLE,
    val occupiedByUserId: Long? = null,
    val occupiedByIgn: String? = null,
    val lockExpiresAtEpochMs: Long? = null,
    val squadNumber: Int = teamNumber,
    val playerName: String? = occupiedByIgn
)

@Serializable
data class SquadCluster(
    val teamNumber: Int = 1,
    val teamName: String = "Squad #$teamNumber",
    val slots: List<SeatSlot> = emptyList(),
    val squadNumber: Int = teamNumber
)
