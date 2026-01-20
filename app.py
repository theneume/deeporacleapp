import os
import json
import stripe
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "oracle_v3_secure_key")

# Stripe Config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Gemini Config
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

# Load Protocols
with open('engagement_protocol_v4.json', 'r') as f:
    PROTCOLS = json.load(f)

FREE_LIMIT = 5

@app.route('/')
def index():
    session.clear() # Fresh start for session tracking
    session['message_count'] = 0
    session['paid'] = False
    session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # 1. Paywall Check
    if session.get('message_count', 0) >= FREE_LIMIT and not session.get('paid', False):
        return jsonify({'show_paywall': True})

    data = request.json
    user_msg = data.get('message')
    
    try:
        # 2. System Prompt Logic (Rules 1-8)
        # In a full implementation, you'd insert your ai_system_prompt_v4.txt content here
        chat_session = model.start_chat(history=session.get('chat_history', []))
        response = chat_session.send_message(user_msg)
        
        # 3. Session Management
        session['message_count'] = session.get('message_count', 0) + 1
        history = session.get('chat_history', [])
        history.append({"role": "user", "parts": [user_msg]})
        history.append({"role": "model", "parts": [response.text]})
        session['chat_history'] = history
        session.modified = True
        
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Backend Error: {str(e)}")
        return jsonify({'error': "The Oracle is momentarily offline. Please try again."}), 500

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    # Validation to prevent HTML error pages
    if not stripe.api_key:
        return jsonify({'error': 'Stripe API Key is missing. Check environment variables.'}), 500

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Oracle Deep Exploration Session'},
                    'unit_amount': 295,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'payment-success',
            cancel_url=request.host_url,
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payment-success')
def payment_success():
    session['paid'] = True
    return render_template('index.html', payment_received=True)

if __name__ == '__main__':
    app.run(debug=True)
