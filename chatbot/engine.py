import json
import random
import re
import os
import joblib
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')


class ChatbotEngine:
    def __init__(self):
        self.intents = self._load_intents()
        self.vader   = SentimentIntensityAnalyzer()
        self.model, self.label_encoder, self.metrics = self._load_model()
        self.conversation_history = []

    def _load_intents(self):
        with open(os.path.join(BASE_DIR, 'intents.json')) as f:
            return json.load(f)['intents']

    def _load_model(self):
        model_path   = os.path.join(MODEL_DIR, 'intent_model.pkl')
        encoder_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
        metrics_path = os.path.join(MODEL_DIR, 'metrics.json')

        # Auto-train if model files are missing
        if not os.path.exists(model_path):
            print("[SupportAI] Model not found — running training pipeline...")
            import sys
            sys.path.insert(0, os.path.dirname(BASE_DIR))
            from train import train
            train()

        model   = joblib.load(model_path)
        encoder = joblib.load(encoder_path)
        metrics = {}
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                metrics = json.load(f)
        return model, encoder, metrics

    def _preprocess(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def _detect_sentiment(self, text):
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        if compound >= 0.05:
            return 'positive', round(compound, 3)
        elif compound <= -0.05:
            return 'negative', round(compound, 3)
        return 'neutral', round(compound, 3)

    def _extract_entities(self, text):
        entities = {}
        order_match = re.search(
            r'\b(order[#\s-]*)?([A-Z]{2,3}[-]?\d{5,10}|\d{6,10})\b', text, re.IGNORECASE
        )
        if order_match:
            entities['order_id'] = order_match.group(0).strip()
        email_match = re.search(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text
        )
        if email_match:
            entities['email'] = email_match.group(0)
        return entities

    def _get_intent(self, text):
        processed  = self._preprocess(text)
        label_idx  = self.model.predict([processed])[0]
        tag        = str(self.label_encoder.inverse_transform([label_idx])[0])

        try:
            scores     = self.model.decision_function([processed])[0]
            # Normalize decision scores to a 0-1 confidence using min-max
            shifted    = scores - scores.min()
            total      = shifted.sum()
            confidence = float(shifted[label_idx] / total) if total > 0 else 0.5
        except Exception:
            confidence = 0.85

        if confidence < 0.08:
            return 'fallback', confidence
        return tag, confidence

    def _get_response(self, tag):
        for intent in self.intents:
            if intent['tag'] == tag:
                return random.choice(intent['responses'])
        fallback = next(i for i in self.intents if i['tag'] == 'fallback')
        return random.choice(fallback['responses'])

    def _get_suggestions(self, tag):
        suggestion_map = {
            'order_status':   ['Return Policy', 'Cancel Order', 'Contact Support'],
            'return_policy':  ['Order Status', 'Warranty', 'Contact Support'],
            'payment_issues': ['Contact Support', 'Account Help', 'Order Status'],
            'account_help':   ['Contact Support', 'Payment Issues', 'Order Status'],
            'shipping_info':  ['Order Status', 'Return Policy', 'Contact Support'],
            'greeting':       ['Track Order', 'Return Policy', 'Shipping Info', 'Contact Support'],
            'complaint':      ['Contact Support', 'Return Policy', 'Warranty'],
            'cancel_order':   ['Order Status', 'Return Policy', 'Contact Support'],
            'warranty':       ['Return Policy', 'Contact Support', 'Order Status'],
            'fallback':       ['Track Order', 'Return Policy', 'Contact Support', 'Shipping Info'],
        }
        return suggestion_map.get(tag, ['Order Status', 'Return Policy', 'Contact Support'])

    def get_response(self, user_input):
        if not user_input.strip():
            return {
                'response': "Please type a message so I can help you!",
                'intent': 'empty', 'confidence': 0,
                'sentiment': 'neutral', 'sentiment_score': 0.0,
                'entities': {}, 'suggestions': []
            }

        entities                  = self._extract_entities(user_input)
        sentiment, sent_score     = self._detect_sentiment(user_input)
        tag, confidence           = self._get_intent(user_input)
        response                  = self._get_response(tag)

        # Sentiment-aware prefix for negative users
        if sentiment == 'negative' and tag not in ('complaint', 'fallback'):
            response = "I understand your frustration, and I'm here to help. " + response

        # Acknowledge extracted order ID in response
        if 'order_id' in entities:
            response = response.replace("your order", f"order {entities['order_id']}", 1)

        self.conversation_history.append({'role': 'user',  'message': user_input, 'intent': tag})
        self.conversation_history.append({'role': 'bot',   'message': response})

        return {
            'response':        response,
            'intent':          tag,
            'confidence':      round(confidence * 100, 1),
            'sentiment':       sentiment,
            'sentiment_score': sent_score,
            'entities':        entities,
            'suggestions':     self._get_suggestions(tag),
            'model':           self.metrics.get('model', 'SVM'),
        }

    def get_metrics(self):
        return self.metrics
