@echo off
setlocal
echo ======================================================================
echo           PLAGIARISM AI - GOOGLE COLAB GPU SCANNER
echo ======================================================================
echo.

if "%~1"=="" (
    echo Drag-and-drop a PDF or Image file onto this .bat, or enter path below:
    set /p "TARGET_FILE=Enter path to file: "
) else (
    set "TARGET_FILE=%~1"
)

if "%TARGET_FILE%"=="" (
    echo No file provided. Exiting.
    pause
    exit /b 1
)

python "%~dp0colab_scanner.py" "%TARGET_FILE%"
echo.
pause
