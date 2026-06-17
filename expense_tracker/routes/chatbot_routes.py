import os
import requests
from collections import defaultdict
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
        
        # 1. Fetch ALL records
        txs = Transaction.query.filter(
            Transaction.user_id == current_user.id
        ).order_by(Transaction.entry_date.desc()).all()
        
        # 2. Create Monthly Summary (Macro View)
        monthly_summary = defaultdict(float)
        for t in txs:
            month_key = t.entry_date.strftime("%Y-%m")
            monthly_summary[month_key] += t.amount
            
        summary_text = "\n".join([f"{month}: Total Expenses {total}" for month, total in monthly_summary.items()])
        
        # 3. Get Recent 10 Transactions (Micro View)
        recent_txs = txs[:10]
        recent_text = "\n".join([f"{t.entry_date}: {t.amount} {t.currency_code} ({t.category})" for t in recent_txs])
        
        # 4. Strict System Prompt
        system_prompt = (
            "You are a financial expert. "
            "Use the 'Monthly Summary' to answer trend questions. "
            "Use the 'Recent Transactions' for specific details. "
            "Strictly follow: 1. If English input, reply in English. 2. If Roman Urdu, reply in Roman Urdu. "
            "DO NOT mix languages or provide translations."
        )
        
        prompt = f"Monthly Summary:\n{summary_text}\n\nRecent Transactions:\n{recent_text}\n\nUser Question: {user_message}"
        
        # GROQ API Call
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if 'choices' in result:
            ai_reply = result['choices'][0]['message']['content']
            return jsonify({'status': 'success', 'response': ai_reply})
        else:
            return jsonify({'response': 'Error connecting to AI.'}), 500
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return jsonify({'response': 'Server error.'}), 500