package com.nextournament.app.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.payment.UpiAppInfo
import com.nextournament.app.ui.theme.*

@Composable
fun UpiDepositDialog(
    amount: Double,
    merchantVpa: String,
    merchantName: String,
    installedUpiApps: List<UpiAppInfo>,
    onSelectUpiApp: (UpiAppInfo) -> Unit,
    onSubmitUtr: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var selectedTab by remember { mutableIntStateOf(0) } // 0: Fast Apps, 1: QR & UTR
    var utrText by remember { mutableStateOf("") }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.88f))
                .padding(20.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(8.dp))
                    .background(ObsidianBlack)
                    .border(1.5.dp, CyberEmerald, CutCornerShape(8.dp))
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
                            painter = painterResource(id = R.drawable.ic_upi_logo),
                            contentDescription = "UPI",
                            tint = Color.Unspecified, // Keep branded orange/green
                            modifier = Modifier.size(32.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "INSTANT UPI DEPOSIT",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            color = Color.White
                        )
                    }

                    Text(
                        text = "₹%.2f".format(amount),
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = CyberEmerald
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Tab Switcher
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(SlateElevated)
                        .padding(4.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(CutCornerShape(2.dp))
                            .background(if (selectedTab == 0) CyberEmerald else Color.Transparent)
                            .clickable { selectedTab = 0 }
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "1-TAP APPS",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = if (selectedTab == 0) Color.Black else Color.White.copy(alpha = 0.7f)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(CutCornerShape(2.dp))
                            .background(if (selectedTab == 1) CyberEmerald else Color.Transparent)
                            .clickable { selectedTab = 1 }
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "QR CODE & UTR",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = if (selectedTab == 1) Color.Black else Color.White.copy(alpha = 0.7f)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                if (selectedTab == 0) {
                    // Fast Apps List
                    if (installedUpiApps.isNotEmpty()) {
                        Text(
                            text = "SELECT PAYMENT APP TO COMPLETE ₹%.2f".format(amount),
                            fontFamily = InterFont,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.6f)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        LazyColumn(
                            modifier = Modifier
                                .fillMaxWidth()
                                .heightIn(max = 240.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(installedUpiApps) { app ->
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(CutCornerShape(4.dp))
                                        .background(SlateCard)
                                        .border(1.dp, SlateElevated, CutCornerShape(4.dp))
                                        .clickable { onSelectUpiApp(app) }
                                        .padding(12.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        text = app.appName,
                                        fontFamily = ChakraPetch,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 14.sp,
                                        color = Color.White
                                    )
                                    Icon(
                                        painter = painterResource(id = R.drawable.ic_bolt_sharp),
                                        contentDescription = "Instant",
                                        tint = CyberAmber,
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                        }
                    } else {
                        Text(
                            text = "No compatible UPI apps detected on this device. Use the QR Code tab to pay via any device.",
                            fontFamily = InterFont,
                            fontSize = 12.sp,
                            color = CyberAmber,
                            textAlign = TextAlign.Center
                        )
                    }
                } else {
                    // QR Code & UTR Verification Mode
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // VPA Copy Card
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(CutCornerShape(4.dp))
                                .background(SlateCard)
                                .border(1.dp, SlateElevated, CutCornerShape(4.dp))
                                .clickable {
                                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                    clipboard.setPrimaryClip(ClipData.newPlainText("UPI VPA", merchantVpa))
                                    Toast.makeText(context, "UPI ID copied!", Toast.LENGTH_SHORT).show()
                                }
                                .padding(10.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("PAY TO UPI ID:", fontFamily = InterFont, fontSize = 9.sp, color = Color.White.copy(alpha = 0.5f))
                                Text(merchantVpa, fontFamily = ChakraPetch, fontWeight = FontWeight.Bold, fontSize = 13.sp, color = CyberEmerald)
                            }
                            Icon(
                                painter = painterResource(id = R.drawable.ic_copy_sharp),
                                contentDescription = "Copy",
                                tint = CyberEmerald,
                                modifier = Modifier.size(16.dp)
                            )
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // UTR Input
                        OutlinedTextField(
                            value = utrText,
                            onValueChange = { if (it.length <= 12) utrText = it },
                            label = { Text("Enter 12-Digit UTR / Ref Number", fontFamily = InterFont, fontSize = 11.sp) },
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

                        Spacer(modifier = Modifier.height(14.dp))

                        CyberActionButton(
                            text = "SUBMIT UTR FOR VERIFICATION",
                            onClick = {
                                if (utrText.length == 12) {
                                    onSubmitUtr(utrText)
                                } else {
                                    Toast.makeText(context, "Please enter full 12-digit UTR", Toast.LENGTH_SHORT).show()
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            iconRes = R.drawable.ic_check_circle_sharp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                TextButton(onClick = onDismiss) {
                    Text(
                        text = "CANCEL DEPOSIT",
                        fontFamily = ChakraPetch,
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
            }
        }
    }
}
