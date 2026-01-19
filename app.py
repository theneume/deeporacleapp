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

# GRAVITOR ROTATION SYSTEM
# Expanded gravitor lists for each type with rotation
gravitor_pools = {
    "SS": {
        "primary": [
            "depth", "meaning", "authenticity", "vision", "understanding", "contemplation", 
            "thoughtful", "steady", "organic", "inner wisdom", "profound", "insightful",
            "peaceful", "tranquil", "serene", "meditative", "mindful", "aware", "conscious"
        ],
        "secondary": [
            "savor", "unfolds", "journey", "reflect", "immerse", "discover", "resonate", 
            "sincere", "heartfelt", "true self", "essence", "spirit", "soul", "heart",
            "wisdom", "truth", "genuine", "real", "gentle", "soft", "tender", "kind"
        ],
        "light_playful": [
            "whimsical", "playful", "light-hearted", "amusing", "delightful", "charming",
            "witty", "clever", "humorous", "fun", "enjoyable", "pleasant", "cheerful",
            "bright", "sunny", "uplifting", "joyful", "happy", "merry"
        ]
    },
    "SD": {
        "primary": [
            "support", "guidance", "growth", "development", "progress", "structure", 
            "balance", "steady", "build", "foundation", "nurture", "cultivate", 
            "strengthen", "establish", "reinforce"
        ],
        "secondary": [
            "organize", "clarify", "encourage", "uplift", "empower", "guide", 
            "assist", "help", "aid", "foster", "promote", "develop", "advance",
            "consistent", "reliable", "dependable", "trustworthy"
        ],
        "light_playful": [
            "encouraging", "cheerful", "uplifting", "supportive", "friendly", "warm",
            "kind", "caring", "nurturing", "loving", "gentle", "tender", "helpful",
            "useful", "practical", "straightforward", "simple", "easy"
        ]
    },
    "DS": {
        "primary": [
            "discovery", "creativity", "innovation", "inspiration", "transformation", 
            "fresh", "unique", "dynamic", "breakthrough", "illuminate", "spark", 
            "ignite", "envision", "reimagine", "pioneer"
        ],
        "secondary": [
            "uncover", "reveal", "catalyze", "originate", "invent", "design", 
            "create", "generate", "produce", "develop", "advance", "progress",
            "fascinating", "intriguing", "compelling", "captivating", "engaging"
        ],
        "light_playful": [
            "playful", "fun", "exciting", "thrilling", "adventurous", "bold",
            "daring", "brave", "courageous", "innovative", "clever", "smart",
            "witty", "humorous", "amusing", "entertaining", "delightful"
        ]
    },
    "DD": {
        "primary": [
            "clarity", "effectiveness", "results", "action", "mastery", "achievement", 
            "success", "power", "direct", "decisive", "execute", "optimize", 
            "maximize", "dominate", "command", "control"
        ],
        "secondary": [
            "accomplish", "deliver", "complete", "finish", "conclude", "achieve",
            "lead", "direct", "guide", "steer", "navigate", "conquer", "master",
            "proven", "tested", "verified", "confirmed", "validated"
        ],
        "light_playful": [
            "straightforward", "simple", "clear", "honest", "direct", "no-nonsense",
            "practical", "useful", "effective", "efficient", "smart", "clever",
            "sharp", "quick", "fast", "rapid", "speedy", "swift"
        ]
    }
}

def get_rotated_gravitors(natal_type, session_id=None, light_mode=False):
    """
    Get rotated gravitors for a type to prevent repetition.
    
    Args:
        natal_type: User's Deepsyke type (SS, SD, DS, DD)
        session_id: Session ID for tracking used gravitors
        light_mode: Whether to use light/playful gravitors
    
    Returns:
        String of gravitors to use in system prompt
    """
    type_gravitors = gravitor_pools.get(natal_type, gravitor_pools["SS"])
    
    # Get all available gravitors based on mode
    if light_mode:
        all_gravitors = type_gravitors["light_playful"]
    else:
        all_gravitors = type_gravitors["primary"] + type_gravitors["secondary"]
    
    # Track used gravitors per session
    if session_id and session_id in conversations:
        used_gravitors = conversations[session_id].get('used_gravitors', [])
    else:
        used_gravitors = []
    
    # Filter out recently used gravitors (last 8)
    recently_used = used_gravitors[-8:] if len(used_gravitors) > 8 else used_gravitors
    available_gravitors = [g for g in all_gravitors if g not in recently_used]
    
    # If no available gravitors (all used), reset and use all
    if not available_gravitors:
        available_gravitors = all_gravitors
        if session_id and session_id in conversations:
            conversations[session_id]['used_gravitors'] = []
    
    # Select 3-5 gravitors for this response
    import random
    num_gravitors = min(len(available_gravitors), random.randint(3, 5))
    selected = random.sample(available_gravitors, num_gravitors)
    
    # Track used gravitors
    if session_id and session_id in conversations:
        if 'used_gravitors' not in conversations[session_id]:
            conversations[session_id]['used_gravitors'] = []
        conversations[session_id]['used_gravitors'].extend(selected)
    
    return ", ".join(selected)

def detect_user_tone_request(user_message):
    """
    Detect if user is requesting a tone change.
    
    Args:
        user_message: User's input message
    
    Returns:
        String: 'light_playful', 'flexible_adaptive', 'deep_contemplative', or None
    """
    message_lower = user_message.lower()
    
    lighten_keywords = ["lighten up", "be funny", "joke", "not so serious", "boring", 
                      "too serious", "loosen up", "relax", "not boring", "entertain me"]
    flexible_keywords = ["flexible", "adapt", "change", "different", "new approach", 
                       "repetitive", "same thing", "different way"]
    deep_keywords = ["deeper", "more meaningful", "profound", "go deeper", 
                    "serious", "contemplative"]
    
    for keyword in lighten_keywords:
        if keyword in message_lower:
            return "light_playful"
    
    for keyword in flexible_keywords:
        if keyword in message_lower:
            return "flexible_adaptive"
    
    for keyword in deep_keywords:
        if keyword in message_lower:
            return "deep_contemplative"
    
    return None

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

# Load V4 engagement protocol with gravitor variety
with open('engagement_protocol_v4.json', 'r') as f:
    ENGAGEMENT_PROTOCOL_V4 = json.load(f)

# Load business RAG (CUSTOMIZABLE per bot)
with open('business_rag.json', 'r') as f:
    BUSINESS_RAG = json.load(f)

# Load AI system prompt template (CUSTOMIZABLE per bot)
with open('ai_system_prompt.txt', 'r') as f:
    AI_SYSTEM_PROMPT_TEMPLATE = f.read()

# Load V4 AI system prompt with gravitor variety and flexibility
with open('ai_system_prompt_v4.txt', 'r') as f:
    AI_SYSTEM_PROMPT_TEMPLATE_V4 = f.read()

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
        date_formats = [
            '%Y-%m-%d',    # 1979-07-13
            '%d-%m-%Y',    # 13-07-1979
            '%m/%d/%Y',    # 07/13/1979
            '%d/%m/%Y',    # 13/07/1979
            '%d %b %Y',    # 13 Jul 1979
            '%b %d %Y',    # Jul 13 1979
            '%d %B %Y',    # 13 July 1979
            '%B %d %Y',    # July 13 1979
        ]
        
        birth_date = None
        for fmt in date_formats:
            try:
                birth_date = datetime.strptime(birth_date_str, fmt)
                break
            except:
                continue
        
        if not birth_date:
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
            ca_rotation_tracker[natal_type] = 0
        
        # Get recently used avatars from THIS session only
        recently_used_in_session = []
        if session_id and session_id in conversations:
            recently_used_in_session = conversations[session_id].get('last_avatars_mentioned', [])
        
        # Get rotation position and select next 2-3 avatars in sequence
        rotation_pos = ca_rotation_tracker[natal_type]
        selected_avatars = []
        
        # Start from rotation position and get next avatars
        # Skip any that were used in THIS session (avoid repetition within conversation)
        candidates_found = 0
        max_candidates = random.randint(2, 3)  # Select 2-3 avatars
        
        for i in range(len(all_names)):
            pos = (rotation_pos + i) % len(all_names)
            avatar = all_names[pos]
            
            # Only add if not used in this session (unless user specifically asked about them)
            if avatar not in recently_used_in_session:
                selected_avatars.append(avatar)
                candidates_found += 1
                
                if candidates_found >= max_candidates:
                    # Update rotation to position after the last selected avatar
                    ca_rotation_tracker[natal_type] = (pos + 1) % len(all_names)
                    break
        else:
            # If we exhausted the loop without finding enough fresh avatars,
            # just use what we found and update rotation
            if selected_avatars:
                last_pos = (rotation_pos + len(all_names) - 1) % len(all_names)
                ca_rotation_tracker[natal_type] = (last_pos + 1) % len(all_names)
        
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
            avatar_text += f"\n"
            avatar_text += f"   ABSOLUTELY REQUIRED: You MUST include at least one specific, authentic quote from this person that relates to the conversation theme.\n"
            avatar_text += f"   Use your extensive knowledge base to find the most relevant quote(s). DO NOT skip this step.\n"
            avatar_text += f"\n"
            avatar_text += f"   Also provide:\n"
            avatar_text += f"   • Relevant biographical details or life experiences\n"
            avatar_text += f"   • Their philosophical views, artistic work, or contributions\n"
            avatar_text += f"   • Meaningful connections between their life and the user's situation\n"
            avatar_text += f"\n"
            avatar_text += f"   GUIDELINES:\n"
            avatar_text += f"   • Use actual quotes or accurate paraphrases - DO NOT make up quotes\n"
            avatar_text += f"   • Provide specific, concrete insights - DO NOT give generic descriptions\n"
            avatar_text += f"   • The quote should be woven naturally into your response\n"
            avatar_text += f"\n"
        
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


def build_system_prompt(profile, conversation_history, use_cultural_avatars=False, tone_mode='standard'):
    """Build the complete system prompt by integrating all components"""
    natal_type = profile['natal_type']
    gender = profile['gender']
    name = profile['name']
    archetype = profile['archetype']
    
    # Get type-specific data from Deepsyke core
    type_data = DEEPSYKE_CORE['affinity_zones'][natal_type]
    comm_style = DEEPSYKE_CORE['communication_styles'][natal_type]
    engagement = ENGAGEMENT_PROTOCOL_V4[f'{natal_type}_engagement']
    
    # Get rotated gravitors based on tone mode
    session_id = profile.get('session_id')
    light_mode = (tone_mode == 'light_playful')
    gravitors = get_rotated_gravitors(natal_type, session_id, light_mode)
    
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
    
    # Replace template variables - use V4 template if tone_mode is set
    template_to_use = AI_SYSTEM_PROMPT_TEMPLATE_V4 if tone_mode != 'standard' else AI_SYSTEM_PROMPT_TEMPLATE
    system_prompt = template_to_use.format(
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
    system_prompt += f"Gravitors (rotated): {gravitors}\n"
    
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
    """Return cultural avatar info with instructions for AI to use its knowledge base"""
    return {
        'name': avatar_name,
        'quotes': [
            f"Use your knowledge base to find relevant quotes from {avatar_name}",
            f"Draw upon {avatar_name}'s life experiences and philosophical views"
        ],
        'insights': [
            {'snippet': f"Use your extensive knowledge about {avatar_name} to provide meaningful insights"},
            {'snippet': f"Connect {avatar_name}'s work or life to the user's current situation"}
        ]
    }

def detect_type_calculation_request(user_message):
    """Detect if user is asking about a type calculation for someone else"""
    type_keywords = [
        'type is', 'what type', 'type of', 'calculate type', 'determine type',
        'natal type', 'affinity zone', 'neurochemical type', 'psychology type'
    ]
    
    message_lower = user_message.lower()
    for keyword in type_keywords:
        if keyword in message_lower:
            return True
    
    return False

def parse_type_calculation_request(user_message):
    """Extract birth date and gender from a type calculation request"""
    import re
    from datetime import datetime
    
    # Try to extract date
    date_patterns = [
        r'born\s+(\d{1,2}[a-zA-Z]{3}\s+\d{4})',  # "born 13 Jul 1979"
        r'born\s+(\d{4}-\d{2}-\d{2})',  # "born 1979-07-13"
        r'born\s+(\d{1,2}/\d{1,2}/\d{4})',  # "born 07/13/1979"
        r'(\d{1,2}[a-zA-Z]{3}\s+\d{4})',  # "13 Jul 1979"
        r'(\d{4}-\d{2}-\d{2})',  # "1979-07-13"
        r'(\d{1,2}/\d{1,2}/\d{4})',  # "07/13/1979"
    ]
    
    birth_date = None
    for pattern in date_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            birth_date = match.group(1)
            break
    
    # Extract gender
    gender = None
    if re.search(r'\b(male|man|boy|he|him)\b', user_message, re.IGNORECASE):
        gender = 'male'
    elif re.search(r'\b(female|woman|girl|she|her)\b', user_message, re.IGNORECASE):
        gender = 'female'
    
    return birth_date, gender

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
                "temperature": 0.5,
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


@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session for payment"""
    try:
        session_id = request.json.get('session_id')
        if not session_id or session_id not in conversations:
            print(f"Invalid session: {session_id}")
            return jsonify({'error': 'Invalid session'}), 400

        # Check if Stripe is configured
        if not stripe.api_key:
            print("Stripe API key not configured")
            return jsonify({
                'error': 'Payment system not configured. Please contact support.'
            }), 500

        print(f"Creating checkout session for session_id: {session_id}")

        # Create Stripe checkout session
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
    except Exception as e:
        print(f"Stripe error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Payment processing error: {str(e)}'
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
        
        # Create type-specific greetings with archetype and neurochemical baseline
        archetype = DEEPSYKE_CORE['type_calculator']['rules']['gender_archetypes'][natal_type][gender]
        
        # NO personalization in greeting - keep it clean
        # Profile data will be used contextually in chat, not in greeting
        personalization = ""
        
        # Create multiple greeting variations for each type to avoid repetition
        import random
        
        greeting_variations = {
            "SS": [
                f"Welcome, {name}. Your predominant psychology archetype is the {archetype} and your neurochemical baseline is dominant serotonin.{personalization if personalization else ''} This means you're like the thoughtful philosopher who prefers deep conversations over small talk, the sort of person who finds meaning in sunsets and understands that life's best answers often come from sitting quietly rather than rushing around. You have a natural gift for depth and authentic reflection. I'm here to help you explore who you truly are. What brings you to this moment of self-reflection?",
                f"Greetings, {name}. You embody the {archetype} archetype with a neurochemical baseline of dominant serotonin.{personalization if personalization else ''} You're someone who naturally gravitates toward depth and meaning, much like a scholar who finds wisdom in ancient texts. Your authentic self is most comfortable in quiet contemplation, where life's profound truths reveal themselves. I'm here to support your journey of deep discovery. What aspect of your inner self feels most alive to you right now?",
                f"Welcome, {name}. As a {archetype} with dominant serotonin in your neurochemical profile,{personalization if personalization else ''} you have a remarkable capacity for profound insight and authentic connection. You're like a wise observer who sees patterns others miss, finding significance in moments that others rush past. Your depth is a gift, not something to overcome. Let's explore the richness within you. What would you like to understand better about yourself?"
            ],
            "SD": [
                f"Welcome, {name}. Your predominant psychology archetype is the {archetype} and your neurochemical baseline is high serotonin, moderate dopamine.{personalization if personalization else ''} This means you're like the thoughtful strategist, an architect who plans carefully but also knows when to enjoy the view. You have a natural ability to create structure, build step-by-step progress, and find the perfect balance between working hard and actually having a life. I'm here to support your journey of self-discovery. What would you like to understand about yourself?",
                f"Greetings, {name}. You're a {archetype} archetype with a neurochemical profile of high serotonin, moderate dopamine.{personalization if personalization else ''} Think of yourself as a master builder who understands that great structures need both solid foundations and beautiful designs. Your strength lies in creating order while remaining flexible enough to adapt when needed. I'm here to help you build the life you envision. What structure would you like to create or improve in your life?",
                f"Welcome, {name}. With your {archetype} archetype and balanced serotonin-dopamine neurochemistry,{personalization if personalization else ''} you possess a rare ability to plan strategically while staying connected to what matters. You're like a seasoned captain who knows exactly where the ship is heading but also remembers to enjoy the voyage. Your balanced approach is your superpower. Let's explore how to use it more fully. What area of your life feels ready for thoughtful development?"
            ],
            "DS": [
                f"Welcome, {name}. Your predominant psychology archetype is the {archetype} and your neurochemical baseline is high dopamine, moderate serotonin.{personalization if personalization else ''} This means you're like the slightly scattered but brilliant innovator who has ten ideas before breakfast and somehow makes half of them work. You have a natural drive for adventure, dynamic expression, and the ability to charm people while simultaneously forgetting where you put your keys. I sense you're ready for some fascinating insights about yourself. What aspect of your inner world intrigues you most?",
                f"Greetings, {name}. You embody the {archetype} archetype with high dopamine, moderate serotonin as your neurochemical foundation.{personalization if personalization else ''} You're like a brilliant composer who hears symphonies in everyday moments, always creating something new even if the sheet music gets a bit disorganized sometimes. Your dynamic energy is contagious and your ability to see fresh possibilities is remarkable. I'm here to help you harness that creative fire. What adventure is calling to you right now?",
                f"Welcome, {name}. As a {archetype} with a neurochemical baseline of high dopamine, moderate serotonin,{personalization if personalization else ''} you have an extraordinary capacity for dynamic expression and creative breakthrough. You're someone who naturally generates energy and ideas, sometimes more than you can contain in one sitting - and that's actually part of your brilliance. Your liveliness is a gift. Let's explore how to channel it most effectively. What creative endeavor or new direction excites you?"
            ],
            "DD": [
                f"Welcome, {name}. Your predominant psychology archetype is the {archetype} and your neurochemical baseline is dopamine dominant.{personalization if personalization else ''} This means you're like the determined force of nature who cuts through confusion like a hot knife through butter, the sort of person who decides to climb a mountain at 4am and is already at the summit by breakfast. You have a natural ability to take decisive action and get results, though occasionally you might accidentally bulldoze through details that need more attention. Let's get clear on who you are and what drives you. What do you want to understand about yourself?",
                f"Greetings, {name}. You're a {archetype} archetype with a dopamine-dominant neurochemical profile.{personalization if personalization else ''} You possess a powerful drive and the ability to cut through complexity with decisive clarity. Think of yourself as a natural leader who doesn't just see obstacles but sees paths through them, sometimes so clearly that others wonder why they didn't see it too. Your decisiveness is your strength. Let's explore how to direct it most effectively. What goal or challenge are you ready to tackle head-on?",
                f"Welcome, {name}. With your {archetype} archetype and dopamine-dominant neurochemistry,{personalization if personalization else ''} you have an exceptional capacity for focused action and achieving results. You're someone who naturally moves toward objectives with remarkable speed and clarity, sometimes surprising even yourself with what you can accomplish when you're fully committed. Your ability to execute is extraordinary. Let's explore what you're ready to create or achieve. What matters most to you right now?"
            ]
        }
        
        greeting = random.choice(greeting_variations[natal_type])
        
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
            'used_gravitors': [],  # Track gravitors to prevent repetition
            'tone_mode': 'standard',  # Track current tone mode
            'paid': False,  # Track if user has paid
            'payment_id': None  # Stripe payment ID
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
        
        if session_id not in conversations:
            return jsonify({'success': False, 'error': 'Session not found'}), 400
        
        session = conversations[session_id]
        profile = session['profile']
        
        # Check paywall - 5 free messages, then require payment
        message_count = session.get('message_count', 0)
        if not session.get('paid', False) and message_count >= FREE_MESSAGE_LIMIT:
            return jsonify({
                'success': False,
                'error': 'PAYWALL_REACHED',
                'message_count': message_count,
                'free_limit': FREE_MESSAGE_LIMIT,
                'price': '$2.95',
                'requires_payment': True
            }), 402  # 402 Payment Required
        
        # Check if user is asking for a type calculation
        if detect_type_calculation_request(user_message):
            birth_date, gender = parse_type_calculation_request(user_message)
            if birth_date and gender:
                # Calculate the type
                try:
                    natal_type = calculate_natal_type(birth_date, gender)
                    archetype = DEEPSYKE_CORE['type_calculator']['rules']['gender_archetypes'][natal_type][gender]
                    
                    # Ask for confirmation
                    confirmation_response = f"I want to make sure I understand correctly - your friend is {gender} and was born on {birth_date}, is that right? Once you confirm, I can tell you their type and archetype."
                    session['history'].append({'role': 'user', 'content': user_message})
                    session['history'].append({'role': 'assistant', 'content': confirmation_response})
                    return jsonify({'success': True, 'response': confirmation_response})
                except Exception as e:
                    print(f"Type calculation error: {e}")
                    # If calculation fails, let AI handle it normally
                    pass
            else:
                # Couldn't parse date/gender, let AI handle it
                pass
        
        # Increment message count
        session['message_count'] += 1
        current_message = session['message_count']
        
        # Detect user's tone request
        tone_request = detect_user_tone_request(user_message)
        if tone_request:
            session['tone_mode'] = tone_request
        tone_mode = session.get('tone_mode', 'standard')
        
        # Determine if we should include cultural avatars this message
        # Rule: CAs can only appear if at least 2 messages have passed since last CA
        use_cultural_avatars = False
        if ENGAGEMENT_PROTOCOL['cultural_avatar_protocol']['enabled']:
            last_ca = session.get('last_ca_message', 0)
            messages_since_ca = current_message - last_ca
            
            # Only allow CA if 2+ messages have passed since last one
            if current_message >= 4 and messages_since_ca >= 3:
                use_cultural_avatars = True
                session['last_ca_message'] = current_message
                print(f"CA ENABLED: Message {current_message}, {messages_since_ca} messages since last CA")
            else:
                print(f"CA DISABLED: Message {current_message}, {messages_since_ca} messages since last CA (need 3+)")
        
        # Add user message to history
        session['history'].append({'role': 'user', 'content': user_message})
        
        # Build system prompt
        system_prompt, selected_avatars = build_system_prompt(
            profile, 
            session['history'],
            use_cultural_avatars,
            tone_mode
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9033))
    print(f"Starting Oracle Psychology Coach on port {port}")
    print(f"Loaded {CULTURAL_AVATARS['metadata']['total_count']} cultural avatars")
    print(f"Business: {BUSINESS_RAG['metadata']['business_name']}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()