import json
import random
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ChatbotEngine:
    def __init__(self):
        self.intents = self._load_intents()
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        self.patterns = []
        self.tags = []
        self._train()
        self.conversation_history = []
        self.user_context = {}

    def _load_intents(self):
        with open(os.path.join(BASE_DIR, 'intents.json'), 'r') as f:
            return json.load(f)['intents']

    def _train(self):
        for intent in self.intents:
            if intent['tag'] == 'fallback':
                continue
            for pattern in intent['patterns']:
                self.patterns.append(self._preprocess(pattern))
                self.tags.append(intent['tag'])
        if self.patterns:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.patterns)

    def _preprocess(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def _detect_sentiment(self, text):
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'angry', 'frustrated', 'disappointed', 'useless']
        positive_words = ['great', 'awesome', 'excellent', 'love', 'perfect', 'amazing', 'wonderful', 'fantastic']
        text_lower = text.lower()
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        if neg_count > pos_count:
            return 'negative'
        elif pos_count > neg_count:
            return 'positive'
        return 'neutral'

    def _extract_entities(self, text):
        entities = {}
        order_match = re.search(r'\b(order[#\s-]*)?([A-Z]{2,3}[-]?\d{5,10}|\d{6,10})\b', text, re.IGNORECASE)
        if order_match:
            entities['order_id'] = order_match.group(0)
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            entities['email'] = email_match.group(0)
        return entities

    def _get_intent(self, text):
        processed = self._preprocess(text)
        query_vec = self.vectorizer.transform([processed])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        if best_score < 0.15:
            return 'fallback', best_score
        return self.tags[best_idx], best_score

    def _get_response(self, tag):
        for intent in self.intents:
            if intent['tag'] == tag:
                return random.choice(intent['responses'])
        return random.choice([i for i in self.intents if i['tag'] == 'fallback'][0]['responses'])

    def _build_response(self, tag, confidence, text, entities, sentiment):
        response = self._get_response(tag)

        # Sentiment-aware prefix
        if sentiment == 'negative' and tag not in ['complaint', 'fallback']:
            response = "I understand your frustration, and I'm here to help. " + response

        # Entity acknowledgment
        if 'order_id' in entities:
            response = response.replace("your order", f"order {entities['order_id']}")

        return {
            'response': response,
            'intent': tag,
            'confidence': round(float(confidence) * 100, 1),
            'sentiment': sentiment,
            'entities': entities,
            'suggestions': self._get_suggestions(tag)
        }

    def _get_suggestions(self, current_tag):
        suggestion_map = {
            'order_status': ['Return Policy', 'Cancel Order', 'Contact Support'],
            'return_policy': ['Order Status', 'Warranty', 'Contact Support'],
            'payment_issues': ['Contact Support', 'Account Help', 'Order Status'],
            'account_help': ['Contact Support', 'Payment Issues', 'Order Status'],
            'shipping_info': ['Order Status', 'Return Policy', 'Contact Support'],
            'greeting': ['Track Order', 'Return Policy', 'Shipping Info', 'Contact Support'],
            'complaint': ['Contact Support', 'Return Policy', 'Warranty'],
            'fallback': ['Track Order', 'Return Policy', 'Contact Support', 'Shipping Info'],
        }
        return suggestion_map.get(current_tag, ['Order Status', 'Return Policy', 'Contact Support'])

    def get_response(self, user_input):
        if not user_input.strip():
            return {'response': "Please type a message so I can help you!", 'intent': 'empty', 'confidence': 0, 'sentiment': 'neutral', 'entities': {}, 'suggestions': []}

        entities = self._extract_entities(user_input)
        sentiment = self._detect_sentiment(user_input)
        tag, confidence = self._get_intent(user_input)

        self.conversation_history.append({'role': 'user', 'message': user_input, 'intent': tag})

        result = self._build_response(tag, confidence, user_input, entities, sentiment)
        self.conversation_history.append({'role': 'bot', 'message': result['response']})

        return result
