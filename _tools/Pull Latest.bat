@echo off
rem Brings this folder up to date with GitHub (replaces copying files by hand). Laptop-only files are never touched.
cd /d "%~dp0.."
git pull --ff-only origin main
if errorlevel 1 (echo. & echo Pull stopped: a laptop file was edited. Send Claude the list above. & git status --short)
pause
