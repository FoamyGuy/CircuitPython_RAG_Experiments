import os
import glob
from pathlib import Path
import time
import toml

from stubs_example_extractor_v1 import StubExampleExtractor

def extract_first_package_or_module(toml_file_path):
    """
    Extract the first value from either 'packages' or 'py-modules' list
    in the [tool.setuptools] section of a TOML file.

    Args:
        toml_file_path (str): Path to the TOML file

    Returns:
        str or None: First package/module name, or None if neither exists
    """
    try:
        # Load the TOML file
        with open(toml_file_path, 'r') as file:
            data = toml.load(file)

        # Navigate to tool.setuptools section
        setuptools_section = data.get('tool', {}).get('setuptools', {})

        # Check for 'packages' first
        if 'packages' in setuptools_section:
            packages = setuptools_section['packages']
            if isinstance(packages, list) and packages:
                return packages[0]

        # If no packages, check for 'py-modules'
        if 'py-modules' in setuptools_section:
            py_modules = setuptools_section['py-modules']
            if isinstance(py_modules, list) and py_modules:
                return py_modules[0]

        # Neither found or both are empty
        return None

    except FileNotFoundError:
        print(f"Error: File '{toml_file_path}' not found.")
        return None
    except toml.TomlDecodeError as e:
        print(f"Error parsing TOML file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

class CircuitPythonCollector:
    def __init__(self, output_dir="circuitpython_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stub_extractor = StubExampleExtractor(output_dir)  # Share output dir

    def collect_official_libraries(self):
        """Collect from official Adafruit libraries"""
        libraries = [
            "Adafruit_CircuitPython_NeoPixel",
            "Adafruit_CircuitPython_Motor",
            "Adafruit_CircuitPython_BME280",
            "Adafruit_CircuitPython_Display_Text",
            "Adafruit_CircuitPython_HID",
            # Add more as needed
        ]

        # for lib in libraries:
        #     repo_url = f"https://github.com/adafruit/{lib}.git"
        #     local_path = self.output_dir / lib
        #
        #     if not local_path.exists():
        #         print(f"Cloning {lib}...")
        #         git.Repo.clone_from(repo_url, local_path)
        #
        #     # Extract examples
        #     self._extract_examples(local_path, lib)


    def process_libs(self):
        bundle_libs_dir = Path("Adafruit_CircuitPython_Bundle/libraries")

        for subdir in {"drivers", "helpers"}:
            for lib in os.listdir(bundle_libs_dir / f"{subdir}"):

                local_repo_path = bundle_libs_dir / subdir / lib

                lib_name = extract_first_package_or_module(str(local_repo_path / "pyproject.toml"))
                # Extract examples
                self._extract_examples(local_repo_path, lib)

    def process_stubs(self, stubs_dir="circuitpython/circuitpython-stubs"):
        """Process all stub files to extract examples"""
        stubs_path = Path(stubs_dir)

        for stub_file in stubs_path.glob("**/*.pyi"):
            # Get library name from directory structure
            library_name = stub_file.parent.name
            if library_name == "circuitpython-stubs":
                library_name = stub_file.stem

            print(f"Processing stub: {stub_file}")
            self.stub_extractor.process_stub_file(stub_file, library_name)

    def _extract_examples(self, repo_path, library_name):
        """Extract code examples from a repository"""
        examples_dir = repo_path / "examples"
        if examples_dir.exists():
            for py_file in examples_dir.glob("**/*.py"):
                self._process_python_file(py_file, library_name)

        # Also check for examples in README or docs
        # for readme in repo_path.glob("**/README*"):
        #     if readme.suffix.lower() in ['.md', '.rst']:
        #         self._extract_code_blocks(readme, library_name)

    def _process_python_file(self, file_path, library_name):
        """Process individual Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip if too short or not actually CircuitPython
            # if len(content) < 100 or not self._is_circuitpython_code(content):
            #     return

            metadata = {
                'source': str(file_path),
                'library': library_name,
                'type': 'example',
                'file_name': file_path.name
            }

            # Save to our processed examples
            output_file = self.output_dir / "processed" / f"{library_name}_{file_path.name}"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w') as f:
                f.write(content)

            # Store metadata separately
            import json
            with open(f"{output_file}.meta", 'w') as f:
                json.dump(metadata, f)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def _is_circuitpython_code(self, content):
        """Check if code is actually CircuitPython"""
        circuitpython_indicators = [
            'import board',
            'import digitalio',
            'import displayio',
            'import analogio',
            'import busio',
            'import microcontroller',
            'import neopixel',
            'import adafruit_'
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in circuitpython_indicators)

    def _extract_code_blocks(self, readme_path, library_name):
        """Extract code blocks from markdown/rst files"""
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract Python code blocks
            import re

            # Markdown code blocks
            md_pattern = r'```python\n(.*?)\n```'
            rst_pattern = r'\.\. code-block:: python\n\n((?:    .*\n)*)'

            for pattern in [md_pattern, rst_pattern]:
                matches = re.findall(pattern, content, re.DOTALL)
                for i, code in enumerate(matches):
                    if self._is_circuitpython_code(code):
                        output_file = self.output_dir / "processed" / f"{library_name}_readme_{i}.py"
                        with open(output_file, 'w') as f:
                            f.write(code.strip())

        except Exception as e:
            print(f"Error extracting from {readme_path}: {e}")


if __name__ == '__main__':
    collector = CircuitPythonCollector()
    collector.process_libs()
    collector.process_stubs()