# SupportAI — Real-World Usage Guide

This document explains how SupportAI can be deployed and used in a real business environment — from embedding it on a website to integrating it with live order systems, CRMs, and cloud infrastructure.

---

## Who Can Use This?

SupportAI is built for any business that handles customer queries at scale:

| Business Type | Use Case |
|---------------|----------|
| E-commerce store | Order tracking, returns, refunds, shipping queries |
| SaaS company | Account help, billing issues, onboarding support |
| Healthcare clinic | Appointment booking, FAQs, insurance queries |
| Bank / Fintech | Transaction issues, card help, account access |
| Telecom provider | Plan info, billing, technical support |
| Food delivery app | Order status, refunds, delivery complaints |

---

## Real-World Deployment Options

### Option 1 — Embed on Your Website

The most common real-world use. Add SupportAI as a floating chat widget on any website.

**Step 1:** Deploy the Flask app to a cloud server (see cloud section below).

**Step 2:** Add this snippet to any webpage:

```html
<!-- Add before </body> on your website -->
<script>
  (function() {
    var iframe = document.createElement('iframe');
    iframe.src = 'https://your-supportai-domain.com';
    iframe.style.cssText = 'position:fixed;bottom:20px;right:20px;width:400px;height:600px;border:none;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.3);z-index:9999';
    document.body.appendChild(iframe);
  })();
</script>
```

**Step 3:** Users on your website can now chat with SupportAI without leaving the page.

---

### Option 2 — REST API Integration

Expose SupportAI as an API so any app (mobile, desktop, third-party) can use it.

**Example: Mobile app calling the chatbot**

```python
import requests

response = requests.post('https://your-domain.com/chat', json={
    'message': 'Where is my order ORD123456?'
})

data = response.json()
print(data['response'])   # "To track order ORD123456, please visit..."
print(data['intent'])     # "order_status"
print(data['confidence']) # 64.2
```

**Example: WhatsApp / Telegram bot integration**

```python
# When a WhatsApp message arrives via Twilio webhook:
@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    user_msg = request.form.get('Body')
    engine   = ChatbotEngine()
    result   = engine.get_response(user_msg)

    # Send reply back via Twilio
    resp = MessagingResponse()
    resp.message(result['response'])
    return str(resp)
```

---

### Option 3 — Connect to a Real Order Database

Right now responses are static text. In production, connect the engine to your actual database so it returns live order data.

**Current behavior:**
> "To track your order, please visit our website..."

**Real-world behavior after DB integration:**
> "Your order ORD123456 was shipped on June 12 via FedEx. Estimated delivery: June 15. Tracking: 794644792798."

**How to implement:**

```python
# In engine.py, inside get_response():
if tag == 'order_status' and 'order_id' in entities:
    order = db.query(f"SELECT * FROM orders WHERE id = '{entities['order_id']}'")
    if order:
        response = f"Your order {order['id']} is currently {order['status']}. " \
                   f"Expected delivery: {order['delivery_date']}."
```

**Supported databases:**

```python
# PostgreSQL (production)
import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])

# MySQL
import mysql.connector
conn = mysql.connector.connect(host='...', user='...', password='...', database='...')

# MongoDB (for flexible schemas)
from pymongo import MongoClient
client = MongoClient(os.environ['MONGO_URI'])
```

---

### Option 4 — Connect to a CRM (Salesforce, HubSpot, Zendesk)

When the bot can't resolve an issue, automatically create a support ticket in your CRM.

```python
# Auto-create Zendesk ticket when bot hits fallback 2x in a row
import requests

def create_zendesk_ticket(user_message, conversation_history):
    requests.post(
        'https://yourcompany.zendesk.com/api/v2/tickets.json',
        auth=('agent@company.com', os.environ['ZENDESK_API_KEY']),
        json={
            'ticket': {
                'subject': 'Chatbot escalation',
                'comment': {'body': f"User said: {user_message}\n\nHistory: {conversation_history}"},
                'priority': 'normal'
            }
        }
    )
```

---

## Cloud Deployment (Step by Step)

### Deploy to AWS EC2 (Recommended for Production)

```bash
# 1. Launch an EC2 instance (Ubuntu 22.04, t2.micro for small traffic)
# 2. SSH into the instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update && sudo apt install python3-pip nginx -y
git clone https://github.com/himanshu0107-cmd/ChatBot-For-Customer-Service.git
cd ChatBot-For-Customer-Service
pip3 install -r requirements.txt

# 4. Train the model
python3 train.py

# 5. Run with Gunicorn (production WSGI server, not Flask dev server)
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 6. Configure Nginx as reverse proxy
sudo nano /etc/nginx/sites-available/supportai
```

```nginx
# Nginx config
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 7. Enable HTTPS with Let's Encrypt (free SSL)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

### Deploy with Docker (Easiest for Any Cloud)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
RUN python train.py
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

```bash
# Build and run
docker build -t supportai .
docker run -d -p 80:8000 --name supportai supportai

# Deploy to AWS ECS, Google Cloud Run, or Azure Container Apps
# by pushing this image to a container registry
```

---

### Deploy to Render (Free Tier — Easiest)

1. Push code to GitHub (already done)
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt && python train.py`
5. Set start command: `gunicorn app:app`
6. Click Deploy — live URL in 2 minutes

---

## Environment Variables for Production

Never hardcode secrets. Use environment variables:

```bash
# .env file (never commit this)
SECRET_KEY=your-very-long-random-secret-key-here
DATABASE_URL=postgresql://user:password@host:5432/dbname
ZENDESK_API_KEY=your-zendesk-key
FLASK_DEBUG=false
```

```python
# Load in app.py
from dotenv import load_dotenv
load_dotenv()
app.secret_key = os.environ['SECRET_KEY']
```

---

## Handling Real Traffic

| Traffic Level | Setup |
|---------------|-------|
| < 100 users/day | Flask dev server, single process |
| 100–1000 users/day | Gunicorn with 4 workers, single server |
| 1000–10,000 users/day | Gunicorn + Nginx + PostgreSQL session store |
| 10,000+ users/day | Load balancer + multiple EC2 instances + Redis sessions |

**Switch to Redis sessions for multi-server deployments:**

```python
from flask_session import Session
app.config['SESSION_TYPE']       = 'redis'
app.config['SESSION_REDIS']      = redis.from_url(os.environ['REDIS_URL'])
Session(app)
```

---

## Adding Your Own Business Data

To make SupportAI answer questions specific to YOUR business:

**Step 1:** Edit `chatbot/intents.json` and add your real FAQs:

```json
{
  "tag": "store_location",
  "patterns": [
    "where is your store", "store address", "physical location",
    "nearest store", "visit your shop", "store hours"
  ],
  "responses": [
    "Our store is located at 123 Main Street, New York, NY 10001. Open Mon-Sat 9AM-8PM."
  ]
}
```

**Step 2:** Retrain the model:

```bash
python train.py
```

**Step 3:** Restart the app — it auto-loads the new model.

> Add at least 20 patterns per intent for reliable classification. The more varied the patterns, the better the model generalizes.

---

## Monitoring in Production

Track how well the bot is performing in real use:

```python
# Log every conversation to a file or database
import logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO)

# In engine.py get_response():
logging.info(f"intent={tag} conf={conf:.2f} sentiment={sentiment} input={user_input[:100]}")
```

**Key metrics to watch:**

| Metric | Healthy Range | Action if Outside |
|--------|--------------|-------------------|
| Fallback rate | < 10% | Add more training patterns |
| Avg confidence | > 50% | Retrain with more data |
| Negative sentiment rate | < 20% | Review complaint responses |
| Response time | < 500ms | Scale up server |

---

## Summary — From Prototype to Production

```
Local Dev          -->   Cloud Server      -->   Real Business
-----------              ------------             -------------
python app.py            Gunicorn + Nginx         Connected to:
localhost:5000           your-domain.com          - Live order DB
Static responses         HTTPS + SSL              - CRM (Zendesk)
In-memory sessions       PostgreSQL sessions      - WhatsApp / SMS
Manual restart           Auto-restart (systemd)   - Mobile app API
```
