# SupportAI — Future Roadmap

This document outlines planned enhancements across model quality, infrastructure, and user experience.

---

## Phase 1 — Model Improvements (Short Term)

### 1.1 Deep Learning Intent Classifier
Replace LinearSVC with a fine-tuned transformer model for significantly higher accuracy.

- Integrate `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) for semantic embeddings
- Replace TF-IDF vectors with dense 384-dim sentence embeddings
- Expected accuracy improvement: 75% → 90%+

```bash
pip install sentence-transformers
```

### 1.2 Named Entity Recognition (NER)
Replace regex entity extraction with a proper NER model.

- Use `spaCy` with a custom NER pipeline
- Detect: order IDs, product names, dates, locations, phone numbers
- Train on domain-specific entities from conversation logs

### 1.3 Larger Training Dataset
- Expand from 453 to 2000+ samples per intent using data augmentation
- Use `nlpaug` for synonym replacement and back-translation augmentation
- Add real customer query logs (anonymized) for production-grade training

---

## Phase 2 — Conversational Intelligence (Medium Term)

### 2.1 Multi-Turn Context Tracking
Current bot treats every message independently. Add conversation memory.

- Track last 3–5 turns in session context
- Resolve pronouns ("it", "that order") using prior context
- Example: User says "cancel it" after asking about an order → resolve "it" to the order

### 2.2 Slot Filling
Proactively ask for missing information before responding.

- If user says "track my order" without an order ID → ask for it
- If user says "I want to return" → ask which item and reason
- Build a slot-filling state machine per intent

### 2.3 Fallback Escalation Flow
Smarter handling when the bot can't answer.

- After 2 consecutive fallbacks → offer live agent handoff
- Log unrecognized queries to a review queue for retraining
- Send email/Slack alert to support team for urgent unresolved issues

---

## Phase 3 — Infrastructure & Deployment (Medium Term)

### 3.1 Database Integration
Replace in-memory session storage with a persistent database.

- Use `SQLite` (dev) or `PostgreSQL` (prod) via `SQLAlchemy`
- Store full conversation history, user profiles, and feedback
- Enable analytics dashboard on past conversations

### 3.2 REST API Authentication
Secure the `/chat` endpoint for production use.

- Add JWT-based authentication (`flask-jwt-extended`)
- Rate limiting per user/IP (`flask-limiter`)
- API key support for third-party integrations

### 3.3 Docker & Cloud Deployment
- Add `Dockerfile` and `docker-compose.yml`
- Deploy to AWS (Elastic Beanstalk or ECS) or Render
- Add CI/CD pipeline via GitHub Actions for auto-deploy on push

```dockerfile
# Planned Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python train.py
CMD ["python", "app.py"]
```

---

## Phase 4 — Advanced AI Features (Long Term)

### 4.1 LLM Integration (GPT / Claude / Bedrock)
For queries outside the trained intents, fall back to a large language model.

- Use AWS Bedrock (Claude) or OpenAI API as a fallback layer
- Only invoke LLM when SVM confidence < 30%
- Keeps costs low while handling edge cases intelligently

### 4.2 Voice Support
- Integrate Web Speech API for voice input in the browser
- Add text-to-speech for bot responses
- Support multilingual voice queries

### 4.3 Multilingual Support
- Detect input language using `langdetect`
- Translate to English → classify → translate response back
- Priority languages: Spanish, French, Hindi, Arabic

### 4.4 Proactive Notifications
- Push order status updates to users without them asking
- Trigger alerts for delayed shipments, payment failures, or policy changes
- Integrate with WebSockets (`flask-socketio`) for real-time push

---

## Phase 5 — Analytics & Monitoring (Long Term)

### 5.1 Conversation Analytics Dashboard
- Track most common intents, fallback rate, average confidence
- Visualize sentiment trends over time
- Identify intents with low F1 scores for retraining priority

### 5.2 A/B Testing for Responses
- Test multiple response variants per intent
- Track which responses lead to faster resolution
- Auto-promote best-performing responses

### 5.3 Continuous Learning Pipeline
- Collect user feedback (thumbs up/down) per response
- Flag low-rated responses for human review
- Periodically retrain model with new labeled data

---

## Summary Table

| Phase | Feature | Priority | Effort |
|-------|---------|----------|--------|
| 1 | Sentence Transformers | High | Medium |
| 1 | spaCy NER | High | Medium |
| 2 | Multi-turn context | High | High |
| 2 | Slot filling | Medium | High |
| 3 | Database (PostgreSQL) | High | Medium |
| 3 | Docker + Cloud deploy | High | Low |
| 4 | LLM fallback (Bedrock) | Medium | Medium |
| 4 | Multilingual support | Medium | High |
| 5 | Analytics dashboard | Low | Medium |
| 5 | Continuous learning | Low | High |
