package com.nextournament.app.data.payment

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.net.Uri
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

data class UpiAppInfo(
    val packageName: String,
    val appName: String,
    val icon: Drawable?
)

@Singleton
class UpiIntentManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    fun getInstalledUpiApps(): List<UpiAppInfo> {
        val uri = Uri.parse("upi://pay")
        val upiIntent = Intent(Intent.ACTION_VIEW, uri)
        val packageManager = context.packageManager
        val resolveInfoList = packageManager.queryIntentActivities(upiIntent, PackageManager.MATCH_DEFAULT_ONLY)

        return resolveInfoList.map { resolveInfo ->
            val packageName = resolveInfo.activityInfo.packageName
            val appName = resolveInfo.loadLabel(packageManager).toString()
            val icon = resolveInfo.loadIcon(packageManager)
            UpiAppInfo(
                packageName = packageName,
                appName = appName,
                icon = icon
            )
        }
    }

    fun buildUpiUri(
        merchantVpa: String,
        merchantName: String,
        amount: Double,
        transactionRef: String,
        note: String = "NexTournament Deposit"
    ): Uri {
        return Uri.Builder()
            .scheme("upi")
            .authority("pay")
            .appendQueryParameter("pa", merchantVpa)
            .appendQueryParameter("pn", merchantName)
            .appendQueryParameter("mc", "0000") // Generic merchant category
            .appendQueryParameter("tr", transactionRef)
            .appendQueryParameter("tn", note)
            .appendQueryParameter("am", "%.2f".format(amount))
            .appendQueryParameter("cu", "INR")
            .build()
    }

    fun launchUpiPayment(
        packageName: String,
        upiUri: Uri
    ): Result<Unit> {
        return try {
            val intent = Intent(Intent.ACTION_VIEW, upiUri).apply {
                setPackage(packageName)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
