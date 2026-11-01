@echo off
rem Downloads Cambodia fossil figures/photos into D:\GDMG_Library\Cambodia_Fossil_Images
rem (or %USERPROFILE%\Documents\GDMG_Library\Cambodia_Fossil_Images if D: is missing).
cd /d "%~dp0"
python -m pip install --quiet --upgrade requests pymupdf
python "%~dp0fetch_cambodia_fossil_images.py" %*
pause
