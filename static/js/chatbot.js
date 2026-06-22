// ===== OLAA SMART ADMISSIONS ASSISTANT – CHATBOT =====

(function() {
    'use strict';

    // --- DOM References ---
    const toggleBtn = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const messagesContainer = document.getElementById('chat-messages');

    // --- State ---
    let isOpen = false;

    // --- Toggle Chat Window ---
    function toggleChat() {
        isOpen = !isOpen;
        chatWindow.classList.toggle('open', isOpen);
        toggleBtn.classList.toggle('active', isOpen);
        if (isOpen) {
            chatInput.focus();
            // Scroll to bottom after opening
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }

    // --- Add Message to UI ---
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        div.innerHTML = `${text}<span class="time">${time}</span>`;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return div;
    }

    // --- Show Typing Indicator ---
    function showTyping() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'typing-indicator';
        div.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return id;
    }

    // --- Remove Typing Indicator ---
    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // --- Send Message to Backend ---
    async function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;

        // Disable input while sending
        chatInput.disabled = true;
        sendBtn.disabled = true;

        // Add user message
        addMessage(escapeHtml(msg), 'user');
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Show typing indicator
        const typingId = showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            const data = await response.json();

            // Remove typing indicator
            removeTyping(typingId);

            if (data.reply) {
                // Add bot response (with support for line breaks)
                const replyText = data.reply.replace(/\n/g, '<br>');
                addMessage(replyText, 'bot');
            } else if (data.error) {
                addMessage('⚠️ ' + data.error, 'bot');
            } else {
                addMessage("Sorry, I didn't quite understand. Please contact the school office directly.", 'bot');
            }
        } catch (error) {
            removeTyping(typingId);
            console.error('Chat error:', error);
            addMessage("⚠️ Oops! Something went wrong. Please try again later, or contact the school office.", 'bot');
        } finally {
            // Re-enable input
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    // --- Simple HTML Escape (to prevent XSS) ---
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Auto-resize textarea (optional) ---
    function autoResize() {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    }

    // --- Event Listeners ---

    // Toggle button
    toggleBtn.addEventListener('click', toggleChat);

    // Send button
    sendBtn.addEventListener('click', sendMessage);

    // Enter key (Send on Enter, Shift+Enter for new line)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize on input
    chatInput.addEventListener('input', autoResize);

    // Close chat when clicking outside (optional)
    document.addEventListener('click', function(e) {
        const isChatElement = chatWindow.contains(e.target) || toggleBtn.contains(e.target);
        if (isOpen && !isChatElement) {
            toggleChat();
        }
    });

    // --- Initial Setup ---
    // Set initial input height
    autoResize();

    // Ensure chat is closed on load (in case of any state mismatch)
    chatWindow.classList.remove('open');
    toggleBtn.classList.remove('active');
    isOpen = false;

    // --- Handle window resize for mobile (optional) ---
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Just ensure messages are scrolled properly
            if (isOpen) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }, 300);
    });

    console.log('OLAA Chatbot initialized successfully.');

})();