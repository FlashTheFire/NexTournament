package com.nextournament.app.ui.components

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.model.UserProfileDto
import com.nextournament.app.ui.theme.*

@Composable
fun AuthLoginDialog(
    onQuickLoginAdmin: () -> Unit,
    onQuickLoginPlayer: () -> Unit,
    onTelegramSync: (String) -> Unit,
    onPhoneVerify: (String, String) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var selectedAuthMode by remember { mutableStateOf(0) } // 0: Quick, 1: Telegram, 2: Phone OTP
    var syncCode by remember { mutableStateOf("") }
    var phoneNumber by remember { mutableStateOf("") }
    var otpCode by remember { mutableStateOf("") }
    var otpSent by remember { mutableStateOf(false) }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.90f))
                .padding(20.dp),
            contentAlignment = Alignment.Center
        ) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .wrapContentHeight()
                    .border(BrutalistBorderThin, NeonCyan, CutCornerShape(12.dp)),
                colors = CardDefaults.cardColors(containerColor = CyberDarkCard),
                shape = CutCornerShape(12.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_shield_sharp),
                                contentDescription = null,
                                tint = NeonCyan,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "AUTH GATEWAY",
                                fontFamily = OrbitronFont,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = Color.White
                            )
                        }

                        CyberBadge(
                            text = "PRODUCTION",
                            color = CyberEmerald,
                            textColor = ObsidianBlack
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Mode Selector Tabs
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(DarkBackground, CutCornerShape(6.dp))
                            .padding(4.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        listOf("1-TAP QUICK", "TELEGRAM", "PHONE OTP").forEachIndexed { index, title ->
                            val isSelected = selectedAuthMode == index
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .background(
                                        if (isSelected) NeonCyan else Color.Transparent,
                                        CutCornerShape(4.dp)
                                    )
                                    .clickable { selectedAuthMode = index }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = title,
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    color = if (isSelected) ObsidianBlack else Color.White.copy(alpha = 0.6f)
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // Mode 0: 1-Tap Quick Production Login
                    if (selectedAuthMode == 0) {
                        Text(
                            text = "Instant 1-Tap Production Login",
                            fontFamily = ChakraPetch,
                            fontSize = 12.sp,
                            color = Color.White.copy(alpha = 0.7f),
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(14.dp))

                        CyberActionButton(
                            text = "LOGIN AS OWNER / SUPERADMIN",
                            onClick = onQuickLoginAdmin,
                            modifier = Modifier.fillMaxWidth(),
                            accentColor = AmberGold,
                            textColor = ObsidianBlack,
                            iconRes = R.drawable.ic_verified_sharp
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        CyberActionButton(
                            text = "LOGIN AS TOURNAMENT PLAYER",
                            onClick = onQuickLoginPlayer,
                            modifier = Modifier.fillMaxWidth(),
                            accentColor = CyberEmerald,
                            textColor = ObsidianBlack,
                            iconRes = R.drawable.ic_person_sharp
                        )
                    }

                    // Mode 1: Telegram Sync Code
                    if (selectedAuthMode == 1) {
                        Text(
                            text = "Enter 6-Digit code from Telegram Bot (/sync)",
                            fontFamily = ChakraPetch,
                            fontSize = 12.sp,
                            color = Color.White.copy(alpha = 0.7f)
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        OutlinedTextField(
                            value = syncCode,
                            onValueChange = { if (it.length <= 8) syncCode = it.uppercase() },
                            placeholder = { Text("e.g. 571697 or ADMIN", color = Color.Gray) },
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = NeonCyan,
                                unfocusedBorderColor = Color.DarkGray
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(14.dp))

                        CyberActionButton(
                            text = "VERIFY & SYNC ACCOUNT",
                            onClick = {
                                if (syncCode.isNotBlank()) onTelegramSync(syncCode)
                                else Toast.makeText(context, "Enter sync code", Toast.LENGTH_SHORT).show()
                            },
                            modifier = Modifier.fillMaxWidth(),
                            accentColor = ElectricBlue,
                            textColor = Color.White,
                            iconRes = R.drawable.ic_bolt_sharp
                        )
                    }

                    // Mode 2: Phone OTP
                    if (selectedAuthMode == 2) {
                        OutlinedTextField(
                            value = phoneNumber,
                            onValueChange = { phoneNumber = it },
                            placeholder = { Text("10-Digit Mobile (+91)", color = Color.Gray) },
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = NeonCyan,
                                unfocusedBorderColor = Color.DarkGray
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        if (otpSent) {
                            OutlinedTextField(
                                value = otpCode,
                                onValueChange = { otpCode = it },
                                placeholder = { Text("Enter 6-Digit OTP", color = Color.Gray) },
                                singleLine = true,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = CyberEmerald,
                                    unfocusedBorderColor = Color.DarkGray
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            CyberActionButton(
                                text = "VERIFY & ENTER",
                                onClick = {
                                    if (phoneNumber.isNotBlank() && otpCode.isNotBlank()) {
                                        onPhoneVerify(phoneNumber, otpCode)
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                accentColor = CyberEmerald,
                                textColor = ObsidianBlack,
                                iconRes = R.drawable.ic_check_circle_sharp
                            )
                        } else {
                            CyberActionButton(
                                text = "SEND OTP CODE",
                                onClick = {
                                    if (phoneNumber.length >= 10) {
                                        otpSent = true
                                        Toast.makeText(context, "OTP Sent to $phoneNumber (Use 123456)", Toast.LENGTH_SHORT).show()
                                    } else {
                                        Toast.makeText(context, "Enter valid 10-digit number", Toast.LENGTH_SHORT).show()
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                accentColor = ElectricBlue,
                                textColor = Color.White,
                                iconRes = R.drawable.ic_bolt_sharp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    TextButton(onClick = onDismiss) {
                        Text(
                            text = "CONTINUE AS GUEST",
                            fontFamily = ChakraPetch,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.4f)
                        )
                    }
                }
            }
        }
    }
}
