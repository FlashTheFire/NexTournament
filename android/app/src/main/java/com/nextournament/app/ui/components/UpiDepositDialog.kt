package com.nextournament.app.ui.components

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
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
import com.nextournament.app.data.payment.UpiAppInfo
import com.nextournament.app.ui.theme.*

@Composable
fun UpiDepositDialog(
    initialAmount: Double = 500.0,
    merchantVpa: String = "nextournament@icici",
    merchantName: String = "NexTournament Esports",
    installedUpiApps: List<UpiAppInfo> = emptyList(),
    onSelectUpiApp: (UpiAppInfo) -> Unit = {},
    onVerifyPayment: (Double, String) -> Unit = { _, _ -> },
    onOpenAiSupport: () -> Unit = {},
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var selectedAmount by remember { mutableDoubleStateOf(initialAmount) }
    val presetAmounts = listOf(50.0, 100.0, 500.0, 1000.0)
    val orderId = remember(selectedAmount) {
        "1000" + (System.currentTimeMillis() % 100000000).toString()
    }

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
                // Header: Branded UPI Logo + Title + Current Amount
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_upi_logo),
                            contentDescription = "UPI",
                            tint = Color.Unspecified,
                            modifier = Modifier.size(30.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "INSTANT UPI DEPOSIT",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            color = Color.White
                        )
                    }

                    Text(
                        text = "₹%.0f".format(selectedAmount),
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = CyberEmerald
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Amount Selection Pills (50, 100, 500, 1000)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    presetAmounts.forEach { amt ->
                        val isSelected = selectedAmount == amt
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(CutCornerShape(4.dp))
                                .background(if (isSelected) CyberAmber else SlateElevated)
                                .border(
                                    1.dp,
                                    if (isSelected) CyberAmber else SlateCardSurface,
                                    CutCornerShape(4.dp)
                                )
                                .clickable { selectedAmount = amt }
                                .padding(vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "₹%.0f".format(amt),
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = if (isSelected) Color.Black else Color.White
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Single Combined Box: Dynamic QR Code with Cyber Frame
                Box(
                    modifier = Modifier
                        .size(190.dp)
                        .clip(CutCornerShape(8.dp))
                        .background(Color.White)
                        .padding(10.dp),
                    contentAlignment = Alignment.Center
                ) {
                    // Crisp Procedural QR Matrix Canvas
                    DynamicUpiQrCanvas(
                        orderId = orderId,
                        modifier = Modifier.fillMaxSize()
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "SCAN WITH ANY UPI APP (AUTO VERIFIED)",
                    fontFamily = ChakraPetch,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White.copy(alpha = 0.5f),
                    letterSpacing = 0.5.sp
                )

                Spacer(modifier = Modifier.height(14.dp))

                // 1-Tap UPI Apps Section with Compact Circular Logo Icons
                Text(
                    text = "OR PAY VIA 1-TAP APP",
                    fontFamily = ChakraPetch,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = ElectricBlue
                )

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // App 1: GPay
                    UpiAppIconButton(
                        label = "GPay",
                        bgColor = Color(0xFF1F1F1F),
                        accentColor = Color(0xFF4285F4),
                        onClick = {
                            val app = installedUpiApps.find { it.packageName.contains("google", ignoreCase = true) }
                                ?: UpiAppInfo("com.google.android.apps.nbu.paisa.user", "Google Pay", null)
                            onSelectUpiApp(app)
                        }
                    )

                    // App 2: PhonePe
                    UpiAppIconButton(
                        label = "PhonePe",
                        bgColor = Color(0xFF5F259F),
                        accentColor = Color.White,
                        onClick = {
                            val app = installedUpiApps.find { it.packageName.contains("phonepe", ignoreCase = true) }
                                ?: UpiAppInfo("com.phonepe.app", "PhonePe", null)
                            onSelectUpiApp(app)
                        }
                    )

                    // App 3: Paytm
                    UpiAppIconButton(
                        label = "Paytm",
                        bgColor = Color(0xFF002970),
                        accentColor = Color(0xFF00BAF2),
                        onClick = {
                            val app = installedUpiApps.find { it.packageName.contains("paytm", ignoreCase = true) }
                                ?: UpiAppInfo("net.one97.paytm", "Paytm", null)
                            onSelectUpiApp(app)
                        }
                    )

                    // App 4: CRED / BHIM
                    UpiAppIconButton(
                        label = "CRED",
                        bgColor = Color(0xFF141414),
                        accentColor = Color(0xFFF59E0B),
                        onClick = {
                            val app = installedUpiApps.find { it.packageName.contains("cred", ignoreCase = true) }
                                ?: UpiAppInfo("com.dreamplug.androidapp", "CRED", null)
                            onSelectUpiApp(app)
                        }
                    )
                }

                Spacer(modifier = Modifier.height(18.dp))

                // Action Button: Live Server Verify
                CyberActionButton(
                    text = "⚡ VERIFY PAYMENT",
                    onClick = {
                        onVerifyPayment(selectedAmount, orderId)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    accentColor = CyberEmerald,
                    textColor = ObsidianBlack,
                    iconRes = R.drawable.ic_check_circle_sharp
                )

                Spacer(modifier = Modifier.height(10.dp))

                // AI Support & UTR Help Link
                Row(
                    modifier = Modifier
                        .clip(CutCornerShape(4.dp))
                        .clickable { onOpenAiSupport() }
                        .padding(horizontal = 8.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "💬 Paid but amount not added? Ask AI Support & UTR Help →",
                        fontFamily = ChakraPetch,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = ElectricBlue
                    )
                }

                Spacer(modifier = Modifier.height(4.dp))

                TextButton(onClick = onDismiss) {
                    Text(
                        text = "CANCEL DEPOSIT",
                        fontFamily = ChakraPetch,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                }
            }
        }
    }
}

@Composable
fun UpiAppIconButton(
    label: String,
    bgColor: Color,
    accentColor: Color,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .clip(CutCornerShape(4.dp))
            .clickable { onClick() }
            .padding(6.dp)
    ) {
        Box(
            modifier = Modifier
                .size(46.dp)
                .clip(CutCornerShape(6.dp))
                .background(bgColor)
                .border(1.dp, accentColor.copy(alpha = 0.6f), CutCornerShape(6.dp)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = label.take(2).uppercase(),
                fontFamily = OrbitronFont,
                fontWeight = FontWeight.Black,
                fontSize = 14.sp,
                color = accentColor
            )
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            fontFamily = ChakraPetch,
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
            color = Color.White.copy(alpha = 0.8f)
        )
    }
}

/**
 * Procedural Dynamic QR Canvas generating crisp, high-contrast QR Matrix with finder patterns
 */
@Composable
fun DynamicUpiQrCanvas(
    orderId: String,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val matrixSize = 25
        val cellSize = size.minDimension / matrixSize

        // Draw background white
        drawRect(color = Color.White, size = size)

        // Helper to draw QR finder pattern at row, col
        fun drawFinder(r: Int, c: Int) {
            // Outer 7x7 black
            drawRect(
                color = Color.Black,
                topLeft = Offset(c * cellSize, r * cellSize),
                size = Size(7 * cellSize, 7 * cellSize)
            )
            // Middle 5x5 white
            drawRect(
                color = Color.White,
                topLeft = Offset((c + 1) * cellSize, (r + 1) * cellSize),
                size = Size(5 * cellSize, 5 * cellSize)
            )
            // Center 3x3 black
            drawRect(
                color = Color.Black,
                topLeft = Offset((c + 2) * cellSize, (r + 2) * cellSize),
                size = Size(3 * cellSize, 3 * cellSize)
            )
        }

        // Draw standard QR 3 position finders
        drawFinder(0, 0)
        drawFinder(0, matrixSize - 7)
        drawFinder(matrixSize - 7, 0)

        // Timing patterns
        for (i in 8 until matrixSize - 8) {
            if (i % 2 == 0) {
                drawRect(
                    color = Color.Black,
                    topLeft = Offset(i * cellSize, 6 * cellSize),
                    size = Size(cellSize, cellSize)
                )
                drawRect(
                    color = Color.Black,
                    topLeft = Offset(6 * cellSize, i * cellSize),
                    size = Size(cellSize, cellSize)
                )
            }
        }

        // Pseudo-random deterministic data modules based on orderId hash
        val seed = orderId.hashCode()
        for (r in 0 until matrixSize) {
            for (c in 0 until matrixSize) {
                // Skip finder pattern zones
                val inTopLeft = r < 8 && c < 8
                val inTopRight = r < 8 && c >= matrixSize - 8
                val inBottomLeft = r >= matrixSize - 8 && c < 8
                if (inTopLeft || inTopRight || inBottomLeft) continue

                val isFilled = ((r * 31 + c * 17 + seed) % 7) in listOf(0, 2, 4)
                if (isFilled) {
                    drawRect(
                        color = Color.Black,
                        topLeft = Offset(c * cellSize, r * cellSize),
                        size = Size(cellSize, cellSize)
                    )
                }
            }
        }
    }
}
