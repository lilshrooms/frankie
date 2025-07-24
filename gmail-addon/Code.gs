/**
 * Frankie Gmail Add-on
 * AI-powered loan assistant for mortgage brokers
 */

// Configuration
const FRANKIE_API_BASE = 'http://localhost:8000'; // Update with your domain for production
const FRANKIE_API_KEY = 'frankie-gmail-addon-key-2024'; // API key for Gmail Add-on

/**
 * Triggered when a Gmail message is selected
 */
function onGmailMessage(e) {
  try {
    const messageId = e.messageMetadata.messageId;
    const threadId = e.messageMetadata.threadId;
    
    // Get email content
    const emailData = getEmailContent(messageId);
    
    // Create the card interface
    const card = createMainCard(emailData, threadId);
    
    return card;
  } catch (error) {
    console.error('Error in onGmailMessage:', error);
    return createErrorCard('Failed to process email');
  }
}

/**
 * Get email content and metadata
 */
function getEmailContent(messageId) {
  const message = GmailApp.getMessageById(messageId);
  const thread = message.getThread();
  
  return {
    subject: message.getSubject(),
    sender: message.getFrom(),
    body: message.getPlainBody(),
    htmlBody: message.getBody(),
    date: message.getDate(),
    threadId: thread.getId(),
    messageId: messageId,
    attachments: getAttachments(message)
  };
}

/**
 * Extract attachments from email
 */
function getAttachments(message) {
  const attachments = message.getAttachments();
  return attachments.map(attachment => ({
    name: attachment.getName(),
    size: attachment.getSize(),
    contentType: attachment.getContentType(),
    data: Utilities.base64Encode(attachment.getBytes())
  }));
}

/**
 * Create the main card interface
 */
function createMainCard(emailData, threadId) {
  const card = CardService.newCardBuilder();
  
  // Header
  const header = CardService.newCardHeader()
    .setTitle('🤖 Frankie AI Assistant')
    .setSubtitle('Analyze loan application')
    .setImageUrl('https://your-domain.com/frankie-logo.png');
  card.setHeader(header);
  
  // Email summary section
  const emailSection = CardService.newCardSection()
    .setHeader('📧 Email Summary');
  
  emailSection.addWidget(
    CardService.newTextParagraph()
      .setText(`**From:** ${emailData.sender}`)
  );
  
  emailSection.addWidget(
    CardService.newTextParagraph()
      .setText(`**Subject:** ${emailData.subject}`)
  );
  
  if (emailData.attachments.length > 0) {
    emailSection.addWidget(
      CardService.newTextParagraph()
        .setText(`**Attachments:** ${emailData.attachments.length} files`)
    );
  }
  
  card.addSection(emailSection);
  
  // Action buttons section
  const actionsSection = CardService.newCardSection()
    .setHeader('🚀 Quick Actions');
  
  // Analyze email button
  const analyzeButton = CardService.newTextButton()
    .setText('🔍 Analyze Email')
    .setOnClickAction(
      CardService.newAction()
        .setFunctionName('analyzeEmail')
        .setParameters({ threadId: threadId })
    );
  actionsSection.addWidget(analyzeButton);
  
  // Generate rate quote button
  const rateButton = CardService.newTextButton()
    .setText('💰 Generate Rate Quote')
    .setOnClickAction(
      CardService.newAction()
        .setFunctionName('generateRateQuote')
        .setParameters({ threadId: threadId })
    );
  actionsSection.addWidget(rateButton);
  
  // Process documents button
  if (emailData.attachments.length > 0) {
    const docsButton = CardService.newTextButton()
      .setText('📄 Process Documents')
      .setOnClickAction(
        CardService.newAction()
          .setFunctionName('processDocuments')
          .setParameters({ threadId: threadId })
      );
    actionsSection.addWidget(docsButton);
  }
  
  card.addSection(actionsSection);
  
  return card.build();
}

/**
 * Analyze email content with Frankie AI
 */
function analyzeEmail(e) {
  const threadId = e.parameters.threadId;
  const emailData = getEmailContentFromThread(threadId);
  
  try {
    // Call Frankie API
    const response = UrlFetchApp.fetch(`${FRANKIE_API_BASE}/email/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${FRANKIE_API_KEY}`
      },
      payload: JSON.stringify({
        email_body: emailData.body,
        sender: emailData.sender,
        subject: emailData.subject,
        thread_id: threadId,
        attachments: emailData.attachments
      })
    });
    
    const result = JSON.parse(response.getContentText());
    
    return createAnalysisCard(result, threadId);
  } catch (error) {
    console.error('Error analyzing email:', error);
    return createErrorCard('Failed to analyze email');
  }
}

/**
 * Generate rate quote from email content
 */
function generateRateQuote(e) {
  const threadId = e.parameters.threadId;
  const emailData = getEmailContentFromThread(threadId);
  
  try {
    // Extract loan information from email
    const loanInfo = extractLoanInfo(emailData.body);
    
    // Call Frankie rate API
    const response = UrlFetchApp.fetch(`${FRANKIE_API_BASE}/rates/quote`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${FRANKIE_API_KEY}`
      },
      payload: JSON.stringify(loanInfo)
    });
    
    const result = JSON.parse(response.getContentText());
    
    return createRateQuoteCard(result, threadId);
  } catch (error) {
    console.error('Error generating rate quote:', error);
    return createErrorCard('Failed to generate rate quote');
  }
}

/**
 * Process email attachments
 */
function processDocuments(e) {
  const threadId = e.parameters.threadId;
  const emailData = getEmailContentFromThread(threadId);
  
  try {
    // Process each attachment
    const results = emailData.attachments.map(attachment => {
      return processAttachment(attachment);
    });
    
    return createDocumentResultsCard(results, threadId);
  } catch (error) {
    console.error('Error processing documents:', error);
    return createErrorCard('Failed to process documents');
  }
}

/**
 * Extract loan information from email text
 */
function extractLoanInfo(emailBody) {
  // Basic extraction - can be enhanced with AI
  const loanAmount = extractLoanAmount(emailBody);
  const creditScore = extractCreditScore(emailBody);
  const ltv = extractLTV(emailBody);
  const loanType = extractLoanType(emailBody);
  
  return {
    loan_amount: loanAmount || 500000,
    credit_score: creditScore || 720,
    ltv: ltv || 80,
    loan_type: loanType || '30yr_fixed'
  };
}

/**
 * Helper functions for data extraction
 */
function extractLoanAmount(text) {
  const match = text.match(/\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:loan|mortgage|amount)/i);
  return match ? parseFloat(match[1].replace(/,/g, '')) : null;
}

function extractCreditScore(text) {
  const match = text.match(/(?:credit\s+score|fico|score)[:\s]*(\d{3})/i);
  return match ? parseInt(match[1]) : null;
}

function extractLTV(text) {
  const match = text.match(/(?:ltv|loan\s+to\s+value)[:\s]*(\d{1,2})/i);
  return match ? parseInt(match[1]) : null;
}

function extractLoanType(text) {
  if (text.match(/fha/i)) return 'fha_30yr';
  if (text.match(/va/i)) return 'va_30yr';
  if (text.match(/usda/i)) return 'usda_30yr';
  if (text.match(/15\s*year/i)) return '15yr_fixed';
  return '30yr_fixed';
}

/**
 * Create analysis results card
 */
function createAnalysisCard(result, threadId) {
  const card = CardService.newCardBuilder();
  
  const header = CardService.newCardHeader()
    .setTitle('🔍 Analysis Results')
    .setSubtitle('AI-powered loan analysis');
  card.setHeader(header);
  
  const section = CardService.newCardSection();
  
  if (result.summary) {
    section.addWidget(
      CardService.newTextParagraph()
        .setText(`**Summary:** ${result.summary}`)
    );
  }
  
  if (result.next_steps && result.next_steps.length > 0) {
    section.addWidget(
      CardService.newTextParagraph()
        .setText('**Next Steps:**')
    );
    
    result.next_steps.forEach(step => {
      section.addWidget(
        CardService.newTextParagraph()
          .setText(`• ${step}`)
      );
    });
  }
  
  // Add action buttons
  const actionButton = CardService.newTextButton()
    .setText('📝 Create Loan File')
    .setOnClickAction(
      CardService.newAction()
        .setFunctionName('createLoanFile')
        .setParameters({ threadId: threadId })
    );
  section.addWidget(actionButton);
  
  card.addSection(section);
  return card.build();
}

/**
 * Create rate quote results card
 */
function createRateQuoteCard(result, threadId) {
  const card = CardService.newCardBuilder();
  
  const header = CardService.newCardHeader()
    .setTitle('💰 Rate Quote')
    .setSubtitle('Current market rates');
  card.setHeader(header);
  
  const section = CardService.newCardSection();
  
  if (result.success && result.quote) {
    const quote = result.quote;
    
    section.addWidget(
      CardService.newTextParagraph()
        .setText(`**Rate:** ${(quote.final_rate * 100).toFixed(3)}%`)
    );
    
    section.addWidget(
      CardService.newTextParagraph()
        .setText(`**Monthly Payment:** $${quote.monthly_payment.toLocaleString()}`)
    );
    
    section.addWidget(
      CardService.newTextParagraph()
        .setText(`**APR:** ${(quote.final_apr * 100).toFixed(3)}%`)
    );
    
    section.addWidget(
      CardService.newTextParagraph()
        .setText(`**Total Interest:** $${quote.total_interest.toLocaleString()}`)
    );
  }
  
  card.addSection(section);
  return card.build();
}

/**
 * Create error card
 */
function createErrorCard(message) {
  const card = CardService.newCardBuilder();
  
  const header = CardService.newCardHeader()
    .setTitle('❌ Error')
    .setSubtitle('Something went wrong');
  card.setHeader(header);
  
  const section = CardService.newCardSection();
  section.addWidget(
    CardService.newTextParagraph()
      .setText(message)
  );
  
  card.addSection(section);
  return card.build();
}

/**
 * Helper function to get email content from thread
 */
function getEmailContentFromThread(threadId) {
  const thread = GmailApp.getThreadById(threadId);
  const messages = thread.getMessages();
  const latestMessage = messages[messages.length - 1];
  
  return {
    subject: latestMessage.getSubject(),
    sender: latestMessage.getFrom(),
    body: latestMessage.getPlainBody(),
    htmlBody: latestMessage.getBody(),
    date: latestMessage.getDate(),
    threadId: threadId,
    attachments: getAttachments(latestMessage)
  };
}

/**
 * Process individual attachment
 */
function processAttachment(attachment) {
  // This would call Frankie's document processing API
  // For now, return basic info
  return {
    name: attachment.name,
    type: attachment.contentType,
    size: attachment.size,
    processed: true
  };
} 