@echo off
REM Build script for the ProLeap COBOL Parser project (Windows).
REM Prerequisites: Java 17+, Maven 3.6+

echo === Step 1/2: Installing proleap-cobol-parser library ===
call mvn install -f proleap-cobol-parser-main\pom.xml -DskipTests -q
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install proleap library.
    exit /b 1
)
echo     Done.

echo.
echo === Step 2/2: Building cobol-parser JAR ===
call mvn clean package -q
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to build JAR.
    exit /b 1
)
echo     Done.

echo.
set JAR=target\cobol-parser-setup-1.0-SNAPSHOT.jar
if exist %JAR% (
    echo Build successful!
    echo JAR: %JAR%
    echo.
    echo Usage:
    echo   java -jar %JAR% ^<file-or-dir^> [copybook-dirs] [output-dir]
    echo.
    echo   Python wrapper:
    echo   python proleap_wrapper.py ^<file-or-dir^> [copybook-dir ...]
) else (
    echo ERROR: Build failed - JAR not found.
    exit /b 1
)
