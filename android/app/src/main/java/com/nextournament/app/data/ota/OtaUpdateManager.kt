package com.nextournament.app.data.ota

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import com.nextournament.app.data.model.UpdateCheckResponse
import com.nextournament.app.data.network.AppVersionApiService
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

sealed interface DownloadState {
    object Idle : DownloadState
    data class Progress(val bytesDownloaded: Long, val totalBytes: Long, val progressPercentage: Int) : DownloadState
    data class VerifyingChecksum(val message: String) : DownloadState
    data class Success(val apkFile: File) : DownloadState
    data class Error(val message: String) : DownloadState
}

@Singleton
class OtaUpdateManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val appVersionApiService: AppVersionApiService,
    private val okHttpClient: OkHttpClient
) {

    suspend fun checkForUpdates(currentVersionCode: Int): Result<UpdateCheckResponse> {
        return try {
            val response = appVersionApiService.checkVersion(versionCode = currentVersionCode)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toUpdateCheckResponse())
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun downloadApkWithProgress(
        apkUrl: String,
        expectedSha256: String,
        targetFileName: String = "NexTournament_update.apk"
    ): Flow<DownloadState> = flow {
        emit(DownloadState.Idle)

        val updateDir = File(context.cacheDir, "updates")
        if (!updateDir.exists()) {
            updateDir.mkdirs()
        }

        val apkFile = File(updateDir, targetFileName)
        if (apkFile.exists()) {
            apkFile.delete()
        }

        try {
            val request = Request.Builder().url(apkUrl).build()
            val response = okHttpClient.newCall(request).execute()

            if (!response.isSuccessful) {
                emit(DownloadState.Error("Server returned HTTP ${response.code}"))
                return@flow
            }

            val body = response.body
            if (body == null) {
                emit(DownloadState.Error("Empty response body from update server"))
                return@flow
            }

            val totalBytes = body.contentLength()
            var bytesDownloaded = 0L

            val inputStream: InputStream = body.byteStream()
            val outputStream = FileOutputStream(apkFile)

            val buffer = ByteArray(8192)
            var read: Int

            while (inputStream.read(buffer).also { read = it } != -1) {
                outputStream.write(buffer, 0, read)
                bytesDownloaded += read

                val progress = if (totalBytes > 0) {
                    ((bytesDownloaded * 100) / totalBytes).toInt()
                } else {
                    0
                }

                emit(DownloadState.Progress(bytesDownloaded, totalBytes, progress))
            }

            outputStream.flush()
            outputStream.close()
            inputStream.close()

            emit(DownloadState.VerifyingChecksum("Verifying SHA-256 package signature..."))

            val computedSha256 = calculateSha256(apkFile)
            if (!computedSha256.equals(expectedSha256, ignoreCase = true)) {
                apkFile.delete()
                emit(DownloadState.Error("Security verification failed: SHA-256 checksum mismatch"))
                return@flow
            }

            emit(DownloadState.Success(apkFile))

        } catch (e: Exception) {
            emit(DownloadState.Error(e.message ?: "Download failed unexpectedly"))
        }
    }.flowOn(Dispatchers.IO)

    fun promptInstallApk(apkFile: File): Result<Unit> {
        return try {
            // Check Unknown Sources Permission for Android 8.0+ (Oreo)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                if (!context.packageManager.canRequestPackageInstalls()) {
                    val settingsIntent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                        data = Uri.parse("package:${context.packageName}")
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK
                    }
                    context.startActivity(settingsIntent)
                    return Result.failure(SecurityException("Permission needed to install unknown apps"))
                }
            }

            val authority = "${context.packageName}.fileprovider"
            val apkUri = FileProvider.getUriForFile(context, authority, apkFile)

            val installIntent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(apkUri, "application/vnd.android.package-archive")
                flags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK
            }

            context.startActivity(installIntent)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun calculateSha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { inputStream ->
            val buffer = ByteArray(8192)
            var bytesRead: Int
            while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                digest.update(buffer, 0, bytesRead)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}
