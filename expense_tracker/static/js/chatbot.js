// Greeting with Dynamic Name
document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.getElementById('chatbot-messages');
    
    // 1. Check if there is saved history in SessionStorage
    const savedHistory = sessionStorage.getItem('chat_history');
    
    if (savedHistory) {
        // If history exists, load it
        chatMessages.innerHTML = savedHistory;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        // Only if NO history, show the greeting
        const userName = (typeof CURRENT_USER_NAME !== 'undefined') ? CURRENT_USER_NAME : "Sir/Madam";
        
        setTimeout(() => {
            if (chatMessages && chatMessages.innerHTML.trim() === "") {
                chatMessages.innerHTML += `
                    <div class='chat-msg ai-msg' style="margin: 10px; padding: 10px; background: #2a2a2a; color: white; border-radius: 10px;">
                        <b>AI:</b> Hello! Welcome to your Financial Assistant. How may I help you today, ${userName}?
                    </div>`;
                saveChatHistory(); // Save the greeting to history
            }
        }, 1500);
    }
});

// Helper function to save current chat state
function saveChatHistory() {
    const chatMessages = document.getElementById('chatbot-messages');
    if (chatMessages) {
        sessionStorage.setItem('chat_history', chatMessages.innerHTML);
    }
}

// Toggle Chatbot Window
function toggleChatbotWindow() {
    const chatContainer = document.getElementById('chatbot-container');
    if (chatContainer) chatContainer.classList.toggle('d-none');
}

// Voice Recognition Function
function toggleVoice() {
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'ur-PK';
        recognition.start();

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('chatbot-input-field').value = transcript;
            sendChatbotMessage();
        };
    } else {
        alert("Voice recognition not supported in your browser.");
    }
}

// Main Send Message Function
async function sendChatbotMessage() {
    const inputField = document.getElementById('chatbot-input-field');
    const chatMessages = document.getElementById('chatbot-messages');
    const messageText = inputField.value.trim();
    
    if (!messageText) return;

    // Add user message to DOM
    chatMessages.innerHTML += `<div class='chat-msg user-msg' style="margin: 10px; padding: 10px; background: #ffc107; border-radius: 10px; text-align: right;"><b>You:</b> ${messageText}</div>`;
    inputField.value = '';
    saveChatHistory(); // Save state

    try {
        const response = await fetch(window.location.origin + '/api/chatbot/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: messageText }),
        });
        const data = await response.json();
        
        // Add AI message to DOM
        chatMessages.innerHTML += `<div class='chat-msg ai-msg' style="margin: 10px; padding: 10px; background: #2a2a2a; color: white; border-radius: 10px;"><b>AI:</b> ${data.response}</div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        saveChatHistory(); // Save updated state
    } catch (err) {
        console.error(err);
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') sendChatbotMessage();
}