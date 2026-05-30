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
    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage': {
                    try {
                        const port = vscode.workspace.getConfiguration("llmQuotaMem").get<number>("serverPort") || 8000;
                        const response = await axios.post(`http://localhost:${port}/v1/chat/completions`, {
                            model: data.model || "coder:gpt-4o",
                            messages: [{ role: "user", content: data.text }],
                            user_id: vscode.env.machineId,
                            project_id: vscode.workspace.name || "default"
                        });

                        webviewView.webview.postMessage({
                            type: 'addResponse',
                            value: response.data.choices[0].message.content
                        });
                    } catch (err: any) {
                        vscode.window.showErrorMessage(`Gateway Error: ${err.message}`);
                    }
                    break;
                }
            }
        });
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
