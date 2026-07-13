const messagesEl = document.getElementById('chat-messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const typingEl = document.getElementById('typing-indicator');
const suggestionsBar = document.getElementById('suggestions-bar');
const confidenceBadge = document.getElementById('confidence-badge');
const confidenceVal = document.getElementById('confidence-val');
const charCount = document.getElementById('char-count');

const sentimentIcons = { positive: '😊', negative: '😟', neutral: '😐' };

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function appendMessage(role, text, meta = {}) {
  const row = document.createElement('div');
  row.className = `message-row ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.innerHTML = role === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

  const content = document.createElement('div');
  content.className = 'msg-content';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const msgMeta = document.createElement('div');
  msgMeta.className = 'msg-meta';
  msgMeta.innerHTML = `<span>${getTime()}</span>`;

  if (role === 'bot' && meta.intent) {
    msgMeta.innerHTML += `<span class="intent-tag">${meta.intent.replace(/_/g, ' ')}</span>`;
  }
  if (role === 'bot' && meta.sentiment) {
    msgMeta.innerHTML += `<span class="sentiment-icon">${sentimentIcons[meta.sentiment] || ''}</span>`;
  }

  content.appendChild(bubble);
  content.appendChild(msgMeta);
  row.appendChild(avatar);
  row.appendChild(content);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  typingEl.style.display = 'flex';
  scrollToBottom();
}

function hideTyping() {
  typingEl.style.display = 'none';
}

function updateSuggestions(suggestions = []) {
  suggestionsBar.innerHTML = '';
  suggestions.forEach(s => {
    const chip = document.createElement('button');
    chip.className = 'suggestion-chip';
    chip.textContent = s;
    chip.onclick = () => sendMessage(s);
    suggestionsBar.appendChild(chip);
  });
}

function updateConfidence(score) {
  confidenceBadge.style.display = 'flex';
  confidenceVal.textContent = score;
  confidenceBadge.style.color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
}

async function sendMessage(text) {
  const message = text || inputEl.value.trim();
  if (!message) return;

  // Remove welcome card if present
  const welcome = messagesEl.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  appendMessage('user', message);
  inputEl.value = '';
  charCount.textContent = '0/500';
  sendBtn.disabled = true;
  updateSuggestions([]);
  showTyping();

  // Simulate realistic typing delay
  const delay = Math.min(800 + message.length * 10, 2000);

  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  })
  .then(res => res.json())
  .then(data => {
    setTimeout(() => {
      hideTyping();
      appendMessage('bot', data.response, { intent: data.intent, sentiment: data.sentiment });
      updateConfidence(data.confidence);
      updateSuggestions(data.suggestions || []);
    }, delay);
  })
  .catch(() => {
    setTimeout(() => {
      hideTyping();
      appendMessage('bot', 'Could not reach the server. Make sure the app is running on http://localhost:5000', {});
    }, 500);
  });
}

// Event listeners
sendBtn.addEventListener('click', () => sendMessage());

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

inputEl.addEventListener('input', () => {
  const len = inputEl.value.length;
  charCount.textContent = `${len}/500`;
  sendBtn.disabled = len === 0;
});

// Sidebar nav items
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    sendMessage(btn.dataset.query);
  });
});

// Welcome chips
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => sendMessage(chip.dataset.query));
});

// Reset conversation
document.getElementById('reset-btn').addEventListener('click', async () => {
  await fetch('/reset', { method: 'POST' });
  messagesEl.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-icon"><i class="fas fa-sparkles"></i></div>
      <h3>Welcome to SupportAI!</h3>
      <p>I'm your intelligent customer service assistant. I can help you with orders, returns, payments, shipping, and much more.</p>
      <div class="welcome-chips">
        <button class="chip" data-query="Track my order">📦 Track Order</button>
        <button class="chip" data-query="Return policy">↩️ Returns</button>
        <button class="chip" data-query="Shipping info">🚚 Shipping</button>
        <button class="chip" data-query="Contact support">🎧 Support</button>
      </div>
    </div>`;
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => sendMessage(chip.dataset.query));
  });
  suggestionsBar.innerHTML = '';
  confidenceBadge.style.display = 'none';
});
