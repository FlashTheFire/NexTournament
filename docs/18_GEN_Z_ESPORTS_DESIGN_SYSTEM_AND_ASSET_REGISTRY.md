# ⚡ 18. Gen Z Esports Design System & Master Asset Registry

> **Design Ethos**: Dark Mode Primacy • Sharp & Angular Corners • Neo-Brutalist High-Contrast HUD • Cyberpunk Neon Accents • Ultra-HD Gaming Assets

---

## 1. Design Philosophy & Visual Language

The NexTournament Universal Platform (Android App, Web, and Bot) enforces a bold, modern **Gen Z Esports Aesthetic**. Moving away from dated, overly bubbly/rounded consumer app designs, NexTournament adopts an **angular, tactical cyber-HUD aesthetic** inspired by competitive tournament broadcast overlays, high-end gaming cockpits, and neo-brutalist interfaces.

### 1.1 Core Aesthetic Pillars
1. **Sharp / Angular Geometry**:
   - Primary elements (buttons, tournament cards, seat grids, dialogs) utilize **sharp corners (`0dp`)** or **chamfered/cut corners (`CutCornerShape(4.dp)`)**.
   - No generic bubbly rounded corners (`> 8dp` is banned for core interactive cards).
2. **Deep Obsidian & Slate Dark Palette**:
   - Ultra-deep dark surfaces (`#020617`, `#0B0F19`, `#0F172A`) to ensure zero screen glare during late-night gaming sessions and high battery efficiency on AMOLED screens.
3. **High-Contrast Neon Accents**:
   - **Electric Amber / Gold (`#F59E0B`, `#FBBF24`)**: Tournament prize pools, 1st place badges, VIP elements.
   - **Toxic / Cyber Green (`#10B981`, `#00FF66`)**: Instant deposits, confirmed seats, alive players, high ping status.
   - **Laser Crimson (`#EF4444`, `#FF003C`)**: Locked seats, elimination alerts, high-risk warnings, emergency stops.
   - **Neon Cyan / Hyper Blue (`#06B6D4`, `#00F0FF`)**: Room credential reveal, timer counters, live streams.
4. **Neo-Brutalist HUD Borders & Shadows**:
   - Crisp 1.5dp – 2dp solid borders (`BorderStroke(1.5.dp, CyberAmber)`) with zero-blur hard offset shadows (`4dp 4dp #000000`) for tactile depth.
5. **Technical Cyber-Esports Typography**:
   - Display Headings: **Clash Display**, **Chakra Petch**, or **Orbitron** (angular, futuristic, authoritative).
   - Monospace Data / Counts / Timers: **JetBrains Mono** or **Space Mono**.
   - UI Body Text: **Inter** or **Cabinet Grotesk** for ultra-clean readability at small sizes.

---

## 2. Master Curated 50-Source Asset Registry

This registry serves as the authoritative asset sourcing and design system baseline across all NexTournament client apps.

### 2.1 UI Kits & Design Systems (Dark + Sharp Corner Priority)

| Rank | Source Name | Primary Specialty | Application in NexTournament | Direct URL |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Untitled UI** (Free Edition) | Full Master Design System | Baseline component architecture, layout grids, spacing scales, and form inputs. | [untitledui.com](https://www.untitledui.com/free-figma-ui-kit) |
| **2** | **shadcn/ui Kit** (Obra Edition) | React + Tailwind Component Tokens | Core token structure for our Web platform and Compose token translation. | [figma.com/community](https://www.figma.com/community/file/1514746685758799870/obra-shadcn-ui-kit-community-edition) |
| **3** | **Moja UI** | Complete Free UI Kit + Dark Mode | Dark-mode elevation surfaces, card borders, and mobile bottom sheet specifications. | [figma.com/community](https://www.figma.com/community/file/1108679668074690379/moja-ui-ultimate-ui-kit-july-2025-update-variables-darkmode) |
| **4** | **Plus UI** | Design-to-Code + Dark Tokens | Pre-built token exports for dark mode contrast and typography hierarchies. | [figma.com/community](https://www.figma.com/community/file/1310670219738074447/plus-ui-free-figma-ui-kit-and-design-system-2026-v2-0) |
| **5** | **Glow UI** (Free) | Modern SaaS & Gaming Dashboards | Ambient neon glow effects around active tournament cards and winner celebrations. | [figma.com/community](https://www.figma.com/community/file/1484939366437997010/glow-ui-free-ui-kit-and-design-system-for-web-apps-and-saas) |
| **6** | **Neo Brutalism UI Library** | Sharp & Bold Angular Styling | Direct source for angular cut-corner buttons, heavy 2dp borders, and high-impact badges. | [figma.com/community](https://www.figma.com/community/file/1613945708230609539/neo-brutalism-ui-library-lite) |
| **7** | **Flowbite Design System** | Tailwind Ecosystem Architecture | Responsive table designs and mobile drawer navigation patterns. | [flowbite.com](https://flowbite.com/figma/) |
| **8** | **Green Mist UI 2.0** | Pure Midnight Dark Theme | Deep black OLED color swatches and emerald cyber accent palettes. | [figma.com/community](https://www.figma.com/community/file/1332091610740792452/green-mist-ui-2-0-free-dark-theme-ui-kit) |
| **9** | **Dark Mode Tokens Kit** | Color Contrast Token Systems | Accessibility-tested AAA contrast tokens between background layers and text. | [figma.com/community](https://www.figma.com/community/file/1122201319789659743/dark-mode-design-tokens-creative-kit-free) |
| **10** | **Carbon Design System** | Enterprise-Grade Dark System | Complex administrative data grids, settlement tables, and audit logs. | [carbondesignsystem.com](https://carbondesignsystem.com/) |

---

### 2.2 SVG Icon Libraries (Sharp Corner Priority)

| Rank | Library | Icon Count | Sharp Styling | Application in NexTournament | Direct URL |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **11** | **Keyline Icons** | 1,435+ | **Primary Choice (Sharp)** | Primary vector icons across Android App topbars, bottom bars, and match filters. | [keylineicons.com](https://keylineicons.com/) |
| **12** | **Tabler Icons** | 6,200+ | Strong Line Style | Utility icons for wallet transactions, settings, copy-to-clipboard, and device stats. | [tabler.io](https://tabler.io/icons) |
| **13** | **Phosphor Icons** | 9,000+ | Geometric Clean | Bold weight icons for bottom navigation tabs and quick action FABs. | [phosphoricons.com](https://phosphoricons.com/) |
| **14** | **Lucide Icons** | 1,800+ | Minimal Sharp | Clean minimal icons for inline match info: entry fees, kill bounty, and map indicators. | [lucide.dev](https://lucide.dev/icons) |
| **15** | **Remix Icons** | 3,200+ | Line + Solid Fill | Status indicator icons (verified check, locked room padlock, live pulse). | [remixicon.com](https://remixicon.com/) |
| **16** | **Heroicons** | 1,200+ | Solid + 20/24 Outline | High-contrast notification bell, search, and user profile icons. | [heroicons.com](https://heroicons.com/) |
| **17** | **Material Symbols Sharp** | 15,000+ | **Sharp Variant** | Native Android Vector Drawables for high-speed hardware-accelerated rendering. | [fonts.google.com/icons](https://fonts.google.com/icons?icon.set=Material+Symbols) |
| **18** | **Iconify + Icon Hub** | 200,000+ | Universal Sets | Dynamic SVG icon loader for multi-game publisher logos and payment gateway icons. | [iconify.design](https://icon-sets.iconify.design/) |
| **19** | **Streamline Cyber / Sharp** | Gaming-Centric | Angular Cyber | Custom tactical icons: crosshairs, shields, helmets, armor, and weapon classes. | [streamlinehq.com](https://www.streamlinehq.com/icons/streamline-cyber) |
| **20** | **theSVG** | 4,000+ Logos | Dark / Light Vectors | Official brand logos for payment methods (UPI, Paytm, OxaPay, TRON, Bitcoin). | [thesvg.org](https://thesvg.org/) |

---

### 2.3 High-Class Imagery, Backgrounds & Game Graphics

| Rank | Platform | Content Specialty | Application in NexTournament | Direct URL |
| :---: | :--- | :--- | :--- | :--- |
| **21** | **Unsplash Gaming** | Cyberpunk cityscapes, neon battlegrounds | Hero header banners for major tournament leagues and championship series. | [unsplash.com](https://unsplash.com/s/photos/gaming-background) |
| **22** | **Pexels Esports** | Competitive stage setups, pro gamers | Community banners, hall-of-fame backdrops, and leaderboard hero cards. | [pexels.com](https://www.pexels.com/search/esports/) |
| **23** | **Pixabay Battle Royale** | Aerial maps, drop zones, futuristic arenas | Map selection thumbnails (Bermuda, Purgatory, Erangel, Kalahari). | [pixabay.com](https://pixabay.com/images/search/battle%20royale/) |
| **24** | **StockCake Cyberpunk** | Ultra-HD AI futuristic arenas & neon stages | Cinematic match lobby backdrops and victory celebration screen artwork. | [stockcake.com](https://stockcake.com/s/cyberpunk) |
| **25** | **Alphacoders** | 4K Gaming & Battle Royale Wallpapers | High-resolution character backdrops for profile cards and clan banners. | [alphacoders.com](https://alphacoders.com/battle-royale-wallpapers) |
| **26** | **WallpaperCat** | Battle Royale Tactical Art | Visual assets for Free Fire and BGMI custom tournament promotional cards. | [wallpapercat.com](https://wallpapercat.com/battle-royale-game-wallpapers) |
| **27** | **Freepik Esports** | Premium vectors, badge shields, ribbons | Rank tier emblems (Bronze, Silver, Gold, Platinum, Diamond, Heroic, Grandmaster). | [freepik.com](https://www.freepik.com/search?format=search&query=battle%20royale&type=psd) |
| **28** | **PurePNG BR Assets** | Transparent PNG weapons, crates, airdrops | Floating UI visual elements: Airdrop box for daily streak, golden trophy for 1st place. | [purepng.com](https://purepng.com/tags/battle%20royale) |
| **29** | **Game-Icons.net** | 4,000+ Tactical & RPG Game SVGs | Kill feed icons, headshot skull, sniper crosshair, bomb defusal icons. | [game-icons.net](https://game-icons.net/) |
| **30** | **Dribbble Esports** | Industry-leading UI/UX inspiration | Reference benchmarks for esports seating grids and broadcast overlays. | [dribbble.com](https://dribbble.com/search/battle-royale) |

---

### 2.4 Video, Motion & Interactive Animation Assets

| Rank | Source Name | Media Type | Application in NexTournament | Direct URL |
| :---: | :--- | :--- | :--- | :--- |
| **31** | **Mixkit Cyberpunk** | 4K Stock Video Loops | Looping cyberpunk video background on the Splash/Auth screen and Championship reveals. | [mixkit.co](https://mixkit.co/free-stock-video/cyberpunk/) |
| **32** | **Pixabay Videos** | Neon grids & HUD motion graphics | Background ambient motion in the T-15m Room Credential Vault. | [pixabay.com](https://pixabay.com/videos/search/neon%20cyberpunk/) |
| **33** | **Pexels Esports Video** | Live esports tournaments & crowd hype | Marketing reels and tutorial background footage. | [pexels.com](https://www.pexels.com/search/videos/esports/) |
| **34** | **Coverr** | Cinematic royalty-free stock loops | Clean abstract tech background loops for web landing pages. | [coverr.co](https://coverr.co/) |
| **35** | **LottieFiles Gaming** | High-performance JSON animations | Micro-interactions: Seat lock countdown, coin credit burst, daily streak flame, Booyah! | [lottiefiles.com](https://lottiefiles.com/search?q=gaming) |
| **36** | **Iconify SVG Spinners** | Lightweight CSS/SVG spinners | Custom cybernetic loading spinners during OCR processing and payment verification. | [iconify.design](https://icon-sets.iconify.design/svg-spinners/) |
| **37** | **Haikei App** | Sharp polygonal & geometric SVGs | Angular SVG section dividers, sharp low-poly tournament card background accents. | [haikei.app](https://haikei.app/) |
| **38** | **SVG Backgrounds** | Pure SVG Dark Patterns | Low-bandwidth geometric patterns for ticket stubs and match ID cards. | [svgbackgrounds.com](https://www.svgbackgrounds.com/) |
| **39** | **Blush Design** | Customizable Character Vectors | Gamer avatar builder elements and empty-state illustrations ("No Matches Found"). | [blush.design](https://blush.design/) |
| **40** | **Storyset Gaming** | Animated SVG Illustrations | Error state screens: "Connection Lost", "Payment Expired", "Under Maintenance". | [storyset.com](https://storyset.com/) |

---

### 2.5 Buttons, Components, Palette Generators & Extra Tools

| Rank | Source Name | Tool Category | Application in NexTournament | Direct URL |
| :---: | :--- | :--- | :--- | :--- |
| **41** | **Free Button UI Kit** | 120 Figma Button Variants | Master reference for angular action buttons (Claim, Join, Lock, Deposit, Reveal Key). | [figma.com/community](https://www.figma.com/community/file/1631259015994163439/free-button-ui-kit-for-figma-120-variants) |
| **42** | **HyperUI** | Dark Tailwind Components | Web dashboard components for tournament hosts and administrative staff. | [hyperui.dev](https://hyperui.dev/) |
| **43** | **DaisyUI** | Semantic Tailwind Themes | Fast prototyping of tournament rules modals and leaderboard drawers. | [daisyui.com](https://daisyui.com/) |
| **44** | **Radix UI Themes** | Accessible Primitive Tokens | Accessible focus rings and keyboard navigation for desktop web players. | [radix-ui.com](https://www.radix-ui.com/themes) |
| **45** | **Chakra UI** | Flexible Theming System | Responsive modal system and notification toast styling. | [chakra-ui.com](https://chakra-ui.com/) |
| **46** | **Coolors** | Gen Z Color Palette Engine | Generating matching seasonal tournament color themes (e.g., Summer Inferno, Winter Frost). | [coolors.co](https://coolors.co/) |
| **47** | **Realtime Colors** | Live Palette Preview Tool | Testing WCAG AAA contrast ratios of neon amber/green on obsidian black backgrounds. | [realtimecolors.com](https://realtimecolors.com/) |
| **48** | **Fontshare** | Premium Open-Source Fonts | Display font sourcing (**Clash Display**, **Cabinet Grotesk**, **Satoshi**). | [fontshare.com](https://www.fontshare.com/) |
| **49** | **Google Fonts** | Global Font Directory | System-wide fonts (**Chakra Petch**, **Orbitron**, **Inter**, **JetBrains Mono**). | [fonts.google.com](https://fonts.google.com/) |
| **50** | **Figma Dark Gaming** | Community Gaming UI Directory | Continuous inspiration pipeline for tournament brackets, prize wheels, and HUD screens. | [figma.com/community](https://www.figma.com/community/search?resource_type=mixed&sort_by=relevancy&query=dark+mode+gaming+ui) |

---

## 3. Implementation Code Blueprint (Jetpack Compose & Kotlin)

Below is the concrete implementation of the **Sharp-Corner Neo-Brutalist HUD Theme** for the Android App.

### 3.1 Jetpack Compose Design Tokens (`Theme.kt`)

```kotlin
package com.nextournament.app.ui.theme

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.darkColorScheme
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.unit.dp

// 1. Obsidian & Slate Dark Palette
val ObsidianBlack = Color(0xFF020617)
val SlateBackground = Color(0xFF0B0F19)
val SlateCardSurface = Color(0xFF131B2E)
val SlateElevated = Color(0xFF1E293B)

// 2. High-Contrast Cyber Neon Accents
val NeonAmber = Color(0xFFF59E0B)       // Primary Call to Action / Gold Prizes
val NeonAmberGlow = Color(0x33F59E0B)   // Ambient Glow
val CyberEmerald = Color(0xFF10B981)    // Success / Available Seats / Deposits
val LaserCrimson = Color(0xFFEF4444)    // Booked Seats / Errors / Urgent Alerts
val NeonCyan = Color(0xFF06B6D4)        // Room Vault / Active Timers

// 3. Text & Content Colors
val TextWhitePrimary = Color(0xFFF8FAFC)
val TextMutedSecondary = Color(0xFF94A3B8)

// 4. Sharp & Angular Shape Tokens (NO BUBBLY CORNERS!)
val SharpCornerShape = RectangleShape               // 0dp absolute sharp
val CutCornerSmall = CutCornerShape(topStart = 0.dp, topEnd = 6.dp, bottomEnd = 0.dp, bottomStart = 6.dp)
val CutCornerCard = CutCornerShape(8.dp)             // Angular 45-degree chamfer
val BrutalistBorderWidth = 1.5.dp

val EsportsColorScheme = darkColorScheme(
    primary = NeonAmber,
    onPrimary = ObsidianBlack,
    secondary = NeonCyan,
    onSecondary = ObsidianBlack,
    background = ObsidianBlack,
    surface = SlateCardSurface,
    onSurface = TextWhitePrimary,
    error = LaserCrimson
)
```

### 3.2 Angular Neo-Brutalist Action Button (`CyberButton.kt`)

Inspired by **Keyline Icons + Neo Brutalism UI Library + Free Button UI Kit**:

```kotlin
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
import androidx.compose.ui.text.font.FontFamily
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
        shape = CutCornerSmall, // Angular chamfered shape
        border = BorderStroke(BrutalistBorderWidth, accentColor),
        colors = ButtonDefaults.buttonColors(
            containerColor = accentColor,
            contentColor = textColor,
            disabledContainerColor = SlateElevated,
            disabledContentColor = TextMutedSecondary
        ),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 10.dp),
        modifier = modifier.height(46.dp)
    ) {
        Text(
            text = text.uppercase(),
            fontSize = 14.sp,
            fontWeight = FontWeight.Black,
            letterSpacing = 1.2.sp
        )
    }
}
```

### 3.3 Angular Tournament Card (`TournamentHudCard.kt`)

```kotlin
package com.nextournament.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.font.FontWeight
import com.nextournament.app.ui.theme.*

@Composable
fun TournamentHudCard(
    title: String,
    game: String,
    map: String,
    entryFee: String,
    prizePool: String,
    slotsStatus: String,
    onJoinClick: () -> Unit
) {
    Card(
        shape = CutCornerCard, // Chamfered corners
        colors = CardDefaults.cardColors(containerColor = SlateCardSurface),
        border = BorderStroke(1.dp, SlateElevated),
        modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = game.uppercase(),
                    color = NeonCyan,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "MAP: $map".uppercase(),
                    color = TextMutedSecondary,
                    fontSize = 11.sp
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = title,
                color = TextWhitePrimary,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("PRIZE POOL", color = TextMutedSecondary, fontSize = 10.sp)
                    Text("₹$prizePool", color = NeonAmber, fontSize = 18.sp, fontWeight = FontWeight.Black)
                }
                Column {
                    Text("ENTRY FEE", color = TextMutedSecondary, fontSize = 10.sp)
                    Text("₹$entryFee", color = TextWhitePrimary, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
                CyberActionButton(
                    text = "JOIN ($slotsStatus)",
                    onClick = onJoinClick
                )
            }
        }
    }
}
```

---

## 4. Integration Guidelines across All Modules

1. **Icons**: Exclusively adopt **Keyline Icons** (Sharp variant) and **Material Symbols Sharp** for all UI vectors. Rounded icon sets are banned.
2. **Cards & Badges**: Always use `CutCornerCard` (45° chamfer) or `RectangleShape` (`0.dp`).
3. **Borders & Elevation**: Do not use diffuse drop shadows. Use 1.5dp solid borders with ambient color glows (`NeonAmberGlow`, `0x3310B981`).
4. **Media Assets**: Source 4K backdrops from **StockCake / Unsplash Gaming** and micro-interaction animations from **LottieFiles Gaming**.
5. **App Version OTA Dialog**: The in-app update modal uses the same angular HUD styling with a neon progress bar for the APK download.
