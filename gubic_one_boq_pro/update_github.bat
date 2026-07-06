@echo off
echo ============================================
echo Updating Gubic ONE BoQ Pro to GitHub
echo ============================================

git status
git add .
git commit -m "Update Gubic ONE BoQ Pro app"
git push

echo.
echo Update complete. Streamlit Cloud will redeploy automatically if this branch is connected.
pause
