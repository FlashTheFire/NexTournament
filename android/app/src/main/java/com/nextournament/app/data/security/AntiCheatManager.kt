package com.nextournament.app.data.security

import android.app.Activity
import android.content.Context
import android.os.Build
import android.view.WindowManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.BufferedReader
import java.io.File
import java.io.FileReader
import java.net.InetSocketAddress
import java.net.Socket
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

enum class DeviceIntegrityTier {
    CLEAN,
    EMULATOR,
    ROOTED,
    HOOK_DETECTED
}

data class DeviceSecurityReport(
    val tier: DeviceIntegrityTier,
    val isRooted: Boolean,
    val isEmulator: Boolean,
    val isHookDetected: Boolean,
    val details: String,
    val integrityToken: String
)

@Singleton
class AntiCheatManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val sessionManager: SessionManager
) {

    fun evaluateDeviceIntegrity(): DeviceSecurityReport {
        val rooted = isRootedDevice()
        val emulator = isEmulator()
        val hookDetected = isHookFrameworkDetected()

        val tier = when {
            hookDetected -> DeviceIntegrityTier.HOOK_DETECTED
            rooted -> DeviceIntegrityTier.ROOTED
            emulator -> DeviceIntegrityTier.EMULATOR
            else -> DeviceIntegrityTier.CLEAN
        }

        val details = buildString {
            if (rooted) append("[ROOTED_DEVICE] ")
            if (emulator) append("[EMULATOR_DETECTED] ")
            if (hookDetected) append("[HOOK_FRAMEWORK_DETECTED] ")
            if (tier == DeviceIntegrityTier.CLEAN) append("[HARDWARE_VERIFIED_CLEAN]")
        }

        val integrityToken = generateIntegrityToken(tier)

        return DeviceSecurityReport(
            tier = tier,
            isRooted = rooted,
            isEmulator = emulator,
            isHookDetected = hookDetected,
            details = details.trim(),
            integrityToken = integrityToken
        )
    }

    fun isRootedDevice(): Boolean {
        // 1. Check Build Tags for Test-Keys
        val buildTags = Build.TAGS
        if (buildTags != null && buildTags.contains("test-keys")) {
            return true
        }

        // 2. Check Standard SuperUser / SU Binaries
        val binaryPaths = arrayOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/su/bin/su",
            "/system/bin/.ext/.su"
        )
        for (path in binaryPaths) {
            if (File(path).exists()) return true
        }

        // 3. Check Magisk mount or directory
        val magiskPaths = arrayOf(
            "/sbin/.magisk",
            "/data/adb/magisk",
            "/cache/.disable_magisk"
        )
        for (path in magiskPaths) {
            if (File(path).exists()) return true
        }

        // 4. Test execution of which su
        return try {
            val process = Runtime.getRuntime().exec(arrayOf("/system/xbin/which", "su"))
            val reader = BufferedReader(java.io.InputStreamReader(process.inputStream))
            val line = reader.readLine()
            process.destroy()
            line != null
        } catch (e: Exception) {
            false
        }
    }

    fun isEmulator(): Boolean {
        val fingerprint = Build.FINGERPRINT.orEmpty()
        val model = Build.MODEL.orEmpty()
        val hardware = Build.HARDWARE.orEmpty()
        val manufacturer = Build.MANUFACTURER.orEmpty()
        val brand = Build.BRAND.orEmpty()
        val product = Build.PRODUCT.orEmpty()

        return (fingerprint.startsWith("generic")
                || fingerprint.startsWith("unknown")
                || model.contains("google_sdk", ignoreCase = true)
                || model.contains("Emulator", ignoreCase = true)
                || model.contains("Android SDK built for", ignoreCase = true)
                || hardware.contains("goldfish", ignoreCase = true)
                || hardware.contains("ranchu", ignoreCase = true)
                || hardware.contains("vbox86", ignoreCase = true)
                || manufacturer.contains("Genymotion", ignoreCase = true)
                || manufacturer.contains("Nox", ignoreCase = true)
                || manufacturer.contains("Bluestacks", ignoreCase = true)
                || brand.startsWith("generic")
                || product.contains("sdk_gphone", ignoreCase = true)
                || product.contains("vbox86p", ignoreCase = true))
    }

    fun isHookFrameworkDetected(): Boolean {
        // 1. Inspect /proc/self/maps for injected memory libraries
        try {
            val mapsFile = File("/proc/self/maps")
            if (mapsFile.exists()) {
                val reader = BufferedReader(FileReader(mapsFile))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    val lower = line?.lowercase() ?: ""
                    if (lower.contains("frida")
                        || lower.contains("xposed")
                        || lower.contains("substrate")
                        || lower.contains("cydia")
                    ) {
                        reader.close()
                        return true
                    }
                }
                reader.close()
            }
        } catch (e: Exception) {
            // Access restriction may occur on locked SELinux
        }

        // 2. Check Frida standard listening ports (27042, 27047)
        val fridaPorts = intArrayOf(27042, 27047)
        for (port in fridaPorts) {
            try {
                val socket = Socket()
                socket.connect(InetSocketAddress("127.0.0.1", port), 50)
                socket.close()
                return true // Connection succeeded, Frida server active!
            } catch (e: Exception) {
                // Expected when port is closed
            }
        }

        return false
    }

    fun applyWindowSecurity(activity: Activity, enableSecure: Boolean) {
        activity.runOnUiThread {
            if (enableSecure) {
                activity.window.setFlags(
                    WindowManager.LayoutParams.FLAG_SECURE,
                    WindowManager.LayoutParams.FLAG_SECURE
                )
            } else {
                activity.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
            }
        }
    }

    private fun generateIntegrityToken(tier: DeviceIntegrityTier): String {
        val deviceUuid = sessionManager.getDeviceUuid()
        val raw = "${deviceUuid}_${Build.BOARD}_${Build.DEVICE}_${tier.name}_${System.currentTimeMillis() / 60000}"
        val digest = MessageDigest.getInstance("SHA-256")
        return digest.digest(raw.toByteArray()).joinToString("") { "%02x".format(it) }
    }
}
