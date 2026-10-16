package com.nextournament.app.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
import com.nextournament.app.ui.theme.*

@Composable
fun CryptoDepositDialog(
    trc20Address: String,
    bep20Address: String,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var selectedNetwork by remember { mutableStateOf("TRC-20") }
    val currentAddress = if (selectedNetwork == "TRC-20") trc20Address else bep20Address

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
                    .border(1.5.dp, Color(0xFF26A17B), CutCornerShape(8.dp))
                    .padding(22.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_crypto_usdt),
                        contentDescription = "USDT",
                        tint = Color.Unspecified, // Keep branded Tether green
                        modifier = Modifier.size(32.dp)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "TETHER USDT DEPOSIT",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            color = Color.White
                        )
                        Text(
                            text = "INSTANT CRYPTO CREDITING",
                            fontFamily = InterFont,
                            fontSize = 10.sp,
                            color = Color(0xFF26A17B)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(18.dp))

                // Network Selector Tabs
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(SlateElevated)
                        .padding(4.dp)
                ) {
                    listOf("TRC-20", "BEP-20").forEach { net ->
                        val isSelected = selectedNetwork == net
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(CutCornerShape(2.dp))
                                .background(if (isSelected) Color(0xFF26A17B) else Color.Transparent)
                                .clickable { selectedNetwork = net }
                                .padding(vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "$net (USDT)",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = if (isSelected) Color.White else Color.White.copy(alpha = 0.7f)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(18.dp))

                // Address Copy Card
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(SlateCard)
                        .border(1.dp, SlateElevated, CutCornerShape(4.dp))
                        .clickable {
                            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                            clipboard.setPrimaryClip(ClipData.newPlainText("USDT Address", currentAddress))
                            Toast.makeText(context, "$selectedNetwork address copied!", Toast.LENGTH_SHORT).show()
                        }
                        .padding(14.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "DEPOSIT ADDRESS ($selectedNetwork):",
                            fontFamily = InterFont,
                            fontSize = 10.sp,
                            color = Color.White.copy(alpha = 0.6f)
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_copy_sharp),
                                contentDescription = "Copy",
                                tint = Color(0xFF26A17B),
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "COPY",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp,
                                color = Color(0xFF26A17B)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = currentAddress,
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 13.sp,
                        color = Color.White,
                        lineHeight = 18.sp
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Important Warning Box
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0xFF26A17B).copy(alpha = 0.1f))
                        .padding(12.dp)
                ) {
                    Text(
                        text = "• Send ONLY USDT via the $selectedNetwork network to this address.",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.8f)
                    )
                    Text(
                        text = "• Minimum deposit is 10 USDT. Smaller amounts cannot be recovered.",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.8f)
                    )
                    Text(
                        text = "• Funds credit automatically after 1 network block confirmation.",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.8f)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                TextButton(onClick = onDismiss) {
                    Text(
                        text = "CLOSE GATEWAY",
                        fontFamily = ChakraPetch,
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
            }
        }
    }
}
