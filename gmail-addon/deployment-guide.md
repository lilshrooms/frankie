# Gmail Add-on Deployment Guide

## Prerequisites

1. **Google Workspace Account** - You need a Google Workspace account to deploy Gmail Add-ons
2. **Frankie Backend** - Your Frankie backend must be deployed and accessible
3. **API Key** - Generate an API key for the Gmail Add-on to authenticate with Frankie

## Step 1: Prepare Your Frankie Backend

### 1.1 Deploy Frankie Backend

Ensure your Frankie backend is deployed and accessible via HTTPS. You'll need the base URL for configuration.

### 1.2 Generate API Key

Create an API key for the Gmail Add-on:

```bash
# In your Frankie backend
# Add API key generation endpoint or use existing authentication
```

### 1.3 Verify API Endpoints

Test these endpoints are working:
- `POST /email/process`
- `POST /rates/quote`
- `POST /loan-files`

## Step 2: Set Up Google Apps Script

### 2.1 Create New Project

1. Go to [Google Apps Script](https://script.google.com/)
2. Click **"New Project"**
3. Rename the project to "Frankie Gmail Add-on"

### 2.2 Add Files

1. **Replace `Code.gs`** with the content from `gmail-addon/Code.gs`
2. **Create `config.js`** and add the content from `gmail-addon/config.js`
3. **Update `appsscript.json`** with the content from `gmail-addon/appsscript.json`

### 2.3 Configure Settings

Update the configuration in `config.js`:

```javascript
const CONFIG = {
  FRANKIE_API_BASE: 'https://your-actual-frankie-domain.com',
  FRANKIE_API_KEY: 'your-actual-api-key',
  // ... other settings
};
```

## Step 3: Test the Add-on

### 3.1 Test Functions

1. In Google Apps Script, click **"Select function"** → **"onGmailMessage"**
2. Click the **play button** to test
3. Check execution logs for any errors

### 3.2 Test API Calls

1. Create a test function to verify API connectivity:

```javascript
function testAPI() {
  try {
    const response = UrlFetchApp.fetch(`${CONFIG.FRANKIE_API_BASE}/rates/current`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${CONFIG.FRANKIE_API_KEY}`
      }
    });
    console.log('API Test Success:', response.getContentText());
  } catch (error) {
    console.error('API Test Failed:', error);
  }
}
```

## Step 4: Deploy as Gmail Add-on

### 4.1 Create Deployment

1. Click **"Deploy"** → **"New deployment"**
2. Choose **"Gmail Add-on"** as the type
3. Set version description (e.g., "v1.0 - Initial Release")
4. Click **"Deploy"**

### 4.2 Configure Add-on Settings

1. **Add-on name**: "Frankie AI Assistant"
2. **Description**: "AI-powered loan assistant for mortgage brokers"
3. **Logo**: Upload your Frankie logo (optional)
4. **Support URL**: Your support contact
5. **Privacy Policy**: Your privacy policy URL

### 4.3 Set Permissions

The add-on will request these permissions:
- **Gmail Read/Write**: To access and process emails
- **External Requests**: To call your Frankie API

## Step 5: Install in Gmail

### 5.1 For Development

1. In the deployment, click **"Install"**
2. Choose your Google Workspace account
3. Grant permissions when prompted
4. The add-on will appear in Gmail's sidebar

### 5.2 For Production

1. **Submit for Review** (if publishing to marketplace):
   - Go to Google Workspace Marketplace
   - Submit your add-on for review
   - Wait for approval (can take 1-2 weeks)

2. **Direct Installation** (for your organization):
   - Share the deployment link with your team
   - Each user installs individually

## Step 6: Verify Installation

### 6.1 Test in Gmail

1. Open Gmail
2. Select any email
3. Look for the Frankie sidebar on the right
4. Test the "Analyze Email" function

### 6.2 Check Logs

1. In Google Apps Script, go to **"Executions"**
2. Monitor function executions
3. Check for any errors or issues

## Step 7: Monitor and Maintain

### 7.1 Monitor Usage

- Check execution logs regularly
- Monitor API usage and costs
- Track user engagement

### 7.2 Update the Add-on

1. Make changes to the code
2. Create a new deployment version
3. Update the existing deployment
4. Users will get the update automatically

## Troubleshooting

### Common Issues

1. **Add-on not appearing**:
   - Check deployment status
   - Verify permissions are granted
   - Clear browser cache

2. **API errors**:
   - Verify API key is correct
   - Check API endpoints are accessible
   - Test with curl or Postman

3. **Email processing fails**:
   - Check email format
   - Verify Gmail permissions
   - Review execution logs

### Debug Commands

```javascript
// Test email processing
function testEmailProcessing() {
  const testEmail = {
    subject: "Loan Application - $500k",
    body: "Looking for a $500,000 loan with 720 credit score and 80% LTV",
    sender: "test@example.com"
  };
  
  const result = analyzeEmail({ parameters: { threadId: 'test' } });
  console.log('Test Result:', result);
}
```

## Security Considerations

1. **API Key Security**: Never expose API keys in client-side code
2. **HTTPS Only**: Ensure all API calls use HTTPS
3. **Data Privacy**: Review what data is being sent to your API
4. **Permissions**: Only request necessary Gmail permissions

## Next Steps

1. **User Training**: Create documentation for your team
2. **Analytics**: Add usage tracking
3. **Enhancements**: Plan future features
4. **Scaling**: Prepare for more users

## Support

For deployment issues:
1. Check Google Apps Script documentation
2. Review execution logs
3. Test with simple examples first
4. Contact Google Workspace support if needed 