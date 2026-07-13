# SupportAI — Customer Service Chatbot

A production-quality NLP-powered customer service chatbot built with Flask, TF-IDF vectorization, and cosine similarity matching.

## Features

- **NLP Engine** — TF-IDF + cosine similarity for intent classification
- **Sentiment Detection** — Detects negative/positive tone and adapts responses
- **Entity Extraction** — Recognizes order IDs and email addresses from user input
- **15+ Intent Categories** — Orders, returns, payments, shipping, account, warranty, and more
- **Smart Suggestions** — Context-aware quick-reply chips after each response
- **Confidence Score** — Visual indicator of how confident the bot is
- **Modern Dark UI** — Professional chat interface with sidebar navigation
- **Session Management** — Per-user conversation history
- **Responsive Design** — Works on mobile and desktop

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| NLP | scikit-learn (TF-IDF, cosine similarity) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Fonts/Icons | Google Fonts (Inter), Font Awesome 6 |

## Project Structure

```
ChatBot For Customer Service/
├── app.py                  # Flask application & API routes
├── requirements.txt        # Python dependencies
├── chatbot/
│   ├── __init__.py
│   ├── engine.py           # NLP engine (TF-IDF, sentiment, entities)
│   └── intents.json        # Training data (intents, patterns, responses)
├── templates/
│   └── index.html          # Chat UI
└── static/
    ├── style.css           # Dark theme styling
    └── script.js           # Frontend logic & API calls
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
# http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Chat UI |
| POST | `/chat` | Send message, get response |
| POST | `/reset` | Reset conversation session |
| GET | `/history` | Get conversation history |

### POST `/chat` Example

```json
// Request
{ "message": "Where is my order?" }

// Response
{
  "response": "To track your order, please visit...",
  "intent": "order_status",
  "confidence": 87.3,
  "sentiment": "neutral",
  "entities": { "order_id": "ORD123456" },
  "suggestions": ["Return Policy", "Cancel Order", "Contact Support"]
}
```

## Extending the Chatbot

To add new intents, edit `chatbot/intents.json`:

```json
{
  "tag": "your_intent",
  "patterns": ["user phrase 1", "user phrase 2"],
  "responses": ["Bot response 1", "Bot response 2"]
}
```

The engine retrains automatically on startup — no additional steps needed.
