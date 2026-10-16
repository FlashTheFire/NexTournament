# ProGuard rules for NexTournament App
-keepattributes *Annotation*, Signature, InnerClasses, EnclosingMethod

# Kotlinx Serialization
-keepclassmembers class * {
    *** Companion;
}
-keepclasseswithmembers class * {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit & OkHttp
-dontwarn okhttp3.**
-dontwarn retrofit2.**
-dontwarn javax.annotation.**

# Dagger Hilt
-keep class * extends com.google.dagger.hilt.android.internal.managers.ViewComponentManager$FragmentContextWrapper { *; }
