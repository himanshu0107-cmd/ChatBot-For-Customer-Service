from flask import Flask, render_template, request, jsonify, session
from chatbot import ChatbotEngine
import uuid
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supportai-secret-key-2024')

# One engine instance per session stored in a dict
engines = {}

def get_engine():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    sid = session['session_id']
    if sid not in engines:
        engines[sid] = ChatbotEngine()
    return engines[sid]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    engine = get_engine()
    try:
        result = engine.get_response(user_message)
        return jsonify(result)
    except Exception as e:
        print(f'[ERROR] /chat failed: {e}')
        return jsonify({'response': 'Something went wrong on my end. Please try again.', 'intent': 'error', 'confidence': 0, 'sentiment': 'neutral', 'sentiment_score': 0.0, 'entities': {}, 'suggestions': [], 'model': 'SVM'}), 200

@app.route('/reset', methods=['POST'])
def reset():
    if 'session_id' in session:
        engines.pop(session['session_id'], None)
        session.pop('session_id', None)
    return jsonify({'status': 'reset'})

@app.route('/history', methods=['GET'])
def history():
    engine = get_engine()
    return jsonify({'history': engine.conversation_history})

@app.route('/metrics', methods=['GET'])
def metrics():
    engine = get_engine()
    return jsonify(engine.get_metrics())

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug)
