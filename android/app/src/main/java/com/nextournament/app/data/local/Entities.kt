package com.nextournament.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.nextournament.app.data.model.TournamentDto
import com.nextournament.app.data.model.TransactionDto
import com.nextournament.app.data.model.UserProfileDto

@Entity(tableName = "tournaments")
data class TournamentEntity(
    @PrimaryKey val id: Long,
    val title: String,
    val gameId: String = "Free Fire",
    val matchType: String = "Battle Royale",
    val teamFormat: String = "SQUAD",
    val mapName: String = "Bermuda",
    val entryFee: Double = 0.0,
    val prizePool: Double = 0.0,
    val perKillBounty: Double = 0.0,
    val totalSlots: Int = 48,
    val filledSlots: Int = 0,
    val status: String = "OPEN",
    val startTime: String = "",
    val gunAttributes: Boolean = false,
    val allowsEmulator: Boolean = false,
    val roomId: String? = null,
    val roomPassword: String? = null,
    val startTimeEpoch: Long = 0L
) {
    val game: String get() = gameId
    val format: String get() = teamFormat
    val map: String get() = mapName
    val maxSlots: Int get() = totalSlots

    fun toDto(): TournamentDto = TournamentDto(
        id = id,
        title = title,
        gameId = gameId,
        matchType = matchType,
        teamFormat = teamFormat,
        mapName = mapName,
        entryFee = entryFee,
        prizePool = prizePool,
        perKillBounty = perKillBounty,
        totalSlots = totalSlots,
        filledSlots = filledSlots,
        status = status,
        startTime = startTime,
        gunAttributes = gunAttributes,
        allowsEmulator = allowsEmulator
    )

    companion object {
        fun fromDto(dto: TournamentDto): TournamentEntity = TournamentEntity(
            id = dto.id,
            title = dto.title,
            gameId = dto.gameId,
            matchType = dto.matchType,
            teamFormat = dto.teamFormat,
            mapName = dto.mapName,
            entryFee = dto.entryFee,
            prizePool = dto.prizePool,
            perKillBounty = dto.perKillBounty,
            totalSlots = dto.totalSlots,
            filledSlots = dto.filledSlots,
            status = dto.status,
            startTime = dto.startTime,
            gunAttributes = dto.gunAttributes,
            allowsEmulator = dto.allowsEmulator
        )
    }
}

@Entity(tableName = "user_profile")
data class UserEntity(
    @PrimaryKey val userId: Long,
    val telegramId: Long? = null,
    val username: String = "Gamer",
    val firstName: String = "",
    val role: String = "PLAYER",
    val gameBalance: Double = 0.0,
    val winBalance: Double = 0.0,
    val bonusBalance: Double = 0.0,
    val phoneNumber: String = "+91 98765 43210",
    val inGameName: String? = null,
    val freeFireUid: String? = null,
    val bgmiId: String? = null,
    val dailyStreak: Int = 1,
    val verificationLevel: Int = 1,
    val isVerified: Boolean = true
) {
    val id: Long get() = userId
    val walletBalance: Double get() = gameBalance + winBalance
    val winningsBalance: Double get() = winBalance

    fun toDto(): UserProfileDto = UserProfileDto(
        userId = userId,
        telegramId = telegramId,
        username = username,
        firstName = firstName,
        role = role,
        gameBalance = gameBalance,
        winBalance = winBalance
    )

    companion object {
        fun fromDto(dto: UserProfileDto): UserEntity = UserEntity(
            userId = dto.userId,
            telegramId = dto.telegramId,
            username = dto.username ?: "Gamer",
            firstName = dto.firstName,
            role = dto.role,
            gameBalance = dto.gameBalance,
            winBalance = dto.winBalance
        )
    }
}

@Entity(tableName = "transactions")
data class TransactionEntity(
    @PrimaryKey val id: Long,
    val type: String,
    val amount: Double,
    val balanceType: String,
    val description: String,
    val referenceId: String?,
    val status: String,
    val createdAt: String
) {
    val paymentMethod: String get() = balanceType
    val timestamp: String get() = createdAt

    fun toDto(): TransactionDto = TransactionDto(
        id = id,
        type = type,
        amount = amount,
        balanceType = balanceType,
        description = description,
        referenceId = referenceId,
        status = status,
        createdAt = createdAt
    )

    companion object {
        fun fromDto(dto: TransactionDto): TransactionEntity = TransactionEntity(
            id = dto.id,
            type = dto.type,
            amount = dto.amount,
            balanceType = dto.balanceType,
            description = dto.description,
            referenceId = dto.referenceId,
            status = dto.status,
            createdAt = dto.createdAt
        )
    }
}
