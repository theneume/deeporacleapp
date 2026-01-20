#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import random
import stripe  # Clean import, no aliases to avoid confusion

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
FREE_MESSAGE_LIMIT = 5
GEMINI_API_KEY = "AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y"

# Initialize Stripe once at the top level
stripe.api_key = STRIPE_SECRET_KEY

# Storage
conversations = {}
ca_rotation_tracker = {}

# --- LOAD RAG DATA (Wrapped in try/except for safety) ---
def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

DEEPSYKE_CORE = load_json('deepsyke_core_rag.json')
CULTURAL_AVATARS = load_json('cultural_avatars_rag.json')
ENGAGEMENT_PROTOCOL = load_json('engagement_protocol.json')
ENGAGEMENT_PROTOCOL_V4 = load_json('engagement_protocol_v4.json')
BUSINESS_RAG = load_json('business_rag.json')

with open('ai_system_prompt.txt', 'r') as f:
    AI_SYSTEM_PROMPT_TEMPLATE = f.read()
with open('ai_system_prompt_v4.txt', 'r') as f:
    AI_SYSTEM_PROMPT_TEMPLATE_V4 = f.read()

# --- STRIPE PAYWALL ENDPOINT ---
@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in conversations:
            return jsonify({'error': 'Invalid session'}), 400

        if not stripe.api_key:
            return jsonify({'error': 'Stripe key not found on server'}), 500

        # Build the session using the global 'stripe' object
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Oracle Psychology - Unlimited Session',
                        'description': 'Continue your deep self-discovery journey',
                    },
                    'unit_amount': 295,  # $2.95
                },
                'quantity': 1,
            }],
            mode='payment',
            # Ensure these URLs match your Render domain
            success_url=f"https://deeporacleapp.onrender.com/payment-success?session_id={session_id}",
            cancel_url=f"https://deeporacleapp.onrender.com/?session_id={session_id}",
            metadata={'session_id': session_id}
        )

        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"STRIPE ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- CHAT ENDPOINT WITH PAYWALL LOGIC ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    session_id = data.get('session_id')
    user_message = data.get('message', '')

    if not session_id or session_id not in conversations:
        return jsonify({'error': 'Session not initialized'}), 400

    conv = conversations[session_id]
    
    # PAYWALL LOGIC
    if not conv.get('paid', False):
        message_count = len([m for m in conv.get('history', []) if m['role'] == 'user'])
        if message_count >= FREE_MESSAGE_LIMIT:
            return jsonify({
                'error': 'Payment required',
                'message': 'You have reached the limit of the free Oracle session.',
                'paywall': True
            }), 402

    # If paid or under limit, proceed to Gemini
    # (Insert your build_system_prompt and call_gemini_api logic here)
    # response_text = call_gemini_api(system_prompt, user_message)
    
    return jsonify({'response': "AI Response placeholder - logic is now safe."})

# --- REMAINING ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/payment-success')
def payment_success():
    session_id = request.args.get('session_id')
    if session_id and session_id in conversations:
        conversations[session_id]['paid'] = True
    return render_template('index.html', payment_success=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
