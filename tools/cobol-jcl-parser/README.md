# ProLeap COBOL Parser

Parses COBOL source files and produces structured JSON output containing program metadata, variables, file definitions, CALL statements, and I/O operations.

Built on the [ProLeap COBOL Parser](https://github.com/uwol/proleap-cobol-parser) (ANTLR4-based).

## Quick Start (One Click)

No setup needed — the run script handles everything automatically:

```bash
# Linux / macOS / Git Bash
bash run.sh path/to/PROGRAM.cbl

# Windows CMD
run.bat path\to\PROGRAM.cbl

# With copybook directories and custom output
bash run.sh path/to/cbl/ path/to/cpy/ --output-dir results/
```

On first run it will:
1. Create a conda environment with Java 17 + Maven
2. Build the parser JAR
3. Parse your files

On subsequent runs it skips setup and runs instantly. CICS stub copybooks (`stubs/`) are included automatically.

## Prerequisites (manual setup)

- **Java 17+** (JDK)
- **Maven 3.6+**
- **Python 3.8+** (optional, for the Python wrapper)

### Quick setup with conda

```bash
conda create -n cobol-parser python=3.13 openjdk=17 maven -c conda-forge -y
conda activate cobol-parser
```

## Build

```bash
# Linux / macOS / Git Bash
bash build.sh

# Windows CMD
build.bat
```

This runs two Maven steps:
1. Installs the `proleap-cobol-parser` library to your local Maven repo
2. Builds the fat JAR at `target/cobol-parser-setup-1.0-SNAPSHOT.jar`

## Usage

### Java (direct)

```bash
# Parse a single file
java -jar target/cobol-parser-setup-1.0-SNAPSHOT.jar path/to/PROGRAM.cbl

# Parse a directory of .cbl files with copybook directories
java -jar target/cobol-parser-setup-1.0-SNAPSHOT.jar path/to/cbl/ "path/to/cpy;stubs" output/

# Arguments:
#   <file-or-dir>       Path to .cbl file or directory (required)
#   [copybook-dirs]     Semicolon-separated copybook directories (default: input dir)
#   [output-dir]        Output directory for JSON files (default: output/)
```

### Python wrapper

```python
from proleap_wrapper import ProLeapWrapper

wrapper = ProLeapWrapper()

# Parse a single file
result = wrapper.parse_file("path/to/PROGRAM.cbl", copybook_dirs=["path/to/cpy", "stubs"])
print(result["program_id"])
print(result["variables"])

# Parse a directory
results = wrapper.parse_directory("path/to/cbl/", copybook_dirs=["path/to/cpy", "stubs"])
for filename, data in results.items():
    print(filename, data["program_id"])
```

CLI mode:

```bash
python proleap_wrapper.py path/to/PROGRAM.cbl path/to/cpy stubs
```

## Output Format

Each COBOL file produces a JSON file:

```json
{
  "program_id": "CBACT01C",
  "source_file": "CBACT01C.cbl",
  "copybooks": [],
  "calls": [
    {"program": "COBDATFT", "type": "static"},
    {"program": "CEE3ABD", "type": "static"}
  ],
  "variables": [
    {"name": "ACCT-ID", "level": 5, "pic": "9(11)", "usage": ""},
    {"name": "ACCT-CURR-BAL", "level": 5, "pic": "S9(10)V99", "usage": ""},
    {"name": "TWO-BYTES-BINARY", "level": 1, "pic": "9(4)", "usage": "BINARY"}
  ],
  "files": [
    {"file_name": "ACCTFILE-FILE", "mode": "input"},
    {"file_name": "OUT-FILE", "mode": "output"}
  ],
  "io_operations": {
    "reads": ["ACCTFILE-FILE"],
    "writes": ["OUT-ACCT-REC"]
  }
}
```

### Fields

| Field | Description |
|-------|-------------|
| `program_id` | PROGRAM-ID from IDENTIFICATION DIVISION |
| `source_file` | Input filename |
| `copybooks` | Referenced copybooks (requires preprocessor hooks, currently empty) |
| `calls` | CALL statements with target program and type (static = literal, dynamic = variable) |
| `variables` | Data description entries from WORKING-STORAGE, LINKAGE, LOCAL-STORAGE, and FILE sections |
| `files` | File definitions from FILE-CONTROL with open mode (input/output/update/unknown) |
| `io_operations` | READ and WRITE statements with associated file/record names |

## CICS Programs

CICS online programs use IBM system copybooks (`DFHBMSCA`, `DFHAID`) that are not available outside a mainframe. Stub versions are provided in the `stubs/` directory.

When parsing CICS programs, include `stubs/` as a copybook directory:

```bash
java -jar target/cobol-parser-setup-1.0-SNAPSHOT.jar cics-programs/ "copybooks;stubs" output/
```

The Python wrapper automatically includes `stubs/`.

## JCL Parser

A pure Python parser for JCL (Job Control Language) files. No Java required.

### Quick Start

```bash
# One-click run
bash run_jcl.sh path/to/jobfile.jcl
bash run_jcl.sh path/to/jcl-dir/ --output-dir results/

# Or directly
python jcl_parser.py path/to/jobfile.jcl [output-dir]
```

### Python API

```python
from jcl_wrapper import JCLWrapper

wrapper = JCLWrapper()
result = wrapper.parse_file("path/to/POSTTRAN.jcl")
print(result["job_name"])         # "POSTTRAN"
print(result["steps"][0]["program"])  # "CBTRN02C"

results = wrapper.parse_directory("path/to/jcl/")
```

### JCL Output Format

```json
{
  "job_name": "POSTTRAN",
  "steps": [
    {
      "step_name": "STEP15",
      "program": "CBTRN02C",
      "datasets": [
        {"dsn": "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS", "type": "input", "disp": "SHR"},
        {"dsn": "AWS.M2.CARDDEMO.DALYREJS(+1)", "type": "output", "disp": "(NEW,CATLG,DELETE)"}
      ],
      "parm": "",
      "cond": ""
    }
  ]
}
```

### JCL Fields

| Field | Description |
|-------|-------------|
| `job_name` | JOB card name |
| `steps[].step_name` | EXEC statement label |
| `steps[].program` | PGM= value, or PROC name |
| `steps[].datasets[]` | DD statements with DSN, type (input/output/temp from DISP), raw DISP |
| `steps[].parm` | PARM= value from EXEC |
| `steps[].cond` | COND= value from EXEC |

Dataset type is classified from DISP: SHR/OLD=input, NEW/MOD=output, &&prefix or no DSN=temp. SYSOUT, DUMMY, and inline data DDs are excluded.

## Project Structure

```
.
├── run.sh / run.bat            # COBOL parser — one-click setup + build + run
├── run_jcl.sh / run_jcl.bat    # JCL parser — one-click run (Python only)
├── build.sh / build.bat        # COBOL build-only scripts
├── jcl_parser.py               # JCL parser (pure Python)
├── jcl_wrapper.py              # JCL Python wrapper
├── pom.xml                     # Outer project POM (COBOL parser)
├── src/main/java/com/example/
│   └── CobolParser.java        # COBOL parser — produces JSON output
├── proleap-cobol-parser-main/  # ProLeap library source (patched)
├── proleap_wrapper.py          # COBOL Python wrapper
├── stubs/                      # IBM CICS stub copybooks
│   ├── DFHBMSCA.cpy
│   └── DFHAID.cpy
├── test-cobol/                 # Sample COBOL files for testing
└── test-jcl/                   # Sample JCL files for testing (47 CardDemo files)
```
