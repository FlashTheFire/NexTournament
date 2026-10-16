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
    val teamNumber: Int,
    val role: String, // "LEADER", "MEMBER"
    val status: SeatSlotStatus = SeatSlotStatus.AVAILABLE,
    val occupiedByUserId: Long? = null,
    val occupiedByIgn: String? = null,
    val lockExpiresAtEpochMs: Long? = null
)

@Serializable
data class SquadCluster(
    val teamNumber: Int,
    val teamName: String,
    val slots: List<SeatSlot>
)
