# 🤖 17. Android App Technical Architecture & In-App OTA Update Engine

---

## 1. Technical Stack & Architecture Overview

The **NexTournament Android App** is engineered as a modern, high-performance native Android application adhering to Google's official Architecture Guidance: **Clean Architecture + MVVM/MVI** (Model-View-ViewModel with unidirectional StateFlow).

### 1.1 Technology Stack Matrix

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Kotlin 2.0+ | Modern language features, coroutines, type safety. |
| **UI Framework** | Jetpack Compose + Material 3 | Declarative UI, dynamic animations, high rendering speed, customizable themes. |
| **Concurrency** | Kotlin Coroutines & StateFlow | Reactive, lifecycle-aware asynchronous streams without memory leaks. |
| **Networking** | Ktor Client / Retrofit 2 + OkHttp | HTTP/2, TLS 1.3, Certificate Pinning, and native WebSocket support. |
| **Serialization** | `kotlinx.serialization` | High-speed, reflection-free JSON decoding. |
| **Dependency Injection** | Hilt (Dagger) / Koin | Modular, testable inversion of control across all app modules. |
| **Local Cache** | Jetpack Room | Offline persistence of tournament cards, player stats, and game rules. |
| **Encrypted Storage** | AndroidX `EncryptedSharedPreferences` | Hardware-backed AES-256 GCM storage for JWT tokens and cryptographic keys. |
| **Image Loading** | Coil | Fast, memory-efficient loading of game banners, avatars, and weapon skins. |
| **Image OCR Capture** | CameraX + Photo Picker | High-resolution capture of end-game scoreboard screenshots. |

---

## 2. UI/UX Architecture & Screen Matrix

The application UI is crafted in an immersive **Gen Z Esports Dark Mode** aesthetic adhering to the master standard defined in **[18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md](file:///d:/Nex-Projects/NexTournament/docs/18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md)**:
- **Geometry**: Sharp and angular corners (`CutCornerShape(4.dp)` / `RectangleShape`), eliminating generic rounded corners.
- **Palette**: Deep Obsidian (`#020617`), Slate (`#0F172A`), Electric Amber (`#F59E0B`), Laser Crimson (`#EF4444`), Toxic Emerald (`#10B981`), and Neon Cyan (`#06B6D4`).
- **Assets**: Built using the **50-Source Asset Pipeline** (Keyline Sharp Icons, StockCake 4K backgrounds, Mixkit video loops, Lottie micro-interactions, and Clash Display / Inter fonts).

```
                              ┌───────────────────────────────────┐
                              │           App Launch              │
                              └─────────────────┬─────────────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │    Version / OTA Check│
                                    └───────────┬───────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     │ [Forced Update]                                     │ [Up to Date / Flexible]
                     ▼                                                     ▼
        ┌──────────────────────────┐                         ┌──────────────────────────┐
        │   Forced OTA Update UI   │                         │  Authentication Gateway  │
        │  (Download & Install)    │                         │  • Phone OTP             │
        └──────────────────────────┘                         │  • Sync with Telegram    │
                                                             │  • Google Sign-In        │
                                                             └─────────────┬────────────┘
                                                                           │
                                                             ┌─────────────▼────────────┐
                                                             │      Main App Shell      │
                                                             │   (Bottom Navigation)    │
                                                             └──────┬──────┬──────┬─────┘
                                                                    │      │      │
            ┌───────────────────────────────────────────────────────┘      │      └───────────────────────────────────┐
            ▼                                                              ▼                                          ▼
┌──────────────────────────┐                                 ┌──────────────────────────┐               ┌──────────────────────────┐
│   🎮 Tournaments Tab     │                                 │   💰 Dual-Wallet Tab     │               │   👤 Profile & Guild     │
│ • Multi-Game Switcher    │                                 │ • Game vs Win Balances   │               │ • In-Game Profiles       │
│ • Match Format Filter    │                                 │ • Dynamic UPI QR Top-up  │               │ • Free Fire UID Verify   │
│ • Cinema Visual Seating  │                                 │ • OxaPay Crypto Gateway  │               │ • 7-Day Daily Streaks    │
│ • T-15m Room Key Vault   │                                 │ • Instant Payout Request │               │ • Multi-Tier Referrals   │
│ • OCR Proof Submission   │                                 │ • Ledger Audit Logs      │               │ • Security & Settings    │
└──────────────────────────┘                                 └──────────────────────────┘               └──────────────────────────┘
```

---

## 3. Independent In-App Self-Update (OTA) Engine

### 3.1 Architecture & Flow Without Google Play Store
The app is fully autonomous and does not require Google Play Store services to update. It includes a native **OTA Update Engine** that:
1. Queries the `/api/v1/app/version-check` endpoint during app startup and network reconnects.
2. Compares the installed `BuildConfig.VERSION_CODE` with the server's `version_code` and `min_supported_version_code`.
3. Downloads the APK in chunks via a foreground download worker with notification progress.
4. Validates the downloaded file's SHA-256 cryptographic hash against the server manifest.
5. Invokes the native Android `PackageInstaller` or `Intent.ACTION_VIEW` via a secure `FileProvider`.

### 3.2 Update Check Payload Model
```json
{
  "platform": "android",
  "latest_version": "2.2.0",
  "version_code": 22,
  "min_supported_version_code": 18,
  "is_force_update": true,
  "download_url": "https://cdn.domain.com/releases/NexTournament_v2.2.0.apk",
  "apk_sha256": "4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123",
  "file_size_bytes": 31457280,
  "release_notes": "🚀 Major Update:\n• Multi-Game BGMI & Valorant support\n• Instant OCR auto-scorecard settlement\n• Faster visual seat locking engine",
  "published_at": "2026-10-16T12:00:00Z"
}
```

### 3.3 Kotlin Implementation Blueprint

#### Step 1: FileProvider Configuration (`AndroidManifest.xml`)
```xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application ...>
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
```

`res/xml/file_paths.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <external-cache-path name="apk_downloads" path="updates/" />
    <cache-path name="internal_apk_downloads" path="updates/" />
</paths>
```

#### Step 2: Download & SHA-256 Checksum Verification
```kotlin
package com.nextournament.app.ota

import android.content.Context
import java.io.File
import java.io.InputStream
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request

class OtaUpdateManager(private val context: Context, private val client: OkHttpClient) {

    suspend fun downloadApk(
        downloadUrl: String, 
        expectedSha256: String, 
        onProgress: (Int) -> Unit
    ): Result<File> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder().url(downloadUrl).build()
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) return@withContext Result.failure(Exception("HTTP ${response.code}"))

            val updateDir = File(context.cacheDir, "updates").apply { if (!exists()) mkdirs() }
            val apkFile = File(updateDir, "update.apk")
            if (apkFile.exists()) apkFile.delete()

            val body = response.body ?: return@withContext Result.failure(Exception("Empty body"))
            val totalBytes = body.contentLength()
            var downloadedBytes = 0L

            body.byteStream().use { input ->
                apkFile.outputStream().use { output ->
                    val buffer = ByteArray(8192)
                    var bytesRead: Int
                    while (input.read(buffer).also { bytesRead = it } != -1) {
                        output.write(buffer, 0, bytesRead)
                        downloadedBytes += bytesRead
                        if (totalBytes > 0) {
                            val percent = ((downloadedBytes * 100) / totalBytes).toInt()
                            onProgress(percent)
                        }
                    }
                }
            }

            // Cryptographic Checksum Verification
            val calculatedSha256 = calculateSha256(apkFile)
            if (!calculatedSha256.equals(expectedSha256, ignoreCase = true)) {
                apkFile.delete()
                return@withContext Result.failure(Exception("SHA-256 checksum mismatch! File may be corrupted."))
            }

            Result.success(apkFile)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun calculateSha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { fis ->
            val buffer = ByteArray(8192)
            var n: Int
            while (fis.read(buffer).also { n = it } != -1) {
                digest.update(buffer, 0, n)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}
```

#### Step 3: Triggering Android Package Installation
```kotlin
package com.nextournament.app.ota

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import java.io.File

fun triggerApkInstallation(context: Context, apkFile: File) {
    // 1. Verify unknown sources permission on Android 8.0+ (Oreo)
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        if (!context.packageManager.canRequestPackageInstalls()) {
            val permissionIntent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                data = Uri.parse("package:${context.packageName}")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(permissionIntent)
            return
        }
    }

    // 2. Obtain content URI via FileProvider
    val contentUri: Uri = FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        apkFile
    )

    // 3. Launch Package Installer Intent
    val installIntent = Intent(Intent.ACTION_VIEW).apply {
        setDataAndType(contentUri, "application/vnd.android.package-archive")
        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
    }
    context.startActivity(installIntent)
}
```

---

## 4. Visual Cinema-Style Seat Picker Implementation

### 4.1 UI Layout Architecture
In battle royale custom rooms, seating position dictates team squad mates and drop-zones. The UI is built using Jetpack Compose `LazyVerticalGrid` and team clusters:

```kotlin
@Composable
fun CinemaSeatPicker(
    matchType: TeamFormat, // SOLO, DUO, SQUAD, SIX_V_SIX
    totalSlots: Int,       // e.g. 48
    lockedSlots: Map<Int, Long>, // Slot -> UserID
    bookedSlots: Set<Int>,       // Confirmed slots
    mySelectedSlot: Int?,
    onSeatClick: (Int) -> Unit
) {
    val teamSize = when (matchType) {
        TeamFormat.SOLO -> 1
        TeamFormat.DUO -> 2
        TeamFormat.SQUAD -> 4
        TeamFormat.SIX_V_SIX -> 6
    }
    val numberOfTeams = totalSlots / teamSize

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        items(numberOfTeams) { teamIndex ->
            val teamNumber = teamIndex + 1
            TeamClusterCard(
                teamNumber = teamNumber,
                teamSize = teamSize,
                startSlot = (teamIndex * teamSize) + 1,
                bookedSlots = bookedSlots,
                lockedSlots = lockedSlots,
                mySelectedSlot = mySelectedSlot,
                onSeatClick = onSeatClick
            )
            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}
```

---

## 5. Security & Anti-Cheat Subsystem

### 5.1 Defense-in-Depth Client Protection

1. **Root Detection (SafetyNet Independent)**:
   - File existence checks for common su binaries: `/system/bin/su`, `/system/xbin/su`, `/sbin/su`, `/data/local/xbin/su`.
   - Build tags inspection: Checking if `Build.TAGS` contains `test-keys`.
   - Root cloaking detection (checks for Magisk `su` mounts and Zygisk injection artifacts).

2. **Hooking & Tamper Detection**:
   - Inspects `/proc/self/maps` for loaded libraries matching `frida-gadget.so`, `xposed.so`, or `substrate.so`.
   - Probes local TCP socket `127.0.0.1:27042` (default Frida server port).

3. **Room Vault Screenshot Blocking**:
   ```kotlin
   // In RoomVaultActivity or RoomVaultDialog:
   activity?.window?.setFlags(
       WindowManager.LayoutParams.FLAG_SECURE,
       WindowManager.LayoutParams.FLAG_SECURE
   )
   ```
   Blocks native Android screenshots, screen recording apps, and HDMI video mirroring of confidential match credentials.

4. **SSL Certificate Pinning**:
   Configured in `network_security_config.xml` with backup server SHA-256 public key pins preventing MITM network interception.
