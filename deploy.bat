@echo off
echo === Bunjang Partner Guide - Deploy ===

echo.
echo [1/3] Building share HTML...
python build.py
if errorlevel 1 (
    echo Build failed. Check image files.
    pause
    exit /b 1
)

git config --global user.email "seanko@users.noreply.github.com"
git config --global user.name "seanko"

if not exist ".git" (
    echo.
    echo [Setup] Initializing git...
    git init
    git remote add origin https://github.com/seanko-cell/bunjang-partner-guide.git
    git branch -M main
)

echo.
echo [2/3] Uploading to GitHub...
git add .
git commit -m "Update %date% %time%"
git push -u origin main

echo.
echo ================================
echo [3/3] Deploy complete!
echo.
echo Hub URL:
echo   https://seanko-cell.github.io/bunjang-partner-guide/
echo.
echo Partner share URL:
echo   https://seanko-cell.github.io/bunjang-partner-guide/bunjang-partner-guide-share.html
echo ================================
pause
