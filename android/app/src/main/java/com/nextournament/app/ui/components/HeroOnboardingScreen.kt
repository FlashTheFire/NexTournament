package com.nextournament.app.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.model.AuthResponse
import com.nextournament.app.data.model.GoogleAuthRequest
import com.nextournament.app.data.network.AuthApiService
import com.nextournament.app.ui.theme.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.UUID

@Composable
fun HeroOnboardingScreen(
    authApiService: AuthApiService?,
    onAuthSuccess: (AuthResponse) -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val pagerState = rememberPagerState(pageCount = { 3 })

    // Auth State Dialogs
    var showGoogleAuthDialog by remember { mutableStateOf(false) }
    var showTelegramSyncDialog by remember { mutableStateOf(false) }
    var activeTelegramSyncToken by remember { mutableStateOf<String?>(null) }
    var isTelegramPolling by remember { mutableStateOf(false) }
    var telegramSyncError by remember { mutableStateOf<String?>(null) }

    // Dynamic background image selection based on active pager page
    val backgroundRes = when (pagerState.currentPage) {
        0 -> R.drawable.hero_bg_battleground
        1 -> R.drawable.hero_bg_cyber_arena
        else -> R.drawable.hero_bg_tournament_stage
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ObsidianBlack)
    ) {
        // 1. Dynamic Hero Background Image
        Image(
            painter = painterResource(id = backgroundRes),
            contentDescription = "Esports Hero Background",
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )

        // 2. Brutalist Gradient Scrim for Content Legibility
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(
                            ObsidianBlack.copy(alpha = 0.55f),
                            ObsidianBlack.copy(alpha = 0.82f),
                            ObsidianBlack.copy(alpha = 0.98f)
                        ),
                        startY = 0f,
                        endY = 1800f
                    )
                )
        )

        // 3. Main Onboarding Layout
        Column(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .padding(horizontal = 16.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // TOP HEADER: Platform Title & Live Pulse Pill
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "NEXTOURNAMENT",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Black,
                        color = CyberAmber,
                        fontSize = 18.sp,
                        letterSpacing = 1.5.sp
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(3.dp))
                            .background(SlateElevated)
                            .padding(horizontal = 5.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "PRO",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 9.sp,
                            color = NeonCyan
                        )
                    }
                }

                // Live Players Pulse Indicator
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = SlateCardSurface.copy(alpha = 0.85f),
                    border = BorderStroke(1.dp, CyberEmerald.copy(alpha = 0.5f))
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Pulsing Green LED
                        val infiniteTransition = rememberInfiniteTransition(label = "pulse")
                        val alpha by infiniteTransition.animateFloat(
                            initialValue = 0.3f,
                            targetValue = 1f,
                            animationSpec = infiniteRepeatable(
                                animation = tween(800, easing = LinearEasing),
                                repeatMode = RepeatMode.Reverse
                            ),
                            label = "alpha"
                        )
                        Box(
                            modifier = Modifier
                                .size(7.dp)
                                .clip(CircleShape)
                                .background(CyberEmerald.copy(alpha = alpha))
                        )
                        Spacer(modifier = Modifier.width(5.dp))
                        Text(
                            text = "5,420+ ONLINE",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 10.sp,
                            color = CyberEmerald
                        )
                    }
                }
            }

            // MIDDLE: Interactive Gen-Z Hero Pager
            HorizontalPager(
                state = pagerState,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(vertical = 12.dp)
            ) { page ->
                when (page) {
                    0 -> HeroSlideWhatItIs()
                    1 -> HeroSlideHowItWorks()
                    2 -> HeroSlideHowYouEarn()
                }
            }

            // PAGER INDICATORS (Brutalist Bars)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 12.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                repeat(3) { index ->
                    val isSelected = pagerState.currentPage == index
                    Box(
                        modifier = Modifier
                            .height(4.dp)
                            .width(if (isSelected) 28.dp else 10.dp)
                            .clip(CutCornerShape(2.dp))
                            .background(if (isSelected) NeonCyan else Color.White.copy(alpha = 0.25f))
                            .clickable {
                                coroutineScope.launch { pagerState.animateScrollToPage(index) }
                            }
                    )
                    if (index < 2) Spacer(modifier = Modifier.width(6.dp))
                }
            }

            // BOTTOM AUTH HUB: ONLY 2 AUTH OPTIONS FOREVER
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = "SELECT ACCESS METHOD",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp,
                    color = Color.White.copy(alpha = 0.5f),
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )

                // OPTION 1: GOOGLE (MAIL)
                Surface(
                    shape = CutCornerShape(8.dp),
                    color = Color.White,
                    border = BorderStroke(1.dp, Color.White),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp)
                        .clickable { showGoogleAuthDialog = true }
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_google_logo),
                            contentDescription = "Google Logo",
                            tint = Color.Unspecified,
                            modifier = Modifier.size(22.dp)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            text = "CONTINUE WITH GOOGLE",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = ObsidianBlack,
                            letterSpacing = 0.8.sp
                        )
                    }
                }

                // OPTION 2: TELEGRAM BOT SYNC
                Surface(
                    shape = CutCornerShape(8.dp),
                    color = Color(0xFF229ED9),
                    border = BorderStroke(1.dp, Color(0xFF29B6F6)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp)
                        .clickable {
                            val key = UUID.randomUUID().toString().replace("-", "").take(10)
                            val time = System.currentTimeMillis() / 1000
                            val deviceTag = android.os.Build.MODEL.filter { it.isLetterOrDigit() }.take(6).ifEmpty { "app" }
                            val token = "sync_${key}_${deviceTag}_${time}"

                            activeTelegramSyncToken = token
                            showTelegramSyncDialog = true
                            isTelegramPolling = true
                            telegramSyncError = null

                            // Launch Telegram Bot with Deep-Link Handshake (native app first, browser fallback)
                            val tgAppUri = "tg://resolve?domain=Testing1stTime_Bot&start=$token"
                            val botWebLink = "https://t.me/Testing1stTime_Bot?start=$token"
                            try {
                                val tgIntent = Intent(Intent.ACTION_VIEW, Uri.parse(tgAppUri)).apply {
                                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                                }
                                context.startActivity(tgIntent)
                            } catch (_: Exception) {
                                try {
                                    val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse(botWebLink)).apply {
                                        flags = Intent.FLAG_ACTIVITY_NEW_TASK
                                    }
                                    context.startActivity(webIntent)
                                } catch (e: Exception) {
                                    Toast.makeText(context, "Could not open Telegram: ${e.message}", Toast.LENGTH_SHORT).show()
                                }
                            }
                        }
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_telegram_logo),
                            contentDescription = "Telegram Logo",
                            tint = Color.White,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            text = "SYNC WITH TELEGRAM BOT",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = Color.White,
                            letterSpacing = 0.8.sp
                        )
                    }
                }

                // Security Seal Footer
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 4.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_shield_sharp),
                        contentDescription = null,
                        tint = NeonCyan.copy(alpha = 0.7f),
                        modifier = Modifier.size(12.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "PROTECTED BY NEXGUARD™ 3-TIER CRYPTOGRAPHIC GATEKEEPER",
                        fontFamily = ChakraPetch,
                        fontSize = 8.sp,
                        color = Color.White.copy(alpha = 0.45f)
                    )
                }
            }
        }

        // ====================================================================
        // DIALOG 1: GOOGLE SIGN-IN MODAL
        // ====================================================================
        if (showGoogleAuthDialog) {
            GoogleSignInModal(
                onConfirmEmail = { email, displayName ->
                    showGoogleAuthDialog = false
                    coroutineScope.launch {
                        try {
                            val res = authApiService?.loginWithGoogle(
                                GoogleAuthRequest(
                                    email = email,
                                    displayName = displayName,
                                    deviceId = "AND-${UUID.randomUUID().toString().take(8)}"
                                )
                            )
                            if (res?.isSuccessful == true && res.body() != null) {
                                Toast.makeText(context, "Welcome ${res.body()!!.user.firstName}!", Toast.LENGTH_SHORT).show()
                                onAuthSuccess(res.body()!!)
                            } else {
                                Toast.makeText(context, "Google Sign-In failed: ${res?.code()}", Toast.LENGTH_LONG).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, "Connection error: ${e.message}", Toast.LENGTH_LONG).show()
                        }
                    }
                },
                onDismiss = { showGoogleAuthDialog = false }
            )
        }

        // ====================================================================
        // DIALOG 2: TELEGRAM BOT HANDSHAKE RADAR MODAL
        // ====================================================================
        if (showTelegramSyncDialog && activeTelegramSyncToken != null) {
            val token = activeTelegramSyncToken!!

            // Background Poller: Checks handshake status every 2 seconds for up to 90 seconds
            LaunchedEffect(token) {
                var attempts = 0
                while (isTelegramPolling && attempts < 45) {
                    delay(2000)
                    attempts++
                    try {
                        val res = authApiService?.checkTelegramSyncStatus(token)
                        if (res?.isSuccessful == true && res.body() != null) {
                            val authRes = res.body()!!
                            isTelegramPolling = false
                            showTelegramSyncDialog = false
                            Toast.makeText(context, "⚡ Telegram Linked: ${authRes.user.firstName}!", Toast.LENGTH_LONG).show()
                            onAuthSuccess(authRes)
                            break
                        }
                    } catch (_: Exception) {}
                }
                if (isTelegramPolling && attempts >= 45) {
                    telegramSyncError = "Handshake timed out. Tap 'START' in the bot and try again."
                    isTelegramPolling = false
                }
            }

            TelegramSyncRadarModal(
                syncToken = token,
                isPolling = isTelegramPolling,
                errorMessage = telegramSyncError,
                onReopenBot = {
                    val tgAppUri = "tg://resolve?domain=Testing1stTime_Bot&start=$token"
                    val botWebLink = "https://t.me/Testing1stTime_Bot?start=$token"
                    try {
                        val tgIntent = Intent(Intent.ACTION_VIEW, Uri.parse(tgAppUri)).apply {
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK
                        }
                        context.startActivity(tgIntent)
                    } catch (_: Exception) {
                        try {
                            val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse(botWebLink)).apply {
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                            }
                            context.startActivity(webIntent)
                        } catch (_: Exception) {}
                    }
                },
                onDismiss = {
                    isTelegramPolling = false
                    showTelegramSyncDialog = false
                }
            )
        }
    }
}

// ============================================================================
// HERO SLIDE 1: WHAT IT IS
// ============================================================================
@Composable
private fun HeroSlideWhatItIs() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center
    ) {
        CyberBadge(
            text = "OFFICIAL COMPETITIVE LEAGUE",
            color = CyberAmber,
            textColor = ObsidianBlack
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = "DOMINATE.\nSURVIVE.\nCASH OUT.",
            fontFamily = OrbitronFont,
            fontWeight = FontWeight.Black,
            fontSize = 32.sp,
            lineHeight = 38.sp,
            color = Color.White
        )

        Spacer(modifier = Modifier.height(14.dp))

        Text(
            text = "India's premier high-stakes esports arena for Free Fire MAX. Verified mobile players, automated room access, and instant UPI & USDT payouts.",
            fontFamily = ChakraPetch,
            fontSize = 13.sp,
            lineHeight = 18.sp,
            color = Color.White.copy(alpha = 0.75f)
        )

        Spacer(modifier = Modifier.height(18.dp))

        // Feature Matrix Badges
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            HeroStatCard(
                modifier = Modifier.weight(1f),
                title = "DAILY POOL",
                value = "₹2,50,000+",
                iconRes = R.drawable.ic_trophy_sharp,
                tint = AmberGold
            )
            HeroStatCard(
                modifier = Modifier.weight(1f),
                title = "KILL BOUNTY",
                value = "₹20 / FRAG",
                iconRes = R.drawable.ic_skull_kill_sharp,
                tint = NeonCyan
            )
            HeroStatCard(
                modifier = Modifier.weight(1f),
                title = "ANTI-CHEAT",
                value = "KERNEL AI",
                iconRes = R.drawable.ic_shield_sharp,
                tint = CyberEmerald
            )
        }
    }
}

// ============================================================================
// HERO SLIDE 2: HOW IT WORKS
// ============================================================================
@Composable
private fun HeroSlideHowItWorks() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center
    ) {
        CyberBadge(
            text = "4-STEP MATCH PIPELINE",
            color = NeonCyan,
            textColor = ObsidianBlack
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "HOW TO PLAY",
            fontFamily = OrbitronFont,
            fontWeight = FontWeight.Black,
            fontSize = 26.sp,
            color = Color.White
        )

        Spacer(modifier = Modifier.height(14.dp))

        val steps = listOf(
            Triple("1. CHOOSE MATCH", "Pick Map (Bermuda, Kalahari) & Format (Solo, Duo, Squad)", R.drawable.ic_sports_esports),
            Triple("2. LOCK YOUR SEAT", "Reserve cinema seat with live 120s timer lock", R.drawable.ic_event_seat_sharp),
            Triple("3. ROOM VAULT", "Room ID & Pass unlocked at T-15m with screenshot shield", R.drawable.ic_vpn_key_sharp),
            Triple("4. SUBMIT SCORECARD", "AI OCR verifies your kills & rank for instant credit", R.drawable.ic_photo_camera_sharp)
        )

        steps.forEach { (title, subtitle, icon) ->
            Surface(
                shape = CutCornerShape(6.dp),
                color = SlateCardSurface.copy(alpha = 0.85f),
                border = BorderStroke(1.dp, SlateElevated),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(34.dp)
                            .clip(CutCornerShape(4.dp))
                            .background(SlateElevated),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            painter = painterResource(id = icon),
                            contentDescription = null,
                            tint = NeonCyan,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = title,
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = Color.White
                        )
                        Text(
                            text = subtitle,
                            fontFamily = ChakraPetch,
                            fontSize = 10.sp,
                            color = Color.White.copy(alpha = 0.65f)
                        )
                    }
                }
            }
        }
    }
}

// ============================================================================
// HERO SLIDE 3: HOW YOU EARN & WITHDRAW
// ============================================================================
@Composable
private fun HeroSlideHowYouEarn() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center
    ) {
        CyberBadge(
            text = "DUAL-CURRENCY REWARDS",
            color = CyberEmerald,
            textColor = ObsidianBlack
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "EARN & WITHDRAW",
            fontFamily = OrbitronFont,
            fontWeight = FontWeight.Black,
            fontSize = 26.sp,
            color = Color.White
        )

        Spacer(modifier = Modifier.height(14.dp))

        Card(
            shape = CutCornerShape(8.dp),
            colors = CardDefaults.cardColors(containerColor = SlateCardSurface.copy(alpha = 0.9f)),
            border = BorderStroke(1.dp, CyberEmerald.copy(alpha = 0.4f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_wallet_sharp),
                        contentDescription = null,
                        tint = CyberEmerald,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "DUAL ESPORTS WALLET",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = Color.White
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "• GAME CASH: Used for booking match seats and squad slots.\n• WIN CASH: Earned via rank placement & kills. 100% withdrawable anytime!",
                    fontFamily = ChakraPetch,
                    fontSize = 11.sp,
                    lineHeight = 16.sp,
                    color = Color.White.copy(alpha = 0.8f)
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "SUPPORTED PAYOUTS:",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 9.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        listOf("GPAY", "PHONEPE", "PAYTM", "USDT").forEach { app ->
                            Box(
                                modifier = Modifier
                                    .clip(CutCornerShape(2.dp))
                                    .background(SlateElevated)
                                    .padding(horizontal = 5.dp, vertical = 2.dp)
                            ) {
                                Text(
                                    text = app,
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 8.sp,
                                    color = NeonCyan
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroStatCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    iconRes: Int,
    tint: Color
) {
    Card(
        shape = CutCornerShape(6.dp),
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface.copy(alpha = 0.85f)),
        border = BorderStroke(1.dp, SlateElevated),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier.padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                painter = painterResource(id = iconRes),
                contentDescription = null,
                tint = tint,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                fontFamily = OrbitronFont,
                fontWeight = FontWeight.Bold,
                fontSize = 10.sp,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            Text(
                text = title,
                fontFamily = ChakraPetch,
                fontSize = 8.sp,
                color = Color.White.copy(alpha = 0.55f),
                textAlign = TextAlign.Center
            )
        }
    }
}

// ============================================================================
// MODAL: GOOGLE SIGN-IN DIALOG
// ============================================================================
@Composable
private fun GoogleSignInModal(
    onConfirmEmail: (String, String) -> Unit,
    onDismiss: () -> Unit
) {
    var emailInput by remember { mutableStateOf("") }
    var nameInput by remember { mutableStateOf("") }

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
            Card(
                shape = CutCornerShape(10.dp),
                colors = CardDefaults.cardColors(containerColor = CyberDarkCard),
                border = BorderStroke(1.dp, Color.White.copy(alpha = 0.3f)),
                modifier = Modifier.fillMaxWidth().wrapContentHeight()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_google_logo),
                        contentDescription = "Google",
                        tint = Color.Unspecified,
                        modifier = Modifier.size(36.dp)
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        text = "SIGN IN WITH GOOGLE",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = Color.White
                    )

                    Text(
                        text = "Enter your Google Mail account to sync stats and payouts",
                        fontFamily = ChakraPetch,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.6f),
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = emailInput,
                        onValueChange = { emailInput = it },
                        label = { Text("Google Email Address", fontFamily = ChakraPetch, fontSize = 11.sp) },
                        placeholder = { Text("yourname@gmail.com", fontFamily = ChakraPetch, fontSize = 11.sp) },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NeonCyan,
                            unfocusedBorderColor = SlateElevated,
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    OutlinedTextField(
                        value = nameInput,
                        onValueChange = { nameInput = it },
                        label = { Text("Display Name (Optional)", fontFamily = ChakraPetch, fontSize = 11.sp) },
                        placeholder = { Text("Harsh", fontFamily = ChakraPetch, fontSize = 11.sp) },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NeonCyan,
                            unfocusedBorderColor = SlateElevated,
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    Button(
                        onClick = {
                            if (emailInput.contains("@") && emailInput.contains(".")) {
                                onConfirmEmail(emailInput.trim(), nameInput.trim().ifEmpty { emailInput.split("@")[0] })
                            }
                        },
                        shape = CutCornerShape(6.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth().height(48.dp)
                    ) {
                        Text(
                            text = "CONFIRM & ENTER ARENA",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = ObsidianBlack
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    TextButton(onClick = onDismiss) {
                        Text(
                            text = "CANCEL",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.5f)
                        )
                    }
                }
            }
        }
    }
}

// ============================================================================
// MODAL: TELEGRAM SYNC RADAR DIALOG (ZERO-TYPING INBUILD BOT LINK)
// ============================================================================
@Composable
private fun TelegramSyncRadarModal(
    syncToken: String,
    isPolling: Boolean,
    errorMessage: String?,
    onReopenBot: () -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val fullBotLink = "https://t.me/Testing1stTime_Bot?start=$syncToken"

    // Parse key_user_time components for visual verification
    val parts = syncToken.split("_")
    val keyPart = parts.getOrNull(1) ?: syncToken
    val devicePart = parts.getOrNull(2) ?: "mobile"
    val timePart = parts.getOrNull(3) ?: ""

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.92f))
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Card(
                shape = CutCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = CyberDarkCard),
                border = BorderStroke(1.5.dp, Color(0xFF29B6F6)),
                modifier = Modifier.fillMaxWidth().wrapContentHeight()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Header Tag
                    Row(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(Color(0xFF229ED9).copy(alpha = 0.2f))
                            .border(1.dp, Color(0xFF29B6F6), CutCornerShape(4.dp))
                            .padding(horizontal = 8.dp, vertical = 3.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(NeonCyan)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "ZERO-CLICK BOT HANDSHAKE",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 9.sp,
                            color = NeonCyan,
                            letterSpacing = 1.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Pulsing Telegram Icon with Radar Waves
                    val infiniteTransition = rememberInfiniteTransition(label = "telegramPulse")
                    val pulseScale by infiniteTransition.animateFloat(
                        initialValue = 0.96f,
                        targetValue = 1.08f,
                        animationSpec = infiniteRepeatable(
                            animation = tween(900, easing = EaseInOutQuad),
                            repeatMode = RepeatMode.Reverse
                        ),
                        label = "scale"
                    )

                    Box(
                        modifier = Modifier
                            .size(68.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF229ED9).copy(alpha = 0.22f))
                            .border(1.5.dp, Color(0xFF29B6F6).copy(alpha = 0.6f), CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_telegram_logo),
                            contentDescription = "Telegram",
                            tint = Color.White,
                            modifier = Modifier.size(36.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = "SYNCING WITH @Testing1stTime_Bot",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = Color.White,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "No user ID or code needed. Tap 'START' in the bot to automatically authenticate your app!",
                        fontFamily = ChakraPetch,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.75f),
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    // INBUILD BOT LINK CONTAINER WITH 1-TAP COPY
                    Surface(
                        shape = CutCornerShape(6.dp),
                        color = SlateElevated,
                        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.15f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "INBUILD BOT LINK",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 9.sp,
                                    color = Color.White.copy(alpha = 0.5f)
                                )
                                Text(
                                    text = "TAP TO COPY",
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 9.sp,
                                    color = NeonCyan
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable {
                                        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
                                        val clip = ClipData.newPlainText("Telegram Bot Link", fullBotLink)
                                        clipboard?.setPrimaryClip(clip)
                                        Toast.makeText(context, "Bot Link copied to clipboard!", Toast.LENGTH_SHORT).show()
                                    },
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = fullBotLink,
                                    fontFamily = ChakraPetch,
                                    fontSize = 10.sp,
                                    color = Color(0xFF29B6F6),
                                    maxLines = 1,
                                    modifier = Modifier.weight(1f)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Surface(
                                    shape = RoundedCornerShape(4.dp),
                                    color = Color(0xFF229ED9).copy(alpha = 0.3f),
                                    border = BorderStroke(1.dp, Color(0xFF29B6F6).copy(alpha = 0.5f))
                                ) {
                                    Text(
                                        text = "COPY",
                                        fontFamily = OrbitronFont,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 8.sp,
                                        color = Color.White,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Tech Diagnostic Nonce Bar: key_user_time
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(CutCornerShape(4.dp))
                            .background(Color.White.copy(alpha = 0.04f))
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "KEY: ${keyPart.take(8)}...",
                            fontFamily = ChakraPetch,
                            fontSize = 9.sp,
                            color = CyberEmerald
                        )
                        Text(
                            text = "DEV: $devicePart",
                            fontFamily = ChakraPetch,
                            fontSize = 9.sp,
                            color = Color.White.copy(alpha = 0.5f)
                        )
                        Text(
                            text = "EXP: 10 MINS",
                            fontFamily = ChakraPetch,
                            fontSize = 9.sp,
                            color = CyberAmber
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Radar Polling Indicator
                    if (isPolling) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(
                                color = Color(0xFF29B6F6),
                                strokeWidth = 2.dp,
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Auto-detecting your start command in bot...",
                                fontFamily = ChakraPetch,
                                fontSize = 10.sp,
                                color = NeonCyan
                            )
                        }
                    } else if (errorMessage != null) {
                        Text(
                            text = errorMessage,
                            fontFamily = ChakraPetch,
                            fontSize = 11.sp,
                            color = Color(0xFFFF5252),
                            textAlign = TextAlign.Center
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // PRIMARY ACTION: OPEN BOT DIRECTLY
                    Button(
                        onClick = onReopenBot,
                        shape = CutCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF229ED9)),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_telegram_logo),
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "OPEN IN TELEGRAM BOT",
                                fontFamily = OrbitronFont,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp,
                                color = Color.White
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    TextButton(onClick = onDismiss) {
                        Text(
                            text = "CANCEL",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.45f)
                        )
                    }
                }
            }
        }
    }
}
