package com.nextournament.app.ui.theme

import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.unit.dp

// ============================================================================
// SHARP & ANGULAR GEOMETRY (NO BUBBLY ROUNDED CORNERS)
// ============================================================================

// Absolute Sharp 0dp
val SharpCornerShape = RectangleShape

// Cut-Corner Chamfered Shapes (45-degree tactical cyber cut)
val CutCornerSmall = CutCornerShape(
    topStart = 0.dp,
    topEnd = 6.dp,
    bottomEnd = 0.dp,
    bottomStart = 6.dp
)

val CutCornerBadge = CutCornerShape(4.dp)
val CutCornerButton = CutCornerShape(6.dp)
val CutCornerCard = CutCornerShape(8.dp)
val CutCornerDialog = CutCornerShape(12.dp)

// Neo-Brutalist HUD Border Widths
val BrutalistBorderThin = 1.dp
val BrutalistBorderStandard = 1.5.dp
val BrutalistBorderThick = 2.dp

val EsportsShapes = Shapes(
    extraSmall = CutCornerBadge,
    small = CutCornerSmall,
    medium = CutCornerButton,
    large = CutCornerCard,
    extraLarge = CutCornerDialog
)
