from flask import Flask, render_template, request, jsonify, session
from chatbot import ChatbotEngine
import uuid
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
    result = engine.get_response(user_message)
    return jsonify(result)

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

if __name__ == '__main__':
    app.run(debug=True)
