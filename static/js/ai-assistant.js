/**
 * ai-assistant.js — demo ChatGPT-style chatbot for the FitAI Assistant page.
 * Responses are looked up from DEMO_AI_RESPONSES (demo-data.js) with a
 * generic fallback. Replace `getAIResponse()` with a real fetch() call to
 * the Django + AI backend once available — the chat rendering logic below
 * can stay exactly the same.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const chatWindow = document.getElementById("chatWindow");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const quickPrompts = document.getElementById("quickPrompts");
    if (!chatWindow || !chatForm) return;

    // Support ?prompt= coming from other pages (e.g. diet plan "ask AI")
    const params = new URLSearchParams(window.location.search);
    const incomingPrompt = params.get("prompt");
    if (incomingPrompt) {
      setTimeout(function () { sendMessage(incomingPrompt); }, 300);
    }

    chatForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      sendMessage(text);
      chatInput.value = "";
    });

    if (quickPrompts) {
      quickPrompts.querySelectorAll("button").forEach(function (btn) {
        btn.addEventListener("click", function () {
          sendMessage(btn.dataset.prompt);
        });
      });
    }

    function sendMessage(text) {
      appendBubble(text, "user");
      const typingEl = appendTyping();
      chatWindow.scrollTop = chatWindow.scrollHeight;

      const headers = (window.FitAI && window.FitAI.csrfHeaders) ? window.FitAI.csrfHeaders() : { "Content-Type": "application/json" };
      fetch("/ai-assistant/send/", { method: "POST", headers: headers, body: JSON.stringify({ message: text }) })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          typingEl.remove();
          appendBubble(data.ok ? data.reply : "Sorry, something went wrong — please try again.", "ai");
          chatWindow.scrollTop = chatWindow.scrollHeight;
        })
        .catch(function () {
          typingEl.remove();
          appendBubble("Sorry, I couldn't reach the server — please try again.", "ai");
        });
    }

    function appendBubble(text, who) {
      const div = document.createElement("div");
      div.className = "chat-bubble chat-bubble--" + who;
      div.textContent = text;
      chatWindow.appendChild(div);
      chatWindow.scrollTop = chatWindow.scrollHeight;
      return div;
    }

    function appendTyping() {
      const div = document.createElement("div");
      div.className = "chat-bubble chat-bubble--ai chat-bubble--typing";
      div.innerHTML = "<span></span><span></span><span></span>";
      chatWindow.appendChild(div);
      return div;
    }
  });
})();
