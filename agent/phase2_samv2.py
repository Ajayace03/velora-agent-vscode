# -----------------------------------------------------------------------------
# Phase 2: AI Struct Agent - Full Refactor v1.0.0
# -----------------------------------------------------------------------------
# This module implements the second phase of the AI Struct Agent, focusing on
# refactoring a messy project structure based on AI-generated recommendations.
# It includes enhanced file discovery, import refactoring using LibCST, and
# structured output generation.
# -----------------------------------------------------------------------------
import argparse
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import re
from google import genai
import jsonschema
import libcst as cst

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
AGENT_VERSION = "1.0.0"
API_KEY = os.getenv("GOOGLE_API_KEY")
CLIENT = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL = "gemini-2.5-flash"
PHASE1_METADATA_JSON = Path("phase1_metadata.json")
OUTPUT_ROOT = Path("./structured_project")

# Schema for AI output: a direct source -> destination mapping
STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "file_mapping": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "string"}},
            "description": "A dictionary mapping original file paths to new file paths."
        },
        "placement_reasons": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "string"}},
            "description": "A dictionary mapping new file paths to the reason for their placement."
        }
    },
    "required": ["file_mapping", "placement_reasons"]
}

# -----------------------------------------------------------------------------
# 1. Enhanced File Discovery
# -----------------------------------------------------------------------------
def discover_and_categorize_files(root: Path):
    """Discovers all files in the project root and categorizes them by type."""
    categories = {
        "Python": [".py"], "Notebook": [".ipynb"], "Data": [".csv", ".json", ".parquet", ".db", ".sqlite3"],
        "Config": [".yaml", ".yml", ".toml", ".ini", ".env", "requirements.txt"], "Web": [".html", ".css", ".js"],
        "Docs": [".md", ".rst"], "Container": ["Dockerfile"], "Tests": [], "Other": []
    }
    file_list = {}
    
    ext_map = {ext: key for key, ext_list in categories.items() for ext in ext_list}
    
    for p in root.rglob("*"):
        # Ignore directories and common VCS/tooling folders
        if p.is_dir() or any(part in p.parts for part in ['.git', '__pycache__', '.venv']):
            continue
        
        rel_path = p.relative_to(root).as_posix()
        
        # Heuristic for test files
        if "test" in p.name.lower() and p.suffix == ".py":
            category = "Tests"
        elif p.name in categories["Container"]:
            category = "Container"
        else:
            category = ext_map.get(p.suffix, "Other")
        
        file_list.setdefault(category, []).append(rel_path)
        
    return file_list

# -----------------------------------------------------------------------------
# 2. LibCST Code Refactoring Engine (CRITICAL COMPONENT)
# -----------------------------------------------------------------------------
class ImportRefactorTransformer(cst.CSTTransformer):
    """
    A LibCST transformer that rewrites relative import statements based on a file move mapping.
    This is the core logic that prevents the restructured project from breaking.
    """
    def __init__(self, current_file_rel_path: str, file_mapping: dict, project_root: Path):
        self.current_file_rel_path = current_file_rel_path
        self.file_mapping = file_mapping
        self.project_root = project_root

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        # We only care about relative imports (e.g., `from . import foo`)
        if not original_node.relative:
            return updated_node

        try:
            # 1. Resolve the absolute path of the module being imported
            level = len(original_node.relative)
            source_dir = (self.project_root / self.current_file_rel_path).parent
            
            # Go up the directory tree based on the number of dots
            imported_module_base_path = source_dir.resolve()
            for _ in range(level - 1):
                imported_module_base_path = imported_module_base_path.parent

            # Append the module name if it exists (e.g., `utils` in `from .utils import`)
            if original_node.module:
                module_name_parts = original_node.module.value.split('.')
                imported_module_path = imported_module_base_path.joinpath(*module_name_parts)
            else:
                imported_module_path = imported_module_base_path

            # Find its corresponding .py file or package directory
            original_target_path = None
            if (imported_module_path.with_suffix(".py")).is_file():
                original_target_path = imported_module_path.with_suffix(".py")
            elif (imported_module_path / "__init__.py").is_file():
                original_target_path = imported_module_path / "__init__.py"
            else:
                return updated_node # Cannot resolve, leave it as is

            original_target_rel_path = original_target_path.relative_to(self.project_root).as_posix()

            # 2. Find the new locations of the current file and the imported file
            new_current_file_path = self.project_root / self.file_mapping[self.current_file_rel_path]
            new_target_file_path = self.project_root / self.file_mapping[original_target_rel_path]
            
            # 3. Calculate the new relative path from the new current file to the new target file
            new_relative_path = os.path.relpath(
                new_target_file_path.parent, 
                new_current_file_path.parent
            )
            
            # 4. Reconstruct the import statement with the new relative path
            if new_relative_path == '.':
                dots = 1
                new_module_parts = []
            else:
                path_parts = new_relative_path.split(os.sep)
                dots = path_parts.count('..') + 1
                new_module_parts = [p for p in path_parts if p != '..']

            if original_node.module:
                original_module_name = original_node.module.value.split('.')[-1]
                new_module_parts.append(original_module_name)

            new_module_str = ".".join(new_module_parts) if new_module_parts else None

            return updated_node.with_changes(
                relative=[cst.Dot() for _ in range(dots)],
                module=cst.Name(value=new_module_str) if new_module_str else None
            )
        except Exception:
            return updated_node # If any step fails, don't modify the import to be safe

def refactor_imports_in_project(project_copy_root: Path, file_mapping: dict):
    """
    Iterates through all Python files in the temporary project copy and refactors their
    imports in-place before they are moved.
    """
    for src_rel_path in file_mapping.keys():
        if not src_rel_path.endswith(".py"):
            continue
        
        file_abs_path = project_copy_root / src_rel_path
        try:
            source_code = file_abs_path.read_text(encoding="utf-8")
            tree = cst.parse_module(source_code)
            transformer = ImportRefactorTransformer(src_rel_path, file_mapping, project_copy_root)
            modified_tree = tree.visit(transformer)
            file_abs_path.write_text(modified_tree.code, encoding="utf-8")
        except Exception as e:
            print(f"⚠️ Could not parse or refactor {src_rel_path}: {e}")

# -----------------------------------------------------------------------------
# 3. AI Interaction, File Operations, and Reporting
# -----------------------------------------------------------------------------
def generate_ai_structure(file_categories, persona):
    """Generates the AI prompt and calls the LLM to get the file mapping."""
    
    # --- NEW: More detailed and structured persona instructions ---
    persona_instructions = {
        "Developer": """
- **Primary Goal**: Create a maintainable, scalable application structure.
- **Source Code**: Place all application source code inside a `src/` directory. Inside `src/`, create sub-packages for different concerns (e.g., `api`, `core`, `utils`).
- **Testing**: Create a top-level `tests/` directory that mirrors the structure of `src/`.
- **Configuration**: Keep configuration files (`.toml`, `.yaml`, `.env`) at the project root.
- **Deployment**: Place `Dockerfile` and CI/CD files (e.g., `.github/workflows`) at the project root.
- **Documentation**: A `docs/` folder for detailed documentation and a primary `README.md` at the root.
""",
        "Data Scientist": """
- **Primary Goal**: Ensure reproducibility and clear separation between data, code, and experiments.
- **Data**: Create a `data/` directory with subfolders for different stages (e.g., `raw`, `processed`, `final`).
- **Notebooks**: Place all Jupyter notebooks for exploration and analysis in a top-level `notebooks/` directory.
- **Source Code**: Reusable Python code (for data processing, feature engineering, modeling) should go into a `src/` directory.
- **Scripts**: One-off scripts for training models or running pipelines should be in `scripts/`.
- **Models**: Saved/serialized models should be placed in a `models/` directory.
- **Reports**: Generated outputs like plots and summary files should go in `reports/`.
""",
        "Researcher": """
- **Primary Goal**: Organize work around experiments, data, and findings for publication.
- **Experiments**: Core runnable scripts should be in an `experiments/` or `scripts/` directory.
- **Source Code**: Place shared, reusable algorithms and utility functions in a `src/` directory.
- **Data**: A `data/` directory is essential, with subfolders for raw and processed data.
- **Results**: Store all outputs (plots, tables, figures) in a `results/` directory, perhaps with subfolders per experiment.
- **Documentation**: A `docs/` or `papers/` directory is crucial for notes, literature, and manuscript drafts.
""",
        "Student": """
- **Primary Goal**: Create a simple, clear, and easy-to-navigate structure. Avoid excessive complexity.
- **Source Code**: Place main scripts in a `src/` or `source/` folder. A single `main.py` or `app.py` at the root is also acceptable if the project is small.
- **Data/Assets**: All data files, images, or other assets should be in a single `data/` or `assets/` folder.
- **Simplicity**: Prefer a flatter structure. Avoid nesting directories more than one or two levels deep.
- **Clarity**: Use simple, self-explanatory folder names.
"""
    }

    prompt = f"""
You are an expert AI software architect tasked with refactoring a messy project. Your goal is to propose a clean, professional folder structure.

**User Persona:** {persona}
**Persona Guidance:** {persona_instructions.get(persona, persona_instructions['Developer'])}

**Project Files:**
```json
{json.dumps(file_categories, indent=2)}
```

**Your Task:**
Create a JSON object that maps every single original file path to a new, structured destination path.

**Output Format Rules:**
1.  The output must be a single JSON object compliant with the provided JSON schema.
2.  The JSON object must have a key "file_mapping" which is a dictionary mapping `source_path` -> `destination_path`.
3.  The JSON object must also have a key "placement_reasons" which is a dictionary mapping `destination_path` -> `reasoning`.
4.  Every file from the input list MUST be a key in the "file_mapping" dictionary. Do not omit any files.

Strictly output JSON only.
"""
    try:
        response = CLIENT.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.2}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        return None

def generate_requirements(project_path="structured_project", output_path="requirements.txt"):
    """
    Try pipreqs first (based on imports in code).
    If it fails, fall back to pip-chill (environment snapshot).
    """
    try:
        # Try pipreqs
        subprocess.run(
            ["pipreqs", project_path, "--force", "--encoding", "utf-8"],
            check=True
        )
        print("✅ requirements.txt generated using pipreqs")
    except Exception as e:
        print(f"⚠️ pipreqs failed: {e}")
        print("👉 Falling back to pip-chill...")
        try:
            result = subprocess.run(
                ["pip-chill"],
                capture_output=True,
                text=True,
                check=True
            )
            with open(os.path.join(project_path, output_path), "w", encoding="utf-8") as f:
                f.write(result.stdout)
            print(f"✅ requirements.txt generated using pip-chill at {project_path}/{output_path}")
        except Exception as e2:
            print(f"❌ Both pipreqs and pip-chill failed: {e2}")

def clean_requirements(req_file="structured_project/requirements.txt"):
    """
    Cleans the generated requirements.txt:
    - Normalize package names (lowercase)
    - Remove duplicates
    - Strip weird characters and spaces
    """

    if not os.path.exists(req_file):
        print(f"⚠️ No requirements.txt found at {req_file}")
        return

    with open(req_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = []
    seen = set()

    for line in lines:
        pkg = line.strip()

        # Skip empty/comment lines
        if not pkg or pkg.startswith("#"):
            continue

        # Normalize case (e.g. Flask → flask)
        pkg = re.sub(r"\s+", "", pkg).lower()

        # Remove weird fake imports if needed
        if any(fake in pkg for fake in ["my_fake_lib", "testlib", "debug"]):
            continue

        # Deduplicate
        if pkg not in seen:
            cleaned.append(pkg)
            seen.add(pkg)

    # Overwrite file
    with open(req_file, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned) + "\n")

    print(f"✅ Cleaned requirements.txt saved ({len(cleaned)} packages)")

def save_refactor_report(output_root: Path, mapping: dict, persona: str):
    """Saves JSON and Markdown reports of the refactoring."""
    report_dir = output_root / "_refactor_report"
    report_dir.mkdir(exist_ok=True)

    # Save JSON mapping
    (report_dir / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")

    # Save Markdown summary
    md_content = [f"# Refactoring Report (Persona: {persona})\n\n## File Placement Reasons\n"]
    for dest, reason in mapping.get("placement_reasons", {}).items():
        md_content.append(f"- **{dest}**: {reason}\n")
    (report_dir / "README.md").write_text("".join(md_content), encoding="utf-8")
    
    print(f"📑 Refactor report saved to {report_dir}")

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

def execute_phase2(auto_confirm: bool = False) -> bool:
    """
    Executes the core logic of Phase 2.
    Designed to be called from an orchestrator.
    Returns True on success, False on failure.
    
    Args:
        auto_confirm (bool): If True, bypasses the user confirmation prompt
                             and proceeds with the refactoring.
    """
    if not CLIENT:
        print("❌ GOOGLE_API_KEY environment variable is not set.")
        return False

    if not PHASE1_METADATA_JSON.exists():
        print(f"❌ Phase 1 output not found at {PHASE1_METADATA_JSON}. Please run Phase 1 first.")
        return False
        
    try:
        metadata = json.loads(PHASE1_METADATA_JSON.read_text(encoding="utf-8"))["metadata"]
        project_root = Path(metadata.get("project_root", "."))
        persona = metadata.get("persona", "Developer")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Failed to read or parse Phase 1 metadata: {e}")
        return False

    print(f"🤖 AI Refactoring Engine v{AGENT_VERSION}")
    print(f"Loaded Phase 1 metadata for '{persona}' on project: {project_root}")

    print("\nStep 1: Discovering and categorizing all project files...")
    file_categories = discover_and_categorize_files(project_root)
    if not any(file_categories.values()):
        print("❌ No files found in the project root to refactor.")
        return False
    
    print("\nStep 2: Asking AI architect for a new project structure...")
    ai_plan = generate_ai_structure(file_categories, persona)
    if not ai_plan:
        return False

    try:
        jsonschema.validate(instance=ai_plan, schema=STRUCTURE_SCHEMA)
        print("✅ AI plan is valid.")
    except jsonschema.ValidationError as e:
        print(f"❌ AI plan validation failed: {e.message}")
        # Optionally, save the invalid plan for debugging
        Path("phase2_invalid_plan.json").write_text(json.dumps(ai_plan, indent=2))
        return False

    file_mapping = ai_plan["file_mapping"]
    
    print("\nProposed File Structure Changes:")
    for src, dst in file_mapping.items():
        print(f"  - {src}  ->  {dst}")
    
    choice = 'n'
    if auto_confirm:
        print("\nAuto-confirming to apply the structure.")
        choice = 'y'
    else:
        choice = input("\nDo you want to apply this structure? (y/n): ").strip().lower()

    if choice != 'y':
        print("Operation aborted by user.")
        return True # Aborting is a successful exit, not a failure.

    # --- Start Refactoring Process ---
    if OUTPUT_ROOT.exists():
        print(f"⚠️ Output folder {OUTPUT_ROOT} exists. It will be cleared before proceeding.")
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(exist_ok=True)
    
    temp_project_copy = Path("temp_project_for_refactor")
    if temp_project_copy.exists(): shutil.rmtree(temp_project_copy)
    shutil.copytree(project_root, temp_project_copy, ignore=shutil.ignore_patterns('.git', '__pycache__', 'structured_project'))
    print(f"\nCreated temporary copy at '{temp_project_copy}' for safe refactoring.")

    print("\n--- Applying Changes ---")
    print("\nStep A (CRITICAL): Refactoring Python imports in the project copy...")
    refactor_imports_in_project(temp_project_copy, file_mapping)
    print("✅ Import refactoring complete.")

    print("\nStep B: Moving refactored files to the new structure...")
    for src_rel, dst_rel in file_mapping.items():
        src_abs = temp_project_copy / src_rel
        dst_abs = OUTPUT_ROOT / dst_rel
        if not src_abs.exists(): 
            print(f"⚠️ Source file not found in temp copy, skipping: {src_rel}")
            continue
        try:
            dst_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_abs), str(dst_abs))
        except Exception as e:
            print(f"❌ Error moving {src_rel} -> {dst_rel}: {e}")
    print("✅ File movement complete.")
    
    shutil.rmtree(temp_project_copy)
    print(f"Cleaned up temporary directory '{temp_project_copy}'.")

    print("\nStep C: Generating and cleaning requirements.txt for the new project...")
    generate_requirements(OUTPUT_ROOT)
    clean_requirements(str(OUTPUT_ROOT / "requirements.txt"))

    print("\nStep D: Saving refactor report...")
    save_refactor_report(OUTPUT_ROOT, ai_plan, persona)

    print(f"\n✅ Phase 2 complete! Your newly structured and functional project is ready at: {OUTPUT_ROOT.resolve()}")
    return True # Signal success


def main():
    """Handles command-line execution for standalone use."""
    # When run directly, we always want user confirmation for safety.
    # Therefore, auto_confirm is False.
    success = execute_phase2(auto_confirm=False)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()