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
        self.intents              = self._load_intents()
        self.vader                = SentimentIntensityAnalyzer()
        self.model, self.label_encoder, self.metrics = self._load_model()
        self.conversation_history = []
        # Build a fast tag -> responses lookup
        self.responses_map = {i['tag']: i['responses'] for i in self.intents}

    # ── Loaders ──────────────────────────────────────────────────────────────

    def _load_intents(self):
        path = os.path.join(BASE_DIR, 'intents.json')
        with open(path, encoding='utf-8') as f:
            return json.load(f)['intents']

    def _load_model(self):
        model_path   = os.path.join(MODEL_DIR, 'intent_model.pkl')
        encoder_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
        metrics_path = os.path.join(MODEL_DIR, 'metrics.json')

        if not os.path.exists(model_path):
            print('[SupportAI] Model not found — running training pipeline...')
            import sys
            sys.path.insert(0, os.path.dirname(BASE_DIR))
            from train import train
            train()

        model   = joblib.load(model_path)
        encoder = joblib.load(encoder_path)
        metrics = {}
        if os.path.exists(metrics_path):
            with open(metrics_path, encoding='utf-8') as f:
                metrics = json.load(f)
        return model, encoder, metrics

    # ── NLP helpers ──────────────────────────────────────────────────────────

    def _preprocess(self, text):
        return re.sub(r'[^\w\s]', '', text.lower().strip())

    def _sentiment(self, text):
        c = self.vader.polarity_scores(text)['compound']
        if c >= 0.05:
            return 'positive', round(c, 3)
        if c <= -0.05:
            return 'negative', round(c, 3)
        return 'neutral', round(c, 3)

    def _entities(self, text):
        out = {}
        m = re.search(r'\b(order[#\s-]*)?([A-Z]{2,3}[-]?\d{5,10}|\d{6,10})\b', text, re.IGNORECASE)
        if m:
            out['order_id'] = m.group(0).strip()
        m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
        if m:
            out['email'] = m.group(0)
        return out

    # ── ML Intent Classification ──────────────────────────────────────────────

    def _classify(self, text):
        """
        Use the trained SVM pipeline to predict intent and confidence.
        Returns (tag: str, confidence: float 0-1)
        """
        processed = self._preprocess(text)

        # SVM predict
        raw_idx = self.model.predict([processed])[0]
        tag     = str(self.label_encoder.inverse_transform([raw_idx])[0])

        # Confidence from decision_function (distance from hyperplane)
        try:
            scores  = self.model.decision_function([processed])[0]
            shifted = scores - scores.min()
            total   = shifted.sum()
            conf    = float(shifted[raw_idx] / total) if total > 0 else 0.5
        except Exception:
            conf = 0.75

        # Low confidence → fallback
        if conf < 0.08:
            return 'fallback', conf

        return tag, conf

    # ── Response builder ─────────────────────────────────────────────────────

    def _pick_response(self, tag):
        responses = self.responses_map.get(tag) or self.responses_map.get('fallback', ['I am not sure how to help with that.'])
        return random.choice(responses)

    def _suggestions(self, tag):
        MAP = {
            'order_status':   ['Return Policy', 'Cancel Order', 'Contact Support'],
            'return_policy':  ['Order Status', 'Warranty', 'Contact Support'],
            'payment_issues': ['Contact Support', 'Account Help', 'Order Status'],
            'account_help':   ['Contact Support', 'Payment Issues', 'Order Status'],
            'shipping_info':  ['Order Status', 'Return Policy', 'Contact Support'],
            'greeting':       ['Track Order', 'Return Policy', 'Shipping Info', 'Contact Support'],
            'complaint':      ['Contact Support', 'Return Policy', 'Warranty'],
            'cancel_order':   ['Order Status', 'Return Policy', 'Contact Support'],
            'warranty':       ['Return Policy', 'Contact Support', 'Order Status'],
            'discount_promo': ['Order Status', 'Contact Support', 'Return Policy'],
            'product_info':   ['Order Status', 'Shipping Info', 'Contact Support'],
            'hours':          ['Contact Support', 'Order Status', 'Return Policy'],
            'thanks':         ['Order Status', 'Return Policy', 'Contact Support'],
            'goodbye':        [],
            'fallback':       ['Track Order', 'Return Policy', 'Contact Support', 'Shipping Info'],
        }
        return MAP.get(tag, ['Order Status', 'Return Policy', 'Contact Support'])

    # ── Public API ────────────────────────────────────────────────────────────

    def get_response(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return {
                'response': 'Please type a message so I can help you!',
                'intent': 'empty', 'confidence': 0,
                'sentiment': 'neutral', 'sentiment_score': 0.0,
                'entities': {}, 'suggestions': [], 'model': 'SVM'
            }

        entities          = self._entities(user_input)
        sentiment, score  = self._sentiment(user_input)
        tag, conf         = self._classify(user_input)
        response          = self._pick_response(tag)

        # Adapt tone for frustrated users
        if sentiment == 'negative' and tag not in ('complaint', 'fallback', 'goodbye'):
            response = "I understand your frustration, and I'm here to help. " + response

        # Inject detected order ID into response
        if 'order_id' in entities:
            response = response.replace('your order', f"order {entities['order_id']}", 1)

        self.conversation_history.append({'role': 'user', 'message': user_input, 'intent': tag})
        self.conversation_history.append({'role': 'bot',  'message': response})

        return {
            'response':        response,
            'intent':          tag,
            'confidence':      round(conf * 100, 1),
            'sentiment':       sentiment,
            'sentiment_score': score,
            'entities':        entities,
            'suggestions':     self._suggestions(tag),
            'model':           str(self.metrics.get('model', 'SVM')),
        }

    def get_metrics(self):
        return self.metrics
