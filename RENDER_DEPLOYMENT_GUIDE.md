# Oracle Bot V3 - Render Deployment Guide

## Quick Fix for Blank Screen Issue

If you're seeing a blank white screen on Render, it's likely one of these issues:

### 1. Check Render Logs
- Go to your Render dashboard
- Click on your service
- Go to the "Logs" tab
- Look for errors during startup

### 2. Common Issues & Solutions

**Issue: "404 Not Found" errors**
- Make sure `templates/index.html` exists
- Check that the file structure is correct

**Issue: "Internal Server Error"**
- Check if all dependencies are installed
- Verify environment variables are set (if any)

**Issue: Static files not loading**
- This is usually a Flask/Gunicorn issue
- The fix below should resolve it

### 3. Add This to app.py (Already Fixed in Current Version)

Make sure your main route looks like this:
```python
@app.route('/')
def index():
    return render_template('index.html')
```

## Complete Render Setup with Stripe

### Step 1: Prepare Your Deployment

**Files Needed:**
- `app.py`
- `requirements.txt`
- `templates/index.html`
- All JSON data files
- `ai_system_prompt.txt`

**Environment Variables to Set on Render:**

1. **GEMINI_API_KEY** (Required)
   - Your Google Gemini API key
   - Example: `AIzaSy...`

2. **STRIPE_SECRET_KEY** (For Paywall - Optional)
   - Your live Stripe secret key
   - Example: `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`

3. **STRIPE_WEBHOOK_SECRET** (For Paywall - Optional)
   - Your Stripe webhook signing secret
   - Example: `whsec_OQjMAyv0fSpjLRzcqBgYVTwtoGGo1PY7`

### Step 2: Deploy to Render

1. **Go to Render.com** and log in
2. **Create New Web Service**
3. **Connect Repository** or upload your code
4. **Configure Build & Runtime:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Runtime:** `Python 3.11`
5. **Add Environment Variables** (see above)
6. **Deploy**

### Step 3: Configure Stripe Webhook (After Deployment)

**IMPORTANT: Do this AFTER your app is deployed!**

1. **Get Your Render URL**
   - Once deployed, copy your Render URL
   - Example: `https://oracle-bot-v3.onrender.com`

2. **Create Webhook in Stripe**
   - Go to: https://dashboard.stripe.com/test/webhooks (or live)
   - Click "Add endpoint"
   - **Endpoint URL:** `https://your-render-url.com/webhook`
   - Replace `your-render-url.com` with your actual URL
   - Click "Add endpoint"

3. **Select Events**
   - `checkout.session.completed`
   - `payment_intent.succeeded`

4. **Copy Webhook Secret**
   - Click "Click to reveal" on the signing secret
   - Copy the secret (starts with `whsec_...`)
   - Add it to Render as `STRIPE_WEBHOOK_SECRET`

5. **Redeploy**
   - Go back to Render
   - Add the `STRIPE_WEBHOOK_SECRET` environment variable
   - Trigger a new deploy

### Step 4: Test the Deployment

**Test Basic Functionality:**
1. Open your Render URL
2. Fill out the profile form
3. Start chatting
4. Verify responses work

**Test Paywall (if enabled):**
1. Send 5 messages to reach the paywall
2. Click "Continue - $2.95"
3. Complete Stripe payment
4. Verify you can continue chatting

## Troubleshooting Blank Screen

### Check These in Order:

1. **Render Logs (Most Important)**
   ```
   Go to Render → Your Service → Logs
   Look for:
   - Application errors
   - Missing files
   - Import errors
   ```

2. **Browser Console**
   ```
   Open browser dev tools (F12)
   Go to Console tab
   Look for:
   - JavaScript errors
   - Failed to load resources
   - Network errors
   ```

3. **Network Tab**
   ```
   Go to Network tab
   Refresh the page
   Look for:
   - Failed requests (red)
   - 404 errors
   - 500 errors
   ```

4. **Common Fixes:**

   **If seeing 404 errors:**
   - Check that `templates/` folder structure is correct
   - Verify `index.html` is in `templates/` folder

   **If seeing 500 errors:**
   - Check Render logs for Python errors
   - Verify all imports are working
   - Check that JSON files are in the right location

   **If seeing CORS errors:**
   - CORS is already enabled in the code
   - This might be a browser cache issue
   - Try incognito mode

### Quick Debug Commands (in Render SSH)

If you can SSH into your Render instance:

```bash
# Check if files exist
ls -la templates/
ls -la *.json

# Check Python version
python --version

# Test import
python -c "import flask; print('Flask OK')"
python -c "import google.generativeai; print('Gemini OK')"
```

## Current Version Status

✅ **No Stripe integration** - Will work without environment variables
✅ **Type labels removed** - SS/SD/DS/DD not mentioned
✅ **Greeting clean** - No user input in greeting
✅ **CA frequency fixed** - CAs appear every 3-4 messages
✅ **Ready for Render deployment**

## Deployment Checklist

Before deploying to Render:

- [ ] All files are in the correct structure
- [ ] `requirements.txt` includes all dependencies
- [ ] `templates/index.html` exists
- [ ] JSON data files are present
- [ ] `ai_system_prompt.txt` is included
- [ ] Environment variables are ready (GEMINI_API_KEY required)

For Paywall (Optional):
- [ ] Stripe account set up
- [ ] Products created in Stripe
- [ ] Webhook endpoint ready (after deployment)
- [ ] STRIPE_SECRET_KEY ready
- [ ] STRIPE_WEBHOOK_SECRET ready (after webhook creation)

## Support

If you're still seeing a blank screen:

1. **Send me your Render logs** - Look for the "Logs" tab in Render
2. **Send browser console errors** - Open F12 → Console tab
3. **Tell me your Render URL** - So I can check the deployed version

The current version should work immediately on Render without any Stripe setup. The blank screen is likely a simple configuration issue that we can debug quickly!