package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.ui.theme.*

@Composable
fun TournamentHudCard(
    title: String,
    game: String,
    map: String,
    entryFee: String,
    prizePool: String,
    slotsStatus: String,
    modifier: Modifier = Modifier,
    perKillBounty: String? = null,
    onJoinClick: () -> Unit
) {
    Card(
        shape = CutCornerCard, // Chamfered corners (No bubbly borders)
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = BorderStroke(BrutalistBorderThin, SlateElevated),
        modifier = modifier.fillMaxWidth().padding(vertical = 6.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header Row: Game Badge + Verified Shield + Map
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CyberBadge(
                        text = game,
                        color = NeonCyan,
                        backgroundColor = SlateElevated
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Icon(
                        painter = painterResource(id = R.drawable.ic_shield_sharp),
                        contentDescription = "Anti-Cheat Shield",
                        tint = CyberEmerald,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Text(
                    text = "MAP: $map".uppercase(),
                    color = TextMutedSecondary,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Match Title
            Text(
                text = title,
                style = EsportsTypography.headlineMedium,
                maxLines = 2
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom Metric Row: Trophy Prize, Kill Bounty / Entry, and Join Action
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_trophy_sharp),
                        contentDescription = "Trophy",
                        tint = NeonAmber,
                        modifier = Modifier.size(22.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Column {
                        Text(
                            text = "PRIZE POOL",
                            style = EsportsTypography.labelSmall
                        )
                        Text(
                            text = "₹$prizePool",
                            color = NeonAmber,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Black
                        )
                    }
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_skull_kill_sharp),
                        contentDescription = "Kill Bounty",
                        tint = LaserCrimson,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Column {
                        Text(
                            text = if (perKillBounty != null) "KILL BOUNTY" else "ENTRY",
                            style = EsportsTypography.labelSmall
                        )
                        Text(
                            text = if (perKillBounty != null) "₹$perKillBounty" else "₹$entryFee",
                            color = TextWhitePrimary,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                CyberActionButton(
                    text = "JOIN ($slotsStatus)",
                    onClick = onJoinClick,
                    accentColor = NeonAmber,
                    textColor = ObsidianBlack
                )
            }
        }
    }
}
