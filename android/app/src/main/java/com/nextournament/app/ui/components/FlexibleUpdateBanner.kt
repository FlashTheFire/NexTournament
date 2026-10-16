package com.nextournament.app.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.R
import com.nextournament.app.data.model.UpdateCheckResponse
import com.nextournament.app.ui.theme.ChakraPetch
import com.nextournament.app.ui.theme.CyberAmber
import com.nextournament.app.ui.theme.InterFont
import com.nextournament.app.ui.theme.SlateCard

@Composable
fun FlexibleUpdateBanner(
    isVisible: Boolean,
    updateInfo: UpdateCheckResponse,
    onDownloadClick: () -> Unit,
    onDismissClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    AnimatedVisibility(
        visible = isVisible,
        enter = expandVertically(),
        exit = shrinkVertically()
    ) {
        Row(
            modifier = modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp)
                .clip(CutCornerShape(4.dp))
                .background(SlateCard)
                .border(1.dp, CyberAmber.copy(alpha = 0.6f), CutCornerShape(4.dp))
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_system_update),
                    contentDescription = null,
                    tint = CyberAmber,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Column {
                    Text(
                        text = "NEW BUILD AVAILABLE",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = Color.White
                    )
                    Text(
                        text = "v${updateInfo.latestVersionName} (${updateInfo.downloadSize})",
                        fontFamily = InterFont,
                        fontSize = 11.sp,
                        color = CyberAmber
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .clip(CutCornerShape(2.dp))
                        .background(CyberAmber)
                        .clickable { onDownloadClick() }
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "UPDATE",
                        fontFamily = ChakraPetch,
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp,
                        color = Color.Black
                    )
                }

                Spacer(modifier = Modifier.width(8.dp))

                Icon(
                    painter = painterResource(id = R.drawable.ic_copy_sharp), // Subtle dismiss icon
                    contentDescription = "Dismiss",
                    tint = Color.White.copy(alpha = 0.5f),
                    modifier = Modifier
                        .size(18.dp)
                        .clickable { onDismissClick() }
                )
            }
        }
    }
}
