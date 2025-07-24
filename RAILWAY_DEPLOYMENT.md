# Railway Deployment Guide for Frankie

## 🚀 Deploy to Railway

### Step 1: Install Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or using Homebrew (macOS)
brew install railway
```

### Step 2: Login to Railway

```bash
railway login
```

### Step 3: Initialize Railway Project

```bash
cd backend-broker
railway init
```

### Step 4: Set Environment Variables

```bash
# Set your Supabase database URL
railway variables set DATABASE_URL="postgresql://postgres:iVYlzK02219DCVcF@db.mzyurrvepchpkzmbzqyx.supabase.co:5432/postgres"

# Set Gmail Add-on API key
railway variables set GMAIL_ADDON_API_KEY="frankie-gmail-addon-key-2025"
```

### Step 5: Deploy

```bash
railway up
```

### Step 6: Get Your Production URL

```bash
railway domain
```

## 🔧 Alternative: Deploy via GitHub

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment files"
git push origin main
```

### Step 2: Connect Railway to GitHub

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `frankie` repository
5. Set the root directory to `backend-broker`

### Step 3: Configure Environment Variables

In Railway Dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add:
   - `DATABASE_URL`: `postgresql://postgres:iVYlzK02219DCVcF@db.mzyurrvepchpkzmbzqyx.supabase.co:5432/postgres`
   - `GMAIL_ADDON_API_KEY`: `frankie-gmail-addon-key-2025`

## 🧪 Test Deployment

Once deployed, test your endpoints:

```bash
# Health check
curl https://your-railway-url.railway.app/health

# Test loan files
curl https://your-railway-url.railway.app/loan-files

# Test Gmail Add-on endpoint
curl -X POST https://your-railway-url.railway.app/email/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer frankie-gmail-addon-key-2025" \
  -d '{"email_body": "Test", "sender": "test@example.com", "subject": "Test"}'
```

## 🔄 Update Gmail Add-on

Once you have your production URL, update `gmail-addon/config.js`:

```javascript
const CONFIG = {
  FRANKIE_API_BASE: 'https://your-railway-url.railway.app',
  FRANKIE_API_KEY: 'frankie-gmail-addon-key-2025',
  // ... rest of config
};
```

## 📊 Monitor Your Deployment

- **Railway Dashboard**: Monitor logs, performance, and usage
- **Supabase Dashboard**: Monitor database performance and usage
- **Health Endpoint**: `https://your-url.railway.app/health`

## 🚨 Troubleshooting

### Common Issues:

1. **Build Fails**: Check Railway logs for dependency issues
2. **Database Connection**: Verify DATABASE_URL is correct
3. **Port Issues**: Railway automatically sets PORT environment variable
4. **Memory Issues**: Railway has memory limits, optimize if needed

### Useful Commands:

```bash
# View logs
railway logs

# Restart deployment
railway restart

# Check status
railway status
```

## 💰 Railway Pricing

- **Free Tier**: $5 credit monthly
- **Pro**: Pay-as-you-go
- **Team**: $20/month per user

Your Frankie backend should fit comfortably in the free tier! 