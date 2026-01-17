import ast
import re
from pathlib import Path
from pprint import pprint
from typing import List, Dict


class StubExampleExtractor:
    def __init__(self):
        self.rst_code_block = re.compile(
            r'::\s*\n\n((?:(?:[ ]{2,}.*|[ \t]*)(?:\n|$))+)',
            re.MULTILINE
        )

        self.explicit_code_block = re.compile(
            r'.. code-block:: python\s*\n\n((?:(?:[ ]{2,}.*|[ \t]*)(?:\n|$))+)',
            re.MULTILINE
        )

        self.example_section = re.compile(
            r'Example(?:\s+usage)?::\s*\n\n((?:(?:[ ]{2,}.*|[ \t]*)(?:\n|$))+)',
            re.MULTILINE | re.IGNORECASE
        )

    def extract_examples_from_stub(self, stub_content: str, metadata: Dict) -> List[Dict]:
        """Extract all code examples from a stub file"""
        examples = []

        # Get all docstrings from the file
        docstrings = self._extract_all_docstrings(stub_content)
        print("docstrings:")
        pprint(docstrings)

        for i, (docstring, context) in enumerate(docstrings):
            # Try all patterns
            for pattern_name, pattern in [
                ('rst_double_colon', self.rst_code_block),
                ('explicit_code_block', self.explicit_code_block),
                ('example_section', self.example_section)
            ]:
                matches = pattern.findall(docstring)
                print(f"Pattern: {pattern_name}")
                pprint(matches)

                for j, match in enumerate(matches):
                    # Dedent the code (remove leading spaces)
                    code = self._dedent_code(match)

                    # Validate it's actually CircuitPython code
                    if self._is_valid_circuitpython_example(code):
                        examples.append({
                            'content': code,
                            'metadata': {
                                **metadata,
                                'type': 'extracted_core_module_stubs',
                                'source_type': 'stub_docstring',
                                'extraction_method': pattern_name,
                                'context': context,
                                'example_index': f"{i}_{j}"
                            }
                        })

        return examples

    def _extract_all_docstrings(self, stub_content: str) -> List[tuple]:
        """Extract all docstrings with their context"""
        docstrings = []

        try:
            import ast
            tree = ast.parse(stub_content)

            # Module-level docstring
            module_doc = ast.get_docstring(tree)
            if module_doc:
                docstrings.append((module_doc, 'module'))

                # Walk through all nodes, but only check types that can have docstrings
                for node in ast.walk(tree):
                    # Only these node types can have docstrings
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            # Determine context
                            if isinstance(node, ast.ClassDef):
                                context = f"class:{node.name}"
                            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                # Get parent class if exists
                                parent = self._find_parent_class(tree, node)
                                if parent:
                                    context = f"method:{parent.name}.{node.name}"
                                else:
                                    context = f"function:{node.name}"
                            else:
                                context = "unknown"

                            docstrings.append((docstring, context))

        except SyntaxError:
            # Fallback: use regex to find docstrings
            docstrings = self._regex_extract_docstrings(stub_content)

        return docstrings

    def _find_parent_class(self, tree, target_node):
        """Find the parent class of a node"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is target_node:
                        return node
        return None

    def _regex_extract_docstrings(self, content: str) -> List[tuple]:
        """Fallback regex-based docstring extraction"""
        # Match triple-quoted strings
        pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        matches = pattern.findall(content)
        return [(match, 'regex_extracted') for match in matches]

    def _dedent_code(self, indented_code: str) -> str:
        """Remove consistent leading indentation"""
        lines = indented_code.split('\n')

        # Find minimum indentation (excluding empty lines)
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return indented_code

        min_indent = min(len(line) - len(line.lstrip())
                         for line in non_empty_lines)

        # Remove that indentation from all lines
        dedented_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                dedented_lines.append(line[min_indent:])
            else:  # Empty line
                dedented_lines.append('')

        return '\n'.join(dedented_lines).strip()

    def _is_valid_circuitpython_example(self, code: str) -> bool:
        """Validate that extracted code is a real CircuitPython example"""
        # Must have actual code (not just comments or empty)
        code_lines = [
            line for line in code.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        if len(code_lines) < 2:
            return False

        # Should have CircuitPython imports or usage
        # circuitpython_indicators = [
        #     'import board',
        #     'import digitalio',
        #     'import analogio',
        #     'import busio',
        #     'import microcontroller',
        #     'import time',
        #     'from digitalio',
        #     'from analogio',
        #     'board.',
        #     'digitalio.',
        #     'analogio.',
        # ]
        #
        # code_lower = code.lower()
        # if not any(indicator.lower() in code_lower for indicator in circuitpython_indicators):
        #     return False

        # Try to parse as valid Python
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def process_stub_file(self, file_path, library_name):
        """Process a stub file and extract examples"""
        #try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        base_metadata = {
            'source': str(file_path),
            'library': library_name,
            'file_name': file_path.name
        }

        # Extract examples
        examples = self.extract_examples_from_stub(content, base_metadata)




        return examples

        # except Exception as e:
        #     print(f"Error processing stub {file_path}: {e}")
        #     return []


if __name__ == '__main__':
    example_extractor = StubExampleExtractor()
    examples = example_extractor.process_stub_file(Path("circuitpython/circuitpython-stubs/digitalio/__init__.pyi"), "digitalio")
    pprint(examples)
