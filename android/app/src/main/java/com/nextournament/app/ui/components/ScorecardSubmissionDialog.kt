package com.nextournament.app.ui.components

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.nextournament.app.R
import com.nextournament.app.ui.theme.*

@Composable
fun ScorecardSubmissionDialog(
    tournamentId: String,
    tournamentTitle: String,
    game: String,
    onSubmitProof: (placement: Int, kills: Int, imageUri: Uri?) -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }
    var placementText by remember { mutableStateOf("1") }
    var killsText by remember { mutableStateOf("4") }
    var isSubmitting by remember { mutableStateOf(false) }

    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri: Uri? ->
        selectedImageUri = uri
    }

    Card(
        shape = CutCornerCard,
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = BorderStroke(BrutalistBorderThin, CyberAmber),
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(18.dp)
                .verticalScroll(rememberScrollState())
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_photo_camera_sharp),
                        contentDescription = null,
                        tint = CyberAmber,
                        modifier = Modifier.size(22.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "SUBMIT MATCH SCORECARD",
                        fontFamily = OrbitronFont,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = Color.White
                    )
                }

                CyberBadge(
                    text = "OCR VERIFY",
                    color = CyberEmerald,
                    backgroundColor = SlateElevated
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = "$game • $tournamentTitle",
                fontFamily = InterFont,
                fontSize = 11.sp,
                color = Color.White.copy(alpha = 0.6f)
            )

            Spacer(modifier = Modifier.height(14.dp))
            Divider(color = SlateElevated, thickness = BrutalistBorderThin)
            Spacer(modifier = Modifier.height(14.dp))

            // Screenshot Upload Picker Area
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(160.dp)
                    .clip(CutCornerShape(4.dp))
                    .background(SlateElevated)
                    .border(
                        BorderStroke(
                            BrutalistBorderThin,
                            if (selectedImageUri != null) CyberEmerald else SlateElevated
                        ),
                        CutCornerShape(4.dp)
                    )
                    .clickable {
                        photoPickerLauncher.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                        )
                    },
                contentAlignment = Alignment.Center
            ) {
                if (selectedImageUri != null) {
                    AsyncImage(
                        model = selectedImageUri,
                        contentDescription = "Match Scorecard Screenshot",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize()
                    )
                    // Change photo overlay tag
                    Box(
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(8.dp)
                            .clip(CutCornerShape(2.dp))
                            .background(Color.Black.copy(alpha = 0.7f))
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = "TAP TO CHANGE PHOTO",
                            fontFamily = ChakraPetch,
                            fontSize = 10.sp,
                            color = CyberAmber
                        )
                    }
                } else {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_photo_camera_sharp),
                            contentDescription = null,
                            tint = CyberAmber,
                            modifier = Modifier.size(36.dp)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "TAP TO SELECT END-GAME SCREENSHOT",
                            fontFamily = ChakraPetch,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Must show placement rank, kills, and player UID clearly",
                            fontFamily = InterFont,
                            fontSize = 10.sp,
                            color = Color.White.copy(alpha = 0.5f)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Placement Rank and Kill Counts Inputs
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Final Placement
                OutlinedTextField(
                    value = placementText,
                    onValueChange = { if (it.all { char -> char.isDigit() }) placementText = it },
                    label = { Text("FINAL RANK (#)", fontFamily = ChakraPetch, fontSize = 11.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberAmber,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedContainerColor = SlateElevated,
                        unfocusedContainerColor = SlateElevated
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.weight(1f)
                )

                // Total Kills
                OutlinedTextField(
                    value = killsText,
                    onValueChange = { if (it.all { char -> char.isDigit() }) killsText = it },
                    label = { Text("CONFIRMED KILLS", fontFamily = ChakraPetch, fontSize = 11.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberAmber,
                        unfocusedBorderColor = SlateElevated,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedContainerColor = SlateElevated,
                        unfocusedContainerColor = SlateElevated
                    ),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // FairPlay Security Notice
            Card(
                shape = CutCornerShape(4.dp),
                colors = CardDefaults.cardColors(containerColor = SlateElevated.copy(alpha = 0.5f)),
                border = BorderStroke(BrutalistBorderThin, SlateElevated),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.ic_shield_sharp),
                        contentDescription = null,
                        tint = CyberEmerald,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Proof is verified via OCR and cross-referenced with server match telemetry. False claims lead to immediate FairPlay bans.",
                        fontFamily = InterFont,
                        fontSize = 10.sp,
                        lineHeight = 14.sp,
                        color = Color.White.copy(alpha = 0.7f)
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                OutlinedButton(
                    onClick = onDismiss,
                    shape = CutCornerButton,
                    border = BorderStroke(BrutalistBorderThin, SlateElevated),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White.copy(alpha = 0.7f)),
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "CANCEL",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp
                    )
                }

                Button(
                    onClick = {
                        isSubmitting = true
                        val rank = placementText.toIntOrNull() ?: 1
                        val kills = killsText.toIntOrNull() ?: 0
                        onSubmitProof(rank, kills, selectedImageUri)
                    },
                    enabled = !isSubmitting,
                    shape = CutCornerButton,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = CyberAmber,
                        contentColor = Color.Black
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
                        text = if (isSubmitting) "SUBMITTING..." else "SUBMIT FOR AUDIT",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp
                    )
                }
            }
        }
    }
}
