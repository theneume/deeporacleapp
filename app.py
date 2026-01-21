#!/usr/bin/env python3
"""
Deepsyke Core Integration - Universal Bot Framework
This code bridges all components and should work for any bot with minimal changes
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import random
import stripe

app = Flask(__name__)
CORS(app)

# Stripe Configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
FREE_MESSAGE_LIMIT = 5  # 5 free messages before paywall

# Set Stripe API key
stripe.api_key = STRIPE_SECRET_KEY

# Validate Stripe configuration
if stripe.api_key:
    print(f"Stripe configured with API key: {stripe.api_key[:10]}...")
    print(f"Full key length: {len(stripe.api_key)} characters")
else:
    print("WARNING: Stripe API key not configured")
    print(f"Environment variable 'STRIPE_SECRET_KEY' value: {STRIPE_SECRET_KEY[:10] if STRIPE_SECRET_KEY else 'NOT SET'}")

# Store conversations in memory
conversations = {}
ca_rotation_tracker = {}  # Tracks rotation position for each type (global across sessions)

# Redirect /api/* to proper routes
@app.route('/api/health')
def api_health():
    return health()

@app.route('/api/init-profile', methods=['POST'])
def api_init_profile():
    return init_profile()

@app.route('/api/chat', methods=['POST'])
def api_chat():
    return chat()

# Redirect /api/* to Flask routes
# API redirect routes handled above

# Load core Deepsyke framework (UNIVERSAL - never changes)
with open('deepsyke_core_rag.json', 'r') as f:
    DEEPSYKE_CORE = json.load(f)

# Load cultural avatars database (UNIVERSAL - never changes)
with open('cultural_avatars_rag.json', 'r') as f:
    CULTURAL_AVATARS = json.load(f)

# Load engagement protocol (CUSTOMIZABLE per bot)
with open('engagement_protocol.json', 'r') as f:
    ENGAGEMENT_PROTOCOL = json.load(f)

# Load business RAG (CUSTOMIZABLE per bot)
with open('business_rag.json', 'r') as f:
    BUSINESS_RAG = json.load(f)

# Load AI system prompt template (CUSTOMIZABLE per bot)
with open('ai_system_prompt.txt', 'r') as f:
    AI_SYSTEM_PROMPT_TEMPLATE = f.read()

# CONFIGURATION - Customize these for your bot
GEMINI_API_KEY = "AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y"  # Replace with your key

def calculate_relationships(relationships):
    """Calculate natal types for all provided relationships"""
    calculated_relationships = []
    for rel in relationships:
        try:
            # Use the correct natal calculator
            result = calculate_natal_type(rel['birth_date'], rel['gender'])
            natal_type = result['type']
            
            calculated_relationships.append({
                'name': rel['name'],
                'gender': rel['gender'],
                'birth_date': rel['birth_date'],
                'natal_type': natal_type
            })
        except Exception as e:
            print(f"Error calculating type for {rel.get('name', 'Unknown')}: {e}")
            # Still add relationship without type if calculation fails
            calculated_relationships.append({
                'name': rel['name'],
                'gender': rel['gender'],
                'birth_date': rel['birth_date'],
                'natal_type': 'Unknown'
            })
    
    return calculated_relationships
BOT_PORT = 9009  # Change if needed


def calculate_natal_type(birth_date_str, gender):
    """Calculate natal type from birth date using the correct 9-year cycle algorithm"""
    try:
        # Try multiple date formats
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                birth_date = datetime.strptime(birth_date_str, fmt)
                break
            except:
                continue
        else:
            # Default to SS if parsing fails
            return {
                "type": "SS",
                "archetype": DEEPSYKE_CORE['type_calculator']['rules']['gender_archetypes']['SS'][gender]
            }
        
        # Import the correct calculator
        import natal_calculator
        
        # Use the correct algorithm
        type_code = natal_calculator.calculate_natal_type(
            birth_date.day,
            birth_date.month,
            birth_date.year,
            gender
        )
        
        archetype = DEEPSYKE_CORE['type_calculator']['rules']['gender_archetypes'][type_code][gender]
        
        return {"type": type_code, "archetype": archetype}
    except Exception as e:
        print(f"Error calculating natal type: {e}")
        return {
            "type": "SS",
            "archetype": DEEPSYKE_CORE['type_calculator']['rules']['gender_archetypes']['SS'][gender]
        }


def load_cultural_avatars_for_type(natal_type, session_id=None):
    """Load a rotating selection of cultural avatars for this type"""
    try:
        type_data = CULTURAL_AVATARS['types'].get(natal_type, {})
        all_names = type_data.get('names', [])
        description = type_data.get('description', '')
        
        if not all_names:
            return "", []
        
        # Initialize rotation tracker for this type if not exists
        if natal_type not in ca_rotation_tracker:
            ca_rotation_tracker[natal_type] = {
                'position': random.randint(0, len(all_names) - 1),
                'last_used': [],
                'shuffle_buffer': []
            }
        
        tracker = ca_rotation_tracker[natal_type]
        
        # Get recently used avatars from THIS session only
        recently_used_in_session = []
        if session_id and session_id in conversations:
            recently_used_in_session = conversations[session_id].get('last_avatars_mentioned', [])
        
        # Create a pool of available avatars (exclude those used in this session)
        available_avatars = [name for name in all_names if name not in recently_used_in_session]
        
        # If we've used too many from this type in this session, allow some reuse after buffer
        if len(available_avatars) < 3:
            # Include recently used but not in immediate history
            buffer_avatars = [name for name in all_names if name not in recently_used_in_session[-3:]]
            available_avatars = list(set(available_avatars + buffer_avatars))
        
        # Shuffle the available avatars for variety
        random.shuffle(available_avatars)
        
        # Select 2-3 avatars based on what's available
        num_to_select = min(random.randint(2, 3), len(available_avatars))
        selected_avatars = available_avatars[:num_to_select]
        
        # Update tracker with selected avatars (for cross-session tracking)
        tracker['last_used'] = selected_avatars
        tracker['position'] = (all_names.index(selected_avatars[-1]) + 1) % len(all_names)
        
        # Fetch quotes and stories for each avatar
        avatar_details = []
        for avatar in selected_avatars:
            ca_info = fetch_ca_quotes_stories(avatar, natal_type)
            if ca_info:
                avatar_details.append(ca_info)
        
        # Format for AI with quotes and stories
        avatar_text = f"\n{'='*60}\n"
        avatar_text += f"CULTURAL AVATARS FOR THIS CONVERSATION\n"
        avatar_text += f"{'='*60}\n\n"
        avatar_text += f"Type: {natal_type} - {description}\n\n"
        avatar_text += f"SELECTED AVATARS FOR THIS SESSION ({len(selected_avatars)} of {len(all_names)} total):\n\n"
        
        # Add detailed information for each avatar
        for i, ca_info in enumerate(avatar_details, 1):
            avatar_text += f"{i}. {ca_info['name']}\n"
            if ca_info['quotes']:
                avatar_text += f"   Quotes/Insights:\n"
                for quote in ca_info['quotes'][:2]:  # Top 2 quotes
                    avatar_text += f"   - {quote}\n"
            if ca_info['insights']:
                avatar_text += f"   Key Insights:\n"
                for insight in ca_info['insights'][:2]:  # Top 2 insights
                    avatar_text += f"   • {insight['snippet'][:200]}...\n"
            avatar_text += "\n"
        
        avatar_text += f"USAGE INSTRUCTIONS:\n"
        for instruction in CULTURAL_AVATARS['metadata']['usage_instructions']:
            avatar_text += f"  • {instruction}\n"
        avatar_text += f"\n⚠️ CRITICAL RULES:\n"
        avatar_text += f"  • ONLY reference avatars from the list above\n"
        avatar_text += f"  • Use DIFFERENT avatars each response - don't fixate on one\n"
        avatar_text += f"  • Pull SPECIFIC QUOTES and STORIES from the provided context\n"
        avatar_text += f"  • TIE AVATAR REFERENCE TO CONVERSATION THEME - don't mention randomly\n"
        avatar_text += f"  • {CULTURAL_AVATARS['metadata']['strict_rule']}\n"
        avatar_text += f"{'='*60}\n"
        
        return avatar_text, selected_avatars
    except Exception as e:
        print(f"Error loading cultural avatars: {e}")
        return "", []


def build_system_prompt(profile, conversation_history, use_cultural_avatars=False):
    """Build the complete system prompt by integrating all components"""
    natal_type = profile['natal_type']
    gender = profile['gender']
    name = profile['name']
    archetype = profile['archetype']
    
    # Get type-specific data from Deepsyke core
    type_data = DEEPSYKE_CORE['affinity_zones'][natal_type]
    comm_style = DEEPSYKE_CORE['communication_styles'][natal_type]
    engagement = ENGAGEMENT_PROTOCOL[f'{natal_type}_engagement']
    
    # Build conversation history text
    history_text = ""
    for msg in conversation_history[-6:]:  # Last 6 messages
        role = "User" if msg['role'] == 'user' else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    
    # Build cultural avatars section if enabled
    cultural_avatars_text = ""
    selected_avatars = []
    if use_cultural_avatars and ENGAGEMENT_PROTOCOL['cultural_avatar_protocol']['enabled']:
        cultural_avatars_text, selected_avatars = load_cultural_avatars_for_type(
            natal_type, 
            profile.get('session_id')
        )
    
    # Replace template variables
    system_prompt = AI_SYSTEM_PROMPT_TEMPLATE.format(
        name=name,
        natal_type=natal_type,
        archetype=archetype,
        gender=gender,
        communication_style=f"{comm_style['pace']}, {comm_style['tone']}",
        conversation_history=history_text,
        user_message="{user_message}"  # Will be filled in later
    )
    
    # Add user's profile data if provided
    profile_data = profile.get('profile_data', {})
    if profile_data:
        system_prompt += f"\n\n# USER'S SELF-DISCOVERY PROFILE\n"
        if profile_data.get('personality'):
            system_prompt += f"Personality: {profile_data['personality']}\n"
        if profile_data.get('goals'):
            system_prompt += f"Goals: {profile_data['goals']}\n"
        if profile_data.get('challenges'):
            system_prompt += f"Challenges: {profile_data['challenges']}\n"
        if profile_data.get('environment'):
            system_prompt += f"Environment: {profile_data['environment']}\n"
        if profile_data.get('past'):
            system_prompt += f"Past influences: {profile_data['past']}\n"
    
    # Add relationships if provided
    relationships = profile.get('relationships', [])
    if relationships:
        system_prompt += f"\n\n# IMPORTANT RELATIONSHIPS IN USER'S LIFE\n"
        for rel in relationships:
            rel_type = rel.get('natal_type', 'Unknown')
            system_prompt += f"- {rel['name']} ({rel['gender']}): {rel_type} type - use this person's type characteristics and archetypes to explain their influence and dynamics with the user\n"
    
    # Add Deepsyke type details
    system_prompt += f"\n\n# TYPE-SPECIFIC DETAILS FOR {natal_type}\n"
    system_prompt += f"Neurochemical: {type_data['neurochemical']}\n"
    system_prompt += f"Processing: {type_data['processing']}\n"
    system_prompt += f"Characteristics: {type_data['characteristics']}\n"
    system_prompt += f"Motivation: {type_data['motivation']}\n"
    system_prompt += f"Zones: {type_data['zones']}\n"
    system_prompt += f"Gravitors: {type_data['gravitors']}\n"
    
    # Add engagement protocol
    system_prompt += f"\n\n# ENGAGEMENT PROTOCOL FOR {natal_type}\n"
    system_prompt += f"Pace: {engagement['communication_approach']['pace']}\n"
    system_prompt += f"Tone: {engagement['communication_approach']['tone']}\n"
    system_prompt += f"Keywords to use: {', '.join(engagement['language_patterns']['keywords'])}\n"
    system_prompt += f"Opening phrases: {', '.join(engagement['language_patterns']['opening_phrases'][:3])}\n"
    system_prompt += f"Acknowledgment phrases: {', '.join(engagement['language_patterns']['acknowledgment_phrases'][:3])}\n"
    system_prompt += f"Closing phrases: {', '.join(engagement['language_patterns']['closing_phrases'][:3])}\n"
    system_prompt += f"Avoid: {', '.join(engagement['language_patterns']['avoid'])}\n"
    
    # Add business RAG
    system_prompt += f"\n\n# BUSINESS KNOWLEDGE\n"
    system_prompt += json.dumps(BUSINESS_RAG, indent=2)
    
    # Add cultural avatars if enabled
    if cultural_avatars_text:
        system_prompt += f"\n\n{cultural_avatars_text}"
    
    return system_prompt, selected_avatars


def fetch_ca_quotes_stories(avatar_name, user_type):
    """Return cultural avatar info - AI will use its knowledge base for quotes"""
    return {
        'name': avatar_name,
        'quotes': [],
        'insights': []
    }

def call_gemini_api(system_prompt, user_message):
    """Call Gemini API with the complete system prompt"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        
        full_prompt = system_prompt.replace("{user_message}", user_message)
        
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 800
            }
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
        
        return "I apologize, but I'm having trouble connecting right now. Please try again in a moment."
    
    except Exception as e:
        print(f"API Error: {e}")
        return f"Error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/init-profile', methods=['POST'])
def init_profile():
    """Initialize user profile and calculate natal type"""
    try:
        data = request.get_json()
        name = data.get('name', 'Friend')
        gender = data.get('gender', 'female')
        birth_date = data.get('birth_date')
        session_id = data.get('session_id', 'default')
        
        # Get optional profile data
        profile_data = data.get('profile_data', {})
        
        # Get optional relationships
        relationships_data = data.get('relationships', [])
        
        # Calculate natal type
        natal_info = calculate_natal_type(birth_date, gender)
        natal_type = natal_info['type']
        archetype = natal_info['archetype']
        
        # Calculate types for relationships
        calculated_relationships = calculate_relationships(relationships_data)
        
        # Get type-specific greeting
        comm_style = DEEPSYKE_CORE['communication_styles'][natal_type]
        
        # Create type-specific greetings
        greetings = {
            "SS": f"Welcome, {name}. I'm here to help you explore the depths of who you truly are. What brings you to this moment of self-reflection?",
            "SD": f"Welcome, {name}. I'm here to support your journey of self-discovery. What would you like to understand about yourself?",
            "DS": f"Welcome, {name}. I sense you're ready for some fascinating insights about yourself. What aspect of your inner world intrigues you most?",
            "DD": f"Welcome, {name}. Let's get clear on who you are and what drives you. What do you want to understand about yourself?"
        }
        
        greeting = greetings[natal_type]
        
        # Store session with enhanced profile data
        conversations[session_id] = {
            'profile': {
                'name': name,
                'natal_type': natal_type,
                'archetype': archetype,
                'gender': gender,
                'session_id': session_id,
                'profile_data': profile_data,
                'relationships': calculated_relationships
            },
            'history': [{'role': 'assistant', 'content': greeting}],
            'last_avatars_mentioned': [],
            'message_count': 0,
            'last_ca_message': 0,
            'paid': False,  # Track if user has paid
            'payment_id': None
        }
        
        return jsonify({
            'success': True, 
            'greeting': greeting,
            'natal_type': natal_type,
            'relationships': calculated_relationships
        })
    except Exception as e:
        print(f"Init profile error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        user_message = data.get('message', '')
        
        # If session doesn't exist but profile is sent, restore session
        if session_id not in conversations:
            profile_data = data.get('profile')
            if profile_data and profile_data.get('sessionId') == session_id:
                # Restore session from frontend profile data
                print(f"Restoring session {session_id} from frontend data")
                conversations[session_id] = {
                    'profile': {
                        'name': profile_data.get('name'),
                        'natal_type': profile_data.get('natalType'),
                        'archetype': profile_data.get('archetype'),
                        'gender': profile_data.get('gender'),
                        'session_id': session_id,
                        'profile_data': profile_data.get('profileData', {}),
                        'relationships': profile_data.get('relationships', [])
                    },
                    'history': [{'role': 'assistant', 'content': f"Welcome back, {profile_data.get('name', 'Friend')}. Let's continue our journey of self-discovery."}],
                    'last_avatars_mentioned': [],
                    'message_count': 0,
                    'last_ca_message': 0,
                    'paid': True,  # Assuming paid if session was restored
                    'payment_id': 'restored'
                }
            else:
                return jsonify({'success': False, 'error': 'Session not found'}), 400
        
        session = conversations[session_id]
        profile = session['profile']
        
        # Check paywall - 5 free messages, then require payment
        message_count = session.get('message_count', 0)
        if not session.get('paid', False) and message_count >= FREE_MESSAGE_LIMIT:
            return jsonify({
                'error': 'PAYWALL_REACHED',
                'free_limit': FREE_MESSAGE_LIMIT,
                'message': f'You\'ve used your {FREE_MESSAGE_LIMIT} free messages. Please upgrade to continue.'
            }), 402
        
        # Increment message count
        session['message_count'] += 1
        current_message = session['message_count']
        
        # Determine if we should include cultural avatars this message
        # Pattern: Messages 4, 7, 11, 14, 18, 21, ... (alternating 3 and 4)
        use_cultural_avatars = False
        if ENGAGEMENT_PROTOCOL['cultural_avatar_protocol']['enabled']:
            # Define the message numbers where CAs should appear
            ca_messages = {4, 7, 11, 14, 18, 21, 25, 28, 32, 35, 40, 43, 47, 50}
            
            if current_message in ca_messages:
                use_cultural_avatars = True
                session['last_ca_message'] = current_message
        
        # Add user message to history
        session['history'].append({'role': 'user', 'content': user_message})
        
        # Build system prompt
        system_prompt, selected_avatars = build_system_prompt(
            profile, 
            session['history'],
            use_cultural_avatars
        )
        
        # Get AI response
        ai_response = call_gemini_api(system_prompt, user_message)
        
        # Add AI response to history
        session['history'].append({'role': 'assistant', 'content': ai_response})
        
        # Update avatar tracking
        if selected_avatars:
            session['last_avatars_mentioned'] = selected_avatars
        
        return jsonify({'success': True, 'response': ai_response})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session for payment"""
    try:
        session_id = request.json.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Validate Stripe configuration
        if not stripe.api_key:
            print("Stripe API key not configured")
            return jsonify({
                'error': 'Payment system not configured. Please contact support.'
            }), 500
        
        print(f"Creating checkout session for session_id: {session_id}")

        # Create Stripe checkout session (Stripe 8.0.0+ has proper checkout module)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Oracle Psychology Session',
                        'description': 'Continue your self-discovery journey',
                    },
                    'unit_amount': 295,  # $2.95 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.url_root + 'payment-success?session_id=' + session_id,
            cancel_url=request.url_root + '?session_id=' + session_id,
            metadata={
                'session_id': session_id
            }
        )

        print(f"Checkout session created: {checkout_session.url}")
        return jsonify({'url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        # Specific Stripe error handling
        print(f"Stripe error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Payment processing error: {str(e)}'
        }), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        # If webhook secret not set, still allow payment to work (for testing)
        print("Warning: STRIPE_WEBHOOK_SECRET not set")
        return jsonify({'success': True}), 200
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        session_id = session_obj.get('metadata', {}).get('session_id')
        
        if session_id and session_id in conversations:
            conversations[session_id]['paid'] = True
            conversations[session_id]['payment_id'] = session_obj.payment_intent
            print(f"Payment received for session {session_id}")
    
    return jsonify({'success': True}), 200


@app.route('/payment-success')
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    if session_id and session_id in conversations:
        conversations[session_id]['paid'] = True
        conversations[session_id]['payment_id'] = 'paid'
    
    return render_template('index.html', payment_success=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9011))
    print(f"Starting Oracle Psychology Coach on port {port}")
    print(f"Loaded {CULTURAL_AVATARS['metadata']['total_count']} cultural avatars")
    print(f"Business: {BUSINESS_RAG['metadata']['business_name']}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()