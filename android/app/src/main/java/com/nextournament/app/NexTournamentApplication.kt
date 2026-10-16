package com.nextournament.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class NexTournamentApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Application startup logic (OTA check scheduler, Notification channels)
    }
}
