package com.nextournament.app.ui.components

import android.widget.Toast
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.nextournament.app.R
import com.nextournament.app.data.local.TournamentEntity
import com.nextournament.app.data.model.AdminAdjustBalanceRequest
import com.nextournament.app.data.model.AdminCreateTournamentRequest
import com.nextournament.app.data.model.AdminSetCredentialsRequest
import com.nextournament.app.ui.theme.*

@Composable
fun AdminConsoleDialog(
    tournaments: List<TournamentEntity>,
    currentUserId: Long,
    onCreateMatch: (AdminCreateTournamentRequest) -> Unit,
    onSetCredentials: (Long, AdminSetCredentialsRequest) -> Unit,
    onAdjustBalance: (AdminAdjustBalanceRequest) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var selectedTab by remember { mutableStateOf(0) } // 0: Create Match, 1: Room Creds, 2: Balance Override

    // Match creation fields
    var matchTitle by remember { mutableStateOf("Bermuda Champions Cup #") }
    var selectedMap by remember { mutableStateOf("Bermuda") }
    val freeFireMaps = listOf("Bermuda", "Purgatory", "Kalahari", "Alpine", "NexTerra")
    var selectedFormat by remember { mutableStateOf("SQUAD") }
    val formats = listOf("SOLO", "DUO", "SQUAD")
    var entryFeeText by remember { mutableStateOf("50") }
    var prizePoolText by remember { mutableStateOf("1800") }
    var perKillText by remember { mutableStateOf("20") }
    var totalSlotsText by remember { mutableStateOf("48") }
    var startMinutesText by remember { mutableStateOf("45") }

    // Room credentials fields
    var selectedTournamentId by remember { mutableStateOf(tournaments.firstOrNull()?.id ?: 101L) }
    var customRoomId by remember { mutableStateOf("8920194") }
    var customRoomPass by remember { mutableStateOf("NEX@FIRE_78") }

    // Balance adjust fields
    var targetUserIdText by remember { mutableStateOf(currentUserId.toString()) }
    var adjustAmountText by remember { mutableStateOf("500") }
    var selectedBalanceType by remember { mutableStateOf("game_balance") } // game_balance or win_balance

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
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.92f)
                    .border(BorderStroke(1.5.dp, CyberAmber), CutCornerShape(12.dp)),
                colors = CardDefaults.cardColors(containerColor = CyberDarkCard),
                shape = CutCornerShape(12.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(18.dp)
                ) {
                    // Header Bar
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_verified_sharp),
                                contentDescription = null,
                                tint = CyberAmber,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Column {
                                Text(
                                    text = "ADMIN COMMAND CENTER",
                                    fontFamily = OrbitronFont,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp,
                                    color = Color.White
                                )
                                Text(
                                    text = "LIVE POSTGRESQL & TRAEFIK BACKEND",
                                    fontFamily = ChakraPetch,
                                    fontSize = 10.sp,
                                    color = CyberAmber
                                )
                            }
                        }

                        IconButton(onClick = onDismiss) {
                            Icon(
                                painter = painterResource(id = R.drawable.ic_close_sharp),
                                contentDescription = "Close",
                                tint = Color.White.copy(alpha = 0.7f)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Navigation Tabs
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(DarkBackground, CutCornerShape(6.dp))
                            .padding(4.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        listOf("1. CREATE MATCH", "2. ROOM VAULT", "3. BALANCES").forEachIndexed { index, tabTitle ->
                            val isSelected = selectedTab == index
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .background(
                                        if (isSelected) CyberAmber else Color.Transparent,
                                        CutCornerShape(4.dp)
                                    )
                                    .clickable { selectedTab = index }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = tabTitle,
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    color = if (isSelected) ObsidianBlack else Color.White.copy(alpha = 0.7f)
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Tab Contents (Scrollable)
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .verticalScroll(rememberScrollState())
                    ) {
                        // TAB 0: CREATE REAL TOURNAMENT
                        if (selectedTab == 0) {
                            Text(
                                text = "MATCH CONFIGURATION",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = NeonCyan
                            )
                            Spacer(modifier = Modifier.height(8.dp))

                            OutlinedTextField(
                                value = matchTitle,
                                onValueChange = { matchTitle = it },
                                label = { Text("Match Title", color = Color.Gray) },
                                singleLine = true,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = CyberAmber,
                                    unfocusedBorderColor = Color.DarkGray
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            // Official Free Fire Map Selector
                            Text(
                                text = "SELECT FREE FIRE MAP:",
                                fontFamily = ChakraPetch,
                                fontSize = 11.sp,
                                color = Color.White.copy(alpha = 0.7f)
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                freeFireMaps.forEach { mapName ->
                                    val isSelected = selectedMap.equals(mapName, ignoreCase = true)
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .background(
                                                if (isSelected) NeonCyan else SlateCardSurface,
                                                CutCornerShape(4.dp)
                                            )
                                            .border(
                                                BorderStroke(1.dp, if (isSelected) NeonCyan else Color.DarkGray),
                                                CutCornerShape(4.dp)
                                            )
                                            .clickable { selectedMap = mapName }
                                            .padding(vertical = 6.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = mapName,
                                            fontFamily = ChakraPetch,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 9.sp,
                                            color = if (isSelected) ObsidianBlack else Color.White
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Format Selector
                            Text(
                                text = "TEAM FORMAT:",
                                fontFamily = ChakraPetch,
                                fontSize = 11.sp,
                                color = Color.White.copy(alpha = 0.7f)
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                formats.forEach { fmt ->
                                    val isSelected = selectedFormat.equals(fmt, ignoreCase = true)
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .background(
                                                if (isSelected) AmberGold else SlateCardSurface,
                                                CutCornerShape(4.dp)
                                            )
                                            .border(
                                                BorderStroke(1.dp, if (isSelected) AmberGold else Color.DarkGray),
                                                CutCornerShape(4.dp)
                                            )
                                            .clickable { selectedFormat = fmt }
                                            .padding(vertical = 6.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = fmt,
                                            fontFamily = ChakraPetch,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 10.sp,
                                            color = if (isSelected) ObsidianBlack else Color.White
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Numerical Inputs Row 1: Entry Fee & Prize Pool
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp)
                            ) {
                                OutlinedTextField(
                                    value = entryFeeText,
                                    onValueChange = { entryFeeText = it },
                                    label = { Text("Entry Fee (₹)", color = Color.Gray) },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.White,
                                        focusedBorderColor = CyberEmerald,
                                        unfocusedBorderColor = Color.DarkGray
                                    ),
                                    modifier = Modifier.weight(1f)
                                )

                                OutlinedTextField(
                                    value = prizePoolText,
                                    onValueChange = { prizePoolText = it },
                                    label = { Text("Prize Pool (₹)", color = Color.Gray) },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.White,
                                        focusedBorderColor = CyberEmerald,
                                        unfocusedBorderColor = Color.DarkGray
                                    ),
                                    modifier = Modifier.weight(1f)
                                )
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            // Numerical Inputs Row 2: Per Kill & Starts In
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp)
                            ) {
                                OutlinedTextField(
                                    value = perKillText,
                                    onValueChange = { perKillText = it },
                                    label = { Text("Per Kill (₹)", color = Color.Gray) },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.White,
                                        focusedBorderColor = CyberEmerald,
                                        unfocusedBorderColor = Color.DarkGray
                                    ),
                                    modifier = Modifier.weight(1f)
                                )

                                OutlinedTextField(
                                    value = startMinutesText,
                                    onValueChange = { startMinutesText = it },
                                    label = { Text("Start In (Mins)", color = Color.Gray) },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.White,
                                        focusedBorderColor = CyberAmber,
                                        unfocusedBorderColor = Color.DarkGray
                                    ),
                                    modifier = Modifier.weight(1f)
                                )
                            }

                            Spacer(modifier = Modifier.height(16.dp))

                            CyberActionButton(
                                text = "🚀 CREATE & BROADCAST MATCH",
                                onClick = {
                                    val fee = entryFeeText.toDoubleOrNull() ?: 50.0
                                    val pool = prizePoolText.toDoubleOrNull() ?: 1800.0
                                    val bounty = perKillText.toDoubleOrNull() ?: 20.0
                                    val slots = totalSlotsText.toIntOrNull() ?: 48
                                    val mins = startMinutesText.toIntOrNull() ?: 45

                                    onCreateMatch(
                                        AdminCreateTournamentRequest(
                                            title = matchTitle.ifBlank { "Free Fire $selectedMap Clash" },
                                            mapName = selectedMap,
                                            teamFormat = selectedFormat.lowercase(),
                                            entryFee = fee,
                                            prizePool = pool,
                                            perKill = bounty,
                                            totalSlots = slots,
                                            startInMinutes = mins
                                        )
                                    )
                                },
                                modifier = Modifier.fillMaxWidth(),
                                accentColor = CyberAmber,
                                textColor = ObsidianBlack,
                                iconRes = R.drawable.ic_bolt_sharp
                            )
                        }

                        // TAB 1: BROADCAST ROOM CREDENTIALS
                        if (selectedTab == 1) {
                            Text(
                                text = "PUSH ROOM ID & PASSWORD",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = NeonCyan
                            )
                            Text(
                                text = "Unlocks Room Vault instantly on enrolled players' devices",
                                fontFamily = ChakraPetch,
                                fontSize = 10.sp,
                                color = Color.White.copy(alpha = 0.6f)
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            Text(
                                text = "SELECT TOURNAMENT:",
                                fontFamily = ChakraPetch,
                                fontSize = 11.sp,
                                color = Color.White.copy(alpha = 0.7f)
                            )
                            Spacer(modifier = Modifier.height(4.dp))

                            tournaments.forEach { t ->
                                val isSelected = t.id == selectedTournamentId
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 3.dp)
                                        .background(
                                            if (isSelected) SlateElevated else SlateCardSurface,
                                            CutCornerShape(4.dp)
                                        )
                                        .border(
                                            BorderStroke(1.dp, if (isSelected) CyberEmerald else Color.DarkGray),
                                            CutCornerShape(4.dp)
                                        )
                                        .clickable { selectedTournamentId = t.id }
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = "#${t.id} - ${t.title}",
                                            fontFamily = ChakraPetch,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 11.sp,
                                            color = if (isSelected) CyberEmerald else Color.White
                                        )
                                        Text(
                                            text = "Map: ${t.mapName} | Format: ${t.teamFormat}",
                                            fontFamily = ChakraPetch,
                                            fontSize = 9.sp,
                                            color = Color.White.copy(alpha = 0.5f)
                                        )
                                    }

                                    if (t.roomId != null) {
                                        CyberBadge(
                                            text = "ID: ${t.roomId}",
                                            color = CyberEmerald,
                                            textColor = ObsidianBlack
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(12.dp))

                            OutlinedTextField(
                                value = customRoomId,
                                onValueChange = { customRoomId = it },
                                label = { Text("Custom Room ID (Free Fire)", color = Color.Gray) },
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

                            OutlinedTextField(
                                value = customRoomPass,
                                onValueChange = { customRoomPass = it },
                                label = { Text("Room Password", color = Color.Gray) },
                                singleLine = true,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = NeonCyan,
                                    unfocusedBorderColor = Color.DarkGray
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(16.dp))

                            CyberActionButton(
                                text = "🔓 BROADCAST TO VAULT",
                                onClick = {
                                    if (customRoomId.isNotBlank() && customRoomPass.isNotBlank()) {
                                        onSetCredentials(
                                            selectedTournamentId,
                                            AdminSetCredentialsRequest(
                                                roomId = customRoomId,
                                                roomPassword = customRoomPass
                                            )
                                        )
                                    } else {
                                        Toast.makeText(context, "Enter Room ID & Password", Toast.LENGTH_SHORT).show()
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                accentColor = ElectricBlue,
                                textColor = Color.White,
                                iconRes = R.drawable.ic_verified_sharp
                            )
                        }

                        // TAB 2: OVERRIDE USER BALANCE
                        if (selectedTab == 2) {
                            Text(
                                text = "REAL-TIME DATABASE BALANCE OVERRIDE",
                                fontFamily = ChakraPetch,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = NeonCyan
                            )
                            Text(
                                text = "Directly modifies balance in PostgreSQL `users` ledger",
                                fontFamily = ChakraPetch,
                                fontSize = 10.sp,
                                color = Color.White.copy(alpha = 0.6f)
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            OutlinedTextField(
                                value = targetUserIdText,
                                onValueChange = { targetUserIdText = it },
                                label = { Text("Target User ID (e.g. 5716978793)", color = Color.Gray) },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                singleLine = true,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = CyberAmber,
                                    unfocusedBorderColor = Color.DarkGray
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            OutlinedTextField(
                                value = adjustAmountText,
                                onValueChange = { adjustAmountText = it },
                                label = { Text("Adjustment Amount (e.g. +500 or -100)", color = Color.Gray) },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                singleLine = true,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = CyberEmerald,
                                    unfocusedBorderColor = Color.DarkGray
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            // Balance Type Selector
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                listOf("game_balance" to "GAME BALANCE (DEPOSIT)", "win_balance" to "WIN BALANCE (WITHDRAWABLE)").forEach { (key, label) ->
                                    val isSelected = selectedBalanceType == key
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .background(
                                                if (isSelected) CyberEmerald else SlateCardSurface,
                                                CutCornerShape(4.dp)
                                            )
                                            .border(
                                                BorderStroke(1.dp, if (isSelected) CyberEmerald else Color.DarkGray),
                                                CutCornerShape(4.dp)
                                            )
                                            .clickable { selectedBalanceType = key }
                                            .padding(vertical = 8.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = label,
                                            fontFamily = ChakraPetch,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 9.sp,
                                            color = if (isSelected) ObsidianBlack else Color.White
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(16.dp))

                            CyberActionButton(
                                text = "💰 EXECUTE BALANCE OVERRIDE",
                                onClick = {
                                    val uid = targetUserIdText.toLongOrNull() ?: currentUserId
                                    val amt = adjustAmountText.toDoubleOrNull() ?: 500.0
                                    onAdjustBalance(
                                        AdminAdjustBalanceRequest(
                                            targetUserId = uid,
                                            amount = amt,
                                            balanceType = selectedBalanceType
                                        )
                                    )
                                },
                                modifier = Modifier.fillMaxWidth(),
                                accentColor = CyberEmerald,
                                textColor = ObsidianBlack,
                                iconRes = R.drawable.ic_wallet_sharp
                            )
                        }
                    }
                }
            }
        }
    }
}
