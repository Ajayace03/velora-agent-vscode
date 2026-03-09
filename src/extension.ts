// src/extension.ts
import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';

let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {

    // Create the channel ONCE when the extension is activated
    outputChannel = vscode.window.createOutputChannel("AI Agent");

    let disposable = vscode.commands.registerCommand('ai-project-refactorer.start', () => {
        const panel = vscode.window.createWebviewPanel(
            'aiProjectRefactorer',             // viewType: unique identifier
            'AI Project Refactorer',           // title shown in the tab
            vscode.ViewColumn.One,             // showOptions: open in first column
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = getWebviewContent();

        panel.webview.onDidReceiveMessage(
            async message => {
                if (message.command === 'submit') {
                    const workspaceFolders = vscode.workspace.workspaceFolders;
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage('Please open a project folder first!');
                        return;
                    }
                    const projectPath = workspaceFolders[0].uri.fsPath;

                    // Validate API key before starting
                    const apiKey = vscode.workspace.getConfiguration('ai-project-refactorer').get<string>('googleApiKey');
                    if (!apiKey) {
                        vscode.window.showErrorMessage('Google API Key not configured. Go to Settings > AI Project Refactorer to set your key.');
                        return;
                    }

                    // Tell the UI we are starting
                    panel.webview.postMessage({ command: 'set-running-state', running: true });

                    try {
                        await vscode.window.withProgress({
                            location: vscode.ProgressLocation.Notification,
                            title: "AI Agent is running...",
                            cancellable: true // Enable cancellation
                        }, (progress, token) => {
                            // Pass the cancellation token to runAgent
                            return runAgent(context, projectPath, message.data, progress, token);
                        });
                    } catch (error) {
                        console.error("Agent run failed", error);
                        // Error messages are already shown in runAgent
                    } finally {
                        // Tell the UI we are finished, no matter what
                        panel.webview.postMessage({ command: 'set-running-state', running: false });
                    }
                }
            },
            undefined,
            context.subscriptions
        );
    });

    context.subscriptions.push(disposable);
}

// UPDATED HELPER FUNCTION TO SETUP PYTHON WITH CONFIGURABLE PATH
async function setupPythonEnvironment(context: vscode.ExtensionContext, progress: vscode.Progress<{ message?: string }>): Promise<string> {
    progress.report({ message: "Setting up Python environment..." });

    // Read the python path from settings, with 'python' as a fallback
    const config = vscode.workspace.getConfiguration('ai-project-refactorer');
    const pythonCommand = config.get<string>('pythonPath') || 'python';

    const agentPath = path.join(context.extensionPath, 'agent');
    const venvPath = path.join(agentPath, '.venv');
    const requirementsPath = path.join(agentPath, 'requirements.txt');

    // Platform-specific paths for Python executable and pip
    const isWindows = process.platform === 'win32';
    const pythonExecutable = isWindows ? path.join(venvPath, 'Scripts', 'python.exe') : path.join(venvPath, 'bin', 'python');
    const pipExecutable = isWindows ? path.join(venvPath, 'Scripts', 'pip.exe') : path.join(venvPath, 'bin', 'pip');

    // Helper function to run commands
    const runCommand = (cmd: string, args: string[]) => new Promise<void>((resolve, reject) => {
        const process = spawn(cmd, args, { cwd: agentPath });
        process.stdout.on('data', data => console.log(`stdout: ${data}`));
        process.stderr.on('data', data => console.error(`stderr: ${data}`));
        process.on('close', code => code === 0 ? resolve() : reject(new Error(`Command failed with code ${code}: ${cmd} ${args.join(' ')}`)));
    });

    try {
        // 1. Check if the virtual environment's Python exists. If not, create it.
        if (!await vscode.workspace.fs.stat(vscode.Uri.file(pythonExecutable)).then(() => true, () => false)) {
            progress.report({ message: "Creating virtual environment..." });
            // Use the configured pythonCommand instead of the hardcoded 'python'
            await runCommand(pythonCommand, ['-m', 'venv', '.venv']);
        }

        // 2. Install dependencies from requirements.txt
        progress.report({ message: "Installing dependencies..." });
        await runCommand(pipExecutable, ['install', '-r', requirementsPath]);

        progress.report({ message: "Environment is ready." });
        return pythonExecutable; // Return the full path to the venv Python
    } catch (error) {
        // Provide more specific error messages for common Python setup issues
        const errorMessage = error instanceof Error ? error.message : String(error);

        let userMessage = `Failed to set up Python environment: ${errorMessage}`;

        if (errorMessage.includes('python')) {
            userMessage = `Python not found. Please check your Python path in settings. Current path: "${pythonCommand}"`;
        } else if (errorMessage.includes('venv')) {
            userMessage = `Failed to create virtual environment. Ensure Python has venv module installed.`;
        } else if (errorMessage.includes('requirements.txt')) {
            userMessage = `Failed to install dependencies. Check if requirements.txt exists and contains valid packages.`;
        }

        vscode.window.showErrorMessage(userMessage);
        throw error;
    }
}

// UPDATED runAgent FUNCTION WITH CANCELLATION SUPPORT AND BETTER ERROR HANDLING
async function runAgent(
    context: vscode.ExtensionContext,
    projectPath: string,
    formData: any,
    progress: vscode.Progress<{ message?: string; increment?: number }>,
    token: vscode.CancellationToken // Add the cancellation token parameter
) {
    try {
        const pythonPath = await setupPythonEnvironment(context, progress);
        const agentPath = path.join(context.extensionPath, 'agent');
        const scriptPath = path.join(agentPath, 'run_agent.py');

        const args = [
            scriptPath,
            '--project-path', projectPath,
            '--persona', formData.persona,
            '--pain-points', formData.painPoints,
            '--use-cases', formData.useCases,
            '--success-metrics', formData.successMetrics,
        ];

        // Clear the channel from previous runs and show it to the user
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine(">>> Starting AI Agent...");
        outputChannel.appendLine(`>>> Project Path: ${projectPath}`);
        outputChannel.appendLine("---------------------------------------------------\n");

        const agentProcess = spawn(pythonPath, args, {
            env: {
                ...process.env,
                'GOOGLE_API_KEY': await vscode.workspace.getConfiguration('ai-project-refactorer').get('googleApiKey'),
                'PYTHONIOENCODING': 'utf-8'
            },
            cwd: projectPath
        });

        // Listen for the user clicking the "Cancel" button
        token.onCancellationRequested(() => {
            outputChannel.appendLine("\n>>> User requested cancellation. Terminating agent...");
            console.log("User cancelled the agent run.");
            agentProcess.kill('SIGTERM'); // Send the termination signal to the Python process
        });

        return new Promise<void>((resolve, reject) => {
            // Pipe stdout to the output channel with improved progress parsing
            agentProcess.stdout.on('data', (data) => {
                const output = data.toString();
                outputChannel.append(output); // Keep appending raw log for debugging

                // Try to parse the output as JSON for cleaner progress
                try {
                    const lines = output.trim().split('\n');
                    for (const line of lines) {
                        if (line.trim()) {
                            const log = JSON.parse(line);
                            if (log.type === 'progress') {
                                const friendlyMessage = `Phase ${log.phase}: ${log.message}`;
                                progress.report({ message: friendlyMessage });
                            }
                        }
                    }
                } catch (e) {
                    // It's not JSON, so it might be a multi-line message.
                    // Just show the last line in the progress notification.
                    const lastLine = output.trim().split('\n').pop();
                    if (lastLine) {
                        progress.report({ message: lastLine });
                    }
                }
            });

            let errorShown = false;

            // Pipe stderr to the output channel
            agentProcess.stderr.on('data', (data) => {
                outputChannel.appendLine(`[ERROR] ${data.toString()}`);
                if (!errorShown) {
                    vscode.window.showErrorMessage(`Agent Error: See the "AI Agent" output channel for details.`);
                    errorShown = true;
                }
            });

            agentProcess.on('close', (code) => {
                outputChannel.appendLine("\n---------------------------------------------------");

                // If the process was killed because of cancellation, just resolve.
                if (token.isCancellationRequested) {
                    outputChannel.appendLine(">>> AI Agent process was cancelled.");
                    vscode.window.showInformationMessage('AI Agent was cancelled by user.');
                    resolve();
                    return;
                }

                if (code === 0) {
                    outputChannel.appendLine(">>> AI Agent finished successfully!");
                    vscode.window.showInformationMessage('AI Agent finished successfully!');
                    resolve();
                } else {
                    outputChannel.appendLine(`>>> AI Agent process exited with error code ${code}.`);

                    // Provide smarter error messages based on exit codes
                    let userMessage = `Agent process exited with error code ${code}.`;
                    switch (code) {
                        case 2:
                            userMessage = "Agent failed during Phase 1 (Discovery & Strategy). Check the output panel for details.";
                            break;
                        case 3:
                            userMessage = "Agent failed during Phase 2 (Execution & Refactoring). Check the output panel for details.";
                            break;
                        case 4:
                            userMessage = "Agent failed during Phase 3 (Documentation & Verification). Check the output panel for details.";
                            break;
                        case 1:
                            userMessage = "Agent encountered a general error. Check the output panel for details.";
                            break;
                        default:
                            userMessage = `Agent process failed with unexpected error code ${code}. Check the output panel for details.`;
                            break;
                    }

                    vscode.window.showErrorMessage(userMessage);
                    reject(new Error(`Agent process exited with code ${code}`));
                }
            });
        });

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        outputChannel.appendLine(`[SETUP ERROR] ${errorMessage}`);
        vscode.window.showErrorMessage('Failed to run the agent. Check the output panel for details.');
        throw error;
    }
}

// Stylish and modern Webview content (same as before, no changes needed)
function getWebviewContent() {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Velora AI Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }

            .container {
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                animation: slideIn 0.6s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .header {
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                padding: 30px;
                text-align: center;
                color: white;
                position: relative;
                overflow: hidden;
            }

            .header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 20px 20px;
                animation: float 20s linear infinite;
            }

            @keyframes float {
                0% { transform: translate(0, 0); }
                100% { transform: translate(-20px, -20px); }
            }

            .header h1 {
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }

            .header .subtitle {
                font-size: 1.1rem;
                opacity: 0.9;
                position: relative;
                z-index: 1;
            }

            .form-content {
                padding: 40px;
            }

            .form-group {
                margin-bottom: 25px;
                position: relative;
            }

            .form-group label {
                display: block;
                font-weight: 600;
                margin-bottom: 8px;
                color: #4a5568;
                font-size: 0.95rem;
            }

            .input-wrapper {
                position: relative;
            }

            input, select, textarea {
                width: 100%;
                padding: 15px 20px;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                font-size: 16px;
                transition: all 0.3s ease;
                background: #f8fafc;
                font-family: inherit;
            }

            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: #6366f1;
                background: white;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
                transform: translateY(-1px);
            }

            select {
                cursor: pointer;
                appearance: none;
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
                background-position: right 12px center;
                background-repeat: no-repeat;
                background-size: 16px;
                padding-right: 45px;
            }

            textarea {
                resize: vertical;
                min-height: 80px;
                font-family: inherit;
            }

            .start-button {
                width: 100%;
                padding: 18px 24px;
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                margin-top: 10px;
            }

            .start-button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
            }

            .start-button:active {
                transform: translateY(0);
            }

            .start-button:disabled {
                background: linear-gradient(135deg, #9ca3af, #6b7280);
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            .start-button::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }

            .start-button:hover:not(:disabled)::before {
                left: 100%;
            }

            .status-area {
                margin-top: 25px;
                padding: 20px;
                background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
                border-radius: 12px;
                border-left: 4px solid #0ea5e9;
                display: none;
                animation: statusSlideIn 0.3s ease-out;
            }

            @keyframes statusSlideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }

            .status-area.success {
                background: linear-gradient(135deg, #f0fdf4, #dcfce7);
                border-left-color: #22c55e;
            }

            .status-area .status-icon {
                display: inline-block;
                margin-right: 8px;
                font-size: 1.2rem;
            }

            .status-text {
                color: #0f172a;
                font-weight: 500;
            }

            .loading-spinner {
                display: inline-block;
                width: 18px;
                height: 18px;
                border: 2px solid #e5e7eb;
                border-radius: 50%;
                border-top-color: #6366f1;
                animation: spin 1s linear infinite;
                margin-right: 8px;
                vertical-align: middle;
            }

            @keyframes spin {
                to {
                    transform: rotate(360deg);
                }
            }

            .form-hint {
                font-size: 0.85rem;
                color: #6b7280;
                margin-top: 5px;
            }

            .feature-badge {
                display: inline-block;
                background: rgba(99, 102, 241, 0.1);
                color: #6366f1;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-left: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .input-icon {
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                color: #9ca3af;
                font-size: 1.1rem;
                pointer-events: none;
            }

            /* Dark theme support */
            @media (prefers-color-scheme: dark) {
                body {
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                }
                
                .container {
                    background: rgba(30, 41, 59, 0.95);
                    color: #e2e8f0;
                }
                
                input, select, textarea {
                    background: #334155;
                    border-color: #475569;
                    color: #e2e8f0;
                }
                
                input:focus, select:focus, textarea:focus {
                    background: #1e293b;
                    border-color: #6366f1;
                }
                
                .form-group label {
                    color: #cbd5e1;
                }
                
                .status-text {
                    color: #e2e8f0;
                }
            }

            /* Mobile responsiveness */
            @media (max-width: 640px) {
                body {
                    padding: 10px;
                }
                
                .header {
                    padding: 20px;
                }
                
                .header h1 {
                    font-size: 1.8rem;
                }
                
                .form-content {
                    padding: 25px;
                }
                
                .start-button {
                    padding: 16px 20px;
                    font-size: 16px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> Velora AI Agent</h1>
                <p class="subtitle">Intelligent Project Refactoring Assistant</p>
            </div>
            
            <div class="form-content">
                <div class="form-group">
                    <label for="persona"> Who are you? <span class="feature-badge">Role</span></label>
                    <div class="input-wrapper">
                        <select id="persona">
                            <option value="Developer"> Developer</option>
                            <option value="Data Scientist"> Data Scientist</option>
                            <option value="Researcher"> Researcher</option>
                            <option value="Student"> Student</option>
                        </select>
                    </div>
					
<div class="form-hint">Select your primary role to customize the AI's approach</div>
                </div>

                <div class="form-group">
                    <label for="pain-points"> What are your main pain points? <span class="feature-badge">Issues</span></label>
                    <div class="input-wrapper">
                        <textarea id="pain-points" placeholder="Describe the challenges you're facing with this project...">Messy code structure, no clear organization, missing documentation, hard to maintain</textarea>
                        <div class="input-icon"></div>
                    </div>
                    <div class="form-hint">Be specific about what's frustrating or blocking your progress</div>
                </div>

                <div class="form-group">
                    <label for="use-cases"> What do you want to achieve? <span class="feature-badge">Goals</span></label>
                    <div class="input-wrapper">
                        <textarea id="use-cases" placeholder="Describe what you want to accomplish with this project...">Better code organization, improved maintainability, automated testing setup, clear documentation</textarea>
                        <div class="input-icon"></div>
                    </div>
                    <div class="form-hint">Outline your desired outcomes and use cases</div>
                </div>

                <div class="form-group">
                    <label for="success-metrics"> How will you measure success? <span class="feature-badge">Metrics</span></label>
                    <div class="input-wrapper">
                        <textarea id="success-metrics" placeholder="Define what success looks like for you...">Reduced code complexity, faster development time, easier onboarding for new developers, comprehensive test coverage</textarea>
                        <div class="input-icon"></div>
                    </div>
                    <div class="form-hint">Define measurable outcomes to track progress</div>
                </div>

                <button class="start-button" id="start-agent" onclick="startAgent()">
                    <span id="button-text"> Start AI Agent</span>
                </button>

                <div class="status-area" id="status-area">
                    <div class="status-icon" id="status-icon">ℹ️</div>
                    <span class="status-text" id="status-text">Ready to begin...</span>
                </div>
            </div>
        </div>

        <script>
            const vscode = acquireVsCodeApi();
            let isRunning = false;

            // Handle messages from the extension
            window.addEventListener('message', event => {
                const message = event.data;
                
                switch (message.command) {
                    case 'set-running-state':
                        isRunning = message.running;
                        updateUIState();
                        break;
                }
            });

            function updateUIState() {
                const startButton = document.getElementById('start-agent');
                const buttonText = document.getElementById('button-text');
                const statusArea = document.getElementById('status-area');
                const statusIcon = document.getElementById('status-icon');
                const statusText = document.getElementById('status-text');

                if (isRunning) {
                    startButton.disabled = true;
                    buttonText.innerHTML = '<div class="loading-spinner"></div>Agent Running...';
                    statusArea.style.display = 'block';
                    statusArea.className = 'status-area';
                    statusIcon.textContent = '';
                    statusIcon.innerHTML = '<div class="loading-spinner"></div>';
                    statusText.textContent = 'AI Agent is analyzing your project...';
                    
                    // Disable form inputs while running
                    const inputs = document.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => input.disabled = true);
                } else {
                    startButton.disabled = false;
                    buttonText.innerHTML = ' Start AI Agent';
                    
                    // Re-enable form inputs
                    const inputs = document.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => input.disabled = false);
                    
                    // Show completion status
                    if (statusArea.style.display === 'block') {
                        statusArea.className = 'status-area success';
                        statusIcon.innerHTML = '✅';
                        statusText.textContent = 'Agent completed! Check the output panel for results.';
                    }
                }
            }

            function startAgent() {
                if (isRunning) return;

                // Validate form inputs
                const persona = document.getElementById('persona').value;
                const painPoints = document.getElementById('pain-points').value.trim();
                const useCases = document.getElementById('use-cases').value.trim();
                const successMetrics = document.getElementById('success-metrics').value.trim();

                if (!painPoints || !useCases || !successMetrics) {
                    showValidationError('Please fill in all required fields.');
                    return;
                }

                // Collect form data
                const formData = {
                    persona: persona,
                    painPoints: painPoints,
                    useCases: useCases,
                    successMetrics: successMetrics
                };

                // Send data to extension
                vscode.postMessage({
                    command: 'submit',
                    data: formData
                });

                // Update UI immediately
                isRunning = true;
                updateUIState();
            }

            function showValidationError(message) {
                const statusArea = document.getElementById('status-area');
                const statusIcon = document.getElementById('status-icon');
                const statusText = document.getElementById('status-text');

                statusArea.style.display = 'block';
                statusArea.className = 'status-area';
                statusArea.style.background = 'linear-gradient(135deg, #fef2f2, #fee2e2)';
                statusArea.style.borderLeftColor = '#ef4444';
                statusIcon.textContent = '⚠️';
                statusText.textContent = message;

                // Hide error after 5 seconds
                setTimeout(() => {
                    if (!isRunning) {
                        statusArea.style.display = 'none';
                    }
                }, 5000);
            }

            // Initialize form with some helpful defaults if empty
            document.addEventListener('DOMContentLoaded', function() {
                const painPoints = document.getElementById('pain-points');
                const useCases = document.getElementById('use-cases');
                const successMetrics = document.getElementById('success-metrics');

                // Set placeholders as actual values if fields are empty
                if (!painPoints.value.trim()) {
                    painPoints.value = "Messy code structure, no clear organization, missing documentation, hard to maintain";
                }
                if (!useCases.value.trim()) {
                    useCases.value = "Better code organization, improved maintainability, automated testing setup, clear documentation";
                }
                if (!successMetrics.value.trim()) {
                    successMetrics.value = "Reduced code complexity, faster development time, easier onboarding for new developers, comprehensive test coverage";
                }

                // Add input validation and auto-resize for textareas
                const textareas = document.querySelectorAll('textarea');
                textareas.forEach(textarea => {
                    textarea.addEventListener('input', function() {
                        this.style.height = 'auto';
                        this.style.height = (this.scrollHeight) + 'px';
                    });

                    // Initial resize
                    textarea.style.height = 'auto';
                    textarea.style.height = (textarea.scrollHeight) + 'px';
                });

                // Add keyboard shortcut (Ctrl/Cmd + Enter) to start agent
                document.addEventListener('keydown', function(e) {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !isRunning) {
                        startAgent();
                    }
                });
            });

            // Add some interactive animations
            document.addEventListener('DOMContentLoaded', function() {
                const inputs = document.querySelectorAll('input, select, textarea');
                
                inputs.forEach(input => {
                    input.addEventListener('focus', function() {
                        this.parentNode.style.transform = 'scale(1.02)';
                        this.parentNode.style.transition = 'transform 0.2s ease';
                    });
                    
                    input.addEventListener('blur', function() {
                        this.parentNode.style.transform = 'scale(1)';
                    });
                });
            });
        </script>
    </body>
    </html>
    `;
}

// Add the missing deactivate function
export function deactivate() {
    // Clean up resources
    if (outputChannel) {
        outputChannel.dispose();
    }
}