package com.nextournament.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.nextournament.app.R
import com.nextournament.app.data.model.SeatSlot
import com.nextournament.app.data.model.SeatSlotStatus
import com.nextournament.app.data.model.SquadCluster
import com.nextournament.app.ui.theme.*

@Composable
fun CinemaSeatGrid(
    squadClusters: List<SquadCluster>,
    selectedSlotNumber: Int?,
    onSlotClick: (SeatSlot) -> Unit,
    modifier: Modifier = Modifier
) {
    val lockTimerComposition by rememberLottieComposition(
        LottieCompositionSpec.Asset("lottie/seat_lock_timer.json")
    )

    Column(modifier = modifier.fillMaxWidth()) {
        // Seat Status Legend Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp)
                .clip(CutCornerShape(4.dp))
                .background(SlateCard)
                .padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            LegendItem(color = CyberEmerald, label = "Available")
            LegendItem(color = CyberAmber, label = "Locking")
            LegendItem(color = Color.White.copy(alpha = 0.35f), label = "Booked")
            LegendItem(color = Color(0xFFFACC15), label = "Selected")
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Squad Clusters List
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(squadClusters, key = { it.teamNumber }) { squad ->
                SquadClusterCard(
                    squad = squad,
                    selectedSlotNumber = selectedSlotNumber,
                    lockTimerComposition = lockTimerComposition,
                    onSlotClick = onSlotClick
                )
            }
        }
    }
}

@Composable
fun SquadClusterCard(
    squad: SquadCluster,
    selectedSlotNumber: Int?,
    lockTimerComposition: com.airbnb.lottie.LottieComposition?,
    onSlotClick: (SeatSlot) -> Unit
) {
    Card(
        shape = CutCornerCard,
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, SlateElevated),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            // Squad Header
            Row(
                modifier = Modifier.fillMaxWidth(),
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
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = squad.teamName.uppercase(),
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = Color.White
                    )
                }

                val occupiedCount = squad.slots.count { it.status == SeatSlotStatus.BOOKED }
                CyberBadge(
                    text = "$occupiedCount/4 FILLED",
                    color = if (occupiedCount == 4) CrimsonRed else CyberEmerald,
                    backgroundColor = SlateElevated
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // 4-Slot Cluster Grid
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                squad.slots.forEach { slot ->
                    SeatSlotTile(
                        slot = slot,
                        isSelected = slot.slotNumber == selectedSlotNumber,
                        lockTimerComposition = lockTimerComposition,
                        onClick = { onSlotClick(slot) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

@Composable
fun SeatSlotTile(
    slot: SeatSlot,
    isSelected: Boolean,
    lockTimerComposition: com.airbnb.lottie.LottieComposition?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isClickable = slot.status == SeatSlotStatus.AVAILABLE || isSelected

    val (tileBg, borderColor, textColor) = when {
        isSelected -> Triple(Color(0xFFFACC15).copy(alpha = 0.2f), Color(0xFFFACC15), Color(0xFFFACC15))
        slot.status == SeatSlotStatus.BOOKED -> Triple(SlateElevated.copy(alpha = 0.5f), Color.Transparent, Color.White.copy(alpha = 0.35f))
        slot.status == SeatSlotStatus.LOCKING_MUTEX -> Triple(CyberAmber.copy(alpha = 0.15f), CyberAmber, CyberAmber)
        else -> Triple(SlateElevated, CyberEmerald.copy(alpha = 0.5f), CyberEmerald)
    }

    Box(
        modifier = modifier
            .aspectRatio(0.85f)
            .clip(CutCornerShape(4.dp))
            .background(tileBg)
            .border(if (isSelected) 2.dp else 1.dp, borderColor, CutCornerShape(4.dp))
            .clickable(enabled = isClickable) { onClick() }
            .padding(4.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            when (slot.status) {
                SeatSlotStatus.LOCKING_MUTEX -> {
                    Box(modifier = Modifier.size(20.dp)) {
                        LottieAnimation(
                            composition = lockTimerComposition,
                            iterations = LottieConstants.IterateForever,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
                SeatSlotStatus.BOOKED -> {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_lock_sharp),
                        contentDescription = "Booked",
                        tint = Color.White.copy(alpha = 0.35f),
                        modifier = Modifier.size(16.dp)
                    )
                }
                else -> {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_event_seat_sharp),
                        contentDescription = "Seat",
                        tint = textColor,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = "#${slot.slotNumber}",
                fontFamily = ChakraPetch,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                color = textColor
            )

            if (!slot.occupiedByIgn.isNullOrBlank()) {
                Text(
                    text = slot.occupiedByIgn,
                    fontFamily = InterFont,
                    fontSize = 9.sp,
                    color = Color.White.copy(alpha = 0.6f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            } else {
                Text(
                    text = slot.role,
                    fontFamily = InterFont,
                    fontSize = 8.sp,
                    color = textColor.copy(alpha = 0.7f)
                )
            }
        }
    }
}

@Composable
private fun LegendItem(color: Color, label: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .clip(CutCornerShape(2.dp))
                .background(color)
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = label,
            fontFamily = ChakraPetch,
            fontSize = 11.sp,
            color = Color.White.copy(alpha = 0.7f)
        )
    }
}
