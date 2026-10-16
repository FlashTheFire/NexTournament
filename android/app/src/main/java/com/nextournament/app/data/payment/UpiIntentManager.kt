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
    val appName: String,
    val packageName: String,
    val icon: Drawable? = null,
    val isInstalled: Boolean = true
) {
    constructor(packageName: String, appName: String, icon: Drawable?) : this(
        appName = appName,
        packageName = packageName,
        icon = icon,
        isInstalled = true
    )
}

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
        note: String = "NexTournament Entry"
    ): Uri {
        return Uri.Builder()
            .scheme("upi")
            .authority("pay")
            .appendQueryParameter("pa", merchantVpa)
            .appendQueryParameter("pn", merchantName)
            .appendQueryParameter("mc", "0000") // General esports category
            .appendQueryParameter("tr", transactionRef)
            .appendQueryParameter("tn", note)
            .appendQueryParameter("am", String.format("%.2f", amount))
            .appendQueryParameter("cu", "INR")
            .build()
    }

    fun launchUpiPaymentIntent(context: Context, upiApp: UpiAppInfo, paymentUri: Uri): Boolean {
        return try {
            val paymentIntent = Intent(Intent.ACTION_VIEW, paymentUri).apply {
                setPackage(upiApp.packageName)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(paymentIntent)
            true
        } catch (e: Exception) {
            false
        }
    }
}
