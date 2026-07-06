@echo off
echo ============================================
echo Force updating Gubic ONE BoQ Pro to GitHub
echo WARNING: this overwrites GitHub main branch with local files.
echo ============================================

git status
git add .
git commit -m "Update Gubic ONE BoQ Pro" || echo Nothing new to commit or commit failed.
git fetch origin
git push --force-with-lease origin main

echo.
echo Done. Streamlit Cloud will redeploy automatically.
pause
