# Oracle Bot V3 - Stripe Fix Deployment Steps

## Problem
Payment was failing with "NoneType object has no attribute 'Session'" error.

## Root Cause
The Stripe API key environment variable might not be read correctly by the application.

## Fix Applied
Enhanced Stripe configuration validation and logging to help diagnose the issue.

## Deployment Steps

### Step 1: Download the Fixed Package
Download: `oracle-bot-v3-stripe-fix-v3.tar.gz`

### Step 2: Extract Files
```bash
tar -xzf oracle-bot-v3-stripe-fix-v3.tar.gz
```

### Step 3: Upload to Render

**Files to replace:**
- `app.py` (main application with enhanced Stripe logging)
- `templates/index.html` (improved error handling)

**Files to keep:**
- All other files (requirements.txt, JSON configs, etc.)

### Step 4: Verify Environment Variables

Go to Render Dashboard → deeporacleapp → Environment

**Verify these are set correctly:**

1. **GEMINI_API_KEY**
   - Value: `AIzaSyC1DgG1w7dm8fbZZ_LlAwhxpMSdNTJJl1Y`

2. **STRIPE_SECRET_KEY**
   - Value: `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`
   - **Check for:**
     - No extra spaces
     - No quotes
     - Exact match (copy-paste)

3. **STRIPE_WEBHOOK_SECRET**
   - Value: `whsec_OQjMAyv0fSpjLRzcqBgYVTwtoGGo1PY7`

### Step 5: Redeploy

1. After uploading files, Render will auto-deploy
2. Wait for deployment to complete
3. Go to "Logs" tab to see startup logs
4. Look for: `Stripe configured with API key: sk_live_51K...`
5. Verify the key length is correct (should show ~140+ characters)

### Step 6: Test Payment

1. Go to: `https://deeporacleapp.onrender.com`
2. Complete profile setup
3. Send 5 messages (to use free limit)
4. Click "Continue - $2.95"
5. **Expected behavior:**
   - Button shows "Processing..."
   - Redirects to Stripe checkout page
   - **OR** shows specific error message

### Step 7: Check Logs if Still Failing

If payment still fails, check Render logs:

**Look for:**
```
Stripe configured with API key: sk_live_51K...
Full key length: XXX characters
Creating checkout session for session_id: sess_xxx
```

**If you see:**
```
WARNING: Stripe API key not configured
Environment variable 'STRIPE_SECRET_KEY' value: NOT SET
```

Then the environment variable is not being read - re-check Step 4.

## What Changed in This Fix

### app.py
- Added detailed logging for Stripe configuration
- Logs key length for verification
- Better error messages

### templates/index.html
- Improved error handling
- Shows specific error messages from backend
- Better user feedback

## Contact Support If Issues Persist

If after following these steps the payment still fails:

1. Check Render logs for specific error messages
2. Verify Stripe account is active (go to Stripe dashboard)
3. Make sure you're using the correct live key (not test key)
4. Try creating a new Stripe product in your dashboard

## Success Criteria

✅ Stripe key is logged on startup
✅ Key length is correct (140+ characters)
✅ Checkout session is created successfully
✅ User redirects to Stripe checkout page