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
    val gameId: String,
    val matchType: String,
    val teamFormat: String,
    val mapName: String,
    val entryFee: Double,
    val prizePool: Double,
    val perKillBounty: Double,
    val totalSlots: Int,
    val filledSlots: Int,
    val status: String,
    val startTime: String,
    val gunAttributes: Boolean,
    val allowsEmulator: Boolean
) {
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
    val telegramId: Long?,
    val username: String?,
    val firstName: String,
    val role: String,
    val gameBalance: Double,
    val winBalance: Double
) {
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
            username = dto.username,
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
