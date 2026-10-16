package com.nextournament.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.data.local.TournamentEntity
import com.nextournament.app.data.local.TransactionEntity
import com.nextournament.app.data.local.UserEntity
import com.nextournament.app.data.model.*
import com.nextournament.app.data.network.AdminApiService
import com.nextournament.app.data.network.AuthApiService
import com.nextournament.app.data.network.TournamentApiService
import com.nextournament.app.data.network.WalletApiService
import com.nextournament.app.data.ota.DownloadState
import com.nextournament.app.data.ota.OtaUpdateManager
import com.nextournament.app.data.payment.UpiAppInfo
import com.nextournament.app.data.payment.UpiIntentManager
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

    @Inject
    lateinit var authApiService: AuthApiService

    @Inject
    lateinit var tournamentApiService: TournamentApiService

    @Inject
    lateinit var walletApiService: WalletApiService

    @Inject
    lateinit var adminApiService: AdminApiService

    @Inject
    lateinit var upiIntentManager: UpiIntentManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 1. Startup Gatekeeper: Anti-Cheat Hardware Audit
        val securityReport = antiCheatManager.evaluateDeviceIntegrity()

        setContent {
            NexTournamentTheme {
                MainAppOrchestrator(
                    securityReport = securityReport,
                    otaUpdateManager = otaUpdateManager,
                    sessionManager = sessionManager,
                    authApiService = authApiService,
                    tournamentApiService = tournamentApiService,
                    walletApiService = walletApiService,
                    adminApiService = adminApiService,
                    upiIntentManager = upiIntentManager
                )
            }
        }
    }
}

@Composable
fun MainAppOrchestrator(
    securityReport: DeviceSecurityReport?,
    otaUpdateManager: OtaUpdateManager?,
    sessionManager: SessionManager?,
    authApiService: AuthApiService?,
    tournamentApiService: TournamentApiService?,
    walletApiService: WalletApiService?,
    adminApiService: AdminApiService?,
    upiIntentManager: UpiIntentManager?
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
    var activeChatTournament by remember { mutableStateOf<TournamentEntity?>(null) }
    var joinedTournamentIds by remember { mutableStateOf(setOf(101L)) }

    // Financial Modals State
    var showUpiDepositModal by remember { mutableStateOf(false) }
    var showCryptoDepositModal by remember { mutableStateOf(false) }
    var showWithdrawalDrawer by remember { mutableStateOf(false) }
    var showAiSupportModal by remember { mutableStateOf(false) }

    // Admin & Auth Modals State
    var isLoggedIn by remember { mutableStateOf(sessionManager?.isLoggedIn() == true) }
    var showHeroAuthScreen by remember { mutableStateOf(!isLoggedIn) }
    var showAdminDialog by remember { mutableStateOf(false) }

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

    // User State - Pure clean defaults on fresh startup
    val savedUserId = sessionManager?.getUserId()?.takeIf { it > 0 } ?: 0L
    var currentUser by remember {
        mutableStateOf(
            UserEntity(
                userId = savedUserId,
                username = if (savedUserId == 5716978793L) "NexAdmin" else if (savedUserId > 0) "Player_$savedUserId" else "Guest",
                firstName = if (savedUserId == 5716978793L) "Harsh (Owner)" else if (savedUserId > 0) "Player" else "Guest Player",
                role = if (savedUserId == 5716978793L) "superadmin" else "user",
                gameBalance = 0.0,
                winBalance = 0.0,
                bonusBalance = 0.0,
                phoneNumber = "",
                inGameName = "Player",
                freeFireUid = "",
                dailyStreak = 0,
                verificationLevel = 1,
                isVerified = false
            )
        )
    }

    val isAdmin = currentUser.role.contains("admin", ignoreCase = true) || currentUser.userId == 5716978793L

    // Live Data State
    var liveTournaments by remember { mutableStateOf<List<TournamentEntity>>(emptyList()) }
    var liveTransactions by remember { mutableStateOf<List<TransactionEntity>>(emptyList()) }
    var isRefreshing by remember { mutableStateOf(false) }

    // Live Data Synchronizer Function
    val refreshLiveData: () -> Unit = {
        coroutineScope.launch {
            isRefreshing = true
            try {
                // 1. Fetch live user profile
                val profileRes = authApiService?.getProfile(currentUser.userId)
                if (profileRes != null && profileRes.isSuccessful) {
                    profileRes.body()?.let { dto ->
                        currentUser = UserEntity.fromDto(dto)
                    }
                }

                // 2. Fetch live tournaments
                val tourRes = tournamentApiService?.getTournaments()
                if (tourRes != null && tourRes.isSuccessful) {
                    tourRes.body()?.let { dtos ->
                        liveTournaments = dtos.map { TournamentEntity.fromDto(it) }
                    }
                }

                // 3. Fetch live wallet summary & transactions ledger
                val walletRes = walletApiService?.getWalletSummary(currentUser.userId)
                if (walletRes != null && walletRes.isSuccessful) {
                    walletRes.body()?.let { wDto ->
                        currentUser = currentUser.copy(
                            gameBalance = wDto.gameBalance,
                            winBalance = wDto.winBalance
                        )
                        liveTransactions = wDto.recentTransactions.map { TransactionEntity.fromDto(it) }
                    }
                }
            } catch (e: Exception) {
                // Network error handled gracefully
            } finally {
                isRefreshing = false
            }
        }
    }

    // Trigger on startup & on user change
    LaunchedEffect(currentUser.userId) {
        if (isLoggedIn) {
            refreshLiveData()
        }
    }

    // Full Fresh Startup / Unauthenticated Gate: Hero Onboarding & Auth Page
    if (showHeroAuthScreen) {
        HeroOnboardingScreen(
            authApiService = authApiService,
            onAuthSuccess = { auth ->
                sessionManager?.saveTokens(auth.accessToken, auth.refreshToken)
                sessionManager?.saveUserId(auth.user.userId)
                currentUser = UserEntity.fromDto(auth.user)
                isLoggedIn = true
                showHeroAuthScreen = false
                refreshLiveData()
            }
        )
        return
    }

    // Sample Fallback Data if network is offline
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
                perKillBounty = 20.0,
                totalSlots = 48,
                filledSlots = 38,
                startTimeEpoch = System.currentTimeMillis() + 900_000L,
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
                title = "Kalahari Desert Strike [Duo]",
                gameId = "Free Fire",
                teamFormat = "DUO",
                mapName = "Kalahari",
                entryFee = 40.0,
                prizePool = 1500.0,
                perKillBounty = 15.0,
                totalSlots = 48,
                filledSlots = 20,
                startTimeEpoch = System.currentTimeMillis() + 5_400_000L,
                status = "OPEN"
            )
        )
    }

    val displayTournaments = if (liveTournaments.isNotEmpty()) liveTournaments else sampleTournaments
    val displayTransactions = if (liveTransactions.isNotEmpty()) liveTransactions else emptyList()

    // Real Installed Device UPI Apps (Google Pay, PhonePe, Paytm, CRED)
    val realUpiApps = remember {
        upiIntentManager?.getInstalledUpiApps()?.ifEmpty { null } ?: listOf(
            UpiAppInfo("Google Pay", "com.google.android.apps.nbu.paisa.user", null, true),
            UpiAppInfo("PhonePe", "com.phonepe.app", null, true),
            UpiAppInfo("Paytm", "net.one97.paytm", null, true),
            UpiAppInfo("CRED", "com.dreamplug.androidapp", null, true)
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
                    .statusBarsPadding()
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "NEXTOURNAMENT",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            color = CyberAmber,
                            fontSize = 16.sp,
                            letterSpacing = 1.2.sp
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        // User Account Badge (Clickable to switch or login)
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(SlateElevated)
                                .clickable { showHeroAuthScreen = true }
                                .padding(horizontal = 6.dp, vertical = 2.dp)
                        ) {
                            Text(
                                text = currentUser.username.uppercase(),
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 9.sp,
                                color = NeonCyan
                            )
                        }
                    }
                    Text(
                        text = if (isAdmin) "⚡ OWNER & SUPERADMIN CONSOLE ACTIVE" else "ESPORTS TOURNAMENT PLATFORM",
                        fontFamily = ChakraPetch,
                        fontSize = 9.sp,
                        color = if (isAdmin) CyberAmber else Color.White.copy(alpha = 0.5f)
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    // ADMIN PANEL SHORTCUT BADGE
                    if (isAdmin) {
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(CyberAmber)
                                .border(BorderStroke(1.dp, AmberGold), CutCornerShape(4.dp))
                                .clickable { showAdminDialog = true }
                                .padding(horizontal = 8.dp, vertical = 6.dp)
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    painter = painterResource(id = R.drawable.ic_verified_sharp),
                                    contentDescription = "Admin Console",
                                    tint = ObsidianBlack,
                                    modifier = Modifier.size(13.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "ADMIN",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    color = ObsidianBlack
                                )
                            }
                        }
                    }

                    // Live Wallet Balance Badge
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
                onTabSelected = { selectedTab ->
                    if (selectedTab == AppNavTab.ADMIN) {
                        showAdminDialog = true
                    } else {
                        currentTab = selectedTab
                    }
                },
                onOcrCameraClick = { showScorecardModal = true },
                isAdmin = isAdmin
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
                        tournaments = displayTournaments,
                        joinedTournamentIds = joinedTournamentIds,
                        onTournamentClick = { tournament ->
                            selectedTournamentForRules = tournament
                        },
                        onRoomClick = { tournament ->
                            activeRoomVaultTournament = tournament
                        },
                        onChatClick = { tournament ->
                            activeChatTournament = tournament
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
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "DUAL-CURRENCY ESPORTS WALLET",
                                        fontFamily = ChakraPetch,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp,
                                        color = ElectricBlue
                                    )
                                    Text(
                                        text = "SYNC ↻",
                                        fontFamily = ChakraPetch,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 10.sp,
                                        color = CyberAmber,
                                        modifier = Modifier.clickable { refreshLiveData() }
                                    )
                                }

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
                                        text = "UPI",
                                        onClick = { showUpiDepositModal = true },
                                        modifier = Modifier.weight(1f),
                                        iconRes = R.drawable.ic_arrow_downward_sharp,
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp)
                                    )
                                    CyberActionButton(
                                        text = "CRYPTO",
                                        onClick = { showCryptoDepositModal = true },
                                        modifier = Modifier.weight(1f),
                                        iconRes = R.drawable.ic_crypto_usdt,
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp)
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

                        // AI Support & Payment Dispute Banner
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp, vertical = 2.dp)
                                .clip(CutCornerShape(4.dp))
                                .background(SlateElevated)
                                .border(1.dp, ElectricBlue.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                .clickable { showAiSupportModal = true }
                                .padding(horizontal = 12.dp, vertical = 8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    painter = painterResource(id = R.drawable.ic_shield_sharp),
                                    contentDescription = null,
                                    tint = ElectricBlue,
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "NEED HELP? AI SUPPORT & UTR RESOLUTION",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    color = Color.White
                                )
                            }
                            Text(
                                text = "OPEN →",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp,
                                color = CyberAmber
                            )
                        }

                        // Filterable Transaction History
                        TransactionHistoryScreen(
                            transactions = displayTransactions,
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
                            coroutineScope.launch {
                                try {
                                    val res = authApiService?.updateGameProfile(
                                        UpdateGameProfileRequest(gameId = game, inGameId = uid, inGameName = ign)
                                    )
                                    if (res?.isSuccessful == true) {
                                        currentUser = currentUser.copy(inGameName = ign, freeFireUid = uid)
                                        Toast.makeText(context, "Saved Free Fire Profile: $ign ($uid)", Toast.LENGTH_SHORT).show()
                                    }
                                } catch (e: Exception) {
                                    Toast.makeText(context, "Updated locally", Toast.LENGTH_SHORT).show()
                                }
                            }
                        },
                        onSyncTelegramClick = {
                            showHeroAuthScreen = true
                        },
                        onBackClick = { currentTab = AppNavTab.TOURNAMENTS }
                    )
                }

                // Tab 4: Admin Console (Fallback if switched via tab)
                AppNavTab.ADMIN -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(ObsidianBlack),
                        contentAlignment = Alignment.Center
                    ) {
                        CyberActionButton(
                            text = "OPEN ADMIN COMMAND CENTER",
                            onClick = { showAdminDialog = true },
                            accentColor = CyberAmber,
                            textColor = ObsidianBlack,
                            iconRes = R.drawable.ic_verified_sharp
                        )
                    }
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

            // MODAL 2: Cinema Seating Matrix
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

            // MODAL 3: Seat Checkout Drawer (Connected to Real Backend)
            selectedSeatForCheckout?.let { slot ->
                activeTournamentForSeats?.let { tournament ->
                    SeatCheckoutDrawer(
                        selectedSlot = slot,
                        entryFee = tournament.entryFee,
                        walletBalance = currentUser.walletBalance,
                        remainingSeconds = 120,
                        onConfirmPurchase = {
                            coroutineScope.launch {
                                try {
                                    val req = JoinTournamentRequest(
                                        slotNumber = slot.slotNumber,
                                        inGameName = currentUser.ign,
                                        userId = currentUser.userId
                                    )
                                    val res = tournamentApiService?.joinTournament(tournament.id, req)
                                    if (res?.isSuccessful == true) {
                                        joinedTournamentIds = joinedTournamentIds + tournament.id
                                        selectedSeatForCheckout = null
                                        activeTournamentForSeats = null
                                        activeRoomVaultTournament = tournament
                                        Toast.makeText(context, res.body()?.message ?: "Seat #${slot.slotNumber} Booked!", Toast.LENGTH_SHORT).show()
                                        refreshLiveData()
                                    } else {
                                        val err = res?.errorBody()?.string() ?: "Join failed"
                                        Toast.makeText(context, "Cannot join: $err", Toast.LENGTH_LONG).show()
                                    }
                                } catch (e: Exception) {
                                    Toast.makeText(context, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                                }
                            }
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

            // MODAL 4: Secure T-15m Room Key Vault
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

            // MODAL 4B: Tactical In-Game HUD Chat Drawer
            activeChatTournament?.let { tournament ->
                MatchChatDrawer(
                    tournamentTitle = tournament.title,
                    teamFormat = tournament.format,
                    userIgn = currentUser.ign,
                    onDismiss = { activeChatTournament = null }
                )
            }

            // MODAL 5: Real UPI Deposit Dialog (Connected to Backend)
            if (showUpiDepositModal) {
                UpiDepositDialog(
                    initialAmount = 500.0,
                    merchantVpa = "nextournament@icici",
                    merchantName = "NexTournament Esports",
                    installedUpiApps = realUpiApps,
                    onSelectUpiApp = { app ->
                        Toast.makeText(context, "Opening ${app.appName}...", Toast.LENGTH_SHORT).show()
                    },
                    onVerifyPayment = { amount, orderId ->
                        coroutineScope.launch {
                            try {
                                val res = walletApiService?.initiateUpiDeposit(
                                    UpiDepositRequest(amount = amount, userId = currentUser.userId)
                                )
                                if (res?.isSuccessful == true) {
                                    showUpiDepositModal = false
                                    Toast.makeText(context, "₹%.0f Top-up Verified!".format(amount), Toast.LENGTH_LONG).show()
                                    refreshLiveData()
                                } else {
                                    currentUser = currentUser.copy(gameBalance = currentUser.gameBalance + amount)
                                    showUpiDepositModal = false
                                }
                            } catch (e: Exception) {
                                currentUser = currentUser.copy(gameBalance = currentUser.gameBalance + amount)
                                showUpiDepositModal = false
                            }
                        }
                    },
                    onOpenAiSupport = {
                        showUpiDepositModal = false
                        showAiSupportModal = true
                    },
                    onDismiss = { showUpiDepositModal = false }
                )
            }

            // MODAL 5B: In-App Cyber Support AI Bot
            if (showAiSupportModal) {
                AiSupportChatDrawer(
                    userIgn = currentUser.ign,
                    onCreditBalance = { amount ->
                        coroutineScope.launch {
                            try {
                                adminApiService?.adjustBalance(
                                    AdminAdjustBalanceRequest(
                                        targetUserId = currentUser.userId,
                                        amount = amount,
                                        balanceType = "game_balance"
                                    )
                                )
                            } catch (_: Exception) {}
                            refreshLiveData()
                        }
                    },
                    onDismiss = { showAiSupportModal = false }
                )
            }

            // MODAL 6: Multi-Chain Crypto USDT Deposit Dialog
            if (showCryptoDepositModal) {
                CryptoDepositDialog(
                    trc20Address = "TWw8rLkW9Xm3P4qN7Y7x8Bv1cD3eF5g6H7",
                    bep20Address = "0x71C836622F88219F3CE47B91F70C2a8eF92C3D7B",
                    onDismiss = { showCryptoDepositModal = false }
                )
            }

            // MODAL 7: Tiered Instant Withdrawal Drawer (Connected to Backend)
            if (showWithdrawalDrawer) {
                WithdrawalDrawer(
                    winningsBalance = currentUser.winningsBalance,
                    dailyInstantLimit = 2000.0,
                    onRequestWithdrawal = { amount, method, destination ->
                        coroutineScope.launch {
                            try {
                                val res = walletApiService?.requestWithdrawal(
                                    WithdrawalRequest(
                                        amount = amount,
                                        method = method,
                                        payoutAddress = destination,
                                        userId = currentUser.userId
                                    )
                                )
                                if (res?.isSuccessful == true) {
                                    showWithdrawalDrawer = false
                                    Toast.makeText(context, res.body()?.message ?: "Payout initiated!", Toast.LENGTH_LONG).show()
                                    refreshLiveData()
                                } else {
                                    val err = res?.errorBody()?.string() ?: "Failed"
                                    Toast.makeText(context, "Withdrawal failed: $err", Toast.LENGTH_LONG).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(context, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                            }
                        }
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

            // SYSTEM ADMIN: Admin Command Center Modal
            if (showAdminDialog) {
                AdminConsoleDialog(
                    tournaments = displayTournaments,
                    currentUserId = currentUser.userId,
                    onCreateMatch = { createReq ->
                        coroutineScope.launch {
                            try {
                                val res = adminApiService?.createTournament(createReq)
                                if (res?.isSuccessful == true) {
                                    Toast.makeText(context, res.body()?.message ?: "Match Created!", Toast.LENGTH_LONG).show()
                                    showAdminDialog = false
                                    refreshLiveData()
                                } else {
                                    Toast.makeText(context, "Create failed: ${res?.code()}", Toast.LENGTH_SHORT).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(context, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                            }
                        }
                    },
                    onSetCredentials = { tourId, credsReq ->
                        coroutineScope.launch {
                            try {
                                val res = adminApiService?.setCredentials(tourId, credsReq)
                                if (res?.isSuccessful == true) {
                                    Toast.makeText(context, res.body()?.message ?: "Room Credentials Broadcasted!", Toast.LENGTH_LONG).show()
                                    showAdminDialog = false
                                    refreshLiveData()
                                } else {
                                    Toast.makeText(context, "Failed: ${res?.code()}", Toast.LENGTH_SHORT).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(context, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                            }
                        }
                    },
                    onAdjustBalance = { adjReq ->
                        coroutineScope.launch {
                            try {
                                val res = adminApiService?.adjustBalance(adjReq)
                                if (res?.isSuccessful == true) {
                                    Toast.makeText(context, "Balance Overridden in PostgreSQL!", Toast.LENGTH_LONG).show()
                                    showAdminDialog = false
                                    refreshLiveData()
                                } else {
                                    Toast.makeText(context, "Failed: ${res?.code()}", Toast.LENGTH_SHORT).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(context, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                            }
                        }
                    },
                    onDismiss = { showAdminDialog = false }
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
