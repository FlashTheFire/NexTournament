package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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
    onJoinClick: () -> Unit
) {
    Card(
        shape = CutCornerCard, // Chamfered corners (No bubbly borders)
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = BorderStroke(BrutalistBorderThin, SlateElevated),
        modifier = modifier.fillMaxWidth().padding(vertical = 6.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header Row: Game Badge + Map
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                CyberBadge(
                    text = game,
                    color = NeonCyan,
                    backgroundColor = SlateElevated
                )
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
                color = TextWhitePrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 2
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom Metric Row: Prize, Entry, and Join Action
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "PRIZE POOL",
                        color = TextMutedSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "₹$prizePool",
                        color = NeonAmber,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black
                    )
                }

                Column {
                    Text(
                        text = "ENTRY FEE",
                        color = TextMutedSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "₹$entryFee",
                        color = TextWhitePrimary,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
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
