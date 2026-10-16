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
)
