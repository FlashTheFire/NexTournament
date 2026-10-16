package com.nextournament.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
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
import com.nextournament.app.ui.components.CyberBadge
import com.nextournament.app.ui.components.TournamentHudCard
import com.nextournament.app.ui.theme.*
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            NexTournamentTheme {
                MainLobbyScreen()
            }
        }
    }
}

@Composable
fun MainLobbyScreen() {
    // Real Lottie animation loaded from android/app/src/main/assets/lottie/daily_streak_fire.json
    val streakComposition by rememberLottieComposition(
        LottieCompositionSpec.Asset("lottie/daily_streak_fire.json")
    )

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
    }
}
