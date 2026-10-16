package com.nextournament.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.ui.theme.*

@Composable
fun WithdrawalDrawer(
    winningsBalance: Double,
    dailyInstantLimit: Double = 2000.0,
    onRequestWithdrawal: (amount: Double, method: String, destination: String) -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    var amountText by remember { mutableStateOf("") }
    var selectedMethod by remember { mutableStateOf("UPI") } // "UPI", "BANK", "USDT"
    var destinationText by remember { mutableStateOf("") }
    var ifscText by remember { mutableStateOf("") }

    val amount = amountText.toDoubleOrNull() ?: 0.0
    val isValidAmount = amount in 100.0..winningsBalance
    val isAutoInstant = amount <= dailyInstantLimit

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(topStart = 12.dp, topEnd = 12.dp))
            .background(ObsidianBlack)
            .border(1.5.dp, CyberEmerald, CutCornerShape(topStart = 12.dp, topEnd = 12.dp))
            .padding(20.dp)
    ) {
        // Top Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "INSTANT WINNINGS PAYOUT",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = Color.White
                )
                Text(
                    text = "WITHDRAWABLE BALANCE: ₹%.2f".format(winningsBalance),
                    fontFamily = InterFont,
                    fontSize = 11.sp,
                    color = CyberEmerald
                )
            }

            CyberBadge(
                text = "LIGHTNING SPEED",
                color = CyberEmerald,
                backgroundColor = SlateElevated
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Payout Method Selector
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(CutCornerShape(4.dp))
                .background(SlateElevated)
                .padding(4.dp)
        ) {
            listOf("UPI", "BANK", "USDT").forEach { method ->
                val isSelected = selectedMethod == method
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(CutCornerShape(2.dp))
                        .background(if (isSelected) CyberEmerald else Color.Transparent)
                        .clickable { selectedMethod = method }
                        .padding(vertical = 8.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = method,
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = if (isSelected) Color.Black else Color.White.copy(alpha = 0.7f)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Amount Input Field
        OutlinedTextField(
            value = amountText,
            onValueChange = { amountText = it },
            label = { Text("Withdrawal Amount (Min ₹100)", fontFamily = InterFont, fontSize = 11.sp) },
            leadingIcon = { Text("₹", fontFamily = ChakraPetch, fontWeight = FontWeight.Bold, color = CyberEmerald, fontSize = 16.sp) },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = CyberEmerald,
                unfocusedBorderColor = SlateElevated,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            ),
            shape = CutCornerShape(4.dp),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Destination Input Field
        when (selectedMethod) {
            "UPI" -> {
                OutlinedTextField(
                    value = destinationText,
                    onValueChange = { destinationText = it },
                    label = { Text("Enter UPI ID (e.g. gamer@okhdfcbank)", fontFamily = InterFont, fontSize = 11.sp) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberEmerald,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                )
            }
            "BANK" -> {
                OutlinedTextField(
                    value = destinationText,
                    onValueChange = { destinationText = it },
                    label = { Text("Bank Account Number", fontFamily = InterFont, fontSize = 11.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberEmerald,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = ifscText,
                    onValueChange = { ifscText = it.uppercase() },
                    label = { Text("Bank IFSC Code (11-Chars)", fontFamily = InterFont, fontSize = 11.sp) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberEmerald,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                )
            }
            "USDT" -> {
                OutlinedTextField(
                    value = destinationText,
                    onValueChange = { destinationText = it },
                    label = { Text("Tether USDT Address (TRC-20 / BEP-20)", fontFamily = InterFont, fontSize = 11.sp) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberEmerald,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Info Banner
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(CutCornerShape(4.dp))
                .background(SlateCard)
                .padding(10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = if (isAutoInstant) "⚡ Instant automated transfer (<60s)" else "🛡️ >₹2,000: 15-min FairPlay audit applies",
                fontFamily = InterFont,
                fontSize = 11.sp,
                color = if (isAutoInstant) CyberEmerald else CyberAmber
            )
            Text(
                text = "Fee: ₹0",
                fontFamily = ChakraPetch,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                color = Color.White
            )
        }

        Spacer(modifier = Modifier.height(18.dp))

        CyberActionButton(
            text = "CONFIRM & DISPATCH PAYOUT",
            onClick = {
                val dest = if (selectedMethod == "BANK") "$destinationText|$ifscText" else destinationText
                onRequestWithdrawal(amount, selectedMethod, dest)
            },
            enabled = isValidAmount && destinationText.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
            iconRes = R.drawable.ic_arrow_upward_sharp
        )

        Spacer(modifier = Modifier.height(8.dp))

        TextButton(
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = "CANCEL",
                fontFamily = ChakraPetch,
                fontSize = 12.sp,
                color = Color.White.copy(alpha = 0.5f)
            )
        }
    }
}
