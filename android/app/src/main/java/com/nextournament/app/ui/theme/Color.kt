package com.nextournament.app.ui.theme

import androidx.compose.ui.graphics.Color

// ============================================================================
// OBSIDIAN & SLATE DARK PALETTE (AMOLED OPTIMIZED)
// ============================================================================
val ObsidianBlack = Color(0xFF020617)       // Deepest screen background
val SlateBackground = Color(0xFF0B0F19)     // Secondary background
val SlateCardSurface = Color(0xFF131B2E)    // Elevated card & HUD container
val SlateElevated = Color(0xFF1E293B)       // Active stroke / secondary surface
val SlateMutedBorder = Color(0xFF334155)    // Muted border / divider

// Aliases for layout compatibility
val SlateCard = SlateCardSurface

// ============================================================================
// CYBER-ESPORTS HIGH-CONTRAST NEON ACCENTS
// ============================================================================
val NeonAmber = Color(0xFFF59E0B)           // Primary CTA / Prize Pools / Gold
val NeonAmberBright = Color(0xFFFBBF24)     // Active hover & high glow
val NeonAmberGlow = Color(0x33F59E0B)       // Ambient glow (20% alpha)

val CyberAmber = NeonAmber

val CyberEmerald = Color(0xFF10B981)        // Success / Available Seats / Deposits
val CyberEmeraldBright = Color(0xFF00FF66)  // Live heartbeat indicator
val CyberEmeraldGlow = Color(0x3310B981)    // Success glow

val LaserCrimson = Color(0xFFEF4444)        // Error / Booked Slots / Anti-Cheat
val LaserCrimsonBright = Color(0xFFFF003C)  // Critical alerts
val LaserCrimsonGlow = Color(0x33EF4444)    // Danger glow

val CrimsonRed = LaserCrimson
val CyberCrimson = LaserCrimson

val NeonCyan = Color(0xFF06B6D4)            // Room Vault / Active Timers / Cyan HUD
val NeonCyanBright = Color(0xFF00F0FF)      // Timer pulse
val NeonCyanGlow = Color(0x3306B6D4)        // Vault glow

val ElectricBlue = Color(0xFF0284C7)

// ============================================================================
// TYPOGRAPHY TEXT COLORS
// ============================================================================
val TextWhitePrimary = Color(0xFFF8FAFC)    // 95% White
val TextMutedSecondary = Color(0xFF94A3B8)  // Slate Muted 60%
val TextDisabled = Color(0xFF64748B)        // Disabled state
