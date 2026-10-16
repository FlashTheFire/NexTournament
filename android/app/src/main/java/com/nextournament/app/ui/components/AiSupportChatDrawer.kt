package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
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
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

enum class SupportActionType {
    NONE,
    UTR_INPUT,
    UPLOAD_SCREENSHOT,
    TICKET_CREATED
}

data class SupportMessage(
    val id: String,
    val sender: String,
    val text: String,
    val isUser: Boolean,
    val timestamp: String,
    val actionType: SupportActionType = SupportActionType.NONE,
    val utrNumber: String? = null,
    val attachedScreenshotName: String? = null
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AiSupportChatDrawer(
    userIgn: String,
    onCreditBalance: (Double) -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()
    val listState = rememberLazyListState()

    var messages by remember {
        mutableStateOf(
            listOf(
                SupportMessage(
                    id = "welcome_1",
                    sender = "NEX-AI ASSISTANT",
                    text = "Welcome to NexTournament 24/7 AI Support! How can I assist you with your wallet, deposits, or tournaments today?",
                    isUser = false,
                    timestamp = "Online",
                    actionType = SupportActionType.NONE
                )
            )
        )
    }

    var inputText by remember { mutableStateOf("") }
    var utrInputText by remember { mutableStateOf("") }
    var selectedScreenshot by remember { mutableStateOf<String?>(null) }
    var isCheckingUtr by remember { mutableStateOf(false) }

    val quickChips = listOf(
        "💳 Paid but Amount Not Added (UTR Help)",
        "🎮 Room ID & Password Policy",
        "💸 Instant Withdrawal Limits",
        "🛡️ FairPlay Anti-Cheat Rules"
    )

    fun handleUserQuery(query: String) {
        val userMsg = SupportMessage(
            id = System.currentTimeMillis().toString(),
            sender = userIgn,
            text = query,
            isUser = true,
            timestamp = "Just now"
        )
        messages = messages + userMsg

        coroutineScope.launch {
            delay(100)
            listState.animateScrollToItem(messages.size - 1)
            delay(800)

            val lower = query.lowercase()
            when {
                lower.contains("paid") || lower.contains("utr") || lower.contains("amount") || lower.contains("deposit") -> {
                    val aiResponse = SupportMessage(
                        id = (System.currentTimeMillis() + 1).toString(),
                        sender = "NEX-AI ASSISTANT",
                        text = "I understand your deposit hasn't appeared yet. Please enter your 12-digit UTR / UPI Reference Number below so I can instantly check our Paytm bank gateway:",
                        isUser = false,
                        timestamp = "Just now",
                        actionType = SupportActionType.UTR_INPUT
                    )
                    messages = messages + aiResponse
                }
                lower.contains("room") || lower.contains("password") -> {
                    val aiResponse = SupportMessage(
                        id = (System.currentTimeMillis() + 1).toString(),
                        sender = "NEX-AI ASSISTANT",
                        text = "Room ID & Password unlock exactly T-15 minutes before match start time in the Room Vault. Only verified enrolled players get access.",
                        isUser = false,
                        timestamp = "Just now"
                    )
                    messages = messages + aiResponse
                }
                lower.contains("withdrawal") || lower.contains("payout") -> {
                    val aiResponse = SupportMessage(
                        id = (System.currentTimeMillis() + 1).toString(),
                        sender = "NEX-AI ASSISTANT",
                        text = "Instant withdrawals are processed within 3 minutes via UPI and USDT. Minimum withdrawal is ₹100 from your Withdrawable Winnings.",
                        isUser = false,
                        timestamp = "Just now"
                    )
                    messages = messages + aiResponse
                }
                else -> {
                    val aiResponse = SupportMessage(
                        id = (System.currentTimeMillis() + 1).toString(),
                        sender = "NEX-AI ASSISTANT",
                        text = "Thank you for reaching out! Our system is connected to live tournament and payment gateways. You can ask for UTR payment verification, room schedule, or dispute filing.",
                        isUser = false,
                        timestamp = "Just now"
                    )
                    messages = messages + aiResponse
                }
            }
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = SlateCardSurface,
        shape = CutCornerShape(topStart = 8.dp, topEnd = 8.dp),
        dragHandle = {
            Box(
                modifier = Modifier
                    .padding(vertical = 8.dp)
                    .width(48.dp)
                    .height(4.dp)
                    .clip(CutCornerShape(2.dp))
                    .background(SlateElevated)
            )
        }
    ) {
        Column(
            modifier = modifier
                .fillMaxWidth()
                .fillMaxHeight(0.88f)
                .navigationBarsPadding()
                .padding(bottom = 12.dp)
        ) {
            // Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(CutCornerShape(4.dp))
                            .background(ElectricBlue.copy(alpha = 0.15f))
                            .border(1.dp, ElectricBlue, CutCornerShape(4.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_shield_sharp),
                            contentDescription = null,
                            tint = ElectricBlue,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "NEX-AI SUPPORT BOT",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            color = CyberAmber
                        )
                        Text(
                            text = "Automated Bank UTR Check & Dispute Escalation",
                            fontFamily = ChakraPetch,
                            fontSize = 10.sp,
                            color = CyberEmerald
                        )
                    }
                }

                // Close Button
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(SlateElevated)
                        .clickable { onDismiss() },
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "✕", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
            }

            HorizontalDivider(
                color = SlateElevated,
                thickness = 1.dp,
                modifier = Modifier.padding(vertical = 6.dp)
            )

            // Smart Quick Prompt Chips
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(quickChips) { chip ->
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(SlateElevated)
                            .border(BorderStroke(1.dp, ElectricBlue.copy(alpha = 0.4f)), CutCornerShape(4.dp))
                            .clickable { handleUserQuery(chip) }
                            .padding(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = chip,
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Medium,
                            fontSize = 11.sp,
                            color = Color.White
                        )
                    }
                }
            }

            // Chat Messages Stream
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(messages, key = { it.id }) { msg ->
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = if (msg.isUser) Alignment.End else Alignment.Start
                    ) {
                        // Sender Tag
                        Text(
                            text = "${msg.sender} • ${msg.timestamp}",
                            fontFamily = ChakraPetch,
                            fontSize = 9.sp,
                            color = if (msg.isUser) ElectricBlue else CyberAmber.copy(alpha = 0.8f)
                        )
                        Spacer(modifier = Modifier.height(3.dp))

                        // Message Bubble
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(if (msg.isUser) SlateElevated else ObsidianBlack)
                                .border(
                                    BorderStroke(
                                        1.dp,
                                        if (msg.isUser) ElectricBlue.copy(alpha = 0.6f) else SlateElevated
                                    ),
                                    CutCornerShape(4.dp)
                                )
                                .padding(12.dp)
                        ) {
                            Column {
                                Text(
                                    text = msg.text,
                                    fontFamily = InterFont,
                                    fontSize = 13.sp,
                                    color = Color.White
                                )

                                // Interactive UTR Input Card
                                if (msg.actionType == SupportActionType.UTR_INPUT) {
                                    Spacer(modifier = Modifier.height(10.dp))
                                    OutlinedTextField(
                                        value = utrInputText,
                                        onValueChange = {
                                            if (it.length <= 12 && it.all { ch -> ch.isDigit() }) {
                                                utrInputText = it
                                            }
                                        },
                                        label = { Text("12-Digit UTR Number", fontSize = 11.sp, fontFamily = ChakraPetch) },
                                        placeholder = { Text("e.g. 428919283746", fontSize = 11.sp, color = Color.White.copy(alpha = 0.3f)) },
                                        singleLine = true,
                                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                        shape = CutCornerShape(4.dp),
                                        colors = OutlinedTextFieldDefaults.colors(
                                            focusedContainerColor = SlateElevated,
                                            unfocusedContainerColor = SlateElevated,
                                            focusedBorderColor = CyberEmerald,
                                            unfocusedBorderColor = SlateCardSurface,
                                            focusedTextColor = Color.White,
                                            unfocusedTextColor = Color.White
                                        ),
                                        modifier = Modifier.fillMaxWidth()
                                    )

                                    Spacer(modifier = Modifier.height(8.dp))

                                    CyberActionButton(
                                        text = if (isCheckingUtr) "VERIFYING WITH GATEWAY..." else "⚡ CHECK UTR WITH BANK",
                                        onClick = {
                                            if (utrInputText.length == 12) {
                                                isCheckingUtr = true
                                                val enteredUtr = utrInputText
                                                coroutineScope.launch {
                                                    delay(1200)
                                                    isCheckingUtr = false
                                                    // Auto-Check Logic:
                                                    // If UTR ends with even digit: SUCCESS! Auto-credit.
                                                    // If UTR ends with odd digit: NOT FOUND, ask for screenshot escalation to admin!
                                                    val isAutoSuccess = enteredUtr.last().digitToInt() % 2 == 0
                                                    if (isAutoSuccess) {
                                                        onCreditBalance(500.0)
                                                        val successMsg = SupportMessage(
                                                            id = System.currentTimeMillis().toString(),
                                                            sender = "NEX-AI ASSISTANT",
                                                            text = "✅ SUCCESS! UTR $enteredUtr was found in our Paytm Settlement Feed.\n\n₹500.00 has been credited to your game balance instantly! Check your wallet ledger.",
                                                            isUser = false,
                                                            timestamp = "Just now"
                                                        )
                                                        messages = messages + successMsg
                                                    } else {
                                                        val failMsg = SupportMessage(
                                                            id = System.currentTimeMillis().toString(),
                                                            sender = "NEX-AI ASSISTANT",
                                                            text = "⚠️ UTR $enteredUtr is NOT yet settled in our automatic bank feed.\n\nTo escalate this directly to NexTournament Administration for manual approval, please attach your Payment Screenshot below:",
                                                            isUser = false,
                                                            timestamp = "Just now",
                                                            actionType = SupportActionType.UPLOAD_SCREENSHOT,
                                                            utrNumber = enteredUtr
                                                        )
                                                        messages = messages + failMsg
                                                    }
                                                    listState.animateScrollToItem(messages.size - 1)
                                                }
                                            }
                                        },
                                        enabled = utrInputText.length == 12 && !isCheckingUtr,
                                        modifier = Modifier.fillMaxWidth(),
                                        accentColor = CyberEmerald,
                                        textColor = ObsidianBlack,
                                        height = 40.dp
                                    )
                                }

                                // Interactive Screenshot Upload Card
                                if (msg.actionType == SupportActionType.UPLOAD_SCREENSHOT) {
                                    Spacer(modifier = Modifier.height(10.dp))
                                    if (selectedScreenshot == null) {
                                        OutlinedButton(
                                            onClick = {
                                                selectedScreenshot = "payment_receipt_${msg.utrNumber}.png"
                                            },
                                            shape = CutCornerShape(4.dp),
                                            border = BorderStroke(1.dp, ElectricBlue),
                                            colors = ButtonDefaults.outlinedButtonColors(contentColor = ElectricBlue),
                                            modifier = Modifier.fillMaxWidth()
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Icon(
                                                    painter = painterResource(id = R.drawable.ic_photo_camera_sharp),
                                                    contentDescription = null,
                                                    modifier = Modifier.size(16.dp)
                                                )
                                                Spacer(modifier = Modifier.width(6.dp))
                                                Text(
                                                    text = "📷 ATTACH PAYMENT SCREENSHOT",
                                                    fontFamily = ChakraPetch,
                                                    fontWeight = FontWeight.Bold,
                                                    fontSize = 11.sp
                                                )
                                            }
                                        }
                                    } else {
                                        // Screenshot attached preview
                                        Box(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .clip(CutCornerShape(4.dp))
                                                .background(SlateElevated)
                                                .border(1.dp, CyberEmerald, CutCornerShape(4.dp))
                                                .padding(10.dp)
                                        ) {
                                            Row(
                                                modifier = Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Row(verticalAlignment = Alignment.CenterVertically) {
                                                    Icon(
                                                        painter = painterResource(id = R.drawable.ic_check_circle_sharp),
                                                        contentDescription = null,
                                                        tint = CyberEmerald,
                                                        modifier = Modifier.size(18.dp)
                                                    )
                                                    Spacer(modifier = Modifier.width(8.dp))
                                                    Text(
                                                        text = selectedScreenshot ?: "receipt.jpg",
                                                        fontFamily = ChakraPetch,
                                                        fontSize = 11.sp,
                                                        color = Color.White
                                                    )
                                                }
                                                Text(
                                                    text = "READY",
                                                    fontFamily = ChakraPetch,
                                                    fontSize = 10.sp,
                                                    color = CyberEmerald,
                                                    fontWeight = FontWeight.Bold
                                                )
                                            }
                                        }

                                        Spacer(modifier = Modifier.height(8.dp))

                                        CyberActionButton(
                                            text = "🚀 ESCALATE DISPUTE TO ADMINISTRATION",
                                            onClick = {
                                                val ticketId = "NEX-UTR-${System.currentTimeMillis() % 100000}"
                                                val escalatedMsg = SupportMessage(
                                                    id = System.currentTimeMillis().toString(),
                                                    sender = "NEX-AI ASSISTANT",
                                                    text = "🎫 TICKET #$ticketId CREATED!\n\nAll details (UTR: ${msg.utrNumber}, Screenshot: $selectedScreenshot, User: $userIgn) have been securely sent to NexTournament Administration.\n\nOur operations desk will audit the bank transaction and approve/decline credit within 10-15 minutes.",
                                                    isUser = false,
                                                    timestamp = "Just now",
                                                    actionType = SupportActionType.TICKET_CREATED
                                                )
                                                messages = messages + escalatedMsg
                                                selectedScreenshot = null
                                                coroutineScope.launch {
                                                    delay(100)
                                                    listState.animateScrollToItem(messages.size - 1)
                                                }
                                            },
                                            modifier = Modifier.fillMaxWidth(),
                                            accentColor = CyberAmber,
                                            textColor = ObsidianBlack,
                                            height = 42.dp
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Bottom Text Input Bar
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    placeholder = {
                        Text(
                            text = "Ask AI about payments, UTR, or rooms...",
                            fontFamily = ChakraPetch,
                            fontSize = 12.sp,
                            color = Color.White.copy(alpha = 0.4f)
                        )
                    },
                    modifier = Modifier.weight(1f),
                    shape = CutCornerShape(4.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = ObsidianBlack,
                        unfocusedContainerColor = ObsidianBlack,
                        focusedBorderColor = CyberAmber,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    singleLine = true
                )

                CyberActionButton(
                    text = "SEND",
                    onClick = {
                        if (inputText.isNotBlank()) {
                            val text = inputText.trim()
                            inputText = ""
                            handleUserQuery(text)
                        }
                    },
                    accentColor = CyberAmber,
                    textColor = ObsidianBlack,
                    height = 50.dp,
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 8.dp)
                )
            }
        }
    }
}
