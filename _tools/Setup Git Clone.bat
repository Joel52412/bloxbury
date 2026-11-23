@echo off
rem ONE-TIME: turns this robloxshorts folder into a git clone of GitHub, keeping every laptop-only file
rem (exports, voice clones, inspo, approval sheets stay: .gitignore leaves them alone).
rem Needs Git for Windows: winget install --id Git.Git -e   (then open a new window)
cd /d "%~dp0.."
if exist .git (echo Already a git clone. Use "Pull Latest.bat". & pause & exit /b)
git init -b main || (echo Git is not installed: run  winget install --id Git.Git -e  & pause & exit /b 1)
git remote add origin https://github.com/Joel52412/bloxbury.git
git fetch origin main || (echo Could not reach GitHub. & pause & exit /b 1)
git reset origin/main
echo.
echo Files that differ from GitHub (laptop copies that were edited or left over):
git status --short
echo.
echo To make tracked files match GitHub exactly, run:  git checkout -- .
pause
