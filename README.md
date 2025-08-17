# 🤖 AI Project Refactorer

**Transform your messy Python projects into well-structured, maintainable codebases with the power of AI.**

![AI Project Refactorer Demo](demo.gif)
*Record a GIF showing the extension in action - from opening the command palette to seeing the refactored project structure*

---

## ✨ Features

* 🤖 **AI-powered project restructuring** based on user persona and requirements
* 📝 **Automated generation** of `README.md` and project workflow documents
* 🔧 **Intelligent refactoring** of Python imports to prevent code breakage
* ⚙️ **Automated creation** of `.gitignore`, `requirements.txt`, and other boilerplate files
* 🎯 **Persona-driven approach** - customized for Developers, Data Scientists, Researchers, and Students
* 📊 **Real-time progress tracking** with detailed output logs
* 🚀 **One-click solution** for project organization and structure improvement

---

## 🔧 Requirements

* **VS Code** version 1.85 or newer
* **Python** 3.8 or newer installed on your system
* **Google Generative AI API Key** (free from Google AI Studio)

---

## ⚡ Extension Setup

### Step 1: Install the Extension
1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for "AI Project Refactorer"
4. Click **Install**

### Step 2: Get Your API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated API key

### Step 3: Configure the Extension
1. In VS Code, open Settings (`Ctrl+,`)
2. Search for **"AI Project Refactorer"**
3. Paste your API key into the **`Google Api Key`** field
4. *(Optional)* If your Python command is not `python`, update the **`Python Path`** setting with the correct path to your executable

---

## 🚀 How to Use

### Quick Start Guide

1. **Open your project** - Open the unstructured Python project folder you want to refactor in VS Code

2. **Launch the agent** - Open the Command Palette (`Ctrl+Shift+P`) and run:
   ```
   AI Agent: Start New Project Refactoring
   ```

3. **Fill out the form** - A beautiful interface will open where you can:
   - Select your persona (Developer, Data Scientist, Researcher, Student)
   - Describe your pain points (default: "Messy code structure, no clear organization, missing documentation")
   - Define your goals (default: "Create src folder, add README, organize tests, improve code structure")
   - Set success metrics (default: "Better code maintainability, improved test coverage, clear project structure")

4. **Start the magic** - Click **"✨ Start AI Agent"** and watch the transformation begin

5. **Monitor progress** - Check the **"AI Agent"** Output Channel to see detailed logs of what's happening

### What the AI Agent Does

- 🔍 **Analyzes** your current project structure
- 📁 **Creates** proper folder organization (`src/`, `tests/`, `docs/`)
- 📄 **Generates** comprehensive documentation
- 🔧 **Refactors** code imports and dependencies
- 🧹 **Cleans up** redundant files and code
- ✅ **Validates** the new structure works correctly

---

## 📸 Screenshots

### Beautiful Modern Interface
The extension features a sleek, modern interface that adapts to your VS Code theme:

![Extension Interface](interface-screenshot.png)

### Real-Time Progress Tracking
Watch your project transform with live updates:

![Progress Tracking](progress-screenshot.png)

---

## 🎯 Use Cases

### For Developers
- **Legacy code modernization** - Transform old Python scripts into modern, maintainable applications
- **Project standardization** - Apply consistent structure across team projects
- **Documentation generation** - Automatically create comprehensive README files and code documentation

### For Data Scientists
- **Notebook organization** - Convert Jupyter notebooks into structured Python packages
- **Experiment tracking** - Create proper folder structures for data, models, and results
- **Reproducibility** - Generate requirements files and environment setup scripts

### For Researchers
- **Academic project structure** - Organize research code following best practices
- **Collaboration ready** - Make projects easy for others to understand and contribute to
- **Publication preparation** - Structure code for sharing with papers and repositories

### For Students
- **Assignment organization** - Transform homework scripts into professional-looking projects
- **Portfolio building** - Create impressive GitHub repositories from coursework
- **Learning best practices** - Understand proper Python project structure through AI guidance

---

## 🔧 Troubleshooting

### Common Issues

**❌ "Failed to set up Python environment"**
- Ensure Python 3.8+ is installed and accessible via command line
- Check that `python` command works in your terminal
- Update the Python Path setting if using a custom Python installation

**❌ "Google API Key not configured"**
- Verify your API key is correctly pasted in VS Code settings
- Ensure the API key is active in Google AI Studio
- Check for any extra spaces in the key

**❌ "Agent process exited with error"**
- Check the "AI Agent" Output Channel for detailed error messages
- Ensure you have write permissions in the project folder
- Verify all required Python packages are installed

### Getting Help

- 📖 Check the [Documentation](https://github.com/your-username/ai-project-refactorer/wiki)
- 🐛 Report issues on [GitHub Issues](https://github.com/your-username/ai-project-refactorer/issues)
- 💬 Ask questions in [Discussions](https://github.com/your-username/ai-project-refactorer/discussions)

---

## 🎨 Customization

The AI agent adapts its approach based on your selected persona:

| Persona | Focus Areas | Output Style |
|---------|-------------|--------------|
| 👨‍💻 **Developer** | Clean architecture, maintainable code, testing | Professional development standards |
| 📊 **Data Scientist** | Data pipelines, experiment tracking, reproducibility | Research-oriented structure |
| 🔬 **Researcher** | Documentation, collaboration, academic standards | Publication-ready organization |
| 🎓 **Student** | Learning-focused, best practices, portfolio building | Educational and clear structure |

---

## 📈 What's Next?

### Upcoming Features
- 🌐 **Multi-language support** (JavaScript, TypeScript, Java)
- 🔄 **Incremental updates** - Update existing structured projects
- 📋 **Custom templates** - Save and reuse your preferred project structures
- 🤝 **Team collaboration** - Share refactoring configurations across teams

### Roadmap
- **v1.1.0** - JavaScript/TypeScript support
- **v1.2.0** - Custom template system
- **v1.3.0** - Team configuration sharing

---

## 📜 License

MIT License - feel free to use this extension in your projects!

---

## 🙏 Contributing

We love contributions! Whether it's:
- 🐛 Bug reports
- 💡 Feature requests  
- 📝 Documentation improvements
- 🔧 Code contributions

Check out our [Contributing Guidelines](CONTRIBUTING.md) to get started.

---

## ⭐ Show Your Support

If this extension helped you organize your projects, please:
- ⭐ Star the repository
- 📝 Leave a review in the VS Code Marketplace
- 🗣️ Share it with your fellow developers

---

<div align="center">

**Made with ❤️ by developers, for developers**

*Transform your chaotic code into beautiful, maintainable projects with just a few clicks!*

</div>