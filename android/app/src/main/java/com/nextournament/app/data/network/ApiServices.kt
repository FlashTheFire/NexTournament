package com.nextournament.app.data.network

import com.nextournament.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface AuthApiService {
    @POST("/api/v1/auth/google")
    suspend fun loginWithGoogle(@Body request: GoogleAuthRequest): Response<AuthResponse>

    @GET("/api/v1/auth/telegram-sync-status")
    suspend fun checkTelegramSyncStatus(@Query("token") token: String): Response<AuthResponse>

    @POST("/api/v1/auth/telegram-sync")
    suspend fun syncWithTelegram(@Body request: TelegramSyncRequest): Response<AuthResponse>

    @POST("/api/v1/auth/quick-login")
    suspend fun quickLogin(@Body request: QuickLoginRequest): Response<AuthResponse>

    @GET("/api/v1/user/profile")
    suspend fun getProfile(@Query("user_id") userId: Long? = null): Response<UserProfileDto>

    @PUT("/api/v1/user/game-profile")
    suspend fun updateGameProfile(@Body request: UpdateGameProfileRequest): Response<UserProfileDto>
}

interface TournamentApiService {
    @GET("/api/v1/tournaments")
    suspend fun getTournaments(
        @Query("game_id") gameId: String? = null,
        @Query("status") status: String? = null
    ): Response<List<TournamentDto>>

    @GET("/api/v1/tournaments/{id}")
    suspend fun getTournamentDetail(@Path("id") tournamentId: Long): Response<TournamentDetailDto>

    @POST("/api/v1/tournaments/{id}/seats/lock")
    suspend fun lockSeat(
        @Path("id") tournamentId: Long,
        @Body request: LockSeatRequest
    ): Response<LockSeatResponse>

    @POST("/api/v1/tournaments/{id}/join")
    suspend fun joinTournament(
        @Path("id") tournamentId: Long,
        @Body request: JoinTournamentRequest
    ): Response<JoinTournamentResponse>
}

interface WalletApiService {
    @GET("/api/v1/wallet/summary")
    suspend fun getWalletSummary(@Query("user_id") userId: Long? = null): Response<WalletSummaryDto>

    @POST("/api/v1/wallet/deposit/upi")
    suspend fun initiateUpiDeposit(@Body request: UpiDepositRequest): Response<UpiDepositResponse>

    @POST("/api/v1/wallet/deposit/crypto")
    suspend fun initiateCryptoDeposit(@Body request: CryptoDepositRequest): Response<CryptoDepositResponse>

    @POST("/api/v1/wallet/withdraw")
    suspend fun requestWithdrawal(@Body request: WithdrawalRequest): Response<WithdrawalResponse>
}

interface AdminApiService {
    @POST("/api/v1/admin/tournaments")
    suspend fun createTournament(@Body request: AdminCreateTournamentRequest): Response<AdminActionResponse>

    @POST("/api/v1/admin/tournaments/{id}/credentials")
    suspend fun setCredentials(
        @Path("id") tournamentId: Long,
        @Body request: AdminSetCredentialsRequest
    ): Response<AdminActionResponse>

    @POST("/api/v1/admin/users/adjust-balance")
    suspend fun adjustBalance(@Body request: AdminAdjustBalanceRequest): Response<AdminAdjustBalanceResponse>
}

interface AppVersionApiService {
    @GET("/api/v1/app/version-check")
    suspend fun checkVersion(
        @Query("platform") platform: String = "android",
        @Query("version_code") versionCode: Int
    ): Response<VersionCheckResponse>
}
