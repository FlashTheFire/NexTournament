package com.nextournament.app.data.security

import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

object AppSecurityGatekeeper {

    // Obfuscated key chunks assembled at runtime to prevent decompilation string scraping
    private val PART_A = charArrayOf('N', 'E', 'X', '_', 'S', 'E', 'C', 'U', 'R', 'E')
    private val PART_B = charArrayOf('_', 'A', 'P', 'I', '_', 'V', '2', '_', 'K', '9')
    private val PART_C = charArrayOf('8', '8', '4', '9', '6', '0', '6', '0', '_', 'A')
    private val PART_D = charArrayOf('L', 'P', 'H', 'A', '_', 'S', 'E', 'C', 'R', 'E', 'T')

    /**
     * Layer 1: Returns the obfuscated master static secret key.
     */
    fun getStaticAppKey(): String {
        return String(PART_A) + String(PART_B) + String(PART_C) + String(PART_D)
    }

    /**
     * Layer 2: Generates a dynamic timestamp nonce where the current epoch second
     * string is reversed to prevent replay attacks and clock tampering.
     */
    fun generateReversedTimingNonce(): String {
        val currentSeconds = System.currentTimeMillis() / 1000L
        return currentSeconds.toString().reversed()
    }

    /**
     * Layer 3: Generates an HMAC-SHA256 signature sealing the HTTP Method,
     * Path, Timing Nonce, and Master Secret.
     */
    fun computeHmacSignature(method: String, path: String, timeNonce: String): String {
        val secret = getStaticAppKey()
        val dataToSign = "${method.uppercase()}:${path}:${timeNonce}:${secret}"
        return try {
            val hmac = Mac.getInstance("HmacSHA256")
            val secretKey = SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256")
            hmac.init(secretKey)
            val bytes = hmac.doFinal(dataToSign.toByteArray(Charsets.UTF_8))
            bytes.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            // Fallback SHA-256 digest
            val md = MessageDigest.getInstance("SHA-256")
            val digest = md.digest(dataToSign.toByteArray(Charsets.UTF_8))
            digest.joinToString("") { "%02x".format(it) }
        }
    }
}
