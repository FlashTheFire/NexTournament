package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
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
import com.nextournament.app.ui.theme.*

enum class AppNavTab(val title: String, val iconRes: Int) {
    TOURNAMENTS("MATCHES", R.drawable.ic_swords_sharp),
    WALLET("WALLET", R.drawable.ic_wallet_sharp),
    PROFILE("PROFILE", R.drawable.ic_person_sharp)
}

@Composable
fun BottomHudNavigationBar(
    currentTab: AppNavTab,
    onTabSelected: (AppNavTab) -> Unit,
    onOcrCameraClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(SlateCardSurface)
            .border(
                BorderStroke(BrutalistBorderThin, SlateElevated),
                CutCornerShape(0.dp)
            )
            .padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Tab 1: TOURNAMENTS
        HudTabItem(
            tab = AppNavTab.TOURNAMENTS,
            isSelected = currentTab == AppNavTab.TOURNAMENTS,
            onClick = { onTabSelected(AppNavTab.TOURNAMENTS) },
            modifier = Modifier.weight(1f)
        )

        // Center Quick-Action OCR Camera Button
        Box(
            modifier = Modifier
                .padding(horizontal = 6.dp)
                .clip(CutCornerShape(4.dp))
                .background(CyberAmber)
                .clickable { onOcrCameraClick() }
                .padding(horizontal = 12.dp, vertical = 8.dp),
            contentAlignment = Alignment.Center
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_photo_camera_sharp),
                    contentDescription = "Submit Match Proof",
                    tint = Color.Black,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    text = "PROOF",
                    fontFamily = ChakraPetch,
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    color = Color.Black
                )
            }
        }

        // Tab 2: WALLET
        HudTabItem(
            tab = AppNavTab.WALLET,
            isSelected = currentTab == AppNavTab.WALLET,
            onClick = { onTabSelected(AppNavTab.WALLET) },
            modifier = Modifier.weight(1f)
        )

        // Tab 3: PROFILE
        HudTabItem(
            tab = AppNavTab.PROFILE,
            isSelected = currentTab == AppNavTab.PROFILE,
            onClick = { onTabSelected(AppNavTab.PROFILE) },
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun HudTabItem(
    tab: AppNavTab,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(CutCornerShape(4.dp))
            .background(if (isSelected) SlateElevated else Color.Transparent)
            .border(
                BorderStroke(
                    BrutalistBorderThin,
                    if (isSelected) CyberAmber else Color.Transparent
                ),
                CutCornerShape(4.dp)
            )
            .clickable { onClick() }
            .padding(vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                painter = painterResource(id = tab.iconRes),
                contentDescription = tab.title,
                tint = if (isSelected) CyberAmber else Color.White.copy(alpha = 0.5f),
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = tab.title,
                fontFamily = ChakraPetch,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                fontSize = 10.sp,
                color = if (isSelected) Color.White else Color.White.copy(alpha = 0.5f)
            )
        }
    }
}
