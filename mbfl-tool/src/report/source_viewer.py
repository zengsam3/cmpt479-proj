"""
Source code analysis and context display for suspicious locations
"""

from pathlib import Path
from typing import Dict, Optional


class SourceCodeAnalyzer:
    """Analyzes source code to provide context for suspicious locations"""

    def __init__(self, source_dir: Optional[Path] = None):
        self.source_dir = Path(source_dir) if source_dir else None

    def get_code_context(self, class_name: str, line_number: int, context_lines: int = 3) -> Dict:
        """Get code context around suspicious line"""
        if not self.source_dir:
            return {"message": "Source code directory not provided"}

        # Find the java file
        java_files = list(self.source_dir.rglob(f"*{class_name.split('.')[-1]}.java"))

        if not java_files:
            return {"error": f"Source file not found for {class_name}"}

        java_file = java_files[0]

        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)

            context = {
                "file_path": str(java_file.relative_to(self.source_dir)),
                "suspicious_line": line_number,
                "code_lines": []
            }

            for i in range(start_line, end_line):
                context["code_lines"].append({
                    "line_number": i + 1,
                    "code": lines[i].rstrip(),
                    "is_suspicious": i + 1 == line_number
                })

            return context

        except Exception as e:
            return {"error": f"Error reading source file: {e}"}


def display_code_context(context: Dict, show_file_path: bool = True):
    """Display code context in a formatted way"""
    if "error" in context:
        print(f"    Error: {context['error']}")
        return

    if "message" in context:
        print(f"    {context['message']}")
        return

    if show_file_path and "file_path" in context:
        print(f"    File: {context['file_path']}")

    if "code_lines" in context:
        for line_info in context["code_lines"]:
            marker = ">>> " if line_info['is_suspicious'] else "    "
            print(f"{marker}{line_info['line_number']:4d}: {line_info['code']}")