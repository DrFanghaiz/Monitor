@echo off
setlocal

cd /d "%~dp0"
set "CONDA_NO_PLUGINS=true"

set "CONDA_BAT=D:\progarm\Miniconda\condabin\conda.bat"
if not exist "%CONDA_BAT%" (
    set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
)
if not exist "%CONDA_BAT%" (
    set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
)

echo [1/4] Checking conda...
if exist "%CONDA_BAT%" (
    echo Using: %CONDA_BAT%
) else (
    where conda >nul 2>nul
    if errorlevel 1 (
        echo Conda was not found.
        echo Please update CONDA_BAT in this file or install Miniconda/Anaconda first.
        pause
        exit /b 1
    )
    set "CONDA_BAT=conda"
    echo Using conda from PATH.
)

echo [2/4] Creating conda environment from environment.yml...
call "%CONDA_BAT%" env create --solver classic -f environment.yml
if errorlevel 1 (
    echo Failed to create environment.
    pause
    exit /b 1
)

echo [3/4] Activating environment...
call "%CONDA_BAT%" activate monitor-app
if errorlevel 1 (
    echo Failed to activate environment.
    echo You can try manually:
    echo   call "%CONDA_BAT%" activate monitor-app
    pause
    exit /b 1
)

echo [4/4] Environment is ready.
echo Run the app with:
echo   python main.py
pause
