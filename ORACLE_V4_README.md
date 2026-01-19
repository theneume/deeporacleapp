# Oracle Psychology Coach V4 - Gravitor Variety & User Flexibility

## Overview

Oracle V4 addresses the critical issue of gravitor repetition and lack of flexibility that caused conversations to become stale and repetitive. The AI now adapts to user requests and maintains variety throughout long conversations.

## Key Improvements

### 1. Gravitor Rotation System
- **Problem**: Same gravitors (like "meaningful", "thoughtful", "naturally") used repeatedly
- **Solution**: 
  - Expanded gravitor pools from ~10 to 30+ per type
  - Rotation system tracks used gravitors per session
  - Buffer system prevents overuse of any gravitor
  - Automatic refresh when buffer is exhausted

### 2. User Responsiveness & Flexibility
- **Problem**: AI ignored user requests to "lighten up" or be flexible
- **Solution**:
  - Tone request detection system
  - Multiple response modes: Standard, Light/Playful, Flexible/Adaptive, Deep/Contemplative
  - Immediate adaptation to user feedback
  - Acknowledgment and tone shift when requested

### 3. Enhanced CA Integration
- **Maintained**: Cultural avatars every 3-4 messages
- **Enhanced**: Web search dynamically finds relevant quotes and stories
- **Improved**: Better variety and connection to conversation themes

## Technical Implementation

### Gravitor Pools

Each type now has three gravitor categories:

**SS (Contemplative)**:
- Primary (18): depth, meaning, authenticity, vision, understanding, contemplation, thoughtful, steady, organic, inner wisdom, profound, insightful, peaceful, tranquil, serene, meditative, mindful, aware, conscious
- Secondary (23): savor, unfolds, journey, reflect, immerse, discover, resonate, sincere, heartfelt, true self, essence, spirit, soul, heart, wisdom, truth, genuine, real, gentle, soft, tender, kind
- Light/Playful (18): whimsical, playful, light-hearted, amusing, delightful, charming, witty, clever, humorous, fun, enjoyable, pleasant, cheerful, bright, sunny, uplifting, joyful, happy, merry

**SD (Structured)**:
- Primary (15): support, guidance, growth, development, progress, structure, balance, steady, build, foundation, nurture, cultivate, strengthen, establish, reinforce
- Secondary (18): organize, clarify, encourage, uplift, empower, guide, assist, help, aid, foster, promote, develop, advance, consistent, reliable, dependable, trustworthy
- Light/Playful (18): encouraging, cheerful, uplifting, supportive, friendly, warm, kind, caring, nurturing, loving, gentle, tender, helpful, useful, practical, straightforward, simple, easy

**DS (Dynamic)**:
- Primary (15): discovery, creativity, innovation, inspiration, transformation, fresh, unique, dynamic, breakthrough, illuminate, spark, ignite, envision, reimagine, pioneer
- Secondary (15): uncover, reveal, catalyze, originate, invent, design, create, generate, produce, develop, advance, progress, fascinating, intriguing, compelling, captivating, engaging
- Light/Playful (15): playful, fun, exciting, thrilling, adventurous, bold, daring, brave, courageous, innovative, clever, smart, witty, humorous, amusing, entertaining, delightful

**DD (Direct)**:
- Primary (15): clarity, effectiveness, results, action, mastery, achievement, success, power, direct, decisive, execute, optimize, maximize, dominate, command, control
- Secondary (15): accomplish, deliver, complete, finish, conclude, achieve, lead, direct, guide, steer, navigate, conquer, master, proven, tested, verified, confirmed, validated
- Light/Playful (15): straightforward, simple, clear, honest, direct, no-nonsense, practical, useful, effective, efficient, smart, clever, sharp, quick, fast, rapid, speedy, swift

### Rotation Algorithm

```python
def get_rotated_gravitors(natal_type, session_id=None, light_mode=False):
    1. Select gravitor pool based on type and mode
    2. Retrieve recently used gravitors from session
    3. Filter out last 8 used gravitors
    4. Randomly select 3-5 from available pool
    5. Track selected gravitors for next rotation
```

### Tone Detection System

**Keywords Detected**:
- **Lighten Up**: "lighten up", "be funny", "joke", "not so serious", "boring", "too serious", "loosen up", "relax"
- **Flexible**: "flexible", "adapt", "change", "different", "new approach", "repetitive", "same thing"
- **Deep**: "deeper", "more meaningful", "profound", "go deeper", "serious", "contemplative"

**Response Modes**:
1. **Standard**: Type-specific protocol with gravitor rotation
2. **Light/Playful**: Humor, lighter gravitors, varied structures, jokes
3. **Flexible/Adaptive**: Adapt to user's explicit feedback
4. **Deep/Contemplative**: Enhanced depth while maintaining variety

## User Experience Improvements

### Before V4
```
User: "lighten up, tell me a joke"
AI: "It's meaningful that you seek levity from me. Perhaps you are naturally feeling a need for lightness..."
User: "this is boring now, you should be more flexible"
AI: "It's meaningful that you find our interaction boring and desire more flexibility..."
```

### After V4
```
User: "lighten up, tell me a joke"
AI: "Ha! You're right, I was getting a bit heavy there. Here's one - why did the psychologist bring a ladder to work? Because they wanted to reach new heights! But seriously, what would actually make this conversation more enjoyable for you?"
User: "this is boring now, you should be more flexible"
AI: "Fair point - let me try a completely different angle. What's something unexpected or surprising about yourself that you've noticed lately? I'm genuinely curious to hear something you wouldn't typically share."
```

## Files Changed

### New Files
- `engagement_protocol_v4.json` - Enhanced protocol with gravitor variety
- `ai_system_prompt_v4.txt` - V4 prompt with flexibility rules

### Modified Files
- `app.py` - Added gravitor rotation, tone detection, session tracking
  - Added `gravitor_pools` dictionary
  - Added `get_rotated_gravitors()` function
  - Added `detect_user_tone_request()` function
  - Updated session initialization to track `used_gravitors` and `tone_mode`
  - Updated chat endpoint to detect tone requests
  - Updated `build_system_prompt()` to use V4 protocol when needed

### Unchanged
- `engagement_protocol.json` - V3 protocol (kept for reference)
- `ai_system_prompt.txt` - V3 prompt (kept for reference)
- All other files remain the same

## Testing Checklist

### Gravitor Variety
- [ ] Conversation continues without gravitor repetition
- [ ] Different gravitors appear in each response
- [ ] After 10+ messages, variety is maintained
- [ ] Light mode uses different gravitors than standard

### User Responsiveness
- [ ] User says "lighten up" → AI shifts to light tone
- [ ] User says "be flexible" → AI adapts approach
- [ ] User complains about repetition → AI acknowledges and varies significantly
- [ ] AI never ignores user's explicit tone requests

### CA Integration
- [ ] CAs appear every 3-4 messages
- [ ] Different CAs appear each time
- [ ] Quotes/stories are relevant to conversation theme
- [ ] Web search finds meaningful content

### Overall Experience
- [ ] Long conversations remain engaging
- [ ] No "stuck in a rut" feeling
- [ ] User feels heard and responsive
- [ ] Conversations flow naturally

## Deployment Instructions

### Step 1: Deploy to Render
1. Upload `oracle-bot-v4.zip` to GitHub
2. Create new Render web service
3. Configure as before (Python 3, gunicorn)
4. Deploy and test

### Step 2: Test Critical Features
1. **Test Gravitor Variety**: Have a 20+ message conversation, check gravitor variety
2. **Test Tone Flexibility**: Say "lighten up", "be funny", "not so serious"
3. **Test Repetition Handling**: Complain about repetition, verify AI adapts
4. **Test CA Integration**: Verify CAs appear with relevant quotes

### Step 3: Monitor User Feedback
1. Watch for complaints about repetition
2. Check if users feel heard
3. Monitor engagement in long conversations
4. Gather feedback on tone flexibility

## Rollback Plan

If V4 causes issues:
1. V4 prompt only activates when tone_mode is set
2. Standard mode uses V3 protocol
3. Can easily revert by disabling tone detection
4. V3 files remain for easy rollback

## Future Enhancements

### Potential V5 Features
1. More sophisticated mood tracking
2. Gravitor usage analytics
3. A/B testing for gravitor combinations
4. User preference learning
5. Context-aware gravitor selection
6. Enhanced joke/humor database
7. More variety in response structures

## Success Metrics

### Quantitative
- Gravitor variety: 20+ unique gravitors used in 20-message conversation
- User satisfaction: Fewer complaints about repetition
- Engagement: Longer conversations without staleness

### Qualitative
- Users feel heard and responsive
- Conversations feel fresh and engaging
- AI adapts naturally to user feedback
- Variety is noticeable without being jarring

## Support

For issues or questions:
1. Check this README
2. Review todo-oracle-v4.md for development details
3. Test in sandbox environment first
4. Monitor conversation examples

## Conclusion

Oracle V4 addresses the core issue of gravitor repetition while maintaining the depth and authenticity that makes Oracle special. The AI now adapts to users, provides variety, and remains engaging throughout long conversations.

**Status**: ✅ Complete and ready for deployment
**Deployment Package**: oracle-bot-v4.zip
**Key Features**: Gravitor rotation, user flexibility, CA integration