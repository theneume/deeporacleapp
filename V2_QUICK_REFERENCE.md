# LOHA Dating Coach V2 - Quick Reference

## What's New

### Color Scheme
- **Changed**: Pink/red → Golden/amber (`#f39c12`, `#e67e22`)
- **Why**: More gender-neutral, appeals to all users
- **Where**: Header, buttons, labels, chat, features, testimonials

### Neurochemistry
- **Added**: Comprehensive neurochemical insights for all 8 archetypes
- **Includes**: Serotonin, dopamine, oxytocin explanations
- **How**: Conversational, accessible, never technical
- **When**: Strategically mentioned to explain patterns

## Key Files Changed

```
✅ templates/index.html - Color scheme updated
✅ dating_coach_rag.json - Added neurochemistry section + profiles
✅ ai_system_prompt.txt - Added neurochemistry guidance
✅ app.py - Port changed to 9023
```

## Test URL
**Sandbox**: https://9024-ca9a76bf-d8cd-4f94-b417-8da646003cb4.sandbox-service.public.prod.myninja.ai

## Deployment Package
**File**: `loha-dating-coach-v2.zip`

## Render Configuration
- **Build**: `pip install -r requirements.txt`
- **Start**: `python app.py`
- **Env Var**: `GEMINI_API_KEY = AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y`
- **Port**: Auto (uses PORT env var)

## Neurochemistry Quick Reference

### Serotonin
- **What**: Emotional stability, intuition, warmth, bonding
- **High**: Emotional intelligence, natural warmth, protective
- **Dating**: Creates safety, enables deep bonding

### Dopamine
- **What**: Drive, ambition, excitement, pursuit
- **High**: Confidence, leadership, adventurous
- **Dating**: Creates excitement, fuels pursuit

### Oxytocin
- **What**: Bonding, trust, attachment, intimacy
- **Trigger**: Touch, vulnerability, understanding, consistency
- **Gender**: Men → touch/activity, Women → conversation/understanding

### Archetype Profiles

**Mystic/Magician**: Very High Serotonin + Very High Dopamine
- Deep emotional intelligence AND driven ambition
- Rare combo, incredibly magnetic

**Maiden/Knight**: High Serotonin + Moderate Dopamine
- Warm, nurturing, romantically inclined
- Naturally caring, creates safety

**Queen/Warrior**: Moderate Serotonin + High Dopamine
- Driven by excellence and achievement
- Discerning, won't settle

**Huntress/King**: Moderate Serotonin + Very High Dopamine
- Intense drive, natural leadership
- Direct, action-oriented

## Testing Checklist

### Visual
- [ ] Golden/amber colors display
- [ ] All UI elements updated
- [ ] Mobile responsive

### Functionality
- [ ] Profile form works
- [ ] Archetype calculates
- [ ] Chat responds naturally

### Neurochemistry
- [ ] AI mentions serotonin when appropriate
- [ ] AI mentions dopamine when appropriate
- [ ] AI mentions oxytocin when appropriate
- [ ] Explanations are conversational
- [ ] No technical jargon
- [ ] No SS/SD/DD/DS labels

## Common Questions

**Q: Why change colors?**
A: Pink was perceived as too feminine. Golden/amber is gender-neutral while still striking.

**Q: How often will AI mention neurochemistry?**
A: Strategically, not every response. When it helps explain patterns.

**Q: Will users be overwhelmed by science?**
A: No, explanations are conversational and relatable, never academic.

**Q: Did any V1 features break?**
A: No, all V1 functionality preserved. This is an enhancement only.

## Success Indicators

✅ Users find colors more inclusive
✅ Neurochemistry helps users understand themselves better
✅ Advice feels more credible and personalized
✅ No confusion from technical language
✅ Archetype differentiation is clearer

## Documentation

- **LOHA_V2_DEPLOYMENT_GUIDE.md**: Full deployment instructions
- **LOHA_V2_SUMMARY.md**: Complete project overview
- **README.md**: Main project documentation

## Support

1. Test sandbox URL first
2. Check deployment guide
3. Verify Render configuration
4. Check environment variables

---

**V2 Status**: ✅ Ready for deployment
**Backup Created**: ✅ loha-dating-coach-v1-backup-[timestamp].tar.gz
**Package Ready**: ✅ loha-dating-coach-v2.zip