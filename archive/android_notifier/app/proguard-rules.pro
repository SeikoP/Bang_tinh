# Add project specific ProGuard rules here.
-keep class com.banknotifier.** { *; }
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
