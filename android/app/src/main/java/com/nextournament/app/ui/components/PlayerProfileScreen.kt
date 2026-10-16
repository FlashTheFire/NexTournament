package com.nextournament.app.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.nextournament.app.R
import com.nextournament.app.data.local.UserEntity
import com.nextournament.app.ui.theme.*

@Composable
fun PlayerProfileScreen(
    user: UserEntity,
    onSaveGameProfile: (game: String, uid: String, ign: String) -> Unit,
    onSyncTelegramClick: () -> Unit,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val streakComposition by rememberLottieComposition(
        LottieCompositionSpec.Asset("lottie/daily_streak_fire.json")
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(ObsidianBlack)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        // Top Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_person_sharp),
                    contentDescription = null,
                    tint = CyberAmber,
                    modifier = Modifier.size(26.dp)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Column {
                    Text(
                        text = user.username.uppercase(),
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp,
                        color = Color.White
                    )
                    Text(
                        text = "UID: #${user.id} • ${user.phoneNumber}",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                }
            }

            CyberBadge(
                text = "TIER ${user.verificationLevel} PRO",
                color = if (user.isVerified) CyberEmerald else CyberAmber,
                backgroundColor = SlateElevated
            )
        }

        Spacer(modifier = Modifier.height(18.dp))

        // Esports Career Stats Card
        Card(
            shape = CutCornerCard,
            colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
            border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, SlateElevated),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "ESPORTS CAREER PERFORMANCE",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = ElectricBlue
                )

                Spacer(modifier = Modifier.height(14.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    StatBox(label = "TOTAL PRIZE WON", value = "₹%.0f".format(user.walletBalance * 2.5), color = CyberEmerald)
                    StatBox(label = "WIN RATE", value = "68.4%", color = Color(0xFFFACC15))
                    StatBox(label = "K/D RATIO", value = "4.2", color = CrimsonRed)
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Streak Banner
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(SlateElevated)
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier.size(28.dp)) {
                            LottieAnimation(
                                composition = streakComposition,
                                iterations = LottieConstants.IterateForever,
                                modifier = Modifier.fillMaxSize()
                            )
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "ACTIVE TOURNAMENT STREAK",
                            fontFamily = ChakraPetch,
                            fontSize = 11.sp,
                            color = CyberAmber
                        )
                    }

                    Text(
                        text = "${user.dailyStreak} DAYS CONSECUTIVE",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = CyberAmber
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(18.dp))

        // Cross-Platform Telegram Sync Card
        Card(
            shape = CutCornerCard,
            colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
            border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, SlateElevated),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "CROSS-PLATFORM TELEGRAM BOT SYNC",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = ElectricBlue
                    )
                    CyberBadge(
                        text = if (user.telegramId != null) "SYNCED" else "UNLINKED",
                        color = if (user.telegramId != null) CyberEmerald else CyberAmber,
                        backgroundColor = SlateElevated
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = if (user.telegramId != null)
                        "Linked to Telegram ID: ${user.telegramId}. Wallet, prizes, and match notifications are synced in real time."
                    else
                        "Link your Telegram account to receive instant room alerts, join match chats, and sync wallet balance with the NexTournament Bot.",
                    fontFamily = InterFont,
                    fontSize = 11.sp,
                    color = Color.White.copy(alpha = 0.7f),
                    lineHeight = 16.sp
                )

                Spacer(modifier = Modifier.height(12.dp))

                CyberActionButton(
                    text = if (user.telegramId != null) "GENERATE /SYNC CODE" else "LINK TELEGRAM BOT",
                    onClick = onSyncTelegramClick,
                    modifier = Modifier.fillMaxWidth(),
                    iconRes = R.drawable.ic_bolt_sharp
                )
            }
        }

        Spacer(modifier = Modifier.height(18.dp))

        // Verified Game Profiles
        Text(
            text = "VERIFIED GAME PROFILES",
            fontFamily = ChakraPetch,
            fontWeight = FontWeight.Bold,
            fontSize = 14.sp,
            color = Color.White
        )

        Spacer(modifier = Modifier.height(10.dp))

        GameProfileCard(
            gameName = "Free Fire MAX",
            currentIgn = user.inGameName ?: "FlashFire99",
            currentUid = "982341209",
            isVerified = true
        )

        Spacer(modifier = Modifier.height(10.dp))

        GameProfileCard(
            gameName = "BGMI",
            currentIgn = "Not Linked",
            currentUid = "5192830192",
            isVerified = false
        )

        Spacer(modifier = Modifier.height(16.dp))

        TextButton(
            onClick = onBackClick,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = "BACK TO LOBBY",
                fontFamily = ChakraPetch,
                fontSize = 12.sp,
                color = Color.White.copy(alpha = 0.6f)
            )
        }
    }
}

@Composable
fun GameProfileCard(
    gameName: String,
    currentIgn: String,
    currentUid: String,
    isVerified: Boolean
) {
    Card(
        shape = CutCornerCard,
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, SlateElevated),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = gameName.uppercase(),
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = Color.White
                )
                Text(
                    text = "IGN: $currentIgn • UID: $currentUid",
                    fontFamily = InterFont,
                    fontSize = 11.sp,
                    color = Color.White.copy(alpha = 0.6f)
                )
            }

            CyberBadge(
                text = if (isVerified) "VERIFIED" else "PENDING",
                color = if (isVerified) CyberEmerald else CyberAmber,
                backgroundColor = SlateElevated
            )
        }
    }
}

@Composable
private fun StatBox(label: String, value: String, color: Color) {
    Column {
        Text(
            text = label,
            fontFamily = InterFont,
            fontSize = 10.sp,
            color = Color.White.copy(alpha = 0.5f)
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            fontFamily = ChakraPetch,
            fontWeight = FontWeight.Bold,
            fontSize = 16.sp,
            color = color
        )
    }
}
