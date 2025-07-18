# Architecture Overview

- **Email Intake:** Gmail API fetches unread emails/attachments
- **Parsing:** PDFs via pdfplumber, images via pytesseract
- **RAG:** Chunks/embeds text, retrieves relevant info for Gemini prompts
- **AI:** Gemini answers underwriting questions, compared to YAML criteria
- **Frontend:** React dashboard for brokers/admins
- **Backend:** FastAPI for API, parsing, and workflow logic 