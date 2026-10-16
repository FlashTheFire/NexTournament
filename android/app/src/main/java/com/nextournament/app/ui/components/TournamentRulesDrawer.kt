package com.nextournament.app.ui.components

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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.ui.theme.*

data class RuleSection(
    val title: String,
    val iconRes: Int,
    val iconTint: Color,
    val rules: List<String>
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TournamentRulesDrawer(
    tournamentTitle: String,
    game: String,
    format: String,
    onAccept: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    var hasAgreedToTerms by remember { mutableStateOf(false) }

    val ruleSections = remember(game) {
        listOf(
            RuleSection(
                title = "1. ZERO-TOLERANCE ANTI-CHEAT & EMULATORS",
                iconRes = R.drawable.ic_gpp_bad,
                iconTint = CyberCrimson,
                rules = listOf(
                    "Mobile devices only. PC Emulators (BlueStacks, LDPlayer, Nox) are strictly prohibited.",
                    "Any use of modified APKs, config files, headshot injectors, ESP, aimbot, or macro triggers results in an immediate permanent ban and permanent forfeiture of wallet balance.",
                    "Hardware ID (HWID), IP telemetry, and Frida/Xposed hooks are continuously scanned."
                )
            ),
            RuleSection(
                title = "2. $game LOADOUT & GAMEPLAY RESTRICTIONS",
                iconRes = R.drawable.ic_sports_esports,
                iconTint = CyberAmber,
                rules = when (game.uppercase()) {
                    "FREE FIRE" -> listOf(
                        "Gun Attributes: Strictly OFF (Default stats apply for all weapons).",
                        "Character Skills: ALLOWED unless specified in custom match title.",
                        "No roof/antenna camping outside combat boundaries.",
                        "Grenade spam / launcher abuse restrictions apply in Clash Squad formats."
                    )
                    "BGMI" -> listOf(
                        "Classic Erangel / Miramar competitive zone settings.",
                        "No teaming up or cross-team collaboration under any circumstances.",
                        "In TDM format: M249 and RPG are strictly prohibited."
                    )
                    else -> listOf(
                        "Standard competitive esports tournament rules apply.",
                        "Tactical pause is only permitted upon organizer admin confirmation.",
                        "Exploiting map clipping bugs or glitches will result in instant match DQ."
                    )
                }
            ),
            RuleSection(
                title = "3. T-15M ROOM VAULT ACCESS & TIMELINE",
                iconRes = R.drawable.ic_alarm_sharp,
                iconTint = CyberEmerald,
                rules = listOf(
                    "Custom Room ID and Password will unlock in the Room Vault exactly 15 minutes before match start.",
                    "You MUST occupy your designated slot number selected during seat lock. Joining another squad's slot will result in being kicked by the in-game room host.",
                    "Match begins promptly at scheduled time. Late players forfeit their entry fee without refund."
                )
            ),
            RuleSection(
                title = "4. SCREENSHOT PROOF & DISPUTE RESOLUTION",
                iconRes = R.drawable.ic_gavel_sharp,
                iconTint = CyberAmber,
                rules = listOf(
                    "All squad leaders must take an end-of-game screenshot displaying final placement, kill counts, and team UID.",
                    "In case of disputes, screen recording proof from match start to finish is mandatory.",
                    "Disputes must be raised in the NexTournament Telegram support desk within 15 minutes of match conclusion."
                )
            ),
            RuleSection(
                title = "5. PRIZE DISTRIBUTION & FAIRPLAY AUDIT",
                iconRes = R.drawable.ic_stars_sharp,
                iconTint = CyberAmber,
                rules = listOf(
                    "Post-match telemetry and kill logs undergo automated FairPlay review for 30 minutes.",
                    "Winnings are auto-credited directly to your Winnings Wallet upon audit approval.",
                    "Instant payouts available via UPI (GPay, PhonePe, Paytm, CRED) or Crypto USDT."
                )
            )
        )
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = SlateCardSurface,
        dragHandle = {
            Box(
                modifier = Modifier
                    .padding(vertical = 12.dp)
                    .width(48.dp)
                    .height(4.dp)
                    .clip(CutCornerShape(2.dp))
                    .background(Color.White.copy(alpha = 0.3f))
            )
        },
        shape = CutCornerShape(topStart = 8.dp, topEnd = 8.dp),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.9f)
                .padding(horizontal = 20.dp, vertical = 8.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_gavel_sharp),
                        contentDescription = null,
                        tint = CyberAmber,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "FAIRPLAY RULES & REGULATIONS",
                            fontFamily = OrbitronFont,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            color = Color.White
                        )
                        Text(
                            text = "$game • $format • $tournamentTitle",
                            fontFamily = InterFont,
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.6f)
                        )
                    }
                }

                CyberBadge(
                    text = "MANDATORY",
                    color = CyberCrimson,
                    backgroundColor = SlateElevated
                )
            }

            Spacer(modifier = Modifier.height(14.dp))
            Divider(color = SlateElevated, thickness = BrutalistBorderThin)
            Spacer(modifier = Modifier.height(14.dp))

            // Scrollable Rule Sections
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                ruleSections.forEach { section ->
                    Card(
                        shape = CutCornerCard,
                        colors = CardDefaults.cardColors(containerColor = SlateElevated.copy(alpha = 0.6f)),
                        border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, SlateElevated),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    painter = painterResource(id = section.iconRes),
                                    contentDescription = null,
                                    tint = section.iconTint,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = section.title,
                                    fontFamily = ChakraPetch,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 13.sp,
                                    color = section.iconTint
                                )
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            section.rules.forEach { rule ->
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 3.dp),
                                    verticalAlignment = Alignment.Top
                                ) {
                                    Text(
                                        text = "• ",
                                        fontFamily = InterFont,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp,
                                        color = CyberAmber
                                    )
                                    Text(
                                        text = rule,
                                        fontFamily = InterFont,
                                        fontSize = 12.sp,
                                        lineHeight = 16.sp,
                                        color = Color.White.copy(alpha = 0.85f)
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))
            Divider(color = SlateElevated, thickness = BrutalistBorderThin)
            Spacer(modifier = Modifier.height(12.dp))

            // Mandatory Agreement Checkbox
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(4.dp))
                    .background(SlateElevated)
                    .clickable { hasAgreedToTerms = !hasAgreedToTerms }
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Checkbox(
                    checked = hasAgreedToTerms,
                    onCheckedChange = { hasAgreedToTerms = it },
                    colors = CheckboxDefaults.colors(
                        checkedColor = CyberEmerald,
                        uncheckedColor = Color.White.copy(alpha = 0.5f),
                        checkmarkColor = Color.Black
                    )
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "I have read and strictly agree to all FairPlay rules, room slot assignments, and zero-tolerance anti-cheat policies.",
                    fontFamily = InterFont,
                    fontSize = 11.sp,
                    lineHeight = 15.sp,
                    color = if (hasAgreedToTerms) Color.White else Color.White.copy(alpha = 0.7f)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Decline Button
                OutlinedButton(
                    onClick = onDismiss,
                    shape = CutCornerButton,
                    border = androidx.compose.foundation.BorderStroke(BrutalistBorderThin, CyberCrimson),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = CyberCrimson),
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "DECLINE",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )
                }

                // Accept Button (Disabled until checkbox is checked)
                Button(
                    onClick = {
                        if (hasAgreedToTerms) {
                            onAccept()
                        }
                    },
                    enabled = hasAgreedToTerms,
                    shape = CutCornerButton,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = CyberEmerald,
                        contentColor = Color.Black,
                        disabledContainerColor = SlateElevated,
                        disabledContentColor = Color.White.copy(alpha = 0.3f)
                    ),
                    modifier = Modifier.weight(2f)
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_check_circle_sharp),
                        contentDescription = null,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "ACCEPT & ENTER SEATS",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}
