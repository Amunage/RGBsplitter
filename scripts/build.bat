@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%" || (
    echo [ERROR] Failed to move to project root: %PROJECT_ROOT%
    pause
    exit /b 1
)

set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "SPEC_FILE=%PROJECT_ROOT%\rgbsplitter.spec"

if not exist "%PYTHON%" (
    echo [ERROR] Python not found: %PYTHON%
    echo Run scripts\new_venv.bat first, then install project dependencies.
    pause
    exit /b 1
)

if not exist "%SPEC_FILE%" (
    echo [ERROR] Spec file not found: %SPEC_FILE%
    pause
    exit /b 1
)

set "VERSION_OUTPUT=%TEMP%\rgbsplitter_build_version.txt"
"%PYTHON%" -c "import ast, pathlib; print(ast.literal_eval(pathlib.Path('src/rgbsplitter/version.py').read_text(encoding='utf-8').split('=', 1)[1].strip()))" > "%VERSION_OUTPUT%"
if errorlevel 1 (
    echo [ERROR] Failed to read app version.
    pause
    exit /b 1
)
set /p APP_VERSION=<"%VERSION_OUTPUT%"
del /q "%VERSION_OUTPUT%" >nul 2>&1
if "%APP_VERSION%"=="" (
    echo [ERROR] Failed to read app version.
    pause
    exit /b 1
)

set "OUTPUT_FILE=%PROJECT_ROOT%\dist\RGBsplitter-v%APP_VERSION%.exe"
set "LEGACY_OUTPUT_FILE=%PROJECT_ROOT%\dist\RGB Splitter.exe"

echo [INFO] Ensuring build dependencies...
"%PYTHON%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo [INFO] Ensuring project dependencies...
"%PYTHON%" -m pip install -e .
if errorlevel 1 (
    echo [ERROR] Failed to install project dependencies.
    pause
    exit /b 1
)

echo [INFO] Building single executable...
if exist "%LEGACY_OUTPUT_FILE%" del /q "%LEGACY_OUTPUT_FILE%"
if exist "%OUTPUT_FILE%" del /q "%OUTPUT_FILE%"
"%PYTHON%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%"
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

if not exist "%OUTPUT_FILE%" (
    echo [ERROR] Build finished, but output file was not found:
    echo %OUTPUT_FILE%
    pause
    exit /b 1
)

echo [DONE] %OUTPUT_FILE%
pause
