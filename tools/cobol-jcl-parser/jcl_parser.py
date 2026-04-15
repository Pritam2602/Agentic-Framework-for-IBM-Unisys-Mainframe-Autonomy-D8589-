"""
JCL (Job Control Language) Parser — produces structured JSON output.

Usage:
    python jcl_parser.py <file-or-dir> [output-dir]
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict


# ─── Data Classes ──────────────────────────────────────────────────

@dataclass
class Dataset:
    dsn: str
    type: str   # "input" | "output" | "temp"
    disp: str   # raw DISP string

@dataclass
class Step:
    step_name: str
    program: str
    datasets: list = field(default_factory=list)
    parm: str = ""
    cond: str = ""


# ─── Phase 1: Line Assembly ───────────────────────────────────────

def assemble_lines(text):
    """Convert raw JCL text into logical statements.

    Returns list of tuples: (label, operation, operand, raw_text)
    """
    raw_lines = text.splitlines()
    logical = []
    in_inline_data = False

    for line in raw_lines:
        # Strip sequence numbers (cols 73-80) if line is 80 chars
        if len(line) >= 80:
            line = line[:72].rstrip()

        # Handle inline data terminator
        if in_inline_data:
            if line.startswith("/*") or line.startswith("//"):
                in_inline_data = False
                if line.startswith("/*"):
                    continue
                # fall through to parse the // line
            else:
                continue

        # Skip empty lines
        if not line.strip():
            continue

        # Must start with //
        if not line.startswith("//"):
            continue

        # Skip comments
        if line.startswith("//*"):
            continue

        # Get content after //
        content = line[2:]

        # Continuation line: col 3+ starts with spaces then content
        if content and content[0] == " ":
            stripped = content.strip()
            # Check if this is actually a new unlabeled statement (e.g., concatenated DD)
            # A continuation won't start with a JCL operation keyword
            first_word = stripped.split()[0].upper() if stripped else ""
            is_new_statement = first_word in (
                "DD", "EXEC", "JOB", "SET", "JCLLIB", "INCLUDE", "OUTPUT",
                "PROC", "PEND",
            )

            if is_new_statement:
                # Parse as a new unlabeled statement
                parts = stripped.split(None, 1)
                operation = parts[0].upper()
                operand = parts[1] if len(parts) > 1 else ""

                # Check for inline data triggers
                if operation == "DD":
                    operand_upper = operand.strip().upper()
                    if operand_upper == "*" or operand_upper.startswith("* ") or operand_upper == "DATA":
                        in_inline_data = True

                logical.append(("", operation, operand, line))
                continue

            # Regular continuation — append to previous logical line
            if stripped and logical:
                prev = logical[-1]
                combined_operand = prev[2]
                if combined_operand:
                    combined_operand = combined_operand.rstrip(",") + "," + stripped
                else:
                    combined_operand = stripped
                logical[-1] = (prev[0], prev[1], combined_operand, prev[3] + "\n" + line)
            continue

        # New statement: parse LABEL OPERATION OPERAND
        parts = content.split(None, 2)

        if len(parts) == 0:
            continue

        label = ""
        operation = ""
        operand = ""

        if len(parts) == 1:
            # Could be just a label or just an operation
            label = parts[0]
        elif len(parts) == 2:
            label = parts[0]
            operation = parts[1].upper()
        else:
            label = parts[0]
            operation = parts[1].upper()
            operand = parts[2]

        # Check for inline data triggers
        if operation == "DD":
            operand_upper = operand.strip().upper()
            if operand_upper == "*" or operand_upper.startswith("* ") or operand_upper == "DATA":
                in_inline_data = True

        logical.append((label, operation, operand, line))

    return logical


# ─── Keyword Extraction ───────────────────────────────────────────

def extract_keyword(operand, keyword):
    """Extract value for a keyword from JCL operand string.

    Handles nested parens and quoted values:
        extract_keyword("PGM=IDCAMS,PARM='X'", "PGM") -> "IDCAMS"
        extract_keyword("DISP=(NEW,CATLG,DELETE)", "DISP") -> "(NEW,CATLG,DELETE)"
    """
    pattern = keyword.upper() + "="
    upper_operand = operand.upper()
    idx = -1

    # Find keyword= at start or after comma (not inside quotes/parens)
    search_from = 0
    while True:
        pos = upper_operand.find(pattern, search_from)
        if pos == -1:
            break
        # Check it's at start or preceded by comma/space
        if pos == 0 or upper_operand[pos - 1] in (",", " "):
            idx = pos
            break
        search_from = pos + 1

    if idx == -1:
        return None

    # Extract value starting after '='
    start = idx + len(pattern)
    if start >= len(operand):
        return ""

    # Scan forward, respecting parens and quotes
    paren_depth = 0
    in_quote = False
    end = start

    for i in range(start, len(operand)):
        ch = operand[i]
        if in_quote:
            if ch == "'":
                # Check for escaped quote ''
                if i + 1 < len(operand) and operand[i + 1] == "'":
                    continue
                in_quote = False
            continue
        if ch == "'":
            in_quote = True
        elif ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth -= 1
        elif ch == "," and paren_depth == 0:
            break
        elif ch == " " and paren_depth == 0:
            break
        end = i + 1

    value = operand[start:end].strip()

    # Strip outer quotes if present
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        value = value[1:-1]

    return value


def parse_disp(disp_str):
    """Parse DISP parameter into (status, normal_disp, abnormal_disp).

    Examples:
        "SHR"                  -> ("SHR", "", "")
        "(NEW,CATLG,DELETE)"   -> ("NEW", "CATLG", "DELETE")
        "(OLD,DELETE)"         -> ("OLD", "DELETE", "")
    """
    if not disp_str:
        return ("", "", "")

    s = disp_str.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]

    parts = [p.strip() for p in s.split(",")]
    status = parts[0].upper() if len(parts) > 0 else ""
    normal = parts[1].upper() if len(parts) > 1 else ""
    abnormal = parts[2].upper() if len(parts) > 2 else ""

    return (status, normal, abnormal)


def classify_dataset_type(disp_str, dsn, operand_upper):
    """Classify a dataset as input, output, or temp."""
    # Temporary datasets
    if dsn and dsn.startswith("&&"):
        return "temp"

    # No DSN and no DISP -> temp
    if not dsn and not disp_str:
        return "temp"

    status, normal, abnormal = parse_disp(disp_str)

    if status in ("NEW",):
        return "output"
    elif status in ("OLD", "SHR"):
        return "input"
    elif status == "MOD":
        # MOD with DELETE -> temp, otherwise output
        if normal == "DELETE" and abnormal == "DELETE":
            return "temp"
        return "output"

    # No DISP -> defaults to NEW,DELETE -> temp
    if not status:
        return "temp"

    return "input"


# ─── Phase 2: Statement Parsing ───────────────────────────────────

def parse_jcl(source, filename=""):
    """Parse JCL source text and return structured dict."""
    lines = assemble_lines(source)

    job_name = ""
    steps = []
    current_step = None

    for label, operation, operand, raw in lines:
        if operation == "JOB":
            job_name = label
            continue

        if operation == "EXEC":
            # Finish previous step
            if current_step:
                steps.append(current_step)

            step_name = label
            program = ""
            parm = ""
            cond = ""

            # Extract program
            pgm = extract_keyword(operand, "PGM")
            proc = extract_keyword(operand, "PROC")
            if pgm:
                program = pgm
            elif proc:
                program = proc
            else:
                # Bare name = proc reference: EXEC PROCNAME,PARM=...
                first = operand.split(",")[0].split()[0] if operand else ""
                if first and "=" not in first:
                    program = first

            # Extract PARM
            p = extract_keyword(operand, "PARM")
            if p:
                parm = p

            # Extract COND
            c = extract_keyword(operand, "COND")
            if c:
                cond = c

            current_step = Step(
                step_name=step_name,
                program=program,
                parm=parm,
                cond=cond,
            )
            continue

        if operation == "DD":
            if current_step is None:
                continue

            operand_upper = operand.upper()

            # Skip SYSOUT DDs
            if "SYSOUT=" in operand_upper:
                continue

            # Skip DUMMY
            if operand.strip().upper() == "DUMMY":
                continue

            # Skip inline data DDs (DD * or DD DATA with no DSN)
            if operand.strip().upper() in ("*", "DATA") or operand.strip().upper().startswith("* "):
                continue

            # Extract DSN
            dsn = extract_keyword(operand, "DSN") or extract_keyword(operand, "DSNAME") or ""

            # Skip DDs with no DSN (system DDs like SYSPRINT without SYSOUT)
            if not dsn:
                continue

            # Extract DISP
            disp_raw = extract_keyword(operand, "DISP") or ""

            # Classify type
            ds_type = classify_dataset_type(disp_raw, dsn, operand_upper)

            current_step.datasets.append(Dataset(
                dsn=dsn,
                type=ds_type,
                disp=disp_raw,
            ))
            continue

        # SET, JCLLIB, other — skip (not in schema)

    # Finish last step
    if current_step:
        steps.append(current_step)

    # Fallback job name
    if not job_name and filename:
        job_name = os.path.splitext(os.path.basename(filename))[0]

    return {
        "job_name": job_name,
        "steps": [
            {
                "step_name": s.step_name,
                "program": s.program,
                "datasets": [asdict(d) for d in s.datasets],
                "parm": s.parm,
                "cond": s.cond,
            }
            for s in steps
        ],
    }


# ─── File I/O ─────────────────────────────────────────────────────

def parse_file(filepath):
    """Parse a single JCL file and return the result dict."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    return parse_jcl(source, filename=filepath)


def parse_and_write(filepath, output_dir):
    """Parse a JCL file and write JSON output. Returns (basename, result_or_error)."""
    basename = os.path.basename(filepath)
    try:
        result = parse_file(filepath)
        out_name = os.path.splitext(basename)[0] + ".json"
        out_path = os.path.join(output_dir, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"  -> {out_path}")
        return (basename, result)
    except Exception as e:
        print(f"  FAILED: {basename} - {e}", file=sys.stderr)
        return (basename, {"error": str(e)})


# ─── CLI ───────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("JCL Parser — produces structured JSON from JCL files")
        print()
        print("Usage:")
        print("  python jcl_parser.py <file-or-dir> [output-dir]")
        print()
        print("Examples:")
        print("  python jcl_parser.py myjob.jcl")
        print("  python jcl_parser.py jcl-files/ output-jcl/")
        sys.exit(0)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output-jcl"
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isfile(input_path):
        files = [input_path]
    elif os.path.isdir(input_path):
        files = [
            os.path.join(input_path, f)
            for f in sorted(os.listdir(input_path))
            if f.lower().endswith(".jcl")
        ]
    else:
        print(f"ERROR: Invalid path: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"ERROR: No JCL files found in {input_path}", file=sys.stderr)
        sys.exit(1)

    success = 0
    failed = 0

    for filepath in files:
        print(f"Parsing: {os.path.basename(filepath)}")
        basename, result = parse_and_write(filepath, output_dir)
        if "error" in result:
            failed += 1
        else:
            success += 1

    print()
    print(f"Done. {success} succeeded, {failed} failed out of {success + failed} files.")
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
