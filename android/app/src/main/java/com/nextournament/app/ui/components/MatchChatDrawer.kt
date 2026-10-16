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
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.ui.theme.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

data class MatchChatMessage(
    val id: String,
    val senderIgn: String,
    val text: String,
    val timestamp: String,
    val isMe: Boolean = false,
    val teamRole: String = "MEMBER",
    val isTacticalPing: Boolean = false
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MatchChatDrawer(
    tournamentTitle: String,
    teamFormat: String,
    userIgn: String,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()
    val isSolo = teamFormat.equals("SOLO", ignoreCase = true)

    // Initial mock messages tailored to Solo vs Squad
    var messages by remember {
        mutableStateOf(
            if (isSolo) {
                listOf(
                    MatchChatMessage("1", "Viper_07", "Who is dropping Factory roof?", "16:40"),
                    MatchChatMessage("2", "Kiter_God", "Factory is a trap, watch Bimasakti Strip", "16:41"),
                    MatchChatMessage("3", "ShadowFF", "Good luck all 48 players, clean match!", "16:42")
                )
            } else {
                listOf(
                    MatchChatMessage("1", "SquadLeader_Rex", "Team #4 check in! Have mics ready.", "16:38", teamRole = "LEADER"),
                    MatchChatMessage("2", "SniperQueen", "Ready! Covering long range with AWM.", "16:39", teamRole = "SNIPER"),
                    MatchChatMessage("3", "Viper_07", "I'll take rusher role with MP40 + Shotgun.", "16:40", teamRole = "RUSHER")
                )
            }
        )
    }

    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    // Free Fire Tactical Quick Pings
    val tacticalPings = if (isSolo) {
        listOf("📍 Safe Zone Alert", "⚡ 1v1 Clash Ready", "🎯 Enemy Camp Ahead", "🛡️ Defending Position")
    } else {
        listOf("📍 Drop Clock Tower", "⚡ Rush Enemy Squad", "🛡️ Fall Back / Defend", "💊 Need Medkits / Gloo", "🎯 Enemy Spotted 240°")
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
                .fillMaxHeight(0.85f)
                .navigationBarsPadding()
                .padding(bottom = 12.dp)
        ) {
            // Header: Channel Identity + Privacy Badge
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = if (isSolo) "LOBBY MATCH COMMS" else "TEAM SQUAD CHAT",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            color = if (isSolo) NeonCyan else CyberAmber
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        CyberBadge(
                            text = if (isSolo) "SOLO 48P" else "SQUAD #4",
                            color = if (isSolo) NeonCyan else CyberEmerald,
                            backgroundColor = SlateElevated
                        )
                    }
                    Text(
                        text = if (isSolo) "Public lobby chat for $tournamentTitle" else "Secure private comms - Teammates only",
                        fontFamily = ChakraPetch,
                        fontSize = 11.sp,
                        color = Color.White.copy(alpha = 0.5f)
                    )
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
                    Text(
                        text = "✕",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                }
            }

            HorizontalDivider(
                color = SlateElevated,
                thickness = 1.dp,
                modifier = Modifier.padding(vertical = 6.dp)
            )

            // Tactical Quick Callout Chips
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(tacticalPings) { ping ->
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(SlateElevated)
                            .border(BorderStroke(1.dp, ElectricBlue.copy(alpha = 0.5f)), CutCornerShape(4.dp))
                            .clickable {
                                val newMsg = MatchChatMessage(
                                    id = System.currentTimeMillis().toString(),
                                    senderIgn = userIgn,
                                    text = ping,
                                    timestamp = "Just now",
                                    isMe = true,
                                    isTacticalPing = true
                                )
                                messages = messages + newMsg
                                coroutineScope.launch {
                                    delay(100)
                                    listState.animateScrollToItem(messages.size - 1)
                                    // Simulated tactical teammate acknowledgement
                                    delay(1200)
                                    val reply = if (isSolo) {
                                        MatchChatMessage(
                                            id = (System.currentTimeMillis() + 1).toString(),
                                            senderIgn = "Combatant_99",
                                            text = "Noted! Stay sharp.",
                                            timestamp = "Just now"
                                        )
                                    } else {
                                        MatchChatMessage(
                                            id = (System.currentTimeMillis() + 1).toString(),
                                            senderIgn = "SquadLeader_Rex",
                                            text = "Roger $userIgn! Moving to coordinate.",
                                            timestamp = "Just now",
                                            teamRole = "LEADER"
                                        )
                                    }
                                    messages = messages + reply
                                    listState.animateScrollToItem(messages.size - 1)
                                }
                            }
                            .padding(horizontal = 10.dp, vertical = 5.dp)
                    ) {
                        Text(
                            text = ping,
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Medium,
                            fontSize = 11.sp,
                            color = ElectricBlue
                        )
                    }
                }
            }

            // Message Stream
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages, key = { it.id }) { msg ->
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = if (msg.isMe) Alignment.End else Alignment.Start
                    ) {
                        // Sender Info
                        if (!msg.isMe) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = msg.senderIgn,
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    color = if (msg.teamRole == "LEADER") CyberAmber else ElectricBlue
                                )
                                if (!isSolo) {
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(
                                        text = "[${msg.teamRole}]",
                                        fontFamily = ChakraPetch,
                                        fontSize = 9.sp,
                                        color = Color.White.copy(alpha = 0.5f)
                                    )
                                }
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = msg.timestamp,
                                    fontFamily = InterFont,
                                    fontSize = 9.sp,
                                    color = Color.White.copy(alpha = 0.4f)
                                )
                            }
                            Spacer(modifier = Modifier.height(2.dp))
                        }

                        // Message Bubble
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(if (msg.isMe) SlateElevated else ObsidianBlack)
                                .border(
                                    BorderStroke(
                                        1.dp,
                                        if (msg.isTacticalPing) CyberAmber
                                        else if (msg.isMe) ElectricBlue.copy(alpha = 0.6f)
                                        else SlateElevated
                                    ),
                                    CutCornerShape(4.dp)
                                )
                                .padding(horizontal = 12.dp, vertical = 8.dp)
                        ) {
                            Text(
                                text = msg.text,
                                fontFamily = InterFont,
                                fontSize = 13.sp,
                                color = if (msg.isTacticalPing) CyberAmber else Color.White
                            )
                        }

                        if (msg.isMe) {
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = msg.timestamp,
                                fontFamily = InterFont,
                                fontSize = 9.sp,
                                color = Color.White.copy(alpha = 0.4f)
                            )
                        }
                    }
                }
            }

            // Input Bar
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
                            text = if (isSolo) "Send to match lobby..." else "Message squad...",
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
                        focusedBorderColor = ElectricBlue,
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
                            val newMsg = MatchChatMessage(
                                id = System.currentTimeMillis().toString(),
                                senderIgn = userIgn,
                                text = inputText.trim(),
                                timestamp = "Just now",
                                isMe = true
                            )
                            messages = messages + newMsg
                            inputText = ""
                            coroutineScope.launch {
                                delay(100)
                                listState.animateScrollToItem(messages.size - 1)
                            }
                        }
                    },
                    accentColor = if (isSolo) NeonCyan else CyberAmber,
                    textColor = ObsidianBlack,
                    height = 50.dp,
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 8.dp)
                )
            }
        }
    }
}
