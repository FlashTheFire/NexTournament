package com.nextournament.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.nextournament.app.data.model.UpdateCheckResponse
import com.nextournament.app.data.ota.DownloadState
import com.nextournament.app.data.ota.OtaUpdateManager
import com.nextournament.app.data.security.AntiCheatManager
import com.nextournament.app.data.security.DeviceIntegrityTier
import com.nextournament.app.data.security.DeviceSecurityReport
import com.nextournament.app.ui.components.AntiCheatViolationDialog
import com.nextournament.app.ui.components.CyberBadge
import com.nextournament.app.ui.components.FlexibleUpdateBanner
import com.nextournament.app.ui.components.ForcedUpdateDialog
import com.nextournament.app.ui.components.TournamentHudCard
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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val securityReport = antiCheatManager.evaluateDeviceIntegrity()

        setContent {
            NexTournamentTheme {
                MainLobbyScreen(
                    securityReport = securityReport,
                    otaUpdateManager = otaUpdateManager
                )
            }
        }
    }
}

@Composable
fun MainLobbyScreen(
    securityReport: DeviceSecurityReport? = null,
    otaUpdateManager: OtaUpdateManager? = null
) {
    val coroutineScope = rememberCoroutineScope()
    var showAntiCheatModal by remember {
        mutableStateOf(securityReport?.tier == DeviceIntegrityTier.ROOTED || securityReport?.tier == DeviceIntegrityTier.HOOK_DETECTED)
    }

    var updateResponse by remember { mutableStateOf<UpdateCheckResponse?>(null) }
    var downloadState by remember { mutableStateOf<DownloadState>(DownloadState.Idle) }
    var isFlexibleBannerDismissed by remember { mutableStateOf(false) }

    // Real Lottie animation loaded from android/app/src/main/assets/lottie/daily_streak_fire.json

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
                        style = EsportsTypography.displayMedium,
                        color = NeonAmber,
                        fontSize = 18.sp,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        text = "UNIVERSAL ESPORTS PLATFORM",
                        style = EsportsTypography.labelSmall,
                        color = TextMutedSecondary
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    CyberBadge(
                        text = "v1.0.0 OTA",
                        color = CyberEmerald,
                        backgroundColor = SlateElevated
                    )
                }
            }
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            // Quick Stats Banner: Dual Wallet & Daily Streak
            item {
                Card(
                    shape = CutCornerCard,
                    colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
                    border = BorderStroke(BrutalistBorderThin, SlateElevated),
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Wallet Balance Box
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_wallet_sharp),
                                contentDescription = "Wallet",
                                tint = NeonAmber,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Column {
                                Text("WALLET BALANCE", style = EsportsTypography.labelSmall)
                                Text("₹2,450.00", color = TextWhitePrimary, fontSize = 16.sp, fontWeight = FontWeight.Black)
                            }
                        }

                        // Lottie Animated Streak Badge
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(modifier = Modifier.size(36.dp)) {
                                LottieAnimation(
                                    composition = streakComposition,
                                    iterations = LottieConstants.IterateForever,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }
                            Spacer(modifier = Modifier.width(4.dp))
                            Column {
                                Text("STREAK", style = EsportsTypography.labelSmall, color = NeonAmber)
                                Text("DAY 5 🔥", color = NeonAmber, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "FEATURED TOURNAMENTS",
                    style = EsportsTypography.headlineMedium,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(6.dp))
            }

            item {
                TournamentHudCard(
                    title = "Bermuda Masters Series #42 [Squad]",
                    game = "Free Fire",
                    map = "Bermuda",
                    entryFee = "50",
                    prizePool = "2,000",
                    perKillBounty = "15",
                    slotsStatus = "38/48",
                    onJoinClick = { /* Seat picker navigation */ }
                )
            }

            item {
                TournamentHudCard(
                    title = "Erangel Showdown Blitz [Duo]",
                    game = "BGMI",
                    map = "Erangel",
                    entryFee = "100",
                    prizePool = "4,500",
                    perKillBounty = "30",
                    slotsStatus = "72/100",
                    onJoinClick = { /* Seat picker navigation */ }
                )
            }

            item {
                TournamentHudCard(
                    title = "Ascent Custom 5v5 Championship",
                    game = "Valorant",
                    map = "Ascent",
                    entryFee = "0 (Free)",
                    prizePool = "1,000",
                    slotsStatus = "8/10",
                    onJoinClick = { /* Seat picker navigation */ }
                )
            }
        }

        // 1. Flexible Ambient Update Banner (Optional updates)
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

        // 2. Critical Forced Update Dialog (Blocks entire UI)
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

        // 3. Hardware Anti-Cheat Violation Modal
        if (showAntiCheatModal && securityReport != null) {
            AntiCheatViolationDialog(
                securityReport = securityReport,
                onDismissOrAcknowledge = {
                    showAntiCheatModal = false
                }
            )
        }
    }
}
