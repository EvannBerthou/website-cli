const commandHistory = []
let promptText = ""
let commandPointer = 0

const body = document.querySelector('body')

document.onkeydown = (input) => {
    switch (input.key) {
        case 'ArrowUp':
            if (!commandHistory.length) break
            commandPointer = Math.max(0, commandPointer - 1)
            promptText = commandHistory[commandPointer];
            break
        case 'ArrowDown':
            if (!commandHistory.length) break
            commandPointer = Math.min(commandPointer + 1, commandHistory.length)
            promptText = commandHistory[commandPointer] || ''
            break
        case 'Backspace':
            promptText = promptText.slice(0, promptText.length - 1)
            break
        case 'Enter':
            if (!handle_local_commands()) {
                const login_form = document.querySelector('#login-form')
                if (login_form) {
                    login_form.requestSubmit()
                } else {
                    const sendEvent = new Event("send_cmd")
                    body.dispatchEvent(sendEvent)
                    commandHistory.push(promptText)
                    commandPointer = commandHistory.length
                }
            }
            promptText = ''
            break
        case '/':
            input.preventDefault()
        default:
            if (input.key.length !== 1) return
            promptText += input.key
    }

    //TODO: Ne pas charger à chaque fois
    const promptInput = document.querySelector('#prompt-input')
    const hiddenCMD = document.querySelector('#hidden-cmd')
    if (promptText.startsWith('login')) {
        promptInput.textContent = filterPasswordString(promptText, [2])
    } else if (promptText.startsWith('register')) {
        promptInput.textContent = filterPasswordString(promptText, [2,3])
    } else {
        promptInput.textContent = promptText
    }
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


function filterPasswordString(str, partsToHide) {
    parts = str.split(' ')
    filteredString = []
    for (i = 0; i < parts.length; i++) {
        if (partsToHide.includes(i)) {
            filteredString.push('*'.repeat(parts[i].length))
        } else {
            filteredString.push(parts[i])
        }
    }
    return filteredString.join(' ')
}
