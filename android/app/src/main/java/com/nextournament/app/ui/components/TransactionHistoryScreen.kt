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
import com.nextournament.app.data.local.TransactionEntity
import com.nextournament.app.ui.theme.*

@Composable
fun TransactionHistoryScreen(
    transactions: List<TransactionEntity>,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedCategory by remember { mutableStateOf("ALL") }

    val filteredList = remember(selectedCategory, transactions) {
        when (selectedCategory) {
            "DEPOSITS" -> transactions.filter { it.type.contains("DEPOSIT", ignoreCase = true) }
            "WINNINGS" -> transactions.filter { it.type.contains("PRIZE", ignoreCase = true) || it.type.contains("BOUNTY", ignoreCase = true) }
            "ENTRIES" -> transactions.filter { it.type.contains("ENTRY", ignoreCase = true) }
            else -> transactions
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(ObsidianBlack)
            .padding(16.dp)
    ) {
        // Top Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_receipt_long_sharp),
                    contentDescription = null,
                    tint = ElectricBlue,
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Text(
                    text = "TRANSACTION LEDGER",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = Color.White
                )
            }

            TextButton(onClick = onBackClick) {
                Text(
                    text = "BACK",
                    fontFamily = ChakraPetch,
                    fontSize = 12.sp,
                    color = Color.White.copy(alpha = 0.7f)
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Category Filter Chips
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(CutCornerShape(4.dp))
                .background(SlateElevated)
                .padding(4.dp)
        ) {
            listOf("ALL", "DEPOSITS", "WINNINGS", "ENTRIES").forEach { cat ->
                val isSelected = selectedCategory == cat
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(CutCornerShape(2.dp))
                        .background(if (isSelected) ElectricBlue else Color.Transparent)
                        .clickable { selectedCategory = cat }
                        .padding(vertical = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = cat,
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 10.sp,
                        color = if (isSelected) Color.Black else Color.White.copy(alpha = 0.7f)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Transactions List
        if (filteredList.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "NO TRANSACTIONS FOUND IN THIS CATEGORY",
                    fontFamily = ChakraPetch,
                    fontSize = 12.sp,
                    color = Color.White.copy(alpha = 0.4f)
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(filteredList, key = { it.id }) { tx ->
                    TransactionItemCard(tx = tx)
                }
            }
        }
    }
}

@Composable
fun TransactionItemCard(tx: TransactionEntity) {
    val isCredit = tx.type.contains("DEPOSIT", ignoreCase = true) ||
            tx.type.contains("PRIZE", ignoreCase = true) ||
            tx.type.contains("BOUNTY", ignoreCase = true)

    val (iconRes, iconColor) = when {
        tx.type.contains("DEPOSIT", ignoreCase = true) -> Pair(R.drawable.ic_arrow_downward_sharp, CyberEmerald)
        tx.type.contains("WITHDRAWAL", ignoreCase = true) -> Pair(R.drawable.ic_arrow_upward_sharp, CyberAmber)
        tx.type.contains("PRIZE", ignoreCase = true) -> Pair(R.drawable.ic_trophy_sharp, Color(0xFFFACC15))
        tx.type.contains("BOUNTY", ignoreCase = true) -> Pair(R.drawable.ic_skull_kill_sharp, CrimsonRed)
        else -> Pair(R.drawable.ic_wallet_sharp, ElectricBlue)
    }

    Card(
        shape = CutCornerCard,
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = BorderStroke(BrutalistBorderThin, SlateElevated),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(iconColor.copy(alpha = 0.15f))
                        .border(1.dp, iconColor.copy(alpha = 0.5f), CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        painter = painterResource(id = iconRes),
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier.size(20.dp)
                    )
                }

                Spacer(modifier = Modifier.width(12.dp))

                Column {
                    Text(
                        text = tx.type.replace("_", " ").uppercase(),
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = Color.White
                    )
                    Text(
                        text = "${tx.paymentMethod} • ${tx.timestamp.take(16)}",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                }
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "${if (isCredit) "+" else "-"}₹%.2f".format(tx.amount),
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = if (isCredit) CyberEmerald else CrimsonRed
                )
                CyberBadge(
                    text = tx.status.uppercase(),
                    color = when (tx.status.uppercase()) {
                        "COMPLETED", "SUCCESS" -> CyberEmerald
                        "PENDING" -> CyberAmber
                        else -> CrimsonRed
                    },
                    backgroundColor = SlateElevated
                )
            }
        }
    }
}
