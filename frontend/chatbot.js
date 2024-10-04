const chatInput = document.querySelector(".input-field input");
const sendChatBtn = document.querySelector(".input-field button");
const chatbox = document.querySelector(".box"); // Adjusted selector to match the chatbox container

sendChatBtn.addEventListener("click", () => {
    let userMessage = chatInput.value.trim();  // Get user input

    if (userMessage) {
        appendMessage("user", userMessage);  // Add user's message to the chat window
        sendToBackend(userMessage);          // Send message to backend for processing
        chatInput.value = "";                // Clear input field
        chatInput.focus();                   // Set focus back to input field for convenience
    }
});

chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {   // Send message on pressing Enter
        sendChatBtn.click();
        e.preventDefault();                  // Prevent newline in the input field
    }
});

// Function to append messages to the chatbox
function appendMessage(sender, message, typingEffect = false) {
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("item", sender);  // Added item class to maintain structure

    let messageContent = document.createElement("div");
    messageContent.classList.add("msg");

    if (typingEffect && sender === "bot") {
        typeText(message, messageContent);  // Apply typing effect for bot messages
    } else {
        messageContent.innerHTML = `<p>${message}</p>`;
    }

    messageDiv.innerHTML = `
        <div class="icon">${sender === 'user' ? '😊' : '🤖'}</div> <!-- Optional: Add icons for user/bot -->
    `;
    messageDiv.appendChild(messageContent);
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;  // Scroll to the bottom of the chat
}

// Function to type text with delay (100ms per character) in a single paragraph
function typeText(text, container) {
    let index = 0;
    const typingSpeed = 10; // speed in milliseconds
    let paragraph = document.createElement("p"); // Create a single paragraph for the message
    container.appendChild(paragraph); // Add the paragraph to the container

    function typeChar() {
        if (index < text.length) {
            paragraph.textContent += text.charAt(index); // Add characters to the paragraph
            index++;
            setTimeout(typeChar, typingSpeed);
        } else {
            paragraph.textContent = text; // Ensure the text is fully written
        }
    }

    typeChar();
}

// Function to send the user message to the backend
function sendToBackend(message) {
    fetch('http://127.0.0.1:5000/chatbot', {  // Ensure this is the correct URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    })
        .then(response => response.json())
        .then(data => {
            const botMessage = data.response?.message?.content || "Sorry, no response!";
            appendMessage("bot", botMessage, true);  // Display the bot's response with typing effect
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage("bot", "Sorry, something went wrong!");  // Fallback message on error
        });
}

// Function to display the welcome message as a bot message on page load
document.addEventListener("DOMContentLoaded", function () {
    const welcomeText = "Hello! Welcome to BuyWheels. I'll do my best to gurantee you the best price for our product.";
    appendMessage("bot", welcomeText, true);  // Use the appendMessage function with typing effect
});
