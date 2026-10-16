package com.nextournament.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.security.DeviceSecurityReport
import com.nextournament.app.ui.theme.ChakraPetch
import com.nextournament.app.ui.theme.CrimsonRed
import com.nextournament.app.ui.theme.InterFont
import com.nextournament.app.ui.theme.ObsidianBlack
import com.nextournament.app.ui.theme.SlateCard

@Composable
fun AntiCheatViolationDialog(
    securityReport: DeviceSecurityReport,
    onDismissOrAcknowledge: () -> Unit
) {
    Dialog(
        onDismissRequest = { /* Cannot dismiss without acknowledgment */ },
        properties = DialogProperties(
            dismissOnBackPress = false,
            dismissOnClickOutside = false,
            usePlatformDefaultWidth = false
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.88f))
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(8.dp))
                    .background(ObsidianBlack)
                    .border(1.5.dp, CrimsonRed, CutCornerShape(8.dp))
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header Shield Icon
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(CrimsonRed.copy(alpha = 0.15f))
                        .border(1.dp, CrimsonRed, CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_gpp_bad),
                        contentDescription = "Integrity Violation",
                        tint = CrimsonRed,
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Alert Title
                Text(
                    text = "INTEGRITY PROTOCOL VIOLATION",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = CrimsonRed,
                    textAlign = TextAlign.Center,
                    letterSpacing = 1.sp
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Fair Play & Anti-Cheat System has detected an unauthorized environment or memory modification attempt on this device.",
                    fontFamily = InterFont,
                    fontSize = 12.sp,
                    color = Color.White.copy(alpha = 0.85f),
                    textAlign = TextAlign.Center,
                    lineHeight = 16.sp
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Violation Breakdown Card
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(SlateCard)
                        .padding(12.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "SECURITY TIER:",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.6f)
                        )
                        Text(
                            text = securityReport.tier.name,
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = CrimsonRed
                        )
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "VIOLATION FLAGS: ${securityReport.details}",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.75f)
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "TOKEN: ${securityReport.integrityToken.take(16)}...",
                        fontFamily = InterFont,
                        fontSize = 10.sp,
                        color = Color.White.copy(alpha = 0.4f)
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                CyberActionButton(
                    text = "ACKNOWLEDGE & EXIT LOBBY",
                    onClick = onDismissOrAcknowledge,
                    modifier = Modifier.fillMaxWidth(),
                    iconRes = R.drawable.ic_shield_sharp
                )
            }
        }
    }
}
