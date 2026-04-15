#!/usr/bin/env bash
#
# One-click setup + build + run for the ProLeap COBOL Parser.
#
# Usage:
#   bash run.sh <file-or-dir> [copybook-dir1 copybook-dir2 ...] [--output-dir DIR]
#
# Examples:
#   bash run.sh test-cobol/minimal-test.cbl
#   bash run.sh myproject/cbl myproject/cpy
#   bash run.sh myproject/cbl myproject/cpy --output-dir results
#
# On first run: installs Java 17 + Maven via conda, builds the JAR.
# On subsequent runs: skips setup, just runs the parser.
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ENV_NAME="cobol-parser"
JAR="target/cobol-parser-setup-1.0-SNAPSHOT.jar"

# ─── Parse arguments ───────────────────────────────────────────────
INPUT_PATH=""
COPYBOOK_DIRS=()
OUTPUT_DIR="output"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            if [ -z "$INPUT_PATH" ]; then
                INPUT_PATH="$1"
            else
                COPYBOOK_DIRS+=("$1")
            fi
            shift
            ;;
    esac
done

if [ -z "$INPUT_PATH" ]; then
    echo "ProLeap COBOL Parser — One-Click Runner"
    echo ""
    echo "Usage:"
    echo "  bash run.sh <file-or-dir> [copybook-dir ...] [--output-dir DIR]"
    echo ""
    echo "Examples:"
    echo "  bash run.sh test-cobol/minimal-test.cbl"
    echo "  bash run.sh myproject/cbl/ myproject/cpy/"
    echo "  bash run.sh cics-programs/ copybooks/ stubs/ --output-dir results/"
    echo ""
    echo "First run will install Java 17 + Maven and build the project."
    exit 0
fi

# ─── Step 1: Ensure conda environment exists ───────────────────────
setup_environment() {
    echo "=== Setting up environment ==="

    if ! command -v conda &>/dev/null; then
        echo "ERROR: conda not found."
        echo "Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi

    if conda env list 2>/dev/null | grep -q "^${ENV_NAME} "; then
        echo "  Environment '${ENV_NAME}' already exists."
    else
        echo "  Creating conda environment '${ENV_NAME}' with Java 17 + Maven..."
        conda create -n "$ENV_NAME" openjdk=17 maven -c conda-forge -y -q
        echo "  Environment created."
    fi
}

# ─── Step 2: Build JAR if needed ───────────────────────────────────
build_jar() {
    echo "=== Building parser JAR ==="
    echo "  Installing proleap library..."
    conda run -n "$ENV_NAME" mvn install -f proleap-cobol-parser-main/pom.xml -DskipTests -q
    echo "  Building fat JAR..."
    conda run -n "$ENV_NAME" mvn clean package -q
    echo "  Build complete."
}

# ─── Step 3: Run the parser ────────────────────────────────────────
run_parser() {
    # Build copybook dirs string (semicolon-separated)
    # Always include stubs/ directory
    local cpy_arg=""
    for dir in "${COPYBOOK_DIRS[@]}"; do
        if [ -n "$cpy_arg" ]; then
            cpy_arg="${cpy_arg};${dir}"
        else
            cpy_arg="${dir}"
        fi
    done

    if [ -d "stubs" ]; then
        if [ -n "$cpy_arg" ]; then
            cpy_arg="${cpy_arg};stubs"
        else
            cpy_arg="stubs"
        fi
    fi

    local cmd=(conda run -n "$ENV_NAME" java -jar "$JAR" "$INPUT_PATH")
    if [ -n "$cpy_arg" ]; then
        cmd+=("$cpy_arg")
    fi
    cmd+=("$OUTPUT_DIR")

    echo ""
    "${cmd[@]}"
}

# ─── Main ──────────────────────────────────────────────────────────

# Check if environment + JAR already exist (skip setup on repeat runs)
NEEDS_SETUP=false

if ! conda env list 2>/dev/null | grep -q "^${ENV_NAME} "; then
    NEEDS_SETUP=true
fi

if [ ! -f "$JAR" ]; then
    NEEDS_SETUP=true
fi

if [ "$NEEDS_SETUP" = true ]; then
    setup_environment
    echo ""
    build_jar
    echo ""
fi

if [ ! -f "$JAR" ]; then
    echo "ERROR: JAR not found at $JAR. Build may have failed."
    exit 1
fi

run_parser

echo ""
echo "JSON output is in: $OUTPUT_DIR/"
