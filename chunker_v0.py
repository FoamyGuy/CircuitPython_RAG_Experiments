import ast
import re
import json
from pathlib import Path


class CircuitPythonChunker:
    def __init__(self):
        self.chunk_size_limit = 1000  # tokens

    def chunk_python_file(self, file_content, metadata):
        """Chunk Python file intelligently"""
        chunks = []

        try:
            tree = ast.parse(file_content)

            # Extract imports (always include these)
            imports = self._extract_imports(tree)

            # Process each top-level element
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    chunk = self._create_function_chunk(node, file_content, imports)
                    if chunk:
                        chunks.append({
                            'content': chunk,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'function',
                                'function_name': node.name
                            }
                        })

                elif isinstance(node, ast.Assign):
                    # Handle global configurations or setup code
                    chunk = self._create_assignment_chunk(node, file_content, imports)
                    if chunk:
                        chunks.append({
                            'content': chunk,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'setup'
                            }
                        })

            # If file is short enough, also include as whole file
            if len(file_content) < self.chunk_size_limit:
                chunks.append({
                    'content': file_content,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'complete_example'
                    }
                })

        except SyntaxError:
            # If can't parse, fall back to simple chunking
            chunks = self._simple_chunk(file_content, metadata)

        return chunks

    def _extract_imports(self, tree):
        """Extract all import statements"""
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))
        return imports

    def _create_function_chunk(self, func_node, file_content, imports):
        """Create a chunk for a function with context"""
        func_code = ast.unparse(func_node)

        # Add docstring context if available
        description = ""
        if (ast.get_docstring(func_node)):
            description = f"# {ast.get_docstring(func_node)}\n"

        # Combine imports + description + function
        chunk = "\n".join(imports) + "\n\n" + description + func_code

        # Add usage example if found in comments
        usage_example = self._find_usage_example(func_node.name, file_content)
        if usage_example:
            chunk += f"\n\n# Usage example:\n{usage_example}"

        return chunk

    def _create_assignment_chunk(self, assign_node, file_content, imports):
        """Create a chunk for important assignments (pin configs, constants, etc.)"""
        assignment_code = ast.unparse(assign_node)

        # Only create chunks for assignments that look like CircuitPython setup
        if self._is_circuitpython_assignment(assignment_code):
            # Find related assignments in the same area
            context_lines = self._get_assignment_context(assign_node, file_content)

            if context_lines:
                chunk = "\n".join(imports) + "\n\n" + "\n".join(context_lines)
                return chunk

        return None

    def _is_circuitpython_assignment(self, assignment_code):
        """Check if assignment is CircuitPython-related"""
        circuitpython_keywords = [
            'board.', 'digitalio.', 'analogio.', 'busio.',
            'neopixel', 'adafruit_', 'microcontroller.',
            '.DigitalInOut', '.AnalogIn', '.PWMOut'
        ]

        return any(keyword in assignment_code for keyword in circuitpython_keywords)

    def _get_assignment_context(self, assign_node, file_content):
        """Get related assignments around this one"""
        lines = file_content.split('\n')

        # Find the line number of this assignment
        target_line = None
        assignment_str = ast.unparse(assign_node)

        for i, line in enumerate(lines):
            if assignment_str.strip() in line.strip():
                target_line = i
                break

        if target_line is None:
            return [assignment_str]

        # Collect related lines (assignments, imports, comments)
        context_lines = []

        # Look backwards for related setup
        for i in range(max(0, target_line - 5), target_line):
            line = lines[i].strip()
            if line and (line.startswith('#') or '=' in line or line.startswith('import')):
                context_lines.append(lines[i])

        # Add the target line
        context_lines.append(lines[target_line])

        # Look forwards for related setup
        for i in range(target_line + 1, min(len(lines), target_line + 5)):
            line = lines[i].strip()
            if line and (line.startswith('#') or '=' in line):
                context_lines.append(lines[i])
            elif line == "":
                continue
            else:
                break  # Stop at first non-setup line

        return context_lines

    def _find_usage_example(self, function_name, file_content):
        """Look for usage examples of a function in the file"""
        lines = file_content.split('\n')
        for i, line in enumerate(lines):
            if function_name in line and 'def ' not in line:
                # Found usage, extract a few lines of context
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                return '\n'.join(lines[start:end])
        return None

    def _simple_chunk(self, file_content, metadata):
        """Fallback chunking when AST parsing fails"""
        # Split by blank lines or logical breaks
        sections = re.split(r'\n\s*\n', file_content)
        chunks = []

        current_chunk = ""
        for section in sections:
            if len(current_chunk) + len(section) < self.chunk_size_limit:
                current_chunk += section + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': {
                            **metadata,
                            'chunk_type': 'simple'
                        }
                    })
                current_chunk = section + "\n\n"

        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': {
                    **metadata,
                    'chunk_type': 'simple'
                }
            })

        return chunks


if __name__ == '__main__':
    chunker = CircuitPythonChunker()

    # Process each collected file
    processed_chunks = []

    for py_file in Path("circuitpython_data/processed").glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()

        # Load metadata
        with open(f"{py_file}.meta", 'r') as f:
            metadata = json.load(f)

        # Chunk the content
        chunks = chunker.chunk_python_file(content, metadata)
        processed_chunks.extend(chunks)

    # Save processed chunks for RAG system
    with open("rag_ready_chunks.json", 'w') as f:
        json.dump(processed_chunks, f, indent=2)

    print(f"Processed {len(processed_chunks)} chunks ready for RAG")