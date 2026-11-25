@echo off
title Aadhya WhatsApp Bulker - Terminal APK Builder
echo ============================================================
echo   Aadhya WhatsApp Bulker - Terminal APK Build Process
echo ============================================================
echo.
echo Setting up Android Studio Java Runtime and SDK...

set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.21.102-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
set "ANDROID_HOME=C:\Users\naiti\AppData\Local\Android\Sdk"
set "ANDROID_SDK_ROOT=%ANDROID_HOME%"

echo JAVA_HOME: %JAVA_HOME%
echo ANDROID_HOME: %ANDROID_HOME%
echo.

cd /d "%~dp0android"

echo Starting Android Studio Gradle Build...
echo (You will see all terminal compile logs below)
echo ============================================================
echo.

if exist "gradlew.bat" (
    call gradlew.bat assembleDebug --stacktrace
) else (
    echo Opening Android Studio to trigger native build...
    start "" "C:\Program Files\Android\Android Studio\bin\studio64.exe" "%~dp0android"
)

echo.
echo ============================================================
echo Build process finished!
echo ============================================================
pause
