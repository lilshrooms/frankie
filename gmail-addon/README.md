# Frankie Gmail Add-on

AI-powered loan assistant for mortgage brokers - directly in Gmail!

## Features

- 🤖 **AI Email Analysis** - Automatically analyze loan application emails
- 💰 **Rate Quote Generation** - Generate mortgage rate quotes from email content
- 📄 **Document Processing** - Process PDFs and images attached to emails
- 📝 **Loan File Creation** - Create loan files directly from Gmail
- 🔍 **Smart Data Extraction** - Extract loan amounts, credit scores, and LTV from emails

## Setup Instructions

### 1. Google Apps Script Setup

1. Go to [Google Apps Script](https://script.google.com/)
2. Create a new project
3. Replace the default `Code.gs` with the content from this repository
4. Copy the `manifest.json` content to the `appsscript.json` file

### 2. Configuration

Update the configuration variables in `Code.gs`:

```javascript
const FRANKIE_API_BASE = 'https://your-frankie-domain.com'; // Your Frankie backend URL
const FRANKIE_API_KEY = 'your-api-key'; // Your Frankie API key
```

### 3. Deploy as Gmail Add-on

1. In Google Apps Script, click **Deploy** → **New deployment**
2. Choose **Gmail Add-on** as the type
3. Set version description (e.g., "v1.0")
4. Click **Deploy**

### 4. Install in Gmail

1. Go to [Gmail Add-ons](https://workspace.google.com/marketplace/category/gmail-add-ons)
2. Find your add-on and click **Install**
3. Grant necessary permissions
4. The add-on will appear in Gmail's sidebar

## Usage

### Basic Workflow

1. **Open an email** in Gmail
2. **Frankie sidebar** appears automatically
3. **Click "Analyze Email"** to process the email content
4. **Review results** - summary, next steps, and recommendations
5. **Generate rate quotes** or **process documents** as needed

### Email Analysis

The add-on automatically:
- Extracts loan information from email text
- Identifies missing documents
- Provides next steps for loan processing
- Suggests rate optimization opportunities

### Rate Quotes

Generate instant rate quotes by:
1. Clicking **"Generate Rate Quote"**
2. Reviewing current market rates
3. Seeing monthly payment calculations
4. Comparing different loan types

### Document Processing

Process attachments by:
1. Clicking **"Process Documents"** (appears when attachments are present)
2. Reviewing extracted information
3. Creating loan files with processed data

## API Integration

The add-on integrates with your Frankie backend through these endpoints:

- `POST /email/process` - Analyze email content
- `POST /rates/quote` - Generate rate quotes
- `POST /loan-files` - Create loan files

## Security

- All API calls use HTTPS
- OAuth2 authentication with Google
- API key authentication with Frankie backend
- No email data stored locally

## Development

### Local Testing

1. Use Google Apps Script's built-in testing
2. Test with sample emails
3. Check execution logs for debugging

### Debugging

- Use `console.log()` for debugging
- Check execution logs in Google Apps Script
- Monitor API responses in the logs

## Deployment Checklist

- [ ] Update API base URL
- [ ] Add API key
- [ ] Test with sample emails
- [ ] Verify all functions work
- [ ] Deploy to Gmail Add-ons
- [ ] Test in production Gmail

## Troubleshooting

### Common Issues

1. **Add-on not appearing**: Check deployment status and permissions
2. **API errors**: Verify API key and base URL
3. **Email parsing issues**: Check email format and content
4. **Rate quote failures**: Verify rate API is working

### Error Messages

- **"Failed to process email"**: Check API connectivity
- **"Failed to generate rate quote"**: Verify rate API endpoint
- **"Failed to process documents"**: Check document processing API

## Support

For issues or questions:
1. Check the execution logs in Google Apps Script
2. Verify API endpoints are working
3. Test with simple email content first

## Future Enhancements

- [ ] Multi-language support
- [ ] Advanced document processing
- [ ] Automated email responses
- [ ] Integration with loan origination systems
- [ ] Real-time rate updates
- [ ] Custom branding options 