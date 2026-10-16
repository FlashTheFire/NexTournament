package com.nextournament.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.data.local.TournamentEntity
import com.nextournament.app.data.local.TransactionEntity
import com.nextournament.app.data.local.UserEntity
import com.nextournament.app.data.model.SeatSlot
import com.nextournament.app.data.model.SeatSlotStatus
import com.nextournament.app.data.model.SquadCluster
import com.nextournament.app.data.model.UpdateCheckResponse
import com.nextournament.app.data.ota.DownloadState
import com.nextournament.app.data.ota.OtaUpdateManager
import com.nextournament.app.data.payment.UpiAppInfo
import com.nextournament.app.data.security.AntiCheatManager
import com.nextournament.app.data.security.DeviceIntegrityTier
import com.nextournament.app.data.security.DeviceSecurityReport
import com.nextournament.app.data.security.SessionManager
import com.nextournament.app.ui.components.*
import com.nextournament.app.ui.theme.*
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var antiCheatManager: AntiCheatManager

    @Inject
    lateinit var otaUpdateManager: OtaUpdateManager

    @Inject
    lateinit var sessionManager: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 1. Startup Gatekeeper: Anti-Cheat Hardware Audit
        val securityReport = antiCheatManager.evaluateDeviceIntegrity()

        setContent {
            NexTournamentTheme {
                MainAppOrchestrator(
                    securityReport = securityReport,
                    otaUpdateManager = otaUpdateManager,
                    sessionManager = sessionManager
                )
            }
        }
    }
}

@Composable
fun MainAppOrchestrator(
    securityReport: DeviceSecurityReport?,
    otaUpdateManager: OtaUpdateManager?,
    sessionManager: SessionManager?
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    // Navigation and Tab State
    var currentTab by remember { mutableStateOf(AppNavTab.TOURNAMENTS) }

    // Modals and Workflow State
    var selectedTournamentForRules by remember { mutableStateOf<TournamentEntity?>(null) }
    var activeTournamentForSeats by remember { mutableStateOf<TournamentEntity?>(null) }
    var selectedSeatForCheckout by remember { mutableStateOf<SeatSlot?>(null) }
    var activeRoomVaultTournament by remember { mutableStateOf<TournamentEntity?>(null) }

    // Financial Modals State
    var showUpiDepositModal by remember { mutableStateOf(false) }
    var showCryptoDepositModal by remember { mutableStateOf(false) }
    var showWithdrawalDrawer by remember { mutableStateOf(false) }

    // OCR Scorecard Proof Modal State
    var showScorecardModal by remember { mutableStateOf(false) }

    // Anti-Cheat & OTA Update States
    var showAntiCheatModal by remember {
        mutableStateOf(
            securityReport?.tier == DeviceIntegrityTier.ROOTED ||
            securityReport?.tier == DeviceIntegrityTier.HOOK_DETECTED ||
            securityReport?.tier == DeviceIntegrityTier.EMULATOR
        )
    }
    var updateResponse by remember { mutableStateOf<UpdateCheckResponse?>(null) }
    var downloadState by remember { mutableStateOf<DownloadState>(DownloadState.Idle) }
    var isFlexibleBannerDismissed by remember { mutableStateOf(false) }

    // User State
    var currentUser by remember {
        mutableStateOf(
            UserEntity(
                userId = 98234L,
                username = "GhostSniperX",
                firstName = "Harsh",
                role = "PLAYER",
                gameBalance = 600.0,
                winBalance = 1850.0,
                bonusBalance = 0.0,
                phoneNumber = "+91 98765 43210",
                inGameName = "FlashFire99",
                freeFireUid = "982341209",
                bgmiId = "5192830192",
                dailyStreak = 5,
                verificationLevel = 1,
                isVerified = true
            )
        )
    }

    // Sample Transaction History
    val sampleTransactions = remember {
        listOf(
            TransactionEntity(
                id = 501L,
                type = "MATCH_WINNING_PRIZE",
                amount = 1200.0,
                balanceType = "WIN",
                description = "1st Place Winner - Bermuda Masters #41",
                referenceId = "WIN-98214",
                status = "COMPLETED",
                createdAt = "Today, 14:32"
            ),
            TransactionEntity(
                id = 502L,
                type = "UPI_DEPOSIT",
                amount = 500.0,
                balanceType = "GAME",
                description = "Google Pay Instant Top-up",
                referenceId = "UPI-67290",
                status = "COMPLETED",
                createdAt = "Yesterday, 19:10"
            ),
            TransactionEntity(
                id = 503L,
                type = "TOURNAMENT_ENTRY_FEE",
                amount = 50.0,
                balanceType = "GAME",
                description = "Entry Slot #7 - Bermuda Masters #42",
                referenceId = "ENTRY-10492",
                status = "COMPLETED",
                createdAt = "Today, 15:45"
            )
        )
    }

    // Sample Installed UPI Apps for Indian payments
    val mockUpiApps = remember {
        listOf(
            UpiAppInfo("Google Pay", "com.google.android.apps.nbu.paisa.user", null, true),
            UpiAppInfo("PhonePe", "com.phonepe.app", null, true),
            UpiAppInfo("Paytm", "net.one97.paytm", null, true),
            UpiAppInfo("CRED", "com.dreamplug.androidapp", null, true)
        )
    }

    // Live Tournaments Catalog Cache
    val sampleTournaments = remember {
        listOf(
            TournamentEntity(
                id = 101L,
                title = "Bermuda Masters Series #42 [Squad]",
                gameId = "Free Fire",
                teamFormat = "SQUAD",
                mapName = "Bermuda",
                entryFee = 50.0,
                prizePool = 2000.0,
                perKillBounty = 15.0,
                totalSlots = 48,
                filledSlots = 38,
                startTimeEpoch = System.currentTimeMillis() + 900_000L, // T-15m
                status = "OPEN",
                roomId = "8920194",
                roomPassword = "NEX@FIRE_78"
            ),
            TournamentEntity(
                id = 102L,
                title = "Purgatory Survival Solo Clash",
                gameId = "Free Fire",
                teamFormat = "SOLO",
                mapName = "Purgatory",
                entryFee = 25.0,
                prizePool = 1000.0,
                perKillBounty = 20.0,
                totalSlots = 48,
                filledSlots = 44,
                startTimeEpoch = System.currentTimeMillis() + 3_600_000L,
                status = "OPEN"
            ),
            TournamentEntity(
                id = 103L,
                title = "Erangel Showdown Blitz [Duo]",
                gameId = "BGMI",
                teamFormat = "DUO",
                mapName = "Erangel",
                entryFee = 100.0,
                prizePool = 4500.0,
                perKillBounty = 30.0,
                totalSlots = 100,
                filledSlots = 72,
                startTimeEpoch = System.currentTimeMillis() + 1_800_000L,
                status = "OPEN",
                roomId = "9940129",
                roomPassword = "BGMI_ALPHA"
            ),
            TournamentEntity(
                id = 104L,
                title = "Ascent Custom 5v5 Spike Rush",
                gameId = "Valorant",
                teamFormat = "SQUAD",
                mapName = "Ascent",
                entryFee = 0.0,
                prizePool = 1000.0,
                perKillBounty = 0.0,
                totalSlots = 10,
                filledSlots = 8,
                startTimeEpoch = System.currentTimeMillis() + 7_200_000L,
                status = "OPEN"
            )
        )
    }

    // Cinema Seating Clusters Generator
    val squadClusters = remember(activeTournamentForSeats) {
        val totalSquads = (activeTournamentForSeats?.totalSlots ?: 48) / 4
        (1..totalSquads).map { squadNum ->
            val startSlot = (squadNum - 1) * 4 + 1
            SquadCluster(
                teamNumber = squadNum,
                teamName = "Squad #$squadNum",
                slots = (startSlot until startSlot + 4).map { slotNum ->
                    val isBooked = slotNum % 3 == 0 || slotNum % 7 == 0
                    SeatSlot(
                        slotNumber = slotNum,
                        teamNumber = squadNum,
                        role = if (slotNum == startSlot) "LEADER" else "MEMBER",
                        status = if (isBooked) SeatSlotStatus.BOOKED else SeatSlotStatus.AVAILABLE,
                        occupiedByUserId = if (isBooked) 1000L + slotNum else null,
                        occupiedByIgn = if (isBooked) "Player_$slotNum" else null
                    )
                }
            )
        }
    }

    Scaffold(
        containerColor = ObsidianBlack,
        topBar = {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SlateBackground)
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "NEXTOURNAMENT",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        color = CyberAmber,
                        fontSize = 17.sp,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        text = "ESPORTS TOURNAMENT PLATFORM",
                        fontFamily = ChakraPetch,
                        fontSize = 10.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    CyberBadge(
                        text = "₹%.0f".format(currentUser.walletBalance),
                        color = CyberEmerald,
                        backgroundColor = SlateElevated
                    )
                }
            }
        },
        bottomBar = {
            BottomHudNavigationBar(
                currentTab = currentTab,
                onTabSelected = { currentTab = it },
                onOcrCameraClick = { showScorecardModal = true }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (currentTab) {
                // Tab 1: Tournaments Catalog & Match Discovery
                AppNavTab.TOURNAMENTS -> {
                    TournamentCatalogScreen(
                        tournaments = sampleTournaments,
                        onTournamentClick = { tournament ->
                            selectedTournamentForRules = tournament
                        }
                    )
                }

                // Tab 2: Dual-Currency Wallet & Payments Engine
                AppNavTab.WALLET -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(ObsidianBlack)
                    ) {
                        // Wallet Balance Top Header
                        Card(
                            shape = CutCornerCard,
                            colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
                            border = BorderStroke(BrutalistBorderThin, SlateElevated),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "DUAL-CURRENCY ESPORTS WALLET",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    color = ElectricBlue
                                )

                                Spacer(modifier = Modifier.height(10.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Column {
                                        Text("TOTAL BALANCE", fontFamily = InterFont, fontSize = 10.sp, color = Color.White.copy(alpha = 0.5f))
                                        Text("₹%.2f".format(currentUser.walletBalance), fontFamily = OrbitronFont, fontWeight = FontWeight.Bold, fontSize = 20.sp, color = CyberAmber)
                                    }
                                    Column(horizontalAlignment = Alignment.End) {
                                        Text("WITHDRAWABLE WINNINGS", fontFamily = InterFont, fontSize = 10.sp, color = Color.White.copy(alpha = 0.5f))
                                        Text("₹%.2f".format(currentUser.winningsBalance), fontFamily = OrbitronFont, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = CyberEmerald)
                                    }
                                }

                                Spacer(modifier = Modifier.height(14.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    CyberActionButton(
                                        text = "+ UPI TOP-UP",
                                        onClick = { showUpiDepositModal = true },
                                        modifier = Modifier.weight(1f),
                                        iconRes = R.drawable.ic_arrow_downward_sharp
                                    )
                                    CyberActionButton(
                                        text = "+ USDT CRYPTO",
                                        onClick = { showCryptoDepositModal = true },
                                        modifier = Modifier.weight(1f),
                                        iconRes = R.drawable.ic_crypto_usdt
                                    )
                                    OutlinedButton(
                                        onClick = { showWithdrawalDrawer = true },
                                        shape = CutCornerButton,
                                        border = BorderStroke(BrutalistBorderThin, CyberEmerald),
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = CyberEmerald),
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("PAYOUT", fontFamily = ChakraPetch, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                                    }
                                }
                            }
                        }

                        // Filterable Transaction History
                        TransactionHistoryScreen(
                            transactions = sampleTransactions,
                            onBackClick = { currentTab = AppNavTab.TOURNAMENTS },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                // Tab 3: Verified Player Profile & Career Stats
                AppNavTab.PROFILE -> {
                    PlayerProfileScreen(
                        user = currentUser,
                        onSaveGameProfile = { game, uid, ign ->
                            Toast.makeText(context, "Saved $game Profile: $ign ($uid)", Toast.LENGTH_SHORT).show()
                        },
                        onSyncTelegramClick = {
                            Toast.makeText(context, "Telegram Sync Token: #NEX-${System.currentTimeMillis() % 100000}", Toast.LENGTH_LONG).show()
                        },
                        onBackClick = { currentTab = AppNavTab.TOURNAMENTS }
                    )
                }
            }

            // MODAL 1: FairPlay Tournament Rules Drawer
            selectedTournamentForRules?.let { tournament ->
                TournamentRulesDrawer(
                    tournamentTitle = tournament.title,
                    game = tournament.game,
                    format = tournament.format,
                    onAccept = {
                        activeTournamentForSeats = tournament
                        selectedTournamentForRules = null
                    },
                    onDismiss = { selectedTournamentForRules = null }
                )
            }

            // MODAL 2: Cinema Seating Matrix & 120s Lottie Countdown
            activeTournamentForSeats?.let { tournament ->
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(ObsidianBlack)
                ) {
                    CinemaSeatGrid(
                        squadClusters = squadClusters,
                        selectedSlotNumber = selectedSeatForCheckout?.slotNumber,
                        onSlotClick = { slot ->
                            if (slot.status == SeatSlotStatus.AVAILABLE) {
                                selectedSeatForCheckout = slot
                            }
                        }
                    )
                }
            }

            // MODAL 3: Seat Checkout Drawer
            selectedSeatForCheckout?.let { slot ->
                activeTournamentForSeats?.let { tournament ->
                    SeatCheckoutDrawer(
                        selectedSlot = slot,
                        entryFee = tournament.entryFee,
                        walletBalance = currentUser.walletBalance,
                        remainingSeconds = 120,
                        onConfirmPurchase = {
                            // Deduct balance and confirm seat
                            currentUser = currentUser.copy(
                                gameBalance = (currentUser.gameBalance - tournament.entryFee).coerceAtLeast(0.0)
                            )
                            selectedSeatForCheckout = null
                            activeTournamentForSeats = null
                            activeRoomVaultTournament = tournament
                            Toast.makeText(context, "Seat #${slot.slotNumber} Booked Successfully!", Toast.LENGTH_SHORT).show()
                        },
                        onTopUpWallet = {
                            showUpiDepositModal = true
                        },
                        onCancelReservation = {
                            selectedSeatForCheckout = null
                        }
                    )
                }
            }

            // MODAL 4: Secure T-15m Room Key Vault (Dynamic FLAG_SECURE + Masked Clipboard)
            activeRoomVaultTournament?.let { tournament ->
                RoomVaultDialog(
                    game = tournament.game,
                    roomId = tournament.roomId ?: "8920194",
                    roomPassword = tournament.roomPassword ?: "NEX@FIRE_78",
                    isUnlocked = true,
                    unlockCountdownSeconds = 0,
                    onDismiss = { activeRoomVaultTournament = null }
                )
            }

            // MODAL 5: High-Conversion UPI Deposit Dialog
            if (showUpiDepositModal) {
                UpiDepositDialog(
                    amount = 500.0,
                    merchantVpa = "nextournament@icici",
                    merchantName = "NexTournament Esports",
                    installedUpiApps = mockUpiApps,
                    onSelectUpiApp = { app ->
                        Toast.makeText(context, "Opening ${app.appName}...", Toast.LENGTH_SHORT).show()
                        showUpiDepositModal = false
                    },
                    onSubmitUtr = { utr ->
                        currentUser = currentUser.copy(gameBalance = currentUser.gameBalance + 500.0)
                        showUpiDepositModal = false
                        Toast.makeText(context, "UTR $utr verified! ₹500 credited.", Toast.LENGTH_LONG).show()
                    },
                    onDismiss = { showUpiDepositModal = false }
                )
            }

            // MODAL 6: Multi-Chain Crypto USDT Deposit Dialog
            if (showCryptoDepositModal) {
                CryptoDepositDialog(
                    trc20Address = "TJn8uK9rD3zV1vL7tY6aX2qW5eP4mB8kC9",
                    bep20Address = "0x71C836622F88219F3CE47B91F70C2a8eF92C3D7B",
                    onDismiss = { showCryptoDepositModal = false }
                )
            }

            // MODAL 7: Tiered Instant Withdrawal Drawer
            if (showWithdrawalDrawer) {
                WithdrawalDrawer(
                    winningsBalance = currentUser.winningsBalance,
                    dailyInstantLimit = 2000.0,
                    onRequestWithdrawal = { amount, method, destination ->
                        currentUser = currentUser.copy(
                            winBalance = currentUser.winBalance - amount
                        )
                        showWithdrawalDrawer = false
                        Toast.makeText(context, "₹$amount Payout initiated via $method to $destination", Toast.LENGTH_LONG).show()
                    },
                    onCancel = { showWithdrawalDrawer = false }
                )
            }

            // MODAL 8: Native OCR Scorecard Submission Dialog
            if (showScorecardModal) {
                ScorecardSubmissionDialog(
                    tournamentId = "ff_bermuda_squad_01",
                    tournamentTitle = "Bermuda Masters Series #42 [Squad]",
                    game = "Free Fire MAX",
                    onSubmitProof = { rank, kills, uri ->
                        showScorecardModal = false
                        Toast.makeText(context, "Scorecard Submitted (Rank #$rank, $kills Kills). FairPlay audit underway!", Toast.LENGTH_LONG).show()
                    },
                    onDismiss = { showScorecardModal = false }
                )
            }

            // SYSTEM 1: Hardware Anti-Cheat Violation Modal
            if (showAntiCheatModal && securityReport != null) {
                AntiCheatViolationDialog(
                    securityReport = securityReport,
                    onDismissOrAcknowledge = { showAntiCheatModal = false }
                )
            }

            // SYSTEM 2: Critical Forced In-App OTA Update Modal
            updateResponse?.let { info ->
                if (info.isForced) {
                    ForcedUpdateDialog(
                        updateInfo = info,
                        downloadState = downloadState,
                        onStartDownload = {
                            coroutineScope.launch {
                                otaUpdateManager?.downloadApkWithProgress(info.apkUrl, info.apkSha256)?.collect { state ->
                                    downloadState = state
                                }
                            }
                        },
                        onInstallApk = {
                            (downloadState as? DownloadState.Success)?.let { success ->
                                otaUpdateManager?.promptInstallApk(success.apkFile)
                            }
                        }
                    )
                }
            }

            // SYSTEM 3: Ambient Flexible OTA Update Banner
            updateResponse?.let { info ->
                if (!info.isForced && !isFlexibleBannerDismissed) {
                    FlexibleUpdateBanner(
                        isVisible = true,
                        updateInfo = info,
                        onDownloadClick = {
                            coroutineScope.launch {
                                otaUpdateManager?.downloadApkWithProgress(info.apkUrl, info.apkSha256)?.collect { state ->
                                    downloadState = state
                                    if (state is DownloadState.Success) {
                                        otaUpdateManager.promptInstallApk(state.apkFile)
                                    }
                                }
                            }
                        },
                        onDismissClick = { isFlexibleBannerDismissed = true }
                    )
                }
            }
        }
    }
}
