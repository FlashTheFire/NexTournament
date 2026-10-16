package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class WalletSummaryDto(
    @SerialName("game_balance") val gameBalance: Double,
    @SerialName("win_balance") val winBalance: Double,
    @SerialName("total_balance") val totalBalance: Double,
    @SerialName("currency") val currency: String = "INR",
    @SerialName("recent_transactions") val recentTransactions: List<TransactionDto> = emptyList()
)

@Serializable
data class TransactionDto(
    @SerialName("id") val id: Long,
    @SerialName("type") val type: String, // "deposit", "withdrawal", "tournament_fee", "tournament_prize", "referral_bonus"
    @SerialName("amount") val amount: Double,
    @SerialName("balance_type") val balanceType: String, // "game_balance", "win_balance"
    @SerialName("description") val description: String,
    @SerialName("reference_id") val referenceId: String? = null,
    @SerialName("status") val status: String = "completed",
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class UpiDepositRequest(
    @SerialName("amount") val amount: Double
)

@Serializable
data class UpiDepositResponse(
    @SerialName("deposit_id") val depositId: Long,
    @SerialName("upi_intent_url") val upiIntentUrl: String,
    @SerialName("qr_payload") val qrPayload: String,
    @SerialName("amount") val amount: Double,
    @SerialName("expires_in_seconds") val expiresInSeconds: Int = 900 // 15 mins
)

@Serializable
data class CryptoDepositRequest(
    @SerialName("currency") val currency: String = "USDT", // USDT, TRX, LTC, BTC
    @SerialName("network") val network: String = "TRC20"
)

@Serializable
data class CryptoDepositResponse(
    @SerialName("pay_address") val payAddress: String,
    @SerialName("currency") val currency: String,
    @SerialName("network") val network: String,
    @SerialName("qr_code_url") val qrCodeUrl: String,
    @SerialName("expires_at") val expiresAt: String
)

@Serializable
data class WithdrawalRequest(
    @SerialName("amount") val amount: Double,
    @SerialName("method") val method: String, // "upi" or "crypto"
    @SerialName("payout_address") val payoutAddress: String // UPI ID (VPA) or Crypto Wallet Address
)

@Serializable
data class WithdrawalResponse(
    @SerialName("withdrawal_id") val withdrawalId: Long,
    @SerialName("status") val status: String = "pending",
    @SerialName("message") val message: String
)
