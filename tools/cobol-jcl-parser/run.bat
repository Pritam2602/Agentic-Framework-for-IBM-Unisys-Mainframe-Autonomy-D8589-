@echo off
setlocal EnableDelayedExpansion
REM
REM One-click setup + build + run for the ProLeap COBOL Parser (Windows).
REM
REM Usage:
REM   run.bat <file-or-dir> [copybook-dir1 copybook-dir2 ...] [--output-dir DIR]
REM
REM Examples:
REM   run.bat test-cobol\minimal-test.cbl
REM   run.bat myproject\cbl myproject\cpy
REM   run.bat myproject\cbl myproject\cpy --output-dir results
REM

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "ENV_NAME=cobol-parser"
set "JAR=target\cobol-parser-setup-1.0-SNAPSHOT.jar"

REM ─── Parse arguments ─────────────────────────────────────────────
set "INPUT_PATH="
set "COPYBOOK_DIRS="
set "OUTPUT_DIR=output"

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
) else (
    if defined COPYBOOK_DIRS (
        set "COPYBOOK_DIRS=!COPYBOOK_DIRS!;%~1"
    ) else (
        set "COPYBOOK_DIRS=%~1"
    )
)
shift
goto parse_args

:done_args
if not defined INPUT_PATH (
    echo ProLeap COBOL Parser - One-Click Runner
    echo.
    echo Usage:
    echo   run.bat ^<file-or-dir^> [copybook-dir ...] [--output-dir DIR]
    echo.
    echo Examples:
    echo   run.bat test-cobol\minimal-test.cbl
    echo   run.bat myproject\cbl\ myproject\cpy\
    echo   run.bat cics-programs\ copybooks\ stubs\ --output-dir results\
    echo.
    echo First run will install Java 17 + Maven and build the project.
    exit /b 0
)

REM ─── Check if setup needed ──────────────────────────────────────
set "NEEDS_SETUP=0"

call conda env list 2>nul | findstr /b /c:"%ENV_NAME% " >nul 2>nul
if %ERRORLEVEL% neq 0 set "NEEDS_SETUP=1"

if not exist "%JAR%" set "NEEDS_SETUP=1"

if "%NEEDS_SETUP%"=="1" (
    call :setup_environment
    if %ERRORLEVEL% neq 0 exit /b 1
    echo.
    call :build_jar
    if %ERRORLEVEL% neq 0 exit /b 1
    echo.
)

if not exist "%JAR%" (
    echo ERROR: JAR not found at %JAR%. Build may have failed.
    exit /b 1
)

call :run_parser
echo.
echo JSON output is in: %OUTPUT_DIR%\
exit /b 0

REM ─── Functions ──────────────────────────────────────────────────

:setup_environment
echo === Setting up environment ===
where conda >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: conda not found.
    echo Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
    exit /b 1
)
call conda env list 2>nul | findstr /b /c:"%ENV_NAME% " >nul 2>nul
if %ERRORLEVEL%==0 (
    echo   Environment '%ENV_NAME%' already exists.
) else (
    echo   Creating conda environment '%ENV_NAME%' with Java 17 + Maven...
    call conda create -n %ENV_NAME% openjdk=17 maven -c conda-forge -y -q
    echo   Environment created.
)
exit /b 0

:build_jar
echo === Building parser JAR ===
echo   Installing proleap library...
call conda run -n %ENV_NAME% mvn install -f proleap-cobol-parser-main\pom.xml -DskipTests -q
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install proleap library.
    exit /b 1
)
echo   Building fat JAR...
call conda run -n %ENV_NAME% mvn clean package -q
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to build JAR.
    exit /b 1
)
echo   Build complete.
exit /b 0

:run_parser
REM Always include stubs directory
set "CPY_ARG="
if defined COPYBOOK_DIRS (
    set "CPY_ARG=!COPYBOOK_DIRS!"
)
if exist "%SCRIPT_DIR%stubs" (
    if defined CPY_ARG (
        set "CPY_ARG=!CPY_ARG!;%SCRIPT_DIR%stubs"
    ) else (
        set "CPY_ARG=%SCRIPT_DIR%stubs"
    )
)

echo.
if defined CPY_ARG (
    call conda run -n %ENV_NAME% java -jar "%JAR%" "%INPUT_PATH%" "!CPY_ARG!" "%OUTPUT_DIR%"
) else (
    call conda run -n %ENV_NAME% java -jar "%JAR%" "%INPUT_PATH%" "" "%OUTPUT_DIR%"
)
exit /b 0
