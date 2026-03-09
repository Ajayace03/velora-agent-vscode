# Velora AI Agent

**An intelligent VS Code extension that transforms messy Python projects into well-structured, maintainable codebases using the power of Google Gemini AI.**

[![VS Code Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue?logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=cryptarchs.velora)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)]()

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [What the Agent Does](#what-the-agent-does)
- [Persona Guide](#persona-guide)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

Velora AI Agent is a VS Code extension designed to automatically analyze, restructure, and document Python projects. Whether you're a developer dealing with legacy code, a data scientist organizing experiment scripts, or a student building a portfolio — Velora does the heavy lifting for you.

It uses **Google Gemini AI** to intelligently propose a clean project structure tailored to your persona, refactors all Python imports to match the new layout (so nothing breaks), and generates professional documentation — all in one click.

---

## Features

- **AI-Powered Restructuring** — Gemini AI analyzes your project and proposes an optimal folder structure based on your role and goals.
- **Intelligent Import Refactoring** — Uses LibCST to rewrite all Python imports so your code works correctly in the new structure.
- **Automated Documentation** — Generates a professional `README.md` and `PROJECT_WORKFLOW.md` tailored to your project.
- **Missing File Generation** — Auto-creates `__init__.py`, `.gitignore`, `setup.py`, and `main.py` where needed.
- **Persona-Driven Approach** — Customized for Developers, Data Scientists, Researchers, and Students.
- **Real-Time Progress Tracking** — Live output in the VS Code Output Channel so you can monitor every step.
- **Cancellation Support** — Cancel the agent at any time from the progress notification.
- **Smoke Testing** — Validates the restructured project by checking syntax and entry points.
- **Requirements Management** — Auto-generates and cleans `requirements.txt` for the new project.

---

## How It Works

Velora runs a **3-phase AI agent pipeline**:

```
Phase 1: Discovery & Strategy
    ↓ Analyzes project files, dependencies, git status, environment
    ↓ Uses AI to generate an executive summary and strategy

Phase 2: Execution & Refactoring
    ↓ AI proposes file-to-folder mapping
    ↓ Refactors Python imports using LibCST
    ↓ Moves files to the new structure
    ↓ Generates requirements.txt

Phase 3: Documentation & Verification
    ↓ AST-based code analysis (classes, functions, entry points)
    ↓ Generates README.md and PROJECT_WORKFLOW.md via AI
    ↓ Creates missing files (__init__.py, .gitignore, setup.py)
    ↓ Runs smoke tests to validate the result
```

The restructured project is saved in a `structured_project/` folder inside your workspace — **your original files are never modified**.

---

## Requirements

| Requirement | Minimum Version |
|-------------|----------------|
| **VS Code** | 1.85 or newer |
| **Python** | 3.8 or newer |
| **Google Gemini API Key** | Free from [Google AI Studio](https://aistudio.google.com/apikey) |

> **Note:** The extension automatically creates a Python virtual environment and installs all required Python dependencies. You do not need to install anything manually.

---

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to **Extensions** (`Ctrl+Shift+X`)
3. Search for **"Velora-Agent"**
4. Click **Install**

### From VSIX File (Manual Install)

1. Download the `.vsix` file from the [Releases](https://github.com/Ajayace03/velora-agent-vscode/releases) page
2. Open VS Code
3. Go to **Extensions** (`Ctrl+Shift+X`)
4. Click the **`...`** menu (top-right) → **Install from VSIX...**
5. Select the downloaded `.vsix` file

---

## Configuration

### Step 1: Get Your Google API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated API key

### Step 2: Configure the Extension

1. Open VS Code **Settings** (`Ctrl+,`)
2. Search for **"AI Project Refactorer"**
3. Paste your API key into the **"Google Api Key"** field
4. *(Optional)* If your Python command is not `python`, update the **"Python Path"** field with the full path to your Python executable (e.g., `C:\Python313\python.exe` or `/usr/bin/python3`)

| Setting | Description | Default |
|---------|-------------|---------|
| `ai-project-refactorer.googleApiKey` | Your Google Gemini API key | *(empty)* |
| `ai-project-refactorer.pythonPath` | Path to Python executable | `python` |

---

## Usage Guide

### Step-by-Step

1. **Open your project** — Open the Python project folder you want to refactor in VS Code.

2. **Launch the agent** — Open the Command Palette (`Ctrl+Shift+P`) and run:
   ```
   AI Agent: Start New Project Refactoring
   ```

3. **Fill out the form** — A modern interface will open where you can:
   - **Select your persona** — Developer, Data Scientist, Researcher, or Student
   - **Describe your pain points** — What problems are you facing?
   - **Define your goals** — What do you want the agent to accomplish?
   - **Set success metrics** — How will you measure if it worked?

4. **Start the agent** — Click **"Start AI Agent"** and watch the transformation begin.

5. **Monitor progress** — Check the **"AI Agent"** Output Channel (bottom panel → dropdown → select "AI Agent") for detailed real-time logs.

6. **Review the output** — Your restructured project will be in the `structured_project/` folder inside your workspace.

### Keyboard Shortcut

You can press **`Ctrl+Enter`** (or **`Cmd+Enter`** on macOS) inside the form to start the agent without clicking the button.

### Cancelling the Agent

If need to stop the agent mid-run, click the **Cancel** button on the progress notification in the bottom-right corner of VS Code.

---

## What the Agent Does

### Phase 1: Discovery & Strategy
- Scans the project directory and creates a file fingerprint (counts by type)
- Detects git status, branch, and remote information
- Parses existing dependency files (`requirements.txt`, `pyproject.toml`)
- Uses AI to cluster and analyze your pain points
- Generates an executive summary for the refactoring plan
- Checks feasibility (internet connectivity, disk space)

### Phase 2: Execution & Refactoring
- Categorizes all files (Python, Data, Config, Docs, Tests, etc.)
- Sends the file list to Gemini AI with persona-specific instructions
- Validates the AI response against a JSON schema
- Creates a temporary copy of your project (safety first)
- **Rewrites all relative Python imports** using LibCST so nothing breaks
- Moves files to the new structure
- Generates and cleans `requirements.txt`
- Saves a detailed refactoring report

### Phase 3: Documentation & Verification
- Performs deep AST-based code analysis (functions, classes, imports, entry points)
- Builds an internal dependency graph
- Generates `__init__.py` files with contextual imports
- Creates `main.py` if no entry point exists
- Generates `.gitignore` and `setup.py`
- Uses AI to generate a professional `README.md`
- Uses AI to generate a `PROJECT_WORKFLOW.md`
- Runs smoke tests (syntax check + entry point execution)

---

## Persona Guide

The AI adapts its restructuring approach based on your selected persona:

| Persona | Focus | Structure Style |
|---------|-------|-----------------|
| **Developer** | Clean architecture, maintainability, testing | `src/` with sub-packages (`api`, `core`, `utils`), `tests/`, `docs/` |
| **Data Scientist** | Reproducibility, experiment tracking | `data/` (raw/processed), `notebooks/`, `src/`, `models/`, `reports/` |
| **Researcher** | Publication readiness, collaboration | `experiments/`, `src/`, `data/`, `results/`, `docs/` |
| **Student** | Simplicity, clarity, learning | Flat `src/` or `source/`, `data/`, minimal nesting |

---

## Troubleshooting

### "Google API Key not configured"
- Open **Settings** (`Ctrl+,`) → search "AI Project Refactorer" → paste your key
- Make sure there are no extra spaces in the key
- Verify the key is active at [Google AI Studio](https://aistudio.google.com/apikey)

### "Failed to set up Python environment"
- Ensure Python 3.8+ is installed: run `python --version` in your terminal
- If using a non-standard Python path, update the **Python Path** setting
- On Windows, you may need to install the `venv` module: `pip install virtualenv`

### "Agent process exited with error code 2/3/4"
- **Code 2** — Phase 1 (Discovery) failed. Check if your API key is valid.
- **Code 3** — Phase 2 (Refactoring) failed. Check the output panel for AI response issues.
- **Code 4** — Phase 3 (Documentation) failed. Usually a non-critical AI call failure.()

### Smoke test warnings
- Entry points failing with return code 2 during smoke tests is **normal** if those scripts require external resources (databases, APIs, credentials) that aren't available during testing.

### "pipreqs failed" / "pip-chill failed"
- This is a non-critical warning. The existing `requirements.txt` from your project is still preserved and cleaned.

---

## Roadmap

| Version | Planned Feature |
|---------|----------------|
| v1.1.0 | JavaScript / TypeScript project support |
| v1.2.0 | Custom template system for project structures |
| v1.3.0 | Team configuration sharing |
| v2.0.0 | Incremental updates for already-structured projects |

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork locally
3. **Install dependencies**: `npm install`
4. **Make changes** in the `src/` (TypeScript) or `agent/` (Python) directories
5. **Compile**: `npm run compile`
6. **Test**: Press `F5` in VS Code to launch the Extension Development Host
7. **Submit** a Pull Request

### Development Setup

```bash
# Clone the repo
git clone https://github.com/Ajayace03/velora-agent-vscode.git
cd velora-agent-vscode

# Install Node.js dependencies
npm install

# Compile TypeScript
npm run compile

# Watch for changes (auto-recompile)
npm run watch

# Launch extension in dev mode
# Press F5 in VS Code
```

### Project Structure

```
velora/
├── src/
│   └── extension.ts          # VS Code extension entry point
├── agent/
│   ├── run_agent.py           # Orchestrator (runs all 3 phases)
│   ├── phase1_samv2.py        # Phase 1: Discovery & Strategy
│   ├── phase2_samv2.py        # Phase 2: Execution & Refactoring
│   ├── phase3_samv1.py        # Phase 3: Documentation & Verification
│   └── requirements.txt       # Python dependencies
├── images/
│   └── icon.png               # Extension icon
├── package.json               # Extension manifest
├── tsconfig.json              # TypeScript configuration
└── README.md                  # This file
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Ajay Bharathi A**

| | |
|---|---|
| **Email** | [ajayak0304@gmail.com](mailto:ajayak0304@gmail.com) |
| **GitHub** | [github.com/Ajayace03](https://github.com/Ajayace03) |
| **LinkedIn** | [linkedin.com/in/ajay-bharathi](https://linkedin.com/in/ajay-bharathi) |
| **Publisher** | Cryptarchs |

---

<div align="center">

**Made with dedication by Ajay Bharathi A**

*Transform your chaotic Python code into beautiful, maintainable projects with just a few clicks.*

</div>