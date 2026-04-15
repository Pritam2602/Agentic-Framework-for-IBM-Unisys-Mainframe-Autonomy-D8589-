import subprocess
import os
import json
import glob


class ProLeapWrapper:
    """Python wrapper for the ProLeap COBOL parser JAR."""

    def __init__(self, jar_path=None):
        if jar_path is None:
            jar_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "target",
                "cobol-parser-setup-1.0-SNAPSHOT.jar",
            )
        if not os.path.exists(jar_path):
            raise FileNotFoundError(
                f"JAR not found at {jar_path}. Run 'build.sh' first."
            )
        self.jar_path = jar_path

    def parse(self, input_path, copybook_dirs=None, output_dir="output"):
        """
        Parse COBOL file(s) and return a dict of {filename: parsed_json}.

        Args:
            input_path:    Path to a .cbl file or directory of .cbl files.
            copybook_dirs: List of directories containing copybooks.
                           The stubs/ directory is always included.
            output_dir:    Directory where JSON output files are written.

        Returns:
            dict mapping base filenames to parsed JSON dicts.
            Files that failed to parse are mapped to {"error": "message"}.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input path not found: {input_path}")

        # Build copybook dirs string — always include stubs/
        stubs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
        dirs = []
        if copybook_dirs:
            dirs.extend(copybook_dirs)
        if os.path.isdir(stubs_dir):
            dirs.append(stubs_dir)

        # If input is a file, include its parent dir for copybooks too
        if os.path.isfile(input_path):
            parent = os.path.dirname(os.path.abspath(input_path))
            if parent not in dirs:
                dirs.append(parent)

        copybook_arg = ";".join(dirs) if dirs else ""

        cmd = ["java", "-jar", self.jar_path, input_path]
        if copybook_arg:
            cmd.append(copybook_arg)
        cmd.append(output_dir)

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print parser output for visibility
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Collect JSON output files
        results = {}
        for json_file in glob.glob(os.path.join(output_dir, "*.json")):
            base = os.path.basename(json_file)
            try:
                with open(json_file, "r") as f:
                    results[base] = json.load(f)
            except json.JSONDecodeError as e:
                results[base] = {"error": f"Invalid JSON: {e}"}

        return results

    def parse_file(self, cobol_file, copybook_dirs=None, output_dir="output"):
        """Parse a single COBOL file. Returns the parsed JSON dict or error dict."""
        results = self.parse(cobol_file, copybook_dirs, output_dir)
        if results:
            return next(iter(results.values()))
        return {"error": f"No output produced for {cobol_file}"}

    def parse_directory(self, directory, copybook_dirs=None, output_dir="output"):
        """Parse all COBOL files in a directory. Returns dict of results."""
        return self.parse(directory, copybook_dirs, output_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python proleap_wrapper.py <file-or-dir> [copybook-dir1 copybook-dir2 ...]")
        sys.exit(1)

    input_path = sys.argv[1]
    copybook_dirs = sys.argv[2:] if len(sys.argv) > 2 else None

    wrapper = ProLeapWrapper()
    results = wrapper.parse(input_path, copybook_dirs)

    for filename, data in results.items():
        print(f"\n{'='*60}")
        print(f"  {filename}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2))
