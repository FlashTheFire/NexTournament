package com.nextournament.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.model.UpdateCheckResponse
import com.nextournament.app.data.ota.DownloadState
import com.nextournament.app.ui.theme.ChakraPetch
import com.nextournament.app.ui.theme.CyberAmber
import com.nextournament.app.ui.theme.ElectricBlue
import com.nextournament.app.ui.theme.InterFont
import com.nextournament.app.ui.theme.ObsidianBlack
import com.nextournament.app.ui.theme.SlateCard

@Composable
fun ForcedUpdateDialog(
    updateInfo: UpdateCheckResponse,
    downloadState: DownloadState,
    onStartDownload: () -> Unit,
    onInstallApk: () -> Unit
) {
    Dialog(
        onDismissRequest = { /* Blocked: Forced Update Cannot Be Dismissed */ },
        properties = DialogProperties(
            dismissOnBackPress = false,
            dismissOnClickOutside = false,
            usePlatformDefaultWidth = false
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.85f))
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(8.dp))
                    .background(ObsidianBlack)
                    .border(1.5.dp, CyberAmber, CutCornerShape(8.dp))
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header Icon
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(CyberAmber.copy(alpha = 0.15f))
                        .border(1.dp, CyberAmber, CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_system_update),
                        contentDescription = "System Update",
                        tint = CyberAmber,
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Title
                Text(
                    text = "CRITICAL PROTOCOL UPDATE",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = Color.White,
                    letterSpacing = 1.sp
                )

                Text(
                    text = "Version ${updateInfo.latestVersionName} (Build ${updateInfo.latestVersionCode})",
                    fontFamily = InterFont,
                    fontWeight = FontWeight.Medium,
                    fontSize = 13.sp,
                    color = CyberAmber
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Changelog Box
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 140.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(SlateCard)
                        .padding(12.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    Text(
                        text = "SECURITY & PROTOCOL LOG:",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = ElectricBlue
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = updateInfo.changelog,
                        fontFamily = InterFont,
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.85f),
                        lineHeight = 16.sp
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                // State Handling
                when (downloadState) {
                    is DownloadState.Idle -> {
                        CyberActionButton(
                            text = "DOWNLOAD UPDATE (${updateInfo.downloadSize})",
                            onClick = onStartDownload,
                            modifier = Modifier.fillMaxWidth(),
                            iconRes = R.drawable.ic_download_sharp
                        )
                    }

                    is DownloadState.Progress -> {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "DOWNLOADING PROTOCOL...",
                                    fontFamily = ChakraPetch,
                                    fontSize = 11.sp,
                                    color = ElectricBlue
                                )
                                Text(
                                    text = "${downloadState.progressPercentage}%",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    color = CyberAmber
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            LinearProgressIndicator(
                                progress = { downloadState.progressPercentage / 100f },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(6.dp)
                                    .clip(CutCornerShape(2.dp)),
                                color = CyberAmber,
                                trackColor = SlateCard
                            )
                        }
                    }

                    is DownloadState.VerifyingChecksum -> {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                color = CyberAmber,
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                text = "VERIFYING SHA-256 SIGNATURE...",
                                fontFamily = ChakraPetch,
                                fontSize = 12.sp,
                                color = Color.White
                            )
                        }
                    }

                    is DownloadState.Success -> {
                        CyberActionButton(
                            text = "INSTALL UPDATE NOW",
                            onClick = onInstallApk,
                            modifier = Modifier.fillMaxWidth(),
                            iconRes = R.drawable.ic_system_update
                        )
                    }

                    is DownloadState.Error -> {
                        Text(
                            text = downloadState.message,
                            fontFamily = InterFont,
                            fontSize = 12.sp,
                            color = Color(0xFFEF4444)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        CyberActionButton(
                            text = "RETRY DOWNLOAD",
                            onClick = onStartDownload,
                            modifier = Modifier.fillMaxWidth(),
                            iconRes = R.drawable.ic_download_sharp
                        )
                    }
                }
            }
        }
    }
}
