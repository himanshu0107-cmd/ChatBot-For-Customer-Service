# SupportAI — Customer Service Chatbot

A production-quality AI/ML-powered customer service chatbot built with Flask, TF-IDF vectorization, SVM classification, and VADER sentiment analysis.

## Features

- **ML Classification** — TF-IDF + LinearSVC (SVM) for intent classification
- **Model Persistence** — Trained model saved with `joblib`, auto-loads on startup
- **VADER Sentiment** — Real NLP sentiment analysis with compound score
- **Entity Extraction** — Recognizes order IDs and email addresses from user input
- **15 Intent Categories** — Orders, returns, payments, shipping, account, warranty, and more
- **Smart Suggestions** — Context-aware quick-reply chips after each response
- **Confidence Score** — Visual indicator of how confident the bot is
- **Modern Dark UI** — Professional chat interface with sidebar navigation
- **Session Management** — Per-user conversation history
- **Responsive Design** — Works on mobile and desktop

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| ML Model | scikit-learn (LinearSVC, Naive Bayes) |
| NLP | TF-IDF Vectorizer (bigrams), VADER Sentiment |
| Model I/O | joblib |
| Frontend | HTML5, CSS3, Vanilla JS |
| Fonts/Icons | Google Fonts (Inter), Font Awesome 6 |

## Project Structure

```
ChatBot For Customer Service/
├── app.py                      # Flask application & API routes
├── train.py                    # ML training pipeline (run once)
├── requirements.txt            # Python dependencies
├── chatbot/
│   ├── __init__.py
│   ├── engine.py               # NLP engine (SVM, VADER, entities)
│   ├── intents.json            # Training data (453 samples, 15 intents)
│   └── model/
│       ├── intent_model.pkl    # Saved SVM pipeline
│       ├── label_encoder.pkl   # Saved label encoder
│       └── metrics.json        # Training metrics
├── templates/
│   └── index.html              # Chat UI
└── static/
    ├── style.css               # Dark theme styling
    └── script.js               # Frontend logic & API calls
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the ML model
python train.py

# 3. Run the app
python app.py

# 4. Open in browser
# http://localhost:5000
```

> The engine auto-trains on first startup if `chatbot/model/` is missing.

## ML Training Pipeline

Running `python train.py` will:

1. Load 453 labeled samples across 15 intent classes from `intents.json`
2. Train two models — **LinearSVC** and **Naive Bayes** — and compare them
3. Run **5-fold cross-validation** on both
4. Evaluate on an **80/20 train/test split**
5. Print a full **classification report** (precision, recall, F1 per intent)
6. Print a **confusion matrix**
7. Retrain the winner on the full dataset and save to `chatbot/model/`

### Training Results

| Metric | Value |
|--------|-------|
| Model | LinearSVC (SVM) |
| Test Accuracy | **75.82%** |
| CV Mean (5-fold) | **71.48%** |
| CV Std | 9.84% |
| Training Samples | 453 |
| Intent Classes | 15 |

### Per-Intent F1 Scores (Best Model)

| Intent | Precision | Recall | F1 |
|--------|-----------|--------|----|
| order_status | 1.00 | 1.00 | **1.00** |
| payment_issues | 1.00 | 1.00 | **1.00** |
| return_policy | 1.00 | 1.00 | **1.00** |
| account_help | 1.00 | 0.86 | 0.92 |
| contact_support | 0.86 | 1.00 | 0.92 |
| shipping_info | 0.88 | 1.00 | 0.93 |
| cancel_order | 1.00 | 0.80 | 0.89 |
| hours | 1.00 | 0.80 | 0.89 |
| warranty | 0.80 | 0.67 | 0.73 |
| complaint | 0.57 | 0.57 | 0.57 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Chat UI |
| POST | `/chat` | Send message, get response |
| POST | `/reset` | Reset conversation session |
| GET | `/history` | Get conversation history |
| GET | `/metrics` | Get model training metrics |

### POST `/chat` Example

```json
// Request
{ "message": "Where is my order?" }

// Response
{
  "response": "To track your order, please visit...",
  "intent": "order_status",
  "confidence": 45.8,
  "sentiment": "neutral",
  "sentiment_score": 0.0,
  "entities": { "order_id": "ORD123456" },
  "suggestions": ["Return Policy", "Cancel Order", "Contact Support"],
  "model": "SVM"
}
```

### GET `/metrics` Example

```json
{
  "model": "SVM",
  "accuracy": 75.82,
  "cv_mean": 71.48,
  "cv_std": 9.84,
  "num_samples": 453,
  "num_classes": 15,
  "svm_accuracy": 75.82,
  "nb_accuracy": 72.53,
  "classes": ["account_help", "cancel_order", "complaint", ...]
}
```

## Extending the Chatbot

To add new intents, edit `chatbot/intents.json` (add at least 20 patterns per intent for good accuracy):

```json
{
  "tag": "your_intent",
  "patterns": ["user phrase 1", "user phrase 2", "...20+ patterns"],
  "responses": ["Bot response 1", "Bot response 2"]
}
```

Then retrain:

```bash
python train.py
```

The engine reloads the new model automatically on next startup.
