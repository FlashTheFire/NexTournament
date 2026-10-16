# 🚀 Phase 3 Execution Plan & Completion Report: In-App OTA Update Engine & Anti-Cheat Pipeline

---

## 📋 1. Executive Summary & Architecture Overview

**Phase 3** implements the mission-critical independent distribution and fair-play security layer for the **NexTournament Universal Android App** (`com.nextournament.app`).

Because NexTournament operates real-money esports tournaments (Free Fire, BGMI, CODM, Valorant) across global and regional demographics, it requires:
1. **Zero-Dependency In-App Self-Update (OTA) Engine**: Bypasses the restrictions and delay of the Google Play Store, enabling instantaneous deployment of critical security fixes, anti-cheat signatures, and match engine patches.
2. **Esports Anti-Cheat & Hardware Integrity Protection**: Guarantees tournament integrity by detecting rooted devices, PC emulators, and dynamic memory hooking frameworks (Frida, Xposed, Substrate), combined with dynamic screenshot/recording blocking (`FLAG_SECURE`) on sensitive room credentials and wallet screens.

---

## 🔄 2. In-App Self-Update (OTA) Engine Architecture

### 2.1 Protocol Specifications & DTOs
- **Endpoint**: `GET /api/v1/app/check-update?currentVersionCode={code}&platform=android`
- **Model** (`UpdateCheckResponse`):
  - `isUpdateAvailable`: Boolean
  - `isForced`: Boolean (Mandatory protocol break vs optional update)
  - `minSupportedVersionCode`: Minimum allowed build
  - `latestVersionCode` & `latestVersionName`
  - `apkUrl`: Direct CDN download URL
  - `apkSha256`: Expected SHA-256 cryptographic package signature
  - `downloadSize`: Formatted string (e.g. `24.5 MB`)
  - `changelog`: Monospaced release notes

### 2.2 Streaming Downloader (`OtaUpdateManager.kt`)
- **Direct OkHttp Chunked Streaming**: Downloads the `.apk` file directly to the app's sandboxed cache (`context.cacheDir/updates/NexTournament_update.apk`).
- **Reactive StateFlow Progress**: Emits `DownloadState` (`Idle`, `Progress(bytes, total, percent)`, `VerifyingChecksum`, `Success(File)`, `Error(message)`).
- **Cryptographic SHA-256 Verification**:
  - Automatically calculates the SHA-256 digest of the downloaded `.apk` using streaming 8KB chunks.
  - Compares the calculated hash against the server-signed `apkSha256`.
  - Automatically deletes corrupted or tampered files if checksum validation fails.

### 2.3 Installation Intent & Android 8.0+ Compatibility
- **Unknown Sources Permission**: Automatically checks `context.packageManager.canRequestPackageInstalls()` on API 26+ (Android 8.0 Oreo). If ungranted, routes the user directly to `Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES`.
- **Android FileProvider**:
  - Authority: `${applicationId}.fileprovider`
  - Configured in `res/xml/file_paths.xml` pointing to `cacheDir/updates/`.
  - Generates secure `content://` URI with `FLAG_GRANT_READ_URI_PERMISSION`.
  - Dispatches `Intent.ACTION_VIEW` with MIME type `application/vnd.android.package-archive` to invoke the native Android package installer.

### 2.4 User Interface Components
- **`ForcedUpdateDialog.kt`**:
  - Non-dismissible full-screen cyberpunk modal (`CutCornerShape(8.dp)`, OLED Obsidian `#020617`, 1.5dp `#F59E0B` border).
  - Displays build version, formatted changelog, and dynamic progress bar.
  - Disables back-press and outside clicks to block app access until the required update is installed.
- **`FlexibleUpdateBanner.kt`**:
  - Dismissible ambient top HUD banner for optional minor updates.
  - Allows players to trigger in-background downloading without leaving their tournament lobby view.

---

## 🛡️ 3. Esports Hardware Anti-Cheat & Fair Play Pipeline

### 3.1 Device Integrity Evaluation (`AntiCheatManager.kt`)
Evaluates the client environment into 4 distinct security tiers:
1. `CLEAN`: Verified physical hardware without root or memory hooking.
2. `EMULATOR`: PC Android emulator (Bluestacks, Nox, LDPlayer, Genymotion, QEMU).
3. `ROOTED`: Rooted operating system with SU binaries or Magisk detected.
4. `HOOK_DETECTED`: Injected hooking libraries (Frida, Xposed, Substrate).

### 3.2 Detection Techniques Implemented
- **Root Detection**:
  - Inspects `Build.TAGS` for `test-keys`.
  - Checks existence of 11 standard SU binary paths (`/system/app/Superuser.apk`, `/sbin/su`, `/system/bin/su`, `/system/xbin/su`, `/data/local/xbin/su`, etc.).
  - Scans for Magisk directories (`/sbin/.magisk`, `/data/adb/magisk`).
  - Executes test command `which su` via `Runtime.getRuntime().exec()`.
- **Emulator Detection**:
  - Scans hardware fingerprints (`Build.FINGERPRINT`, `Build.HARDWARE`, `Build.MODEL`, `Build.MANUFACTURER`, `Build.PRODUCT`).
  - Detects QEMU drivers (`goldfish`, `ranchu`, `vbox86`) and PC emulator brands (`Nox`, `Bluestacks`, `Genymotion`).
- **Frida / Xposed / Memory Hook Detection**:
  - Scans `/proc/self/maps` at runtime for injected libraries (`frida-agent`, `frida-gadget`, `xposed`, `substrate`, `cydia`).
  - Probes Frida default server listening ports (`27042` and `27047`) on localhost.
- **Dynamic Window Security (`FLAG_SECURE`)**:
  - `applyWindowSecurity(activity, enableSecure = true)` dynamically enables `WindowManager.LayoutParams.FLAG_SECURE`.
  - Blocks screenshots and video recordings specifically when viewing the T-15m Room Credentials Vault and payment gateways.

### 3.3 Anti-Cheat UI
- **`AntiCheatViolationDialog.kt`**:
  - High-impact neo-brutalist modal alert (`#EF4444` Crimson Red).
  - Outlines exact violation flags, device integrity token, and immediately locks the user out of tournament registrations and live lobbies.

---

## 📦 4. Official Assets Embedded for Phase 3

All vector XML drawables were pulled directly from Google's official `google/material-design-icons` repository without manual path editing:
- [`ic_system_update.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_system_update.xml): Official `system_update_24px.xml` (OTA update banner & modal badge).
- [`ic_gpp_bad.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_gpp_bad.xml): Official `gpp_bad_24px.xml` (Anti-Cheat integrity violation shield).
- [`ic_download_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_download_sharp.xml): Official `download_24px.xml` (Download APK progress action).
- [`ic_fingerprint_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_fingerprint_sharp.xml): Official `fingerprint_24px.xml` (Device hardware verification token).

---

## 📁 5. Directory Structure for Phase 3

```
NexTournament/
└── android/app/src/main/
    ├── res/drawable/
    │   ├── ic_system_update.xml       # Official Google Material Symbols Sharp
    │   ├── ic_gpp_bad.xml             # Official Google Material Symbols Sharp
    │   ├── ic_download_sharp.xml      # Official Google Material Symbols Sharp
    │   └── ic_fingerprint_sharp.xml   # Official Google Material Symbols Sharp
    └── java/com/nextournament/app/
        ├── MainActivity.kt            # Wired with AntiCheat & OTA lifecycle
        ├── data/
        │   ├── ota/
        │   │   └── OtaUpdateManager.kt    # OkHttp streaming + SHA-256 + FileProvider intent
        │   └── security/
        │       └── AntiCheatManager.kt    # Root, emulator, Frida, and FLAG_SECURE
        └── ui/components/
            ├── ForcedUpdateDialog.kt      # Non-dismissible cyberpunk modal
            ├── FlexibleUpdateBanner.kt    # Ambient top HUD banner
            └── AntiCheatViolationDialog.kt# Security lockout modal
```

---

## 🎯 6. Verification Checklist & Current Status

| Component | Target Requirement | Status |
|---|---|---|
| **OTA Update Protocol** | Server check endpoint integration with DTO | ✅ Verified |
| **Streaming Downloader** | OkHttp chunked streaming with StateFlow progress | ✅ Verified |
| **Cryptographic Integrity**| SHA-256 package hash verification before install | ✅ Verified |
| **FileProvider Plumbing** | `file_paths.xml` cache integration and `ACTION_VIEW` intent | ✅ Verified |
| **Android 8.0+ Unknown Apps**| `canRequestPackageInstalls()` permission flow | ✅ Verified |
| **Forced & Flexible UI** | `ForcedUpdateDialog.kt` and `FlexibleUpdateBanner.kt` | ✅ Verified |
| **Root Detection** | Test-keys, binary paths, Magisk, and `which su` | ✅ Verified |
| **Emulator Detection** | Hardware/fingerprint checks (Bluestacks, Nox, QEMU) | ✅ Verified |
| **Hook Detection** | `/proc/self/maps` inspection + Frida port scanning | ✅ Verified |
| **Window Security** | Dynamic `FLAG_SECURE` window screenshot blocking | ✅ Verified |

**Phase 3 Status**: **100% COMPLETE, INTEGRATED, AND READY FOR CINEMA SEATING & ROOM VAULT (PHASE 4)**.
