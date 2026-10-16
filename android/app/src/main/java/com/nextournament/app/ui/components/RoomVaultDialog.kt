package com.nextournament.app.ui.components

import android.app.Activity
import android.content.ClipData
import android.content.ClipDescription
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.PersistableBundle
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
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
fun RoomVaultDialog(
    game: String, // "Free Fire", "BGMI", "Valorant"
    roomId: String?,
    roomPassword: String?,
    isUnlocked: Boolean,
    unlockCountdownSeconds: Int,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val activity = context as? Activity

    // Dynamic FLAG_SECURE: Enable screenshot & screen recording blocking while vault is open
    DisposableEffect(Unit) {
        activity?.window?.setFlags(
            android.view.WindowManager.LayoutParams.FLAG_SECURE,
            android.view.WindowManager.LayoutParams.FLAG_SECURE
        )
        onDispose {
            activity?.window?.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
        }
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
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header Key Vault Icon
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(CyberEmerald.copy(alpha = 0.15f))
                        .border(1.dp, CyberEmerald, CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_vpn_key_sharp),
                        contentDescription = "Room Key",
                        tint = CyberEmerald,
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "T-15m ROOM VAULT",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = Color.White,
                    letterSpacing = 1.sp
                )

                Text(
                    text = "OFFICIAL CUSTOM MATCH CREDENTIALS",
                    fontFamily = InterFont,
                    fontSize = 11.sp,
                    color = CyberEmerald,
                    letterSpacing = 0.5.sp
                )

                Spacer(modifier = Modifier.height(18.dp))

                if (isUnlocked && !roomId.isNullOrBlank() && !roomPassword.isNullOrBlank()) {
                    // Credentials Revealed Cards
                    CredentialFieldCard(
                        label = "CUSTOM ROOM ID",
                        value = roomId,
                        onCopy = {
                            copyToClipboard(context, "Room ID", roomId, isSensitive = false)
                        }
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    CredentialFieldCard(
                        label = "ROOM PASSWORD",
                        value = roomPassword,
                        onCopy = {
                            copyToClipboard(context, "Room Password", roomPassword, isSensitive = true)
                        }
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    // 1-Tap Direct Game Launch Button
                    CyberActionButton(
                        text = "LAUNCH ${game.uppercase()} NOW",
                        onClick = {
                            copyToClipboard(context, "Room ID", roomId, isSensitive = false)
                            launchGamePackage(context, game)
                        },
                        modifier = Modifier.fillMaxWidth(),
                        iconRes = R.drawable.ic_open_in_new_sharp
                    )
                } else {
                    // Countdown Locked Box
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(CutCornerShape(4.dp))
                            .background(SlateCard)
                            .padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_lock_sharp),
                            contentDescription = null,
                            tint = CyberAmber,
                            modifier = Modifier.size(28.dp)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = "CREDENTIALS VAULT ENCRYPTED",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            color = CyberAmber
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        val minutes = unlockCountdownSeconds / 60
                        val seconds = unlockCountdownSeconds % 60
                        Text(
                            text = "Unlocks automatically in %02d:%02d".format(minutes, seconds),
                            fontFamily = InterFont,
                            fontSize = 12.sp,
                            color = Color.White.copy(alpha = 0.7f),
                            textAlign = TextAlign.Center
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                TextButton(onClick = onDismiss) {
                    Text(
                        text = "CLOSE VAULT",
                        fontFamily = ChakraPetch,
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
            }
        }
    }
}

@Composable
fun CredentialFieldCard(
    label: String,
    value: String,
    onCopy: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(CutCornerShape(4.dp))
            .background(SlateCard)
            .border(1.dp, SlateElevated, CutCornerShape(4.dp))
            .clickable { onCopy() }
            .padding(14.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = label,
                    fontFamily = InterFont,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 10.sp,
                    color = Color.White.copy(alpha = 0.6f)
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = value,
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = Color.White,
                    letterSpacing = 1.sp
                )
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .clip(CutCornerShape(2.dp))
                    .background(SlateElevated)
                    .padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_copy_sharp),
                    contentDescription = "Copy",
                    tint = CyberEmerald,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "COPY",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    color = CyberEmerald
                )
            }
        }
    }
}

private fun copyToClipboard(context: Context, label: String, text: String, isSensitive: Boolean) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    val clip = ClipData.newPlainText(label, text)

    // Android 13+ Sensitive Clipboard Masking
    if (isSensitive && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        clip.description.extras = PersistableBundle().apply {
            putBoolean(ClipDescription.EXTRA_IS_SENSITIVE, true)
        }
    }

    clipboard.setPrimaryClip(clip)
    Toast.makeText(context, "$label copied to clipboard!", Toast.LENGTH_SHORT).show()
}

private fun launchGamePackage(context: Context, game: String) {
    val packageManager = context.packageManager
    val targetPackages = when {
        game.contains("Free Fire", ignoreCase = true) -> listOf("com.dts.freefiremax", "com.dts.freefireth")
        game.contains("BGMI", ignoreCase = true) -> listOf("com.pubg.imobile")
        else -> emptyList()
    }

    for (pkg in targetPackages) {
        val launchIntent = packageManager.getLaunchIntentForPackage(pkg)
        if (launchIntent != null) {
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(launchIntent)
            return
        }
    }

    Toast.makeText(context, "Game client not found. Please open manually.", Toast.LENGTH_LONG).show()
}
