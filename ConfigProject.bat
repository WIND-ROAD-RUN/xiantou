@echo off
setlocal enabledelayedexpansion

REM Check if Git is installed
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git is not installed. Please install Git first.
    exit /b 1
)

set "REPO_URL=https://github.com/WIND-ROAD-RUN/MaixCAM.git"
set "CLONE_DIR=%TEMP%\MaixCAM_clone_%RANDOM%"

echo Cloning repository to "%CLONE_DIR%"...
git clone "%REPO_URL%" "%CLONE_DIR%"
if %ERRORLEVEL% NEQ 0 (
    echo Repository clone failed. Please check your network connection or repository URL.
    exit /b 1
)

REM Copy CameraModule if exists
if exist "%CLONE_DIR%\CameraModule" (
    echo Copying CameraModule to "%CD%\CameraModule"...
    robocopy "%CLONE_DIR%\CameraModule" "%CD%\CameraModule" /E /COPYALL /R:2 /W:2
) else (
    echo CameraModule not found in repo.
)

REM Copy ImgProModule if exists
if exist "%CLONE_DIR%\ImgProModule" (
    echo Copying ImgProModule to "%CD%\ImgProModule"...
    robocopy "%CLONE_DIR%\ImgProModule" "%CD%\ImgProModule" /E /COPYALL /R:2 /W:2
) else (
    echo ImgProModule not found in repo.
)

REM Copy all folders inside Mt to current directory
if exist "%CLONE_DIR%\Mt" (
    for /d %%F in ("%CLONE_DIR%\Mt\*") do (
        echo Copying %%~nxF to "%CD%\%%~nxF"...
        robocopy "%%F" "%CD%\%%~nxF" /E /COPYALL /R:2 /W:2
    )

    REM Also copy the whole Mt folder to current directory as .\Mt
    echo Copying Mt folder to "%CD%\Mt"...
    robocopy "%CLONE_DIR%\Mt" "%CD%\Mt" /E /COPYALL /R:2 /W:2
) else (
    echo Mt directory not found in repo.
)

REM Cleanup temporary clone
echo Removing temporary clone directory "%CLONE_DIR%"...
rmdir /s /q "%CLONE_DIR%"

endlocal

echo Done.
echo Press any key to exit...
pause >nul