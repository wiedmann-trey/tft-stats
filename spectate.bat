@echo off
setlocal enabledelayedexpansion
title MetaTFT Spectator

set LOL_PATH=%1

for /f "tokens=* delims= " %%a in ("%LOL_PATH%") do set LOL_PATH=%%a
for /l %%a in (1,1,100) do if "!LOL_PATH:~-1!"==" " set LOL_PATH=!LOL_PATH:~0,-1!
cd /D %LOL_PATH%

for /f "tokens=1,* delims=" %%i in ('type Config\LeagueClientSettings.yaml ^| find /i "locale:"') do (
    set line=%%i
    call :Trim trimmed !line!
    SET locale=!trimmed:~9,-1!
)

cd Game

REM Check if vanguard is running
sc query vgk | find "RUNNING" >nul
if %ERRORLEVEL% equ 0 (
    set IS_VGK_RUNNING=1
) else (
    set IS_VGK_RUNNING=0
)

echo Launching League of Legends...

if %IS_VGK_RUNNING% equ 1 (
    net stop vgc >nul 2>&1
    net stop vgk >nul 2>&1
)

@start "" "League of Legends.exe" "spectator spectator.na1.lol.pvp.net:8080 %2 %3 NA1" -UseRads -GameBaseDir=.. "-Locale=%locale%" -SkipBuild -EnableCrashpad=true -EnableLNP -Product=TFT

if %IS_VGK_RUNNING% equ 1 (
    timeout 5 >nul 2>&1
    net start vgk >nul 2>&1
    net start vgc >nul 2>&1
)

goto exit

:Trim
SetLocal EnableDelayedExpansion
set Params=%*
for /f "tokens=1*" %%a in ("!Params!") do EndLocal & set %1=%%b
exit /b

:exit
