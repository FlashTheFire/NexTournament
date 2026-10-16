package com.nextournament.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.nextournament.app.R

// ============================================================================
// REAL DOWNLOADED GOOGLE FONTS & CYBER-ESPORTS FAMILIES
// ============================================================================

val OrbitronFontFamily = FontFamily(
    Font(R.font.orbitron_bold, FontWeight.Bold)
)

val ChakraPetchFontFamily = FontFamily(
    Font(R.font.chakra_petch_bold, FontWeight.Bold)
)

val InterFontFamily = FontFamily(
    Font(R.font.inter_regular, FontWeight.Normal),
    Font(R.font.inter_bold, FontWeight.Bold)
)

// Convenient aliases for direct font-family reference
val OrbitronFont = OrbitronFontFamily
val ChakraPetch = ChakraPetchFontFamily
val InterFont = InterFontFamily

val EsportsTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = OrbitronFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 30.sp,
        letterSpacing = 1.sp,
        color = TextWhitePrimary
    ),
    displayMedium = TextStyle(
        fontFamily = OrbitronFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 22.sp,
        letterSpacing = 0.5.sp,
        color = TextWhitePrimary
    ),
    headlineMedium = TextStyle(
        fontFamily = ChakraPetchFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 18.sp,
        letterSpacing = 0.5.sp,
        color = TextWhitePrimary
    ),
    titleMedium = TextStyle(
        fontFamily = ChakraPetchFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 15.sp,
        letterSpacing = 0.25.sp,
        color = TextWhitePrimary
    ),
    bodyLarge = TextStyle(
        fontFamily = InterFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        color = TextWhitePrimary
    ),
    bodyMedium = TextStyle(
        fontFamily = InterFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        color = TextMutedSecondary
    ),
    labelSmall = TextStyle(
        fontFamily = ChakraPetchFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 11.sp,
        letterSpacing = 0.5.sp,
        color = TextMutedSecondary
    )
)
