/*
  script.js
  ---------
  Handles all client-side chat behavior for SmartSupport:
    - sending messages to the Flask backend (POST /chat)
    - rendering user/bot chat bubbles with timestamps
    - quick-action buttons
    - a JS-only typing indicator
    - clearing the conversation (POST /clear)
    - Enter-to-send and auto-scroll
*/

const chatArea = document.getElementById("chatArea");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const typingIndicator = document.getElementById("typingIndicator");

// Greet the user as soon as the page loads
window.addEventListener("DOMContentLoaded", () => {
  addBotMessage("Hello! 👋 Welcome to SmartSupport. How can I help you today?");
});

/** Format the current time as HH:MM for message timestamps. */
function currentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

/** Append a bot message bubble to the chat area. */
function addBotMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row bot";
  row.innerHTML = `
    <div class="avatar-sm">🤖</div>
    <div class="bubble-group">
      <div class="bubble"></div>
      <span class="msg-time">${currentTime()}</span>
    </div>
  `;
  row.querySelector(".bubble").textContent = text;
  chatArea.appendChild(row);
  scrollToBottom();
}

/** Append a user message bubble to the chat area. */
function addUserMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row user";
  row.innerHTML = `
    <div class="avatar-sm">🧑</div>
    <div class="bubble-group">
      <div class="bubble"></div>
      <span class="msg-time">${currentTime()}</span>
    </div>
  `;
  row.querySelector(".bubble").textContent = text;
  chatArea.appendChild(row);
  scrollToBottom();
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function showTyping() {
  typingIndicator.classList.remove("hidden");
  scrollToBottom();
}

function hideTyping() {
  typingIndicator.classList.add("hidden");
}

/** Send a message to the backend and display the response. */
async function sendMessage(text) {
  const message = text.trim();
  if (!message) return;

  addUserMessage(message);
  messageInput.value = "";
  showTyping();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();

    // Small delay so the typing indicator is visible briefly (feels natural)
    setTimeout(() => {
      hideTyping();
      addBotMessage(data.response || "Sorry, something went wrong. Please try again.");
    }, 500);
  } catch (err) {
    hideTyping();
    addBotMessage("⚠️ I couldn't reach the server. Please check your connection and try again.");
  }
}

// ---------------- Event listeners ----------------

sendBtn.addEventListener("click", () => sendMessage(messageInput.value));

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage(messageInput.value);
  }
});

// Quick action buttons send their pre-set message
document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    sendMessage(btn.dataset.message);
  });
});

// Clear chat
clearBtn.addEventListener("click", async () => {
  try {
    await fetch("/clear", { method: "POST" });
  } catch (err) {
    // Even if the server call fails, still clear the visible chat
  }
  chatArea.innerHTML = "";
  addBotMessage("Hello! 👋 Welcome to SmartSupport. How can I help you today?");
});
