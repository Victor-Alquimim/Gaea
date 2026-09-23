@echo off
title GAEA
cd /d "%~dp0"
where pythonw >nul 2>&1 && (start "" pythonw "gaea_app.py" %* & exit /b)
where python  >nul 2>&1 && (start "" python  "gaea_app.py" %* & exit /b)
echo Python nao encontrado no PATH.
echo Instale em https://www.python.org/downloads/ (marque "Add to PATH") e rode de novo.
pause
