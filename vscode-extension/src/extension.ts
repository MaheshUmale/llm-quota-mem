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

            // Add Initial Context (Current File) - Fresh for each message
            let systemContext = "";
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor) {
                const fileName = activeEditor.document.fileName;
                const content = activeEditor.document.getText();
                systemContext = `CURRENT FILE CONTEXT:\nFile: ${fileName}\n\nContent:\n${content}`;
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

                const assistantMsg = response.data.choices[0].message.content;

                // Parse for tool use
                const toolMatch = assistantMsg.match(/<tool_use>([\s\S]*?)<\/tool_use>/);

                if (toolMatch) {
                    try {
                        const toolCall = JSON.parse(toolMatch[1].trim());
                        webviewView.webview.postMessage({ type: 'status', value: `Executing ${toolCall.tool}...` });

                        const result = await this._executeTool(toolCall.tool, toolCall.parameters);

                        currentMessages.push({ role: "assistant", content: assistantMsg });
                        currentMessages.push({ role: "user", content: `TOOL_RESULT: ${result}` });

                        // Continue loop to let model see tool result
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
                    const dirPath = path.join(workspaceRoot, params.path || "");
                    const files = await vscode.workspace.fs.readDirectory(vscode.Uri.file(dirPath));
                    return files.map(([name, type]) => `${name} (${type === vscode.FileType.Directory ? 'Dir' : 'File'})`).join("\n");
                }
                case 'read_file': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const doc = await vscode.workspace.openTextDocument(filePath);
                    return doc.getText();
                }
                case 'write_file': {
                    const filePath = path.join(workspaceRoot, params.path);
                    const content = Buffer.from(params.content, 'utf8');
                    await vscode.workspace.fs.writeFile(vscode.Uri.file(filePath), content);
                    return `Successfully wrote to ${params.path}`;
                }
                case 'search_code': {
                    const results = await vscode.commands.executeCommand('vscode.executeWorkspaceSymbolProvider', params.query);
                    return JSON.stringify(results);
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
