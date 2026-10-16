# 🚀 Phase 1 Execution Plan: Android App Scaffolding & Foundation

---

## 📋 Overview & Technical Specifications

**Phase 1** establishes the clean, production-grade foundation for the **NexTournament Universal Android App** (`com.nextournament.app`), built inside the `android/` directory of the project monorepo.

### Confirmed Architectural Decisions:
- **Min SDK**: `24` (Android 7.0 Nougat) for maximum budget smartphone accessibility.
- **Target / Compile SDK**: `35` (Android 15) with modern Android runtime standards.
- **Dependency Injection**: **Google Dagger Hilt** (`@HiltAndroidApp`, `@AndroidEntryPoint`, `@HiltViewModel`).
- **Networking & Serialization**: **Retrofit 2.11** + **OkHttp 4.12** + **Kotlinx Serialization** + native WebSocket engine.
- **UI Framework**: **Jetpack Compose (BOM 2024.09+)** with **Material 3**.
- **Design Language**: **Gen Z Esports Dark HUD** — Deep Obsidian (`#020617`), Electric Amber (`#F59E0B`), Toxic Green (`#10B981`), Laser Crimson (`#EF4444`), Neon Cyan (`#06B6D4`), and **Sharp / Cut-Corner Geometry** (`CutCornerShape(4.dp)`).
- **OTA Update Plumbing**: Android `FileProvider` (`${applicationId}.fileprovider`) and `file_paths.xml` pre-configured for direct APK downloading and 1-tap installation without Google Play Store.

---

## 📁 Phase 1 Directory Structure

```
NexTournament/
├── android/
│   ├── gradle/
│   │   ├── wrapper/
│   │   │   ├── gradle-wrapper.jar
│   │   │   └── gradle-wrapper.properties
│   │   └── libs.versions.toml             # Centralized Version Catalog
│   ├── build.gradle.kts                   # Root build script
│   ├── settings.gradle.kts                # Project & repository settings
│   ├── gradle.properties                  # JVM & AndroidX memory options
│   └── app/
│       ├── build.gradle.kts               # App-level build script & plugins
│       ├── proguard-rules.pro             # ProGuard / R8 keep rules
│       └── src/
│           └── main/
│               ├── AndroidManifest.xml    # App manifest with permissions & FileProvider
│               ├── res/
│               │   ├── xml/
│               │   │   └── file_paths.xml # FileProvider paths for updates/
│               │   └── values/
│               │       ├── colors.xml
│               │       └── strings.xml
│               └── java/com/nextournament/app/
│                   ├── NexTournamentApplication.kt  # @HiltAndroidApp
│                   ├── MainActivity.kt              # @AndroidEntryPoint Compose Root
│                   ├── ui/
│                   │   ├── theme/
│                   │   │   ├── Color.kt             # Obsidian, Amber, Emerald, Crimson
│                   │   │   ├── Shape.kt             # CutCornerSmall, CutCornerCard, Sharp
│                   │   │   ├── Type.kt              # Clash Display & Inter typography
│                   │   │   └── Theme.kt             # EsportsColorScheme MaterialTheme
│                   │   └── components/
│                   │       ├── CyberActionButton.kt # Neo-brutalist angular button
│                   │       ├── CyberBadge.kt        # Chamfered HUD status badge
│                   │       └── TournamentHudCard.kt # Match preview card with HUD borders
│                   └── di/
│                       └── AppModule.kt             # Hilt singleton network & storage providers
```

---

## 🎯 Deliverables & Verification Checklist

- [x] Technical choices confirmed by user (Retrofit + Hilt + Min SDK 24).
- [ ] Create `android/` directory and configure `settings.gradle.kts` and `build.gradle.kts`.
- [ ] Configure `gradle/libs.versions.toml` with Compose, Hilt, Retrofit, Coil, and Lottie.
- [ ] Setup `app/build.gradle.kts` with plugins and dependencies.
- [ ] Configure `AndroidManifest.xml` with permissions (`INTERNET`, `REQUEST_INSTALL_PACKAGES`, `POST_NOTIFICATIONS`) and `FileProvider`.
- [ ] Setup `res/xml/file_paths.xml` for OTA update downloads.
- [ ] Implement `Color.kt`, `Shape.kt`, `Type.kt`, and `Theme.kt` with Gen Z Sharp-Corner tokens.
- [ ] Implement `CyberActionButton.kt`, `CyberBadge.kt`, and `TournamentHudCard.kt`.
- [ ] Implement `NexTournamentApplication.kt` and `MainActivity.kt`.
- [ ] Verify Gradle build configuration syntax.
- [ ] Copy completed artifact to `phase/PHASE_1_SCAFFOLDING_AND_FOUNDATION.md`.
