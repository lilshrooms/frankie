#!/bin/bash

# Frankie Gmail Add-on Deployment Script
echo "🚀 Frankie Gmail Add-on Deployment Script"
echo "=========================================="

# Check if backend is running
echo "📡 Checking backend connectivity..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "❌ Backend is not running. Please start it first:"
    echo "   cd backend-broker && python main.py"
    exit 1
fi

# Test API endpoints
echo "🧪 Testing API endpoints..."

# Test email processing
echo "Testing email processing..."
curl -s -X POST http://localhost:8000/email/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer frankie-gmail-addon-key-2024" \
  -d '{"email_body": "Test loan application", "sender": "test@example.com", "subject": "Test"}' \
  > /dev/null && echo "✅ Email processing endpoint working" || echo "❌ Email processing failed"

# Test rate quotes
echo "Testing rate quotes..."
curl -s -X POST http://localhost:8000/rates/quote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer frankie-gmail-addon-key-2024" \
  -d '{"loan_amount": 500000, "credit_score": 720, "ltv": 80, "loan_type": "30yr_fixed"}' \
  > /dev/null && echo "✅ Rate quotes endpoint working" || echo "❌ Rate quotes failed"

# Test document processing
echo "Testing document processing..."
curl -s -X POST http://localhost:8000/documents/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer frankie-gmail-addon-key-2024" \
  -d '{"attachments": [{"name": "test.pdf", "contentType": "application/pdf", "data": "dGVzdA=="}], "thread_id": "test"}' \
  > /dev/null && echo "✅ Document processing endpoint working" || echo "❌ Document processing failed"

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Go to https://script.google.com/"
echo "2. Create a new project called 'Frankie Gmail Add-on'"
echo "3. Replace Code.gs with the content from gmail-addon/Code.gs"
echo "4. Update appsscript.json with content from gmail-addon/appsscript.json"
echo "5. Deploy as Gmail Add-on"
echo "6. Install in Gmail"
echo ""
echo "📚 For detailed instructions, see: gmail-addon/deployment-guide.md"
echo "📖 For configuration, see: gmail-addon/config.js"
echo ""
echo "🔑 API Key: frankie-gmail-addon-key-2024"
echo "🌐 Backend URL: http://localhost:8000 (update for production)"
echo ""
echo "✨ Ready to deploy!" 