@echo off
REM LAB-12 dashboard: launch the ONE-FILE HTML console in Google Chrome.
REM Does not install a Python bridge, server, or any USB driver.
set "HTML=%~dp0lab12_dashboard.html"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%HTML%"
  goto :eof
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%HTML%"
  goto :eof
)
start "" chrome "%HTML%"
