@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ======================================
echo       TESTES AUTOMATIZADOS
echo             COMISSIONA
echo ======================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Verificando dependencias...
"%PYTHON%" -m pip install Flask Flask-SQLAlchemy python-dotenv

if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar/verificar as dependencias.
    pause
    exit /b 1
)

echo.
echo Iniciando testes...
"%PYTHON%" testar_comissiona.py

echo.
pause
