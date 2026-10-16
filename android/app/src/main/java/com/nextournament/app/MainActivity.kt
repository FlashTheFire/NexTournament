package com.nextournament.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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
    Scaffold(
        containerColor = ObsidianBlack,
        topBar = {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SlateBackground)
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "NEXTOURNAMENT",
                        color = NeonAmber,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        text = "UNIVERSAL ESPORTS PLATFORM",
                        color = TextMutedSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.8.sp
                    )
                }
                CyberBadge(
                    text = "v1.0.0 OTA",
                    color = CyberEmerald,
                    backgroundColor = SlateElevated
                )
            }
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "FEATURED TOURNAMENTS",
                    color = TextWhitePrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Black,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
            }

            item {
                TournamentHudCard(
                    title = "Bermuda Masters Series #42 [Squad]",
                    game = "Free Fire",
                    map = "Bermuda",
                    entryFee = "50",
                    prizePool = "2,000",
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
