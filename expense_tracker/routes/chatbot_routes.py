import os
import requests
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from expense_tracker.models.transaction_model import Transaction

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/message', methods=['POST'])
@login_required
def handle_chat_message():
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        
        txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.entry_date.desc()).limit(15).all()
        history = "\n".join([f"{t.entry_date}: {t.amount} {t.currency_code} ({t.category})" for t in txs])
        
        prompt = f"Data: {history}. \nUser: {user_message}. \nAnswer in user's language."
        
        # GROQ API Call
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, json=payload, headers={**headers})
        result = response.json()
        
        if 'choices' in result:
            ai_reply = result['choices'][0]['message']['content']
            return jsonify({'status': 'success', 'response': ai_reply})
        else:
            print("GROQ ERROR:", result) # Yahan error dikhega agar phir kuch hua
            return jsonify({'response': 'Model update ki wajah se error aya, ab theek hai.'}), 500
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return jsonify({'response': 'Server error, check terminal.'}), 500