"""
Python wrapper for the JCL Parser.

Usage:
    from jcl_wrapper import JCLWrapper

    wrapper = JCLWrapper()
    result = wrapper.parse_file("path/to/job.jcl")
    results = wrapper.parse_directory("path/to/jcl/")
"""

import json
import os
import sys

import jcl_parser


class JCLWrapper:
    """Wrapper class for the JCL parser, mirroring the ProLeapWrapper API."""

    def parse_file(self, jcl_file, output_dir="output-jcl"):
        """Parse a single JCL file. Returns the parsed JSON dict."""
        os.makedirs(output_dir, exist_ok=True)
        basename, result = jcl_parser.parse_and_write(jcl_file, output_dir)
        return result

    def parse_directory(self, directory, output_dir="output-jcl"):
        """Parse all JCL files in a directory. Returns dict of {filename: result}."""
        os.makedirs(output_dir, exist_ok=True)

        files = [
            os.path.join(directory, f)
            for f in sorted(os.listdir(directory))
            if f.lower().endswith(".jcl")
        ]

        results = {}
        for filepath in files:
            print(f"Parsing: {os.path.basename(filepath)}")
            basename, result = jcl_parser.parse_and_write(filepath, output_dir)
            results[basename] = result

        return results

    def parse(self, input_path, output_dir="output-jcl"):
        """Parse file or directory. Returns dict of results."""
        if os.path.isfile(input_path):
            result = self.parse_file(input_path, output_dir)
            return {os.path.basename(input_path): result}
        elif os.path.isdir(input_path):
            return self.parse_directory(input_path, output_dir)
        else:
            raise FileNotFoundError(f"Path not found: {input_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python jcl_wrapper.py <file-or-dir> [output-dir]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output-jcl"

    wrapper = JCLWrapper()
    results = wrapper.parse(input_path, output_dir)

    for filename, data in results.items():
        print(f"\n{'='*60}")
        print(f"  {filename}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2))
