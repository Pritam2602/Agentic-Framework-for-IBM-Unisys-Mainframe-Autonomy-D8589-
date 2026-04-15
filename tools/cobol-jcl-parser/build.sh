#!/usr/bin/env bash
#
# Build script for the ProLeap COBOL Parser project.
# Installs the proleap library to the local Maven repo, then builds
# the outer project into a fat JAR.
#
# Prerequisites: Java 17+, Maven 3.6+
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Step 1/2: Installing proleap-cobol-parser library ==="
mvn install -f proleap-cobol-parser-main/pom.xml -DskipTests -q
echo "    Done."

echo ""
echo "=== Step 2/2: Building cobol-parser JAR ==="
mvn clean package -q
echo "    Done."

echo ""
JAR="target/cobol-parser-setup-1.0-SNAPSHOT.jar"
if [ -f "$JAR" ]; then
    echo "Build successful!"
    echo "JAR: $JAR"
    echo ""
    echo "Usage:"
    echo "  java -jar $JAR <file-or-dir> [copybook-dirs] [output-dir]"
    echo ""
    echo "  Python wrapper:"
    echo "  python proleap_wrapper.py <file-or-dir> [copybook-dir ...]"
else
    echo "ERROR: Build failed — JAR not found."
    exit 1
fi
