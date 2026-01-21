import requests
import json
import os
from datetime import datetime
import random
from flask import Flask, render_template, request, jsonify
from natal_calculator import calculate_natal_type_from_dob

app = Flask(__name__)

# Load configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y')

# Load data files
with open('deepsyke_core_rag.json', 'r') as f:
    DEEPSYKE_CORE = json.load(f)

with open('dating_coach_rag.json', 'r') as f:
    DATING_COACH = json.load(f)

# Load system prompt
with open('ai_system_prompt.txt', 'r') as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()

# Store conversations in memory
conversations = {}

# Cultural avatars for dating coach (celebrities, socialites, fun people)
DATING_CAS = {
    'female': [
        'Taylor Swift', 'Beyoncé', 'Rihanna', 'Zendaya', 'Margot Robbie',
        'Emma Stone', 'Jennifer Lawrence', 'Priyanka Chopra', 'Gal Gadot',
        'Lupita Nyong\'o', 'Scarlett Johansson', 'Angelina Jolie', 'Megan Fox',
        'Kim Kardashian', 'Kylie Jenner', 'Kendall Jenner', 'Hailey Bieber',
        'Gigi Hadid', 'Bella Hadid', 'Dua Lipa', 'Ariana Grande', 'Billie Eilish',
        'Olivia Rodrigo', 'Selena Gomez', 'Miley Cyrus', 'Demi Lovato'
    ],
    'male': [
        'Ryan Reynolds', 'Leonardo DiCaprio', 'Brad Pitt', 'George Clooney',
        'Tom Hardy', 'Henry Cavill', 'Idris Elba', 'Chris Evans', 'Chris Hemsworth',
        'Chris Pratt', 'Robert Downey Jr.', 'Tom Cruise', 'Johnny Depp',
        'Justin Bieber', 'Shawn Mendes', 'Harry Styles', 'Zac Efron', 'Timothée Chalamet',
        'Michael B. Jordan', 'John Legend', 'Drake', 'Post Malone', 'Travis Scott',
        'Lewis Hamilton', 'David Beckham', 'Cristiano Ronaldo', 'Neymar'
    ]
}

# Cultural avatars rotation tracker
ca_rotation_tracker = {}

def get_archetype(natal_type, gender):
    """Map natal type and gender to archetype"""
    try:
        archetype_mapping = DATING_COACH['archetype_mappings'][natal_type][gender]
        archetype = archetype_mapping['primary']
        description = archetype_mapping['description']
        nicknames = DATING_COACH['archetype_nicknames'][archetype]
        return archetype, description, nicknames
    except KeyError:
        return 'Mystic', 'Soft, spiritual, and deeply feminine', ['the Dreamy One']

def get_archetype_advice(archetype, topic):
    """Get archetype-specific dating advice"""
    try:
        # Try new structure first
        if 'archetype_communication_styles' in DATING_COACH:
            if topic == 'communication':
                return DATING_COACH['archetype_communication_styles'][archetype]['approach']
            elif topic == 'dating_advice_focus':
                return DATING_COACH['archetype_communication_styles'][archetype]['dating_advice_focus']
        
        # Fall back to old structure
        advice = DATING_COACH['dating_topics'][topic]['archetype_specific_advice'][archetype]
        return advice
    except KeyError:
        return "Your unique energy is your superpower - embrace it fully."

def create_contextual_greeting(profile):
    """Create a contextual greeting based on user's archetype and input"""
    name = profile['name']
    gender = profile['gender']
    archetype, description, nicknames = get_archetype(profile['natal_type'], gender)
    nickname = nicknames[0] if nicknames else name
    
    goals = profile.get('goals', '').lower()
    challenges = profile.get('challenges', '').lower()
    
    # Contextual greeting templates based on archetype
    greetings = {
        'Mystic': [
            f"Hey {name}, good to meet you. I can see you're someone who values depth and real connection in dating. That's actually rare these days, and it's going to serve you well. Let's figure out how to get you the kind of relationships that match that energy.",
            f"Hi {name}. You strike me as someone who doesn't want surface-level dating - you want something that actually means something. That's completely valid, and honestly, it's what makes for the best connections. Let's talk about how to make that happen for you.",
            f"Hello {name}. I get the sense you're looking for something deeper than the usual dating scene offers. That takes patience and the right approach, but it's absolutely worth it. Let's work on getting you what you're actually looking for."
        ],
        'Maiden': [
            f"Hey {name}! I love that you're being real about this - your authenticity is going to be your biggest strength in dating. Let's talk about how to navigate things in a way that honors who you are while still getting you the connection you want.",
            f"Hi {name}. Your warmth and honesty come through, and those are exactly the qualities that create lasting attraction. Let's figure out how to show up in dating in a way that feels true to you.",
            f"Hey there, {name}. I can tell you're someone who cares deeply and wants genuine connection. That's beautiful, and also something to protect. Let's talk about how to date in a way that honors your heart."
        ],
        'Queen': [
            f"Hello {name}. I respect that you have standards and won't settle - that's exactly right. The right people will appreciate that about you. Let's talk about how to navigate dating in a way that maintains your standards while still being open to real connection.",
            f"Hi {name}. You clearly know what you want, and I like that. High standards aren't intimidating when they're backed by self-respect. Let's discuss how to date in a way that matches the quality you bring to the table.",
            f"Hey {name}. Your sophistication and discernment are clear, and those are qualities that attract the right people. Let's work on finding the kind of connections that actually meet your criteria."
        ],
        'Huntress': [
            f"Hey {name}. I can see you're someone who knows what you want and goes after it - that's incredibly attractive. Let's talk about how to channel that energy into creating the kind of connection you're looking for.",
            f"Hi {name}. Your strength and directness are refreshing, and honestly, that's what makes for exciting dating dynamics. Let's figure out how to leverage your natural power in dating.",
            f"Hello {name}. You're clearly ambitious and driven, and that's magnetic. Let's talk about how to create space for genuine connection alongside all your goals."
        ],
        'Magician': [
            f"Hey {name}. I can tell you're someone who sees beneath the surface and wants real transformation in your relationships. That depth is going to serve you well. Let's talk about how to develop the kind of emotional intelligence that creates real attraction.",
            f"Hi {name}. Your intuition and perceptiveness are clear, and those are qualities that make for profound connections. Let's work on understanding people on the level you're looking for.",
            f"Hey {name}. You seem like someone who wants to understand the deeper dynamics of attraction and connection. That's exactly the right approach - let's dive into that."
        ],
        'Knight': [
            f"Hey {name}. Your romantic nature and desire to be a protector are clear - those are genuinely attractive qualities when expressed the right way. Let's talk about how to channel that energy into healthy, respectful pursuit.",
            f"Hi {name}. I can see you want to be the one who can provide and protect, which is admirable. The key is doing it in a way that shows genuine care without being controlling. Let's work on that balance.",
            f"Hello {name}. Your chivalrous energy is refreshing, and when it's combined with respect, it's incredibly attractive. Let's talk about how to show up in dating in a way that honors both your nature and modern dynamics."
        ],
        'Warrior': [
            f"Hey {name}. Your confidence and ambition are clear, and those are qualities that create real attraction. Let's talk about how to channel that energy into pursuing the connections you want while also developing emotional depth.",
            f"Hi {name}. You're clearly someone who thrives on challenge and achievement - that energy is magnetic in dating when it's balanced with genuine connection. Let's work on that balance.",
            f"Hello {name}. Your excellence and drive are impressive, and those are qualities that attract quality people. Let's talk about how to pursue dating with the same effectiveness you bring to other areas of life."
        ],
        'King': [
            f"Hey {name}. Your natural leadership and decisiveness are clear - those are qualities that create respect and attraction. Let's talk about how to lead in dating in a way that also creates genuine emotional connection.",
            f"Hi {name}. You're clearly someone who wants to be in control of your dating life, which is right. The key is balancing that command with authentic emotional availability. Let's work on that.",
            f"Hello {name}. Your vision and authority are clear, and those are qualities that draw people to you. Let's discuss how to date in a way that matches your natural leadership while remaining emotionally connected."
        ]
    }
    
    # Select a greeting based on archetype
    archetype_greetings = greetings.get(archetype, greetings['Mystic'])
    greeting = random.choice(archetype_greetings)
    
    # Add contextual element based on goals/challenges if provided
    if goals:
        if 'relationship' in goals or 'partner' in goals or 'love' in goals:
            greeting += f" Since you mentioned wanting {goals.strip()}, we can definitely work on strategies to get you there."
    
    return greeting

def build_dating_system_prompt(profile, conversation_history):
    """Build the complete dating coach system prompt"""
    natal_type = profile['natal_type']
    gender = profile['gender']
    archetype, description, nicknames = get_archetype(natal_type, gender)
    
    # Get Deepsyke type details (for AI's knowledge, not for user-facing content)
    type_data = DEEPSYKE_CORE['affinity_zones'].get(natal_type, {})
    
    # Build user info section
    user_info = f"\n# USER INFORMATION\n"
    user_info += f"Name: {profile['name']}\n"
    user_info += f"Archetype: {archetype}\n"
    user_info += f"Archetype Description: {description}\n"
    user_info += f"Nickname Options: {', '.join(nicknames[:3])}\n"
    user_info += f"Gender: {gender}\n"
    
    if profile.get('goals'):
        user_info += f"\nDating Goals: {profile['goals']}\n"
    if profile.get('challenges'):
        user_info += f"Challenges: {profile['challenges']}\n"
    if profile.get('improvements'):
        user_info += f"Areas for Improvement: {profile['improvements']}\n"
    
    # Add relationships if provided
    relationships = profile.get('relationships', [])
    if relationships:
        user_info += f"\n# IMPORTANT RELATIONSHIPS\n"
        for rel in relationships:
            rel_type = rel.get('natal_type', 'Unknown')
            rel_archetype, _, rel_nicknames = get_archetype(rel_type, rel.get('gender', 'male'))
            user_info += f"- {rel['name']} ({rel.get('gender', '')}): {rel.get('type', 'unknown')} - {rel_archetype} archetype\n"
    
    # Add archetype-specific guidance
    user_info += f"\n# YOUR ARCHETYPE: {archetype.upper()}\n"
    user_info += f"{description}\n"
    
    # Add archetype communication style if available
    if 'archetype_communication_styles' in DATING_COACH:
        comm_style = DATING_COACH['archetype_communication_styles'].get(archetype, {})
        if comm_style:
            user_info += f"\nCommunication Style:\n"
            user_info += f"Approach: {comm_style.get('approach', '')}\n"
            user_info += f"Language: {comm_style.get('language', '')}\n"
            user_info += f"Dating Advice Focus: {comm_style.get('dating_advice_focus', '')}\n"
            user_info += f"Texting Style: {comm_style.get('texting_style', '')}\n"
    
    # Add tone protocol (use new structure if available)
    if 'tone_protocol' in DATING_COACH:
        tone = DATING_COACH['tone_protocol']
        if 'communication_rules' in tone:
            user_info += f"\n# COMMUNICATION GUIDELINES\n"
            user_info += f"Format: {tone['communication_rules'].get('format', '')}\n"
            user_info += f"Pacing: {tone['communication_rules'].get('pacing', '')}\n"
            user_info += f"Emotion: {tone['communication_rules'].get('emotion', '')}\n"
            user_info += f"Humor: {tone['communication_rules'].get('humor', '')}\n"
            user_info += f"Language: {tone['communication_rules'].get('language', '')}\n"
    
    # Add chemistry building principles if available
    if 'chemistry_building' in DATING_COACH:
        chem = DATING_COACH['chemistry_building']
        user_info += f"\n# CHEMISTRY BUILDING PRINCIPLES\n"
        for principle in chem.get('principles', [])[:3]:
            user_info += f"- {principle}\n"
    
    # Add texting strategies if available
    if 'texting_strategies' in DATING_COACH:
        texting = DATING_COACH['texting_strategies']
        user_info += f"\n# TEXTING STRATEGIES\n"
        for principle in texting.get('general_principles', [])[:3]:
            user_info += f"- {principle}\n"
        archetype_texting = texting.get('archetype_specific', {}).get(archetype, '')
        if archetype_texting:
            user_info += f"\nFor Your Archetype: {archetype_texting}\n"
    
    # Build conversation history
    history_text = "\n# CONVERSATION HISTORY\n"
    for msg in conversation_history[-10:]:
        role = "YOU" if msg['role'] == 'user' else "LOHA"
        history_text += f"{role}: {msg['content']}\n\n"
    
    # Replace placeholders in system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.replace('{user_name}', profile['name'])
    system_prompt = system_prompt.replace('{archetype}', archetype)
    system_prompt = system_prompt.replace('{nickname}', nicknames[0])
    
    # Combine all parts
    full_prompt = system_prompt + "\n\n" + user_info + "\n\n" + history_text + "\n\n# USER'S MESSAGE:\n{user_message}"
    
    return full_prompt

def load_cultural_avatars(gender, session_id=None):
    """Load rotating selection of cultural avatars for dating coach"""
    try:
        all_names = DATING_CAS.get(gender, DATING_CAS['female'])
        
        if not all_names:
            return "", []
        
        # Initialize rotation tracker if not exists
        if gender not in ca_rotation_tracker:
            ca_rotation_tracker[gender] = 0
        
        # Get recently used avatars from session
        recently_used = []
        if session_id and session_id in conversations:
            recently_used = conversations[session_id].get('last_cas_mentioned', [])
        
        # Get rotation position
        rotation_pos = ca_rotation_tracker[gender]
        selected_cas = []
        
        # Select 2-3 avatars, skipping any used in this session
        max_candidates = random.randint(2, 3)
        
        for i in range(len(all_names)):
            pos = (rotation_pos + i) % len(all_names)
            ca = all_names[pos]
            
            if ca in recently_used:
                continue
            
            selected_cas.append(ca)
            
            if len(selected_cas) >= max_candidates:
                ca_rotation_tracker[gender] = (pos + 1) % len(all_names)
                break
        
        # Format for AI
        if selected_cas:
            ca_text = f"\n{'='*60}\n"
            ca_text += f"CULTURAL REFERENCES FOR THIS SESSION\n"
            ca_text += f"{'='*60}\n\n"
            ca_text += f"Selected: {', '.join(selected_cas)}\n\n"
            ca_text += f"Use these celebrities as examples when relevant to the conversation.\n"
            ca_text += f"Reference their dating history, quotes, or public persona when it helps illustrate a point.\n"
            ca_text += f"{'='*60}\n"
            return ca_text, selected_cas
        
        return "", []
    except Exception as e:
        print(f"Error loading cultural avatars: {e}")
        return "", []

def call_gemini_api(system_prompt, user_message, max_retries=2):
    """Call Gemini API with the complete system prompt and retry logic"""
    
    # User-friendly error messages
    error_messages = [
        "Hmm, having a momentary glitch. Let me try that again...",
        "Technical hiccup - give me one second to recover...",
        "Almost there, just a small delay on my end..."
    ]
    
    for attempt in range(max_retries + 1):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
            
            full_prompt = system_prompt.replace('{user_message}', user_message)
            
            # Truncate prompt if too long to avoid API errors
            if len(full_prompt) > 100000:
                # Keep the most recent parts of conversation
                parts = full_prompt.split('\n\n')
                full_prompt = '\n\n'.join(parts[-20:])  # Keep last 20 sections
            
            data = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(url, json=data, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            # If we get here, we got a non-200 response
            if attempt < max_retries:
                print(f"API error, retry attempt {attempt + 1}/{max_retries}")
                import time
                time.sleep(1)  # Wait before retry
            else:
                print(f"API returned status {response.status_code}")
                return "I'm having some technical difficulties right now. Your message was saved though - just try sending it again in a moment."
                
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                print(f"Timeout, retry attempt {attempt + 1}/{max_retries}")
                import time
                time.sleep(2)  # Wait longer for timeout
            else:
                print("API timeout after retries")
                return "Taking a bit longer than usual to respond. Your message is safe - just give it another try."
                
        except Exception as e:
            print(f"Error calling Gemini API (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                import time
                time.sleep(1)
            else:
                # Give a more helpful error message
                return "I hit a snag processing that. Don't worry, our conversation is saved - just try rephrasing or sending it again."
    
    return "Something unexpected happened. Let's try once more - I'm right here with you."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'LOHA Dating Coach'})

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize a new coaching session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        name = data.get('name', '')
        dob = data.get('dob', '')
        gender = data.get('gender', '')
        goals = data.get('goals', '')
        challenges = data.get('challenges', '')
        improvements = data.get('improvements', '')
        relationships = data.get('relationships', [])
        
        # Calculate natal type (silent, for AI's knowledge only)
        natal_type = calculate_natal_type_from_dob(dob, gender)
        
        # Build profile
        profile = {
            'name': name,
            'dob': dob,
            'gender': gender,
            'natal_type': natal_type,
            'goals': goals,
            'challenges': challenges,
            'improvements': improvements,
            'relationships': []
        }
        
        # Calculate natal types for relationships
        for rel in relationships:
            if rel.get('dob'):
                rel_natal_type = calculate_natal_type_from_dob(rel['dob'], rel.get('gender', 'male'))
                profile['relationships'].append({
                    'name': rel.get('name', ''),
                    'dob': rel.get('dob', ''),
                    'gender': rel.get('gender', ''),
                    'type': rel.get('type', ''),
                    'natal_type': rel_natal_type
                })
        
        # Get archetype
        archetype, _, nicknames = get_archetype(natal_type, gender)
        nickname = nicknames[0] if nicknames else "babe"
        
        # Create contextual greeting
        greeting = create_contextual_greeting(profile)
        
        # Store session
        conversations[session_id] = {
            'profile': profile,
            'history': [{'role': 'assistant', 'content': greeting}],
            'last_cas_mentioned': []
        }
        
        return jsonify({
            'success': True,
            'message': greeting
        })
    except Exception as e:
        print(f"Error initializing session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        user_message = data.get('message', '')
        
        if session_id not in conversations:
            return jsonify({
                'success': False, 
                'error': 'Session not found',
                'user_friendly': 'Our conversation got disconnected. Let me start fresh with you.'
            }), 400
        
        session = conversations[session_id]
        profile = session['profile']
        
        # Add user message to history
        session['history'].append({'role': 'user', 'content': user_message})
        
        # Build system prompt
        system_prompt = build_dating_system_prompt(profile, session['history'])
        
        # Call AI (now with retry logic)
        response = call_gemini_api(system_prompt, user_message)
        
        # Add response to history
        session['history'].append({'role': 'assistant', 'content': response})
        
        return jsonify({
            'success': True,
            'message': response
        })
        
    except Exception as e:
        print(f"Error in chat: {e}")
        # Import traceback for better debugging
        import traceback
        traceback.print_exc()
        
        # Return a user-friendly error that explains what happened
        return jsonify({
            'success': False, 
            'error': str(e),
            'user_friendly': "I encountered an unexpected issue. Don't worry - I remember everything we've talked about. Just try sending your message again."
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9024))
    print(f"Starting LOHA Dating Coach V2 on port {port}")
    print("Natural, helpful, and authentically human!")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        # Try alternative port
        for alt_port in [9021, 9022, 9023]:
            try:
                print(f"Trying alternative port {alt_port}")
                app.run(host='0.0.0.0', port=alt_port, debug=False)
                break
            except:
                continue