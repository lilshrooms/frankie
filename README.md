# Frankie: AI-Powered Loan Assistant

Frankie is a B2B platform that automates the intake, understanding, and preliminary underwriting of homebuyer loan requests. It is designed to reduce manual work for loan officers and processors by parsing unstructured emails and attachments, extracting relevant information, and analyzing it against underwriting criteria using advanced AI models.

## Key Features
- **Email-Based Intake:** Brokers send loan requests and supporting documents (PDFs, images) via email.
- **Attachment Parsing:** The system extracts text from PDFs (e.g., W2s, 1099s, bank statements) and images using OCR.
- **RAG Pipeline:** Implements a simple Retrieval-Augmented Generation (RAG) pipeline:
  - Chunks and embeds extracted text from all attachments.
  - Retrieves the most relevant chunks for a given query (e.g., "What is the borrower's total income?").
  - Prepares a context-rich prompt for Gemini (or other LLMs) to answer underwriting questions or extract structured data.
- **Criteria Comparison:** Extracted data is compared against YAML-based underwriting criteria for automated analysis.
- **Admin UI:** React/TypeScript frontend and FastAPI backend for managing criteria, permissions, and AI-assisted suggestions.

## How It Works
1. **Email Ingestion:** Fetch unread emails and attachments from a designated Gmail inbox.
2. **Document Parsing:** Use `pdfplumber` for PDFs and `pytesseract` for images to extract text.
3. **RAG Pipeline:**
   - Chunk and embed all extracted text.
   - Retrieve relevant chunks for underwriting queries.
   - Prepare prompts for Gemini to extract or reason over borrower data.
4. **Analysis:** Compare extracted data to underwriting criteria and generate responses or follow-up questions.
5. **Admin UI:** Loan officers can view/edit criteria and use an AI assistant to suggest changes.

## Getting Started
- Clone the repo and set up your `.env` with Gmail and Gemini credentials.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Run the email ingestion script:
  ```bash
  python3 -m email_ingest.gmail_fetcher
  ```
- Start the frontend and backend for the admin UI as described in their respective README files.

## Roadmap
- Mark emails as read after processing
- Automated replies to brokers
- Multi-turn, context-aware workflows
- Multi-broker support and advanced admin UI
- Production deployment (Vercel for frontend, cloud for backend)

---
For more details, see the code comments and the criteria/ folder for example underwriting rules.
