import sys
import argparse
import json
from pathlib import Path

# Import the core logic functions directly from your refactored scripts
from phase1_samv2 import execute_phase1
from phase2_samv2 import execute_phase2
from phase3_samv1 import execute_phase3

# Define custom error codes for better error handling
EXIT_CODE_PHASE_1_FAILED = 2
EXIT_CODE_PHASE_2_FAILED = 3
EXIT_CODE_PHASE_3_FAILED = 4
EXIT_CODE_GENERAL_ERROR = 1

def log_progress(phase, status, message):
    """Prints a structured JSON log for the VS Code extension to parse."""
    log_entry = {"type": "progress", "phase": phase, "status": status, "message": message}
    print(json.dumps(log_entry), flush=True)

def main():
    """
    Main orchestrator for the AI Refactoring Agent.
    This script gathers all initial inputs from command-line arguments and runs
    the three phases in sequence for a clean, automated workflow.
    """
    parser = argparse.ArgumentParser(
        description="AI Project Refactoring Agent Orchestrator",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--project-path", required=True, type=str, help="Path to the unstructured project folder.")
    parser.add_argument("--persona", required=True, type=str, choices=["Developer", "Data Scientist", "Researcher", "Student"], help="Your user persona.")
    parser.add_argument("--pain-points", required=True, type=str, help="Comma-separated list of problems you face.\n(e.g., 'messy imports,no tests')")
    parser.add_argument("--use-cases", required=True, type=str, help="Comma-separated list of what you want the agent to do.\n(e.g., 'create src folder,add docs')")
    parser.add_argument("--success-metrics", type=str, default="A functional, easy-to-navigate project structure.", help="How you will measure success.")
    
    args = parser.parse_args()
    
    log_progress(0, "Initializing", "Starting the refactoring process...")
    print("-" * 50)

    # --- Phase 1: Discovery & Strategy ---
    try:
        log_progress(1, "Running", "Discovery & Strategy...")
        
        pain_points = [p.strip() for p in args.pain_points.split(',') if p.strip()]
        use_cases = [u.strip() for u in args.use_cases.split(',') if u.strip()]

        phase1_success = execute_phase1(
            project_path=args.project_path,
            persona=args.persona,
            pain_points=pain_points,
            use_cases=use_cases,
            success_metrics=args.success_metrics
        )
        
        if not phase1_success:
            raise RuntimeError("Phase 1 failed to execute.")
        
        log_progress(1, "Success", "Discovery & Strategy complete.")

    except Exception as e:
        log_progress(1, "Error", f"Phase 1 failed: {str(e)}")
        print(f"ERROR during Phase 1: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE_PHASE_1_FAILED)
        
    # --- Phase 2: Execution & Refactoring ---
    try:
        log_progress(2, "Running", "Execution & Refactoring...")
        
        phase2_success = execute_phase2(auto_confirm=True)
        
        if not phase2_success:
            raise RuntimeError("Phase 2 failed to execute.")

        log_progress(2, "Success", "Execution & Refactoring complete.")

    except Exception as e:
        log_progress(2, "Error", f"Phase 2 failed: {str(e)}")
        print(f"ERROR during Phase 2: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE_PHASE_2_FAILED)

    # --- Phase 3: Documentation & Verification ---
    try:
        log_progress(3, "Running", "Documentation & Verification...")
        
        phase3_success = execute_phase3()

        if not phase3_success:
            raise RuntimeError("Phase 3 failed to execute.")
            
        log_progress(3, "Success", "Documentation & Verification complete.")

    except Exception as e:
        log_progress(3, "Error", f"Phase 3 failed: {str(e)}")
        print(f"ERROR during Phase 3: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE_PHASE_3_FAILED)
        
    print("-" * 50)
    final_project_path = Path("./structured_project").resolve()
    log_progress(0, "Complete", f"Agent finished successfully! Your new project is ready at: {final_project_path}")

if __name__ == "__main__":
    main()