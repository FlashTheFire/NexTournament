# ProGuard / R8 Rules for NexTournament Production Release
-keepattributes *Annotation*, Signature, InnerClasses, EnclosingMethod

# ==============================================================================
# RETROFIT & OKHTTP
# ==============================================================================
-dontwarn retrofit2.**
-dontwarn okhttp3.**
-dontwarn javax.annotation.**
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}
-keep interface com.nextournament.app.data.network.** { *; }

# ==============================================================================
# DAGGER & HILT DEPENDENCY INJECTION
# ==============================================================================
-dontwarn dagger.hilt.**
-dontwarn com.google.errorprone.annotations.**
-dontwarn org.checkerframework.**
-keep class dagger.hilt.** { *; }
-keep class * extends dagger.hilt.internal.GeneratedEntryPoint { *; }
-keep class * extends dagger.hilt.internal.ComponentEntryPoint { *; }
-keep class * implements dagger.hilt.internal.GeneratedEntryPoint { *; }
-keep class * implements dagger.hilt.internal.ComponentEntryPoint { *; }
-keep class com.nextournament.app.Dagger* { *; }
-keep class com.nextournament.app.**_MembersInjector { *; }
-keep class com.nextournament.app.**_Factory { *; }
-keep class com.nextournament.app.**_Provide*Factory { *; }
-keep class com.nextournament.app.di.** { *; }
-keep class * extends com.google.dagger.hilt.android.internal.managers.ViewComponentManager$FragmentContextWrapper { *; }

-keepclasseswithmembers class * {
    @javax.inject.Inject <init>(...);
}
-keepclasseswithmembers class * {
    @javax.inject.Inject <fields>;
}

# ==============================================================================
# APP DATA, MANAGERS, SECURITY & MODELS
# ==============================================================================
-keep class com.nextournament.app.data.security.** { *; }
-keep class com.nextournament.app.data.ota.** { *; }
-keep class com.nextournament.app.data.payment.** { *; }
-keep class com.nextournament.app.data.local.** { *; }
-keep class com.nextournament.app.data.model.** { *; }

# ==============================================================================
# KOTLINX SERIALIZATION
# ==============================================================================
-dontnote kotlinx.serialization.SerializationKt
-keepclassmembers class * {
    *** Companion;
}
-keepclasseswithmembers class * {
    kotlinx.serialization.KSerializer serializer(...);
}
-keepclassmembers class * {
    @kotlinx.serialization.Serializable class *;
}
-keepclassmembers class * {
    @kotlinx.serialization.SerialName <fields>;
}
-keep,allowobfuscation class * implements kotlinx.serialization.KSerializer {
    java.lang.Object deserialize(...);
    void serialize(...);
}

# ==============================================================================
# GOOGLE TINK & ANDROIDX SECURITY CRYPTO
# ==============================================================================
-keep class com.google.crypto.tink.** { *; }
-dontwarn com.google.crypto.tink.**
-keep class androidx.security.crypto.** { *; }
