const promptInput = document.querySelector('#prompt-input')
const hiddenCMD = document.querySelector('#hidden-cmd')
let promptText = ""

const body = document.querySelector('body')

document.onkeydown = (input) => {
    switch (input.key) {
        case 'Backspace':
            promptText = promptText.slice(0, promptText.length - 1)
            break
        case 'Enter':
            if (!handle_local_commands()) {
                const sendEvent = new Event("send_cmd")
                body.dispatchEvent(sendEvent)
            }
            promptText = ''
            break
        case '/':
            input.preventDefault()
        default:
            if (input.key.length !== 1) return
            promptText += input.key
    }

    promptInput.textContent = promptText
    hiddenCMD.value = promptText
}

const innerHistory = document.querySelector('#innerHistory')
function handle_local_commands() {
    switch (promptText.trim()) {
        case 'clear':
            innerHistory.replaceChildren()
            return true;
    }

    return false;
}
