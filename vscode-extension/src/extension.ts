import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import axios from 'axios';

let serverProcess: ChildProcess | null = null;
let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel("LLM Quota Mem");

    // Register the sidebar provider
    const provider = new SidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("llmQuotaMemSidebar", provider)
    );

    // Commands to manage the server
    context.subscriptions.push(vscode.commands.registerCommand('llm-quota-mem.startServer', () => {
        startGatewayServer();
    }));

    context.subscriptions.push(vscode.commands.registerCommand('llm-quota-mem.stopServer', () => {
        stopGatewayServer();
    }));

    context.subscriptions.push(vscode.commands.registerCommand('llm-quota-mem.clearChat', () => {
        provider.clearHistory();
    }));

    // Auto-start server if enabled (default true logic)
    startGatewayServer();
}

export function deactivate() {
    stopGatewayServer();
}

function startGatewayServer() {
    if (serverProcess) {
        vscode.window.showInformationMessage("LLM Quota Mem server is already running.");
        return;
    }

    const config = vscode.workspace.getConfiguration("llmQuotaMem");
    const pythonPath = config.get<string>("pythonPath") || "python";
    const port = config.get<number>("serverPort") || 8000;

    // Resolve the path to the app.py - assuming extension is in a subfolder of the repo root
    // In a real build, we'd package the python app or point to the installed package
    const scriptPath = path.join(vscode.workspace.workspaceFolders?.[0].uri.fsPath || "", "llm_quota_mem", "app.py");

    outputChannel.appendLine(`Starting server: ${pythonPath} -m llm_quota_mem.app on port ${port}`);

    serverProcess = spawn(pythonPath, ["-m", "llm_quota_mem.app"], {
        env: { ...process.env, PORT: port.toString() },
        cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath
    });

    serverProcess.stdout?.on('data', (data) => {
        outputChannel.append(`[STDOUT] ${data}`);
    });

    serverProcess.stderr?.on('data', (data) => {
        outputChannel.append(`[STDERR] ${data}`);
    });

    serverProcess.on('close', (code) => {
        outputChannel.appendLine(`Server process exited with code ${code}`);
        serverProcess = null;
    });

    vscode.window.showInformationMessage(`LLM Quota Mem Gateway started on port ${port}`);
}

function stopGatewayServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
        vscode.window.showInformationMessage("LLM Quota Mem Gateway stopped.");
    }
}

class SidebarProvider implements vscode.WebviewViewProvider {
    private _history: { role: string, content: string }[] = [];
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public clearHistory() {
        this._history = [];
        if (this._view) {
            this._view.webview.postMessage({ type: 'clearChat' });
        }
        vscode.window.showInformationMessage("Chat history cleared.");
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage': {
                    await this._handleMessage(webviewView, data.text, data.model);
                    break;
                }
            }
        });
    }

    private async _handleMessage(webviewView: vscode.WebviewView, text: string, model?: string) {
        try {
            const port = vscode.workspace.getConfiguration("llmQuotaMem").get<number>("serverPort") || 8000;

            // Add Initial Context (Current File & Workspace Tree)
            let systemContext = "";
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor) {
                const fileName = activeEditor.document.fileName;
                const content = activeEditor.document.getText();
                systemContext = `CURRENT FILE CONTEXT:\nFile: ${fileName}\n\nContent:\n${content}\n\n`;
            }

            // Add workspace structure if it's the beginning of the conversation
            if (this._history.length === 0) {
                const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
                if (workspaceRoot) {
                    try {
                        const entries = await vscode.workspace.fs.readDirectory(vscode.Uri.file(workspaceRoot));
                        const tree = entries.map(([name, type]) => `- ${name} (${type === vscode.FileType.Directory ? 'Dir' : 'File'})`).join("\n");
                        systemContext += `WORKSPACE STRUCTURE:\n${tree}\n`;
                    } catch (e) {}
                }
            }

            // Append user message to history
            this._history.push({ role: "user", content: text });

            let loop = true;
            // Build current messages: System Context + History
            let currentMessages: any[] = [];
            if (systemContext) {
                currentMessages.push({ role: "system", content: systemContext });
            }
            currentMessages = currentMessages.concat(this._history);

            while (loop) {
                const response = await axios.post(`http://localhost:${port}/v1/chat/completions`, {
                    model: model || "coder:gpt-4o",
                    messages: currentMessages,
                    user_id: vscode.env.machineId,
                    project_id: vscode.workspace.name || "default"
                });

                const msg = response.data.choices[0].message;
                const assistantMsg = msg.content || "";
                const toolCalls = msg.tool_calls;

                // 1. Handle Native Tool Calls
                if (toolCalls && toolCalls.length > 0) {
                    currentMessages.push(msg); // Push assistant message with tool calls

                    for (const toolCall of toolCalls) {
                        const functionName = toolCall.function.name;
                        const args = JSON.parse(toolCall.function.arguments);

                        webviewView.webview.postMessage({ type: 'status', value: `Executing ${functionName}...` });
                        const result = await this._executeTool(functionName, args);

                        currentMessages.push({
                            role: "tool",
                            tool_call_id: toolCall.id,
                            name: functionName,
                            content: result
                        });
                    }
                    continue;
                }

                // 2. Handle Fallback Tag Parsing
                const toolMatch = assistantMsg.match(/<tool_use>([\s\S]*?)<\/tool_use>/);

                if (toolMatch) {
                    try {
                        const toolCall = JSON.parse(toolMatch[1].trim());
                        // Normalize format if it's {"tool": "...", "parameters": {...}} or just {"name": "...", "args": {...}}
                        const toolName = toolCall.tool || toolCall.name || toolCall.function;
                        const toolParams = toolCall.parameters || toolCall.arguments || toolCall.params || {};

                        webviewView.webview.postMessage({ type: 'status', value: `Executing ${toolName}...` });

                        const result = await this._executeTool(toolName, toolParams);

                        currentMessages.push({ role: "assistant", content: assistantMsg });
                        currentMessages.push({ role: "user", content: `TOOL_RESULT: ${result}` });

                        continue;
                    } catch (e: any) {
                        webviewView.webview.postMessage({ type: 'addResponse', value: assistantMsg + `\n\n[Error parsing tool: ${e.message}]` });
                        loop = false;
                    }
                } else {
                    // Final response from assistant: Add to history
                    this._history.push({ role: "assistant", content: assistantMsg });

                    webviewView.webview.postMessage({
                        type: 'addResponse',
                        value: assistantMsg
                    });
                    loop = false;
                }
            }
        } catch (err: any) {
            vscode.window.showErrorMessage(`Gateway Error: ${err.message}`);
        }
    }

    private async _executeTool(tool: string, params: any): Promise<string> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceRoot) return "Error: No workspace open";

        try {
            switch (tool) {
                case 'list_files': {
                    const targetDir = path.join(workspaceRoot, params.directory || "");
                    const maxDepth = params.depth || 3;

                    const listRecursive = async (dir: string, depth: number): Promise<string[]> => {
                        if (depth <= 0) return [];
                        const entries = await vscode.workspace.fs.readDirectory(vscode.Uri.file(dir));
                        let result: string[] = [];
                        for (const [name, type] of entries) {
                            const relPath = path.relative(workspaceRoot, path.join(dir, name));
                            result.push(`${relPath} (${type === vscode.FileType.Directory ? 'Dir' : 'File'})`);
                            if (type === vscode.FileType.Directory) {
                                const sub = await listRecursive(path.join(dir, name), depth - 1);
                                result = result.concat(sub);
                            }
                        }
                        return result;
                    };

                    const allFiles = await listRecursive(targetDir, maxDepth);
                    return allFiles.join("\n");
                }
                case 'read_file': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const doc = await vscode.workspace.openTextDocument(filePath);
                    let content = doc.getText();

                    if (params.start_line !== undefined && params.end_line !== undefined) {
                        const lines = content.split("\n");
                        content = lines.slice(params.start_line - 1, params.end_line).join("\n");
                    }
                    return content;
                }
                case 'write_file': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const content = Buffer.from(params.content, 'utf8');
                    await vscode.workspace.fs.writeFile(vscode.Uri.file(filePath), content);
                    return `Successfully wrote to ${params.path}`;
                }
                case 'patch_file': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const doc = await vscode.workspace.openTextDocument(filePath);
                    const text = doc.getText();

                    // Fuzzy matching or multiple attempts
                    let searchBlock = params.search;
                    let replaceBlock = params.replace;

                    if (!text.includes(searchBlock)) {
                        // Try trimming whitespace from each line
                        const trimLines = (s: string) => s.split('\n').map(l => l.trim()).join('\n');
                        const textTrimmed = trimLines(text);
                        const searchTrimmed = trimLines(searchBlock);

                        if (textTrimmed.includes(searchTrimmed)) {
                             // This is a bit risky but better than failing immediately
                             // For a "perfect" agent we should ideally use a proper diff library
                             return `Error: Exact match not found, but similar block exists. Please provide exact character-for-character match including indentation.`;
                        }
                        return `Error: Could not find exact search block in ${params.path}. Make sure indentation and whitespace match exactly.`;
                    }

                    const newText = text.replace(searchBlock, replaceBlock);
                    const edit = new vscode.WorkspaceEdit();

                    // Replace entire content to be safe with line endings and ranges
                    const fullRange = new vscode.Range(
                        doc.positionAt(0),
                        doc.positionAt(text.length)
                    );

                    edit.replace(doc.uri, fullRange, newText);
                    const success = await vscode.workspace.applyEdit(edit);
                    if (success) {
                        await doc.save();
                        return `Successfully patched ${params.path}`;
                    } else {
                        return `Error: Failed to apply edit to ${params.path}`;
                    }
                }
                case 'search_code': {
                    // Use ripgrep-like search via VS Code API
                    const pattern = params.pattern || params.query;
                    const results = await vscode.workspace.findFiles(params.file_pattern || '**/*', '**/node_modules/**');
                    let output = "";
                    for (const file of results.slice(0, 50)) {
                        const doc = await vscode.workspace.openTextDocument(file);
                        const content = doc.getText();
                        if (content.includes(pattern)) {
                            output += `Found in ${vscode.workspace.asRelativePath(file)}\n`;
                        }
                    }
                    return output || "No matches found.";
                }
                case 'execute_command': {
                    return new Promise((resolve) => {
                        const child = spawn(params.command, {
                            shell: true,
                            cwd: workspaceRoot,
                            env: { ...process.env }
                        });

                        let stdout = "";
                        let stderr = "";

                        child.stdout?.on('data', (data) => stdout += data);
                        child.stderr?.on('data', (data) => stderr += data);

                        const timeout = setTimeout(() => {
                            child.kill();
                            resolve(`Command timed out after ${params.timeout_seconds || 30}s\nStdout: ${stdout}\nStderr: ${stderr}`);
                        }, (params.timeout_seconds || 30) * 1000);

                        child.on('close', (code) => {
                            clearTimeout(timeout);
                            resolve(`Exit Code: ${code}\nStdout: ${stdout}\nStderr: ${stderr}`);
                        });
                    });
                }
                case 'view_outline': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const symbols = await vscode.commands.executeCommand<vscode.SymbolInformation[]>(
                        'vscode.executeDocumentSymbolProvider',
                        vscode.Uri.file(filePath)
                    );
                    if (!symbols) return "No symbols found or file type not supported.";
                    return symbols.map(s => `${s.name} [${vscode.SymbolKind[s.kind]}]`).join("\n");
                }
                default:
                    return `Unknown tool: ${tool}`;
            }
        } catch (e: any) {
            return `Error executing tool: ${e.message}`;
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, "media", "style.css"));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, "media", "main.js"));

        return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<link href="${styleUri}" rel="stylesheet">
				<title>AI Assistant</title>
			</head>
			<body>
                <div class="chat-container">
                    <div id="response-container"></div>
                    <div class="input-area">
                        <textarea id="prompt-input" placeholder="Ask anything..."></textarea>
                        <button id="send-button">Send</button>
                    </div>
                </div>
				<script src="${scriptUri}"></script>
			</body>
			</html>`;
    }
}
