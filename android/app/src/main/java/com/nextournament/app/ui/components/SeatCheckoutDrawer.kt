package com.nextournament.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.data.model.SeatSlot
import com.nextournament.app.ui.theme.*

@Composable
fun SeatCheckoutDrawer(
    selectedSlot: SeatSlot,
    entryFee: Double,
    walletBalance: Double,
    remainingSeconds: Int,
    onConfirmPurchase: () -> Unit,
    onCancelReservation: () -> Unit,
    onTopUpWallet: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isBalanceSufficient = walletBalance >= entryFee

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(topStart = 12.dp, topEnd = 12.dp))
            .background(ObsidianBlack)
            .border(1.5.dp, CyberAmber, CutCornerShape(topStart = 12.dp, topEnd = 12.dp))
            .padding(20.dp)
    ) {
        // Top Header with Lock Countdown
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "SEAT RESERVED: #${selectedSlot.slotNumber}",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = Color.White
                )
                Text(
                    text = "TEAM ${selectedSlot.teamNumber} • ${selectedSlot.role}",
                    fontFamily = InterFont,
                    fontSize = 12.sp,
                    color = CyberAmber
                )
            }

            // 120s Countdown Timer Chip
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .clip(CutCornerShape(4.dp))
                    .background(CyberAmber.copy(alpha = 0.15f))
                    .border(1.dp, CyberAmber, CutCornerShape(4.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_alarm_sharp),
                    contentDescription = null,
                    tint = CyberAmber,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                val minutes = remainingSeconds / 60
                val seconds = remainingSeconds % 60
                Text(
                    text = "%02d:%02d".format(minutes, seconds),
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = CyberAmber
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Price & Balance Card
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(CutCornerShape(4.dp))
                .background(SlateCard)
                .padding(14.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "ENTRY TICKET FEE",
                    fontFamily = InterFont,
                    fontSize = 12.sp,
                    color = Color.White.copy(alpha = 0.7f)
                )
                Text(
                    text = "₹%.2f".format(entryFee),
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = Color.White
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "YOUR WALLET BALANCE",
                    fontFamily = InterFont,
                    fontSize = 12.sp,
                    color = Color.White.copy(alpha = 0.7f)
                )
                Text(
                    text = "₹%.2f".format(walletBalance),
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = if (isBalanceSufficient) CyberEmerald else CrimsonRed
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Action Buttons
        if (isBalanceSufficient) {
            CyberActionButton(
                text = "PAY ₹%.2f & CONFIRM SEAT".format(entryFee),
                onClick = onConfirmPurchase,
                modifier = Modifier.fillMaxWidth(),
                iconRes = R.drawable.ic_check_circle_sharp
            )
        } else {
            val deficit = entryFee - walletBalance
            CyberActionButton(
                text = "TOP-UP WALLET (₹%.2f NEEDED)".format(deficit),
                onClick = onTopUpWallet,
                modifier = Modifier.fillMaxWidth(),
                iconRes = R.drawable.ic_wallet_sharp
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        TextButton(
            onClick = onCancelReservation,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = "CANCEL & RELEASE SEAT",
                fontFamily = ChakraPetch,
                fontSize = 12.sp,
                color = Color.White.copy(alpha = 0.5f)
            )
        }
    }
}
