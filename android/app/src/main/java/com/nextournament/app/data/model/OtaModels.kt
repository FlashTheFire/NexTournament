package com.nextournament.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class VersionCheckResponse(
    @SerialName("platform") val platform: String = "android",
    @SerialName("latest_version") val latestVersion: String,
    @SerialName("version_code") val versionCode: Int,
    @SerialName("min_supported_version_code") val minSupportedVersionCode: Int,
    @SerialName("is_force_update") val isForceUpdate: Boolean = false,
    @SerialName("download_url") val downloadUrl: String,
    @SerialName("apk_sha256") val apkSha256: String,
    @SerialName("file_size_bytes") val fileSizeBytes: Long,
    @SerialName("release_notes") val releaseNotes: String,
    @SerialName("published_at") val publishedAt: String? = null
) {
    val isForced: Boolean get() = isForceUpdate
    val latestVersionName: String get() = latestVersion
    val latestVersionCode: Int get() = versionCode
    val downloadSize: String get() = "%.1f MB".format(fileSizeBytes / (1024.0 * 1024.0))
    val changelog: String get() = releaseNotes
    val apkUrl: String get() = downloadUrl

    fun toUpdateCheckResponse(): UpdateCheckResponse = UpdateCheckResponse(
        latestVersionName = latestVersion,
        latestVersionCode = versionCode,
        minSupportedVersionCode = minSupportedVersionCode,
        isForced = isForceUpdate,
        apkUrl = downloadUrl,
        apkSha256 = apkSha256,
        apkSizeBytes = fileSizeBytes,
        changelog = releaseNotes,
        downloadSize = downloadSize
    )
}

@Serializable
data class UpdateCheckResponse(
    @SerialName("latest_version") val latestVersionName: String,
    @SerialName("version_code") val latestVersionCode: Int,
    @SerialName("min_supported_version_code") val minSupportedVersionCode: Int = 1,
    @SerialName("is_forced") val isForced: Boolean = false,
    @SerialName("apk_url") val apkUrl: String,
    @SerialName("apk_sha256") val apkSha256: String,
    @SerialName("apk_size_bytes") val apkSizeBytes: Long = 0L,
    @SerialName("changelog") val changelog: String = "",
    @SerialName("download_size") val downloadSize: String = "15.4 MB"
)
