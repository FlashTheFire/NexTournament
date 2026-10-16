package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nextournament.app.ui.theme.*

@Composable
fun CyberActionButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    accentColor: Color = NeonAmber,
    textColor: Color = ObsidianBlack,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        shape = CutCornerButton, // Angular chamfered shape
        border = BorderStroke(BrutalistBorderStandard, if (enabled) accentColor else SlateMutedBorder),
        colors = ButtonDefaults.buttonColors(
            containerColor = accentColor,
            contentColor = textColor,
            disabledContainerColor = SlateElevated,
            disabledContentColor = TextDisabled
        ),
        contentPadding = PaddingValues(horizontal = 18.dp, vertical = 8.dp),
        modifier = modifier.height(44.dp)
    ) {
        Text(
            text = text.uppercase(),
            fontSize = 13.sp,
            fontWeight = FontWeight.Black,
            letterSpacing = 1.sp
        )
    }
}
