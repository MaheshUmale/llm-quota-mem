(function () {
    const vscode = acquireVsCodeApi();
    const responseContainer = document.getElementById('response-container');
    const promptInput = document.getElementById('prompt-input');
    const sendButton = document.getElementById('send-button');

    sendButton.addEventListener('click', () => {
        sendMessage();
    });

    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    window.addEventListener('message', event => {
        const message = event.data;
        switch (message.type) {
            case 'addResponse': {
                removeStatus();
                addMessage('bot', message.value);
                break;
            }
            case 'status': {
                showStatus(message.value);
                break;
            }
            case 'clearChat': {
                responseContainer.innerHTML = '';
                break;
            }
        }
    });

    function sendMessage() {
        const text = promptInput.value;
        if (text) {
            removeStatus();
            addMessage('user', text);
            vscode.postMessage({
                type: 'sendMessage',
                text: text
            });
            promptInput.value = '';
            showStatus('Thinking...');
        }
    }

    function showStatus(text) {
        let status = document.getElementById('status-msg');
        if (!status) {
            status = document.createElement('div');
            status.id = 'status-msg';
            status.className = 'message bot status';
            responseContainer.appendChild(status);
        }
        status.innerText = text;
        responseContainer.scrollTop = responseContainer.scrollHeight;
    }

    function removeStatus() {
        const status = document.getElementById('status-msg');
        if (status) status.remove();
    }

    function addMessage(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerText = text;
        responseContainer.appendChild(div);
        responseContainer.scrollTop = responseContainer.scrollHeight;
    }
}());
