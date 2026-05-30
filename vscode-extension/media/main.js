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
                addMessage('bot', message.value);
                break;
            }
        }
    });

    function sendMessage() {
        const text = promptInput.value;
        if (text) {
            addMessage('user', text);
            vscode.postMessage({
                type: 'sendMessage',
                text: text
            });
            promptInput.value = '';
        }
    }

    function addMessage(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerText = text;
        responseContainer.appendChild(div);
        responseContainer.scrollTop = responseContainer.scrollHeight;
    }
}());
