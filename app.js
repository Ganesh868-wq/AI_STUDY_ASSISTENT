/**
 * AI Study Assistant - Frontend Client Application
 * Handles UI interactions, message rendering, auto-scrolling,
 * and communication with the Python backend server.
 */

// DOM Elements
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesList = document.getElementById('messagesList');
const messagesViewport = document.getElementById('messagesViewport');
const backendBadge = document.getElementById('backendBadge');
const aiBadge = document.getElementById('aiBadge');
const clearChatBtn = document.getElementById('clearChatBtn');
const chipButtons = document.querySelectorAll('.chip-btn');

/**
 * Format current time as HH:MM AM/PM
 */
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Smoothly scroll chat viewport to the latest message
 */
function scrollToBottom() {
  messagesViewport.scrollTo({
    top: messagesViewport.scrollHeight,
    behavior: 'smooth',
  });
}

/**
 * Update the connectivity badges in the header
 */
function updateBackendStatus(isOnline, isAiConfigured = false, provider = 'OpenAI', model = 'gpt-4o-mini') {
  if (isOnline) {
    backendBadge.className = 'status-pill status-online';
    backendBadge.innerHTML = '<span class="status-dot"></span><span>Backend: Online</span>';
  } else {
    backendBadge.className = 'status-pill status-offline';
    backendBadge.innerHTML = '<span class="status-dot"></span><span>Backend: Offline</span>';
  }

  if (isAiConfigured) {
    aiBadge.className = 'status-pill status-online';
    aiBadge.innerHTML = `<span class="status-dot"></span><span>AI: ${provider} (${model})</span>`;
    aiBadge.title = `Connected to ${provider} API using ${model}`;
  } else {
    aiBadge.className = 'status-pill status-pending';
    aiBadge.innerHTML = '<span class="status-dot"></span><span>AI API: Pending Setup</span>';
    aiBadge.title = 'Add your API key to .env to enable live AI responses';
  }
}

/**
 * Check backend health on initial load
 */
async function checkBackendStatus() {
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error('Status endpoint returned error');
    const data = await response.json();
    updateBackendStatus(true, Boolean(data.ai_configured), data.provider || 'Google Gemini', data.model || 'gemini-2.5-flash-lite');
  } catch (error) {
    console.warn('Backend server is not reachable:', error);
    updateBackendStatus(false, false);
  }
}

/**
 * Basic markdown formatter for clean assistant message rendering
 */
function formatMarkdown(text) {
  if (!text) return '';
  // Sanitize raw HTML
  let formatted = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Headers (### and ##)
  formatted = formatted.replace(/^### (.*$)/gim, '<h4 style="margin: 10px 0 4px; font-size: 1.02rem; color: #1e293b; font-weight: 600;">$1</h4>');
  formatted = formatted.replace(/^## (.*$)/gim, '<h3 style="margin: 12px 0 6px; font-size: 1.12rem; color: #0f172a; font-weight: 700;">$1</h3>');

  // Horizontal rules
  formatted = formatted.replace(/^---$/gim, '<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 10px 0;">');

  // Bullet items
  formatted = formatted.replace(/^[\*\-] (.*$)/gim, '<div style="margin-left: 14px; margin-bottom: 2px;">• $1</div>');

  // Bold **text**
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Inline code `text`
  formatted = formatted.replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.88em;">$1</code>');
  // Clickable links
  formatted = formatted.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: #4f46e5; text-decoration: underline;">$1</a>'
  );
  // Line breaks
  formatted = formatted.replace(/\n/g, '<br>');
  return formatted;
}

/**
 * Append a user message bubble to the chat
 */
function appendUserMessage(text) {
  const card = document.createElement('div');
  card.className = 'message-card user-card';
  card.innerHTML = `
    <div class="message-header">
      <span class="message-avatar">👤</span>
      <span class="message-sender">You</span>
      <span class="message-time">${getCurrentTime()}</span>
    </div>
    <div class="message-body">
      <p>${formatMarkdown(text)}</p>
    </div>
  `;
  messagesList.appendChild(card);
  scrollToBottom();
}

/**
 * Append a temporary loading indicator
 */
function appendLoadingIndicator() {
  const loadingCard = document.createElement('div');
  loadingCard.className = 'message-card assistant-card';
  loadingCard.id = 'loadingIndicator';
  loadingCard.innerHTML = `
    <div class="message-header">
      <span class="message-avatar">🤖</span>
      <span class="message-sender">Study Assistant</span>
      <span class="message-time">${getCurrentTime()}</span>
    </div>
    <div class="message-body">
      <p><em>Thinking & connecting to OpenAI...</em></p>
    </div>
  `;
  messagesList.appendChild(loadingCard);
  scrollToBottom();
  return loadingCard;
}

/**
 * Append an assistant message response to the chat
 */
function appendAssistantResponse(message, isAiConfigured = false, isSuccess = true) {
  // Remove loading indicator if present
  const loadingIndicator = document.getElementById('loadingIndicator');
  if (loadingIndicator) {
    loadingIndicator.remove();
  }

  const card = document.createElement('div');
  card.className = 'message-card assistant-card';

  if (!isSuccess) {
    card.style.borderColor = '#f59e0b';
    card.style.backgroundColor = '#fffdf7';
  }

  let configBanner = '';
  if (!isAiConfigured) {
    configBanner = `
      <div class="setup-notice" style="margin-top: 10px;">
        <span class="notice-icon">⚙️</span>
        <div>
          <strong>Backend Status: Working (AI Unset)</strong>
          <p>No fake AI replies are generated. To activate intelligent study answers, add your AI API key to the <code>.env</code> file.</p>
        </div>
      </div>
    `;
  }

  card.innerHTML = `
    <div class="message-header">
      <span class="message-avatar">🤖</span>
      <span class="message-sender">Study Assistant</span>
      <span class="message-time">${getCurrentTime()}</span>
    </div>
    <div class="message-body">
      <p>${formatMarkdown(message)}</p>
      ${configBanner}
    </div>
  `;

  messagesList.appendChild(card);
  scrollToBottom();
}

/**
 * Append an error message bubble
 */
function appendErrorMessage(errorText) {
  const loadingIndicator = document.getElementById('loadingIndicator');
  if (loadingIndicator) {
    loadingIndicator.remove();
  }

  const card = document.createElement('div');
  card.className = 'message-card assistant-card';
  card.style.borderColor = '#fca5a5';
  card.innerHTML = `
    <div class="message-header">
      <span class="message-avatar">⚠️</span>
      <span class="message-sender" style="color: #b91c1c;">Connection Error</span>
      <span class="message-time">${getCurrentTime()}</span>
    </div>
    <div class="message-body">
      <p style="color: #b91c1c;">${formatMarkdown(errorText)}</p>
    </div>
  `;
  messagesList.appendChild(card);
  scrollToBottom();
}

/**
 * Send user query to backend server
 */
async function handleSendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return;

  // Display user's question
  appendUserMessage(trimmed);

  // Clear and reset input field
  messageInput.value = '';
  messageInput.style.height = 'auto';
  messageInput.focus();

  // Show loading indicator & disable send button during request
  appendLoadingIndicator();
  sendBtn.disabled = true;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: trimmed }),
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    appendAssistantResponse(data.reply, Boolean(data.ai_configured), data.success !== false);
    updateBackendStatus(true, Boolean(data.ai_configured), data.provider || 'Google Gemini', data.model || 'gemini-2.5-flash-lite');
  } catch (err) {
    console.error('Failed to communicate with backend:', err);
    appendErrorMessage(
      'Could not connect to the backend server. Make sure `python server.py` is running in your terminal.'
    );
    updateBackendStatus(false, false);
  } finally {
    sendBtn.disabled = false;
  }
}

/**
 * Event Listeners
 */

// Form Submission
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  handleSendMessage(messageInput.value);
});

// Auto-expand textarea and support Enter key to submit
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage(messageInput.value);
  }
});

messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
});

// Suggested prompt chips
chipButtons.forEach((chip) => {
  chip.addEventListener('click', () => {
    const promptText = chip.getAttribute('data-prompt');
    if (promptText) {
      messageInput.value = promptText;
      handleSendMessage(promptText);
    }
  });
});

// Clear Chat button
clearChatBtn.addEventListener('click', () => {
  const welcomeCard = messagesList.querySelector('.welcome-card');
  messagesList.innerHTML = '';
  if (welcomeCard) {
    messagesList.appendChild(welcomeCard);
  }
  messageInput.focus();
});

// Initial startup check
checkBackendStatus();
