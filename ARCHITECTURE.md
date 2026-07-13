# SupportAI — System Architecture

This document describes the full system architecture, data flow, component responsibilities, and the phases a user message travels through from input to response.

---

## High-Level Architecture

```
+------------------+        HTTP/JSON         +----------------------+
|                  | -----------------------> |                      |
|   Browser UI     |   POST /chat             |   Flask Backend      |
|  (index.html)    | <----------------------- |   (app.py)           |
|                  |   JSON Response          |                      |
+------------------+                          +----------+-----------+
                                                         |
                                                         | calls
                                                         v
                                              +----------+-----------+
                                              |                      |
                                              |   ChatbotEngine      |
                                              |   (engine.py)        |
                                              |                      |
                                              +--+--------+--------+-+
                                                 |        |        |
                                          +------+  +-----+  +-----+------+
                                          |         |         |            |
                                    +-----v---+ +---v-----+ +-v----------+
                                    |  SVM    | |  VADER  | |   Regex    |
                                    | Model   | |Sentiment| |  Entities  |
                                    |(joblib) | | Analyzer| | Extractor  |
                                    +---------+ +---------+ +------------+
```

---

## Phase-by-Phase Request Flow

A single user message passes through **6 distinct phases** before a response is returned.

---

### Phase 1 — Input & Preprocessing

**File:** `static/script.js` → `app.py`

```
User types message
       |
       v
[script.js] validates input (non-empty, max 500 chars)
       |
       v
POST /chat  { "message": "where is my order?" }
       |
       v
[app.py] get_engine() — loads or creates ChatbotEngine for session
       |
       v
[engine.py] _preprocess(text)
  - lowercase
  - strip whitespace
  - remove punctuation via regex
  Output: "where is my order"
```

---

### Phase 2 — Entity Extraction

**File:** `chatbot/engine.py` → `_extract_entities()`

```
Raw user input (before preprocessing)
       |
       v
Regex pattern 1: Order ID
  r'\b(order[#\s-]*)?([A-Z]{2,3}[-]?\d{5,10}|\d{6,10})\b'
  Match: "ORD12345" or "123456789"
       |
Regex pattern 2: Email address
  r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
  Match: "user@example.com"
       |
       v
entities = { "order_id": "ORD12345", "email": "..." }
```

---

### Phase 3 — Sentiment Analysis

**File:** `chatbot/engine.py` → `_detect_sentiment()`

```
Raw user input
       |
       v
VADER SentimentIntensityAnalyzer.polarity_scores(text)
  Returns: { neg: 0.0, neu: 0.511, pos: 0.0, compound: -0.511 }
       |
       v
Threshold check:
  compound >= +0.05  --> "positive"
  compound <= -0.05  --> "negative"
  else               --> "neutral"
       |
       v
sentiment = "negative", sentiment_score = -0.511
```

---

### Phase 4 — Intent Classification (ML Core)

**File:** `chatbot/engine.py` → `_get_intent()`

```
Preprocessed text: "where is my order"
       |
       v
[Loaded SVM Pipeline from chatbot/model/intent_model.pkl]
  Step 1: TfidfVectorizer (bigrams, sublinear_tf=True)
          "where is my order" --> sparse vector [0.0, 0.43, 0.0, 0.71, ...]
       |
  Step 2: LinearSVC.predict()
          sparse vector --> label index (e.g. 8)
       |
  Step 3: LinearSVC.decision_function()
          Returns raw scores for all 15 classes
          e.g. [-1.2, -0.8, ..., 2.1, ..., -0.3]
       |
  Step 4: Min-max normalize scores to get confidence
          shifted = scores - scores.min()
          confidence = shifted[predicted_idx] / shifted.sum()
          confidence = 0.458  (45.8%)
       |
       v
[LabelEncoder from chatbot/model/label_encoder.pkl]
  label index 8 --> "order_status"
       |
       v
tag = "order_status", confidence = 0.458
```

---

### Phase 5 — Response Generation

**File:** `chatbot/engine.py` → `_build_response()`

```
tag = "order_status"
sentiment = "neutral"
entities = {}
       |
       v
[intents.json] find intent where tag == "order_status"
  Pick random response from responses[] array
       |
       v
Sentiment gate:
  if sentiment == "negative" AND tag not in ["complaint", "fallback"]:
      prepend "I understand your frustration..."
       |
       v
Entity injection:
  if "order_id" in entities:
      replace "your order" with "order ORD12345"
       |
       v
Suggestion lookup from suggestion_map[tag]
  --> ["Return Policy", "Cancel Order", "Contact Support"]
       |
       v
Final response dict assembled
```

---

### Phase 6 — Response Delivery

**File:** `app.py` → `static/script.js`

```
engine.get_response() returns:
{
  "response":        "To track your order...",
  "intent":          "order_status",
  "confidence":      45.8,
  "sentiment":       "neutral",
  "sentiment_score": 0.0,
  "entities":        {},
  "suggestions":     ["Return Policy", "Cancel Order", "Contact Support"],
  "model":           "SVM"
}
       |
       v
Flask jsonify() --> HTTP 200 JSON response
       |
       v
[script.js] receives response after simulated typing delay
  - appendMessage("bot", response.response, meta)
  - updateConfidence(response.confidence)
  - updateSuggestions(response.suggestions)
  - Show intent tag + sentiment icon in message metadata
```

---

## ML Training Architecture

**File:** `train.py`

```
intents.json
     |
     v
load_data()
  - Extract all patterns + labels
  - preprocess() each pattern
  - Output: X (453 strings), y (453 labels)
     |
     v
LabelEncoder.fit_transform(y)
  - Maps string labels to integers
  - "order_status" --> 8
     |
     +---------------------------+
     |                           |
     v                           v
SVM Pipeline                NB Pipeline
TfidfVectorizer              TfidfVectorizer
  ngram_range=(1,2)            ngram_range=(1,2)
  sublinear_tf=True
LinearSVC(C=1.0)             MultinomialNB(alpha=0.1)
     |                           |
     v                           v
cross_val_score(cv=5)       cross_val_score(cv=5)
SVM  mean=0.7148            NB   mean=0.7016
     |
     v
train_test_split(test_size=0.2, stratify=y)
     |
     +---------------------------+
     |                           |
     v                           v
svm.fit(X_train)            nb.fit(X_train)
svm.predict(X_test)         nb.predict(X_test)
accuracy=75.82%             accuracy=72.53%
     |
     v
Winner: SVM (75.82%)
     |
     v
classification_report()  +  confusion_matrix()
     |
     v
best_pipeline.fit(X_full, y_full)   <-- retrain on ALL data
     |
     v
joblib.dump(pipeline,  chatbot/model/intent_model.pkl)
joblib.dump(encoder,   chatbot/model/label_encoder.pkl)
json.dump(metrics,     chatbot/model/metrics.json)
```

---

## File Responsibilities

| File | Phase | Responsibility |
|------|-------|---------------|
| `static/script.js` | 1, 6 | User input capture, API calls, DOM rendering |
| `templates/index.html` | 1, 6 | Chat UI structure |
| `static/style.css` | 6 | Visual styling, dark theme |
| `app.py` | 1, 6 | Flask routes, session management, JSON I/O |
| `chatbot/engine.py` | 1–5 | Full NLP pipeline orchestration |
| `chatbot/intents.json` | 5 | Intent definitions, patterns, responses |
| `chatbot/model/intent_model.pkl` | 4 | Trained TF-IDF + SVM pipeline |
| `chatbot/model/label_encoder.pkl` | 4 | Integer-to-label mapping |
| `chatbot/model/metrics.json` | 6 | Training metrics for `/metrics` endpoint |
| `train.py` | Training | Model training, evaluation, persistence |

---

## Session & State Management

```
Browser                Flask (app.py)              engines dict (memory)
  |                         |                              |
  |-- POST /chat ---------->|                              |
  |                         |-- session['session_id'] --->|
  |                         |   (uuid per browser tab)    |
  |                         |                              |
  |                         |<-- ChatbotEngine instance --|
  |                         |   (one per session)         |
  |                         |                              |
  |                         |   engine.conversation_history
  |                         |   grows with each turn      |
  |                         |                              |
  |-- POST /reset --------->|                              |
  |                         |-- del engines[session_id] ->|
  |                         |-- del session['session_id'] |
```

---

## Technology Dependency Map

```
app.py
  └── flask
  └── chatbot/__init__.py
        └── chatbot/engine.py
              └── scikit-learn  (TfidfVectorizer, LinearSVC pipeline)
              └── joblib        (model load/save)
              └── vaderSentiment (SentimentIntensityAnalyzer)
              └── numpy         (decision_function score normalization)
              └── chatbot/intents.json
              └── chatbot/model/intent_model.pkl
              └── chatbot/model/label_encoder.pkl

train.py
  └── scikit-learn  (Pipeline, TfidfVectorizer, LinearSVC, MultinomialNB,
  |                  cross_val_score, train_test_split, classification_report,
  |                  confusion_matrix, LabelEncoder)
  └── joblib
  └── numpy
  └── chatbot/intents.json  (input)
  └── chatbot/model/        (output)
```
