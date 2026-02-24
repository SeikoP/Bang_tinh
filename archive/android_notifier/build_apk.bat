@echo off
echo ========================================
echo Building Bank Notifier APK
echo ========================================
echo.

REM Check if gradlew exists
if not exist gradlew.bat (
    echo ERROR: gradlew.bat not found!
    echo Please run this script from android_notifier folder
    pause
    exit /b 1
)

REM Clean previous build
echo [1/3] Cleaning previous build...
call gradlew.bat clean
if %ERRORLEVEL% neq 0 (
    echo ERROR: Clean failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Building APK...
call gradlew.bat assembleDebug
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Copying APK to output folder...
if not exist "output" mkdir output
copy /Y "app\build\outputs\apk\debug\app-debug.apk" "output\BankNotifier.apk"

echo.
echo ========================================
echo BUILD SUCCESS!
echo ========================================
echo APK location: output\BankNotifier.apk
echo File size:
dir output\BankNotifier.apk | find "BankNotifier.apk"
echo.
echo Next steps:
echo 1. Copy BankNotifier.apk to your Android phone
echo 2. Install the APK (enable "Install from unknown sources")
echo 3. Open the app and grant Notification Access permission
echo 4. Configure server URL: http://192.168.2.17:5005/notify
echo 5. Test connection and save
echo ========================================
pause
