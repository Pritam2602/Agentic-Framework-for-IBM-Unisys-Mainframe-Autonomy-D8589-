@echo off
setlocal EnableDelayedExpansion
REM
REM One-click runner for the JCL Parser (Windows).
REM No Java/Maven/conda needed — just Python 3.
REM
REM Usage:
REM   run_jcl.bat <file-or-dir> [--output-dir DIR]
REM

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "INPUT_PATH="
set "OUTPUT_DIR=output-jcl"

:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--output-dir" (
    set "OUTPUT_DIR=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="-o" (
    set "OUTPUT_DIR=%~2"
    shift
    shift
    goto parse_args
)
if not defined INPUT_PATH (
    set "INPUT_PATH=%~1"
)
shift
goto parse_args

:done_args
if not defined INPUT_PATH (
    echo JCL Parser - One-Click Runner
    echo.
    echo Usage:
    echo   run_jcl.bat ^<file-or-dir^> [--output-dir DIR]
    echo.
    echo Examples:
    echo   run_jcl.bat test-jcl\POSTTRAN.jcl
    echo   run_jcl.bat test-jcl\
    echo   run_jcl.bat myjobs\ --output-dir results\
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python 3 not found. Install Python 3.8+ to use this tool.
    exit /b 1
)

python "%SCRIPT_DIR%jcl_parser.py" "%INPUT_PATH%" "%OUTPUT_DIR%"

echo.
echo JSON output is in: %OUTPUT_DIR%\
