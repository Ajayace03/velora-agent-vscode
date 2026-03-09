# -----------------------------------------------------------------------------
# Phase 3: AI Struct Agent - Documentation & File Generation v1.0.0
# -----------------------------------------------------------------------------
# This module implements the third phase of the AI Struct Agent, focusing on
# comprehensive project documentation, missing file generation, and smoke testing.
# It includes enhanced code analysis, AI-powered documentation generation,
# and a structured output generation.
# -----------------------------------------------------------------------------

import os
import sys
import json
import subprocess
from pathlib import Path
import ast
from google import genai
from typing import Dict, List, Set, Tuple

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
AGENT_VERSION = "1.0.0"
API_KEY = os.getenv("GOOGLE_API_KEY")
CLIENT = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL = "gemini-2.5-flash"
PHASE2_OUTPUT_ROOT = Path("./structured_project")
PHASE1_METADATA_JSON = Path("phase1_metadata.json")

# -----------------------------------------------------------------------------
# 1. AST-based Code Analysis & Dependency Graph Builder
# -----------------------------------------------------------------------------
class CodeAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_metadata = {}
        self.dependency_graph = {}
        self.entry_points = []
        self.all_classes = []
        self.all_functions = []
        
    def analyze_project(self) -> Dict:
        """Comprehensive project analysis."""
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            rel_path = py_file.relative_to(self.project_root).as_posix()
            metadata = self._analyze_file(py_file, rel_path)
            self.file_metadata[rel_path] = metadata
            
            if metadata['entry_point']:
                self.entry_points.append(rel_path)
            self.all_classes.extend(metadata['classes'])
            self.all_functions.extend(metadata['functions'])
            
        self._build_dependency_graph()
        return self._generate_analysis_summary()
    
    def _analyze_file(self, file_path: Path, rel_path: str) -> Dict:
        """Extract functions, classes, imports, docstrings from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            print(f"⚠️ Could not parse {rel_path}: {e}")
            return self._empty_metadata()
        
        imports = []
        classes = []
        functions = []
        docstring = ast.get_docstring(tree) or ""
        entry_point = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node) or ""
                classes.append({
                    'name': node.name,
                    'docstring': class_doc,
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                })
            elif isinstance(node, ast.FunctionDef):
                func_doc = ast.get_docstring(node) or ""
                functions.append({
                    'name': node.name,
                    'docstring': func_doc,
                    'args': [arg.arg for arg in node.args.args]
                })
            elif isinstance(node, ast.If) and self._is_main_guard(node):
                entry_point = True
                
        return {
            'imports': list(set(imports)),
            'classes': classes,
            'functions': functions,
            'docstring': docstring,
            'entry_point': entry_point,
            'role': self._classify_file_role(rel_path, classes, functions, entry_point)
        }
    
    def _is_main_guard(self, node: ast.If) -> bool:
        """Check if node is 'if __name__ == "__main__"'."""
        try:
            return (isinstance(node.test, ast.Compare) and
                   isinstance(node.test.left, ast.Name) and
                   node.test.left.id == "__name__" and
                   any(isinstance(c, ast.Constant) and c.value == "__main__" 
                       for c in node.test.comparators))
        except Exception:
            return False
    
    def _classify_file_role(self, rel_path: str, classes: List, functions: List, entry_point: bool) -> str:
        """Heuristically classify file role."""
        path_lower = rel_path.lower()
        
        if 'test' in path_lower:
            return 'test'
        elif '__init__' in path_lower:
            return 'package_init'
        elif entry_point:
            return 'entry_point'
        elif 'main' in path_lower:
            return 'main_module'
        elif 'config' in path_lower or 'setting' in path_lower:
            return 'configuration'
        elif 'util' in path_lower or 'helper' in path_lower:
            return 'utility'
        elif classes and not functions:
            return 'class_definition'
        elif functions and not classes:
            return 'function_module'
        else:
            return 'mixed_module'
    
    def _build_dependency_graph(self):
        """Build internal dependency relationships."""
        for file_path, metadata in self.file_metadata.items():
            deps = []
            for imp in metadata['imports']:
                # Check if import is internal (matches other files in project)
                for other_file in self.file_metadata:
                    if imp in other_file.replace('/', '.').replace('.py', ''):
                        deps.append(other_file)
            self.dependency_graph[file_path] = deps
    
    def _generate_analysis_summary(self) -> Dict:
        """Generate comprehensive analysis summary."""
        return {
            'total_files': len(self.file_metadata),
            'entry_points': self.entry_points,
            'total_classes': len(self.all_classes),
            'total_functions': len(self.all_functions),
            'file_roles': {role: [f for f, m in self.file_metadata.items() 
                                 if m['role'] == role] 
                          for role in set(m['role'] for m in self.file_metadata.values())},
            'dependency_graph': self.dependency_graph,
            'detailed_metadata': self.file_metadata
        }
    
    def _empty_metadata(self) -> Dict:
        return {
            'imports': [], 'classes': [], 'functions': [],
            'docstring': '', 'entry_point': False, 'role': 'unknown'
        }

# -----------------------------------------------------------------------------
# 2. Missing File Generator
# -----------------------------------------------------------------------------
class MissingFileGenerator:
    def __init__(self, project_root: Path, analysis: Dict):
        self.project_root = project_root
        self.analysis = analysis
        
    def generate_missing_files(self):
        """Generate all missing essential files."""
        print("🔧 Generating missing core files...")
        
        self._generate_init_files()
        self._generate_main_file()
        self._generate_gitignore()
        self._generate_setup_py()
        
        print("✅ Missing files generated.")
        
    def _generate_init_files(self):
        """Generate __init__.py files for Python packages."""
        for root, dirs, files in os.walk(self.project_root):
            # Skip if already has __init__.py or no Python files
            if '__init__.py' in files:
                continue
                
            py_files = [f for f in files if f.endswith('.py')]
            if not py_files:
                continue
                
            init_path = Path(root) / '__init__.py'
            
            # Generate contextual __init__.py content
            modules = [f[:-3] for f in py_files if f != '__init__.py']
            content = f'"""Package initialization for {Path(root).name}."""\n\n'
            
            if modules:
                content += "# Auto-generated imports\n"
                for module in modules:
                    content += f"from .{module} import *\n"
                content += f"\n__all__ = {modules}\n"
            
            init_path.write_text(content, encoding='utf-8')
            print(f"Created: {init_path.relative_to(self.project_root)}")
    
    def _generate_main_file(self):
        """Generate main.py if no clear entry point exists."""
        if self.analysis['entry_points']:
            return  # Already has entry points
            
        main_path = self.project_root / 'main.py'
        if main_path.exists():
            return
            
        # Generate main.py based on project structure
        content = '''"""Main application entry point.

This file was auto-generated. Modify as needed for your application.
"""

def main():
    """Main application function."""
    print("Hello from your restructured project!")
    print("This is an auto-generated main file.")
    
    # TODO: Add your main application logic here
    

if __name__ == "__main__":
    main()
'''
        
        main_path.write_text(content, encoding='utf-8')
        print(f"Created: main.py")
    
    def _generate_gitignore(self):
        """Generate .gitignore file."""
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            return
            
        content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
'''
        
        gitignore_path.write_text(content, encoding='utf-8')
        print(f"Created: .gitignore")
    
    def _generate_setup_py(self):
        """Generate basic setup.py."""
        setup_path = self.project_root / 'setup.py'
        if setup_path.exists():
            return
            
        project_name = self.project_root.name
        content = f'''"""Setup script for {project_name}."""

from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="1.0.0",
    description="Auto-generated setup for restructured project",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={{
        "console_scripts": [
            # Add CLI commands here
        ],
    }},
)
'''
        
        setup_path.write_text(content, encoding='utf-8')
        print(f"Created: setup.py")

# -----------------------------------------------------------------------------
# 3. AI-Powered Documentation Agent
# -----------------------------------------------------------------------------
class DocumentationAgent:
    def __init__(self, project_root: Path, analysis: Dict, phase1_metadata: Dict):
        self.project_root = project_root
        self.analysis = analysis
        self.phase1_metadata = phase1_metadata
        
    def generate_documentation(self):
        """Generate comprehensive project documentation."""
        print("📝 Generating professional README and documentation...")
        
        readme_content = self._generate_readme()
        self._write_readme(readme_content)
        
        workflow_content = self._generate_workflow_doc()
        self._write_workflow_doc(workflow_content)
        
        print("✅ Documentation generated.")
    
    def _generate_readme(self) -> str:
        """Generate professional README using AI."""
        prompt = f"""
Generate a professional, comprehensive README.md for this Python project.

**Project Analysis:**
{json.dumps(self.analysis, indent=2)}

**User Context:**
- Persona: {self.phase1_metadata.get('persona', 'Developer')}
- Pain Points: {self.phase1_metadata.get('pain_points', {})}
- Use Cases: {self.phase1_metadata.get('use_cases', [])}

**Project Structure Summary:**
- Total Files: {self.analysis['total_files']}
- Entry Points: {self.analysis['entry_points']}
- File Roles: {self.analysis['file_roles']}

Create a README that includes:
1. Project title and description
2. Features and capabilities (inferred from code analysis)
3. Installation instructions
4. Usage examples
5. Project structure overview
6. Contributing guidelines
7. License information

Make it professional, clear, and tailored to the user's persona and project type.
Output only the README content in Markdown format.
"""
        
        try:
            response = CLIENT.models.generate_content(model=MODEL, contents=prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ AI README generation failed: {e}")
            return self._fallback_readme()
    
    def _generate_workflow_doc(self) -> str:
        """Generate project workflow documentation."""
        prompt = f"""
Create a detailed PROJECT_WORKFLOW.md document explaining how this Python project works.

**Project Analysis:**
{json.dumps(self.analysis, indent=2)}

Include:
1. Project architecture overview
2. File organization and responsibilities  
3. Data flow and dependencies
4. Entry points and how to run the project
5. Key classes and functions
6. Development workflow
7. Testing approach

Make it technical but accessible for developers joining the project.
Output only the workflow document in Markdown format.
"""
        
        try:
            response = CLIENT.models.generate_content(model=MODEL, contents=prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Workflow generation failed: {e}")
            return self._fallback_workflow()
    
    def _fallback_readme(self) -> str:
        """Fallback README template."""
        project_name = self.project_root.name
        return f'''# {project_name}

## Description
This project was automatically restructured and documented using an AI agent.

## Installation
pip install -r requirements.txt

text

## Usage
python main.py

text

## Project Structure
{self._generate_tree_structure()}

text

## Features
- Auto-generated project structure
- Comprehensive documentation
- Clean code organization

## Contributing
Contributions are welcome! Please follow standard Python conventions.

## License
This project is licensed under the MIT License.
'''
    
    def _fallback_workflow(self) -> str:
        """Fallback workflow documentation."""
        return f'''# Project Workflow

## Overview
This document describes the workflow and architecture of the project.

## Entry Points
{chr(10).join(f"- {ep}" for ep in self.analysis['entry_points']) or "- main.py"}

## Project Structure
The project follows a standard Python structure with clear separation of concerns.

## Development Workflow
1. Make changes to source files
2. Run tests (if available)
3. Update documentation as needed
4. Commit and push changes

## Dependencies
See requirements.txt for project dependencies.
'''
    
    def _generate_tree_structure(self) -> str:
        """Generate ASCII tree of project structure."""
        lines = []
        for root, dirs, files in os.walk(self.project_root):
            level = root.replace(str(self.project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            lines.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                lines.append(f"{subindent}{file}")
        return '\n'.join(lines[:20])  # Limit to first 20 lines
    
    def _write_readme(self, content: str):
        """Write README.md file."""
        readme_path = self.project_root / 'README.md'
        readme_path.write_text(content, encoding='utf-8')
        print(f"Created: README.md")
    
    def _write_workflow_doc(self, content: str):
        """Write PROJECT_WORKFLOW.md file."""
        workflow_path = self.project_root / 'PROJECT_WORKFLOW.md'
        workflow_path.write_text(content, encoding='utf-8')
        print(f"Created: PROJECT_WORKFLOW.md")

# -----------------------------------------------------------------------------
# 4. Smoke Test Suite
# -----------------------------------------------------------------------------
class SmokeTestSuite:
    def __init__(self, project_root: Path, analysis: Dict):
        self.project_root = project_root
        self.analysis = analysis
        
    def run_smoke_tests(self) -> Tuple[bool, List[str]]:
        """Run basic smoke tests on the restructured project."""
        print("🧪 Running smoke tests...")
        
        issues = []
        
        # Test 1: All Python files can be imported
        issues.extend(self._test_import_syntax())
        
        # Test 2: Entry points are executable
        issues.extend(self._test_entry_points())
        
        # Test 3: Required files exist
        issues.extend(self._test_required_files())
        
        success = len(issues) == 0
        print(f"{'✅' if success else '⚠️'} Smoke tests {'passed' if success else 'completed with issues'}")
        
        return success, issues
    
    def _test_import_syntax(self) -> List[str]:
        """Test that all Python files have valid syntax."""
        issues = []
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                issues.append(f"Syntax error in {py_file.relative_to(self.project_root)}: {e}")
        return issues
    
    def _test_entry_points(self) -> List[str]:
        """Test that entry points can be executed."""
        issues = []
        for entry_point in self.analysis['entry_points']:
            entry_path = self.project_root / entry_point
            try:
                result = subprocess.run([
                    sys.executable, str(entry_path)
                ], capture_output=True, text=True, timeout=10, cwd=self.project_root)
                if result.returncode != 0:
                    issues.append(f"Entry point {entry_point} failed with return code {result.returncode}")
            except Exception as e:
                issues.append(f"Could not execute {entry_point}: {e}")
        return issues
    
    def _test_required_files(self) -> List[str]:
        """Test that required files exist."""
        issues = []
        required_files = ['README.md', 'requirements.txt']
        
        for req_file in required_files:
            if not (self.project_root / req_file).exists():
                issues.append(f"Missing required file: {req_file}")
                
        return issues

# -----------------------------------------------------------------------------
# 5. Main Phase 3 Execution
# -----------------------------------------------------------------------------

def execute_phase3() -> bool:
    """
    Executes the core logic of Phase 3.
    This function is designed to be called from an orchestrator.
    Returns True on success, False on failure.
    """
    print(f"🚀 AI Structure Agent Phase 3: Documentation & File Generation v{AGENT_VERSION}")
    
    if not CLIENT:
        print("❌ GOOGLE_API_KEY environment variable is not set.")
        return False

    # Check if Phase 2 output exists
    if not PHASE2_OUTPUT_ROOT.exists():
        print(f"❌ Phase 2 output not found at {PHASE2_OUTPUT_ROOT}. Please run Phase 2 first.")
        return False
    
    # Load Phase 1 metadata for context
    phase1_metadata = {}
    if PHASE1_METADATA_JSON.exists():
        try:
            phase1_data = json.loads(PHASE1_METADATA_JSON.read_text(encoding="utf-8"))
            phase1_metadata = phase1_data.get("metadata", {})
        except Exception as e:
            print(f"⚠️ Could not load Phase 1 metadata: {e}")
    
    print(f"📁 Analyzing structured project at: {PHASE2_OUTPUT_ROOT}")
    
    # Step 1: Comprehensive code analysis
    analyzer = CodeAnalyzer(PHASE2_OUTPUT_ROOT)
    analysis = analyzer.analyze_project()
    
    print(f"📊 Analysis complete:")
    print(f"   - {analysis['total_files']} Python files analyzed")
    print(f"   - {len(analysis['entry_points'])} entry points found")
    print(f"   - {analysis['total_classes']} classes, {analysis['total_functions']} functions")
    
    # Step 2: Generate missing files
    file_generator = MissingFileGenerator(PHASE2_OUTPUT_ROOT, analysis)
    file_generator.generate_missing_files()
    
    # Step 3: Generate comprehensive documentation
    doc_agent = DocumentationAgent(PHASE2_OUTPUT_ROOT, analysis, phase1_metadata)
    doc_agent.generate_documentation()
    
    # Step 4: Run smoke tests
    test_suite = SmokeTestSuite(PHASE2_OUTPUT_ROOT, analysis)
    success, issues = test_suite.run_smoke_tests()
    
    if issues:
        print("\n⚠️ Issues detected:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Step 5: Final summary
    print(f"\n✅ Phase 3 complete! Your project is now fully documented and ready to use.")
    print(f"📁 Enhanced project available at: {PHASE2_OUTPUT_ROOT.resolve()}")
    print("\nGenerated files:")
    print("   - README.md (Professional project documentation)")
    print("   - PROJECT_WORKFLOW.md (Technical workflow guide)")  
    print("   - __init__.py files (Package initialization)")
    print("   - main.py (Entry point, if needed)")
    print("   - setup.py (Package setup)")
    print("   - .gitignore (Git ignore rules)")
    
    return True # Signal success


def main():
    """
    Handles command-line execution for standalone use.
    """
    success = execute_phase3()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()