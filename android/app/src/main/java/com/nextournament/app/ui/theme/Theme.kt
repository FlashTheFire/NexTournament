package com.nextournament.app.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = NeonAmber,
    onPrimary = ObsidianBlack,
    primaryContainer = SlateElevated,
    onPrimaryContainer = NeonAmberBright,
    secondary = NeonCyan,
    onSecondary = ObsidianBlack,
    secondaryContainer = SlateElevated,
    onSecondaryContainer = NeonCyanBright,
    tertiary = CyberEmerald,
    onTertiary = ObsidianBlack,
    background = ObsidianBlack,
    onBackground = TextWhitePrimary,
    surface = SlateCardSurface,
    onSurface = TextWhitePrimary,
    surfaceVariant = SlateElevated,
    onSurfaceVariant = TextMutedSecondary,
    error = LaserCrimson,
    onError = ObsidianBlack
)

@Composable
fun NexTournamentTheme(
    content: @Composable () -> Unit
) {
    val colorScheme = DarkColorScheme
    val view = LocalView.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = ObsidianBlack.toArgb()
            window.navigationBarColor = ObsidianBlack.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = false
                isAppearanceLightNavigationBars = false
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = EsportsTypography,
        shapes = EsportsShapes,
        content = content
    )
}
