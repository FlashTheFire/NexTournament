package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.data.local.TournamentEntity
import com.nextournament.app.ui.theme.*

@Composable
fun TournamentCatalogScreen(
    tournaments: List<TournamentEntity>,
    onTournamentClick: (TournamentEntity) -> Unit,
    modifier: Modifier = Modifier,
    joinedTournamentIds: Set<Long> = emptySet(),
    onRoomClick: (TournamentEntity) -> Unit = {},
    onChatClick: (TournamentEntity) -> Unit = {}
) {
    var selectedFormat by remember { mutableStateOf("ALL") }
    val formatsList = listOf("ALL", "SOLO", "DUO", "SQUAD")

    val filteredTournaments = remember(selectedFormat, tournaments) {
        tournaments.filter { t ->
            val gameMatches = t.game.contains("Free Fire", ignoreCase = true)
            val formatMatches = if (selectedFormat == "ALL") true else t.format.equals(selectedFormat, ignoreCase = true)
            gameMatches && formatMatches
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(ObsidianBlack)
    ) {
        // Combined Dynamic Game & Match Types HUD Row (Single Horizontal Bar)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(SlateBackground)
                .padding(horizontal = 14.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Left: Glowing Free Fire Badge
            Box(
                modifier = Modifier
                    .clip(CutCornerShape(4.dp))
                    .background(SlateElevated)
                    .border(BorderStroke(1.dp, CyberAmber.copy(alpha = 0.8f)), CutCornerShape(4.dp))
                    .padding(horizontal = 10.dp, vertical = 7.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_flame_streak),
                        contentDescription = "Free Fire",
                        tint = CyberAmber,
                        modifier = Modifier.size(15.dp)
                    )
                    Spacer(modifier = Modifier.width(5.dp))
                    Text(
                        text = "FREE FIRE",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp,
                        color = CyberAmber,
                        letterSpacing = 0.5.sp
                    )
                }
            }

            // Right: Segmented Format Tabs (ALL | SOLO | DUO | SQUAD)
            Row(
                modifier = Modifier
                    .weight(1f)
                    .clip(CutCornerShape(4.dp))
                    .background(SlateElevated)
                    .padding(2.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                formatsList.forEach { format ->
                    val isSelected = selectedFormat == format
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(CutCornerShape(2.dp))
                            .background(if (isSelected) ElectricBlue else Color.Transparent)
                            .clickable { selectedFormat = format }
                            .padding(vertical = 6.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = format,
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = if (isSelected) Color.Black else Color.White.copy(alpha = 0.7f)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        // Match Cards Feed
        if (filteredTournaments.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_filter_list_sharp),
                        contentDescription = null,
                        tint = Color.White.copy(alpha = 0.3f),
                        modifier = Modifier.size(40.dp)
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        text = "NO MATCHES CURRENTLY OPEN FOR FREE FIRE [$selectedFormat]",
                        fontFamily = ChakraPetch,
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(filteredTournaments, key = { it.id }) { t ->
                    val isJoined = joinedTournamentIds.contains(t.id)
                    TournamentHudCard(
                        title = t.title,
                        game = t.game,
                        map = t.map,
                        entryFee = t.entryFee.toInt().toString(),
                        prizePool = t.prizePool.toInt().toString(),
                        perKillBounty = t.perKillBounty.toInt().toString(),
                        slotsStatus = "${t.filledSlots}/${t.maxSlots}",
                        isJoined = isJoined,
                        format = t.format,
                        onRoomClick = { onRoomClick(t) },
                        onChatClick = { onChatClick(t) },
                        onJoinClick = { onTournamentClick(t) }
                    )
                }
            }
        }
    }
}
