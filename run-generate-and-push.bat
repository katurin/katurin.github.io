@echo off
REM run-serve.bat -- Activate conda env py39 and run build/serve.py
REM Place this file in repository root (same folder that contains posts/ build/ index.html etc.)

REM Change working directory to the directory of this batch file
cd /d %~dp0

REM Set your Anaconda installation base (adjusted to your environment)
set "CONDA_BASE=C:\Users\taki\anaconda3"

REM Verify conda.bat exists
if not exist "%CONDA_BASE%\condabin\conda.bat" (
  echo ERROR: Could not find conda.bat at "%CONDA_BASE%\condabin\conda.bat"
  echo Please check CONDA_BASE in this batch file.
  pause
  exit /b 1
)

REM Activate the conda environment 'py39'
call "%CONDA_BASE%\condabin\conda.bat" activate py39
if ERRORLEVEL 1 (
  echo ERROR: Failed to activate conda environment 'py39'
  pause
  exit /b 1
)

REM Optional: show which python is active
where python

REM Run the livereload serve script
python build/serve.py
if ERRORLEVEL 1 (
  echo ERROR: serve script exited with error
  pause
  exit /b 1
)

pause