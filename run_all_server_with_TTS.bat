@echo off
REM 開始所有伺服器

REM 確保當前在專案目錄
cd /d "D:\物聯網專案\NTTU-IoT-Project-2024"

REM 啟動 accept_mic_from_max9814.bat
start "accept_mic_from_max9814" cmd /k "call accept_mic_from_max9814.bat"

REM 啟動 home_assistant_speaker_server.bat
start "home_assistant_speaker_server" cmd /k "call home_assistant_speaker_server.bat"

REM 啟動 reminder_server.bat
start "reminder_server" cmd /k "call reminder_server.bat"

REM 啟動 home_assistant_main.bat
start "home_assistant_main" cmd /k "call home_assistant_main.bat"

REM 啟動 api.bat
start "api_server" cmd /k "call C:\project\new-GPT-SoVITS-main\GPT-SoVITS-main\api.bat"

REM 結束
echo 所有伺服器已啟動
pause
