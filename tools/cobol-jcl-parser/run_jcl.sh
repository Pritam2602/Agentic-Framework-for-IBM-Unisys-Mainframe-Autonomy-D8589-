#!/usr/bin/env bash
#
# One-click runner for the JCL Parser.
# No Java/Maven/conda needed — just Python 3.
#
# Usage:
#   bash run_jcl.sh <file-or-dir> [--output-dir DIR]
#
# Examples:
#   bash run_jcl.sh test-jcl/POSTTRAN.jcl
#   bash run_jcl.sh test-jcl/
#   bash run_jcl.sh myjobs/ --output-dir results/
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ─── Parse arguments ───────────────────────────────────────────────
INPUT_PATH=""
OUTPUT_DIR="output-jcl"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            INPUT_PATH="$1"
            shift
            ;;
    esac
done

if [ -z "$INPUT_PATH" ]; then
    echo "JCL Parser — One-Click Runner"
    echo ""
    echo "Usage:"
    echo "  bash run_jcl.sh <file-or-dir> [--output-dir DIR]"
    echo ""
    echo "Examples:"
    echo "  bash run_jcl.sh test-jcl/POSTTRAN.jcl"
    echo "  bash run_jcl.sh test-jcl/"
    echo "  bash run_jcl.sh myjobs/ --output-dir results/"
    exit 0
fi

# ─── Find Python ───────────────────────────────────────────────────
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "ERROR: Python 3 not found. Install Python 3.8+ to use this tool."
    exit 1
fi

# ─── Run ───────────────────────────────────────────────────────────
"$PYTHON" "$SCRIPT_DIR/jcl_parser.py" "$INPUT_PATH" "$OUTPUT_DIR"

echo ""
echo "JSON output is in: $OUTPUT_DIR/"
