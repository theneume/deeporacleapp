# LOHA Dating Coach V2 - Deployment Guide

## Overview

LOHA Dating Coach V2 introduces two major improvements:
1. **Updated Color Scheme**: Replaced pink/red highlights with golden/amber accents for better gender appeal
2. **Neurochemistry Insights**: Added comprehensive neurochemical explanations to help users understand attraction, dating dynamics, and relationship chemistry

## What's New in V2

### 1. UI/Appearance Updates
- **Color Change**: Pink/red gradients (`#e94560`, `#ff6b6b`) → Golden/amber gradients (`#f39c12`, `#e67e22`)
- **Benefits**: More gender-neutral, equally striking, works beautifully with royal blue background
- **Updated Elements**:
  - Header gradient
  - Button gradients
  - Label colors
  - Feature card highlights
  - Chat message bubbles
  - Form focus states
  - Typing indicators
  - Testimonials

### 2. Neurochemistry Integration
- **Comprehensive RAG**: Added `neurochemistry_and_attraction` section with:
  - Core concepts (serotonin, dopamine, oxytocin)
  - Neurochemical combinations by archetype
  - Attraction neuroscience
  - Gender-specific insights
  - Practical applications
  - Common patterns

- **Archetype-Specific Profiles**: Each archetype now includes:
  - Serotonin/dopamine levels
  - Neurochemical description
  - Relationship insights
  - Dating implications

- **AI System Prompt Enhancement**: Added section on:
  - When to explain neurochemistry
  - How to explain it naturally
  - Neurochemical combinations by archetype
  - Gender-specific bonding patterns
  - Guidelines for balanced, accessible explanations

## Technical Details

### Port Configuration
- **Default Port**: 9024 (updated from 9020)
- **Environment Variable**: `PORT` (overrides default)
- **Render Deployment**: Automatically uses Render's assigned port

### File Structure
```
loha-dating-coach-v2/
├── app.py                          # Flask application (port 9023)
├── ai_system_prompt.txt            # Enhanced with neurochemistry section
├── dating_coach_rag.json          # Includes neurochemistry_and_attraction
├── natal_calculator.py             # Correct 9-year cycle algorithm
├── deepsyke_core_rag.json         # Type definitions
├── cultural_avatars_rag.json       # Cultural avatar definitions
├── requirements.txt                # Dependencies
├── templates/
│   └── index.html                  # Updated with golden/amber colors
├── static/
│   ├── lologo8.png                # LOHA logo
│   ├── lohafront1.png             # Couple photo
│   └── archtokens.png             # Archetype tokens
└── research/                      # Research documents
```

## Deployment Instructions

### Step 1: GitHub Repository Setup

1. **Create New Repository**
   - Go to GitHub → New repository
   - Name: `loha-dating-coach-v2`
   - Make it public or private (your choice)
   - Click "Create repository"

2. **Upload Files**
   - **CRITICAL**: Create file as `templates/index.html` (WITH the slash)
   - Upload all other files normally
   - **Do NOT upload**:
     - `__pycache__` folders
     - `*.pyc` files
     - `.DS_Store` or other system files
     - Documentation files (keep them locally)

3. **File Upload Order** (to ensure folder structure):
   ```
   First upload: templates/index.html
   Then upload: static/lologo8.png
   Then upload: static/lohafront1.png
   Then upload: static/archtokens.png
   Then upload: app.py
   Then upload: all other files
   ```

### Step 2: Render Deployment

1. **Go to Render**
   - Visit https://render.com
   - Sign in to your account
   - Click "New +" → "Web Service"

2. **Configure Web Service**
   - **Name**: `loha-dating-coach-v2`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

3. **Environment Variables**
   - Click "Advanced" → "Add Environment Variable"
   - **Name**: `GEMINI_API_KEY`
   - **Value**: `AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y`
   - Click "Save"

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment (2-3 minutes)
   - Your bot will be live at: `https://loha-dating-coach-v2.onrender.com`

### Step 3: Verify Deployment

1. **Test Basic Functionality**
   - Visit your Render URL
   - Fill in profile form
   - Click "Discover Your Archetype"
   - Verify greeting appears

2. **Test Chat**
   - Send a message about dating challenges
   - Check for natural, human-like responses
   - Verify tone is helpful and supportive

3. **Test Neurochemistry**
   - Ask about attraction or chemistry
   - Verify AI explains serotonin/dopamine/oxytocin naturally
   - Check that explanations are accessible, not technical

4. **Test Different Archetypes**
   - Try different birth dates
   - Verify archetype-specific greetings
   - Check neurochemical profile mentions

## Testing Checklist

### UI Testing
- [ ] Golden/amber colors appear correctly
- [ ] Royal blue background displays properly
- [ ] All buttons use new color scheme
- [ ] Form labels have correct colors
- [ ] Chat messages show new colors
- [ ] Mobile responsive works

### Functionality Testing
- [ ] Profile form submits correctly
- [ ] Archetype calculation works
- [ ] Chat responses are natural
- [ ] Error handling works
- [ ] Relationships calculate correctly

### Neurochemistry Testing
- [ ] AI explains serotonin when appropriate
- [ ] AI explains dopamine when appropriate
- [ ] AI explains oxytocin when appropriate
- [ ] Explanations are conversational, not technical
- [ ] No mention of SS/SD/DD/DS labels
- [ ] Archetype profiles mention neurochemistry naturally

## Key Features to Highlight

### Color Scheme
- Golden/amber accents are gender-neutral
- Maintains visual impact and attractiveness
- Works beautifully with royal blue
- Appeals to all users, not just women

### Neurochemistry Insights
- Helps users understand themselves better
- Explains attraction patterns naturally
- Provides context for dating experiences
- Makes advice more actionable and relatable
- Differentiates LOHA from generic dating coaches

### Archetype-Specific Guidance
- Each archetype has unique neurochemical profile
- Dating implications explained naturally
- Relationship insights tailored to chemistry
- Gender-specific bonding patterns acknowledged

## Common Issues and Solutions

### Issue: Colors Still Show Pink
**Solution**: Clear browser cache and hard refresh (Ctrl+Shift+R)

### Issue: Neurochemistry Not Mentioned
**Solution**: The AI uses neurochemistry strategically, not in every response. Ask specifically about attraction, chemistry, or why you're drawn to certain types of people.

### Issue: Deployment Fails
**Solution**: 
1. Verify all files uploaded correctly
2. Check `templates/index.html` path (must include slash)
3. Verify environment variable is set correctly
4. Check Render logs for specific errors

### Issue: Port Conflicts Locally
**Solution**: Change default port in `app.py` line 475

## Support

For issues or questions:
1. Check this deployment guide
2. Review the main README
3. Test the sandbox URL first
4. Check Render deployment logs

## Sandbox Testing URL

Before deploying to production, test the sandbox version:
**https://9024-ca9a76bf-d8cd-4f94-b417-8da646003cb4.sandbox-service.public.prod.myninja.ai**

## Success Criteria

✅ Golden/amber color scheme deployed
✅ Neurochemistry explanations working naturally
✅ No technical jargon or SS/SD/DD/DS labels
✅ Archetype-specific insights enhanced
✅ All core functionality preserved
✅ User testing complete
✅ Ready for production deployment

---

**LOHA V2 is now ready for deployment!**