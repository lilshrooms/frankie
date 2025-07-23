# Frankie Unified Backend API

A comprehensive FastAPI backend that combines loan file management, email pipeline processing, rate optimization, and conversation management for the Frankie B2B AI-powered loan assistant platform.

## Features

### 🏦 Loan File Management
- Create, read, update, and soft delete loan files
- File upload and attachment management
- Document classification and analysis
- Status tracking and outstanding items management

### 📧 Email Pipeline
- Email processing and analysis with Gemini AI
- Conversation tracking by Gmail thread ID
- Multi-turn conversation management
- Automated response generation
- Document extraction from email attachments

### 💰 Rate System
- Current mortgage rate fetching and storage
- Rate optimization for borrower scenarios
- Quote generation with LLPAs (Loan Level Price Adjustments)
- AI-powered rate analysis and recommendations
- Quick rate analysis with optimization suggestions

### 🤖 AI Integration
- Gemini AI for email analysis and document processing
- AI-powered criteria suggestions
- Rate quote analysis and explanations
- Conversation context management

### 💬 Conversation Management
- Thread-based conversation tracking
- State management (initial_request, waiting_docs, underwriting, complete)
- Turn counting and document tracking
- Automated response generation based on conversation state

## API Endpoints

### Health & Status
- `GET /` - API overview and available endpoints
- `GET /health` - Health check with component status

### Loan Files
- `GET /loan-files` - List all loan files
- `GET /loan-files/{id}` - Get specific loan file
- `POST /loan-files` - Create new loan file with optional document upload
- `DELETE /loan-files/{id}` - Soft delete loan file
- `POST /loan-files/{id}/analyze` - Analyze loan file with AI

### Email Processing
- `POST /email/process` - Process incoming email through pipeline

### Conversations
- `GET /conversations` - List all conversations
- `GET /conversations/{thread_id}` - Get specific conversation
- `DELETE /conversations/{thread_id}` - Delete conversation

### Rate System
- `GET /rates/current` - Get current mortgage rates
- `POST /rates/quote` - Generate rate quote
- `POST /rates/optimize` - Optimize rates for borrower scenario
- `POST /rates/analyze` - Analyze rate quote with AI
- `GET /rates/quick` - Quick rate analysis with optimization

### Criteria Management
- `GET /criteria` - List available criteria files
- `GET /criteria/{loan_type}` - Get criteria for specific loan type
- `POST /criteria/{loan_type}/suggest` - Get AI suggestions for criteria improvements

## Setup & Installation

### Prerequisites
- Python 3.8+
- SQLite (development) or PostgreSQL (production)
- Google Cloud credentials (for Gmail and Gemini integration)

### Installation

1. **Clone the repository and navigate to backend-broker:**
   ```bash
   cd backend-broker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Configure your environment variables
   DATABASE_URL=sqlite:///./frankie.db  # Development
   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Initialize the database:**
   ```bash
   python -c "from database import engine; from models import Base; Base.metadata.create_all(engine)"
   ```

5. **Start the server:**
   ```bash
   python main.py
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Schema

### Core Tables
- **loan_files** - Main loan file records with conversation tracking
- **email_messages** - Email messages with Gmail integration
- **ai_analyses** - AI analysis results with conversation context
- **attachments** - File attachments with document classification
- **user_actions** - User activity tracking

### Key Features
- Soft deletes for audit purposes
- Gmail thread and message ID tracking
- Conversation state management
- Document type classification
- Timestamp tracking for all records

## Development

### Project Structure
```
backend-broker/
├── main.py              # Main FastAPI application
├── models.py            # SQLAlchemy models
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── uploads/            # File upload directory
└── frankie.db          # SQLite database (created automatically)
```

### Adding New Features

1. **New API Endpoints**: Add to `main.py` with proper error handling
2. **Database Models**: Add to `models.py` and run migrations
3. **External Integrations**: Add to appropriate module with error handling
4. **AI Features**: Integrate with Gemini or other AI services

### Testing

```bash
# Test the API
curl http://localhost:8000/health

# Test loan file creation
curl -X POST http://localhost:8000/loan-files \
  -F "borrower=John Doe" \
  -F "broker=Jane Smith" \
  -F "loan_type=conventional" \
  -F "amount=500000"

# Test rate optimization
curl -X POST http://localhost:8000/rates/optimize \
  -H "Content-Type: application/json" \
  -d '{"loan_amount": 500000, "credit_score": 720, "ltv": 80}'
```

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GEMINI_API_KEY=your_production_api_key
ENVIRONMENT=production
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Integration with Frontend

The backend is designed to work with the React frontend (`frontend-broker`). Key integration points:

- **CORS**: Configured for localhost:3000 and localhost:5173
- **File Uploads**: Multipart form data support
- **Real-time Updates**: WebSocket support planned
- **Authentication**: JWT-based auth planned

## Monitoring & Logging

- **Logging**: Configured with INFO level logging
- **Health Checks**: `/health` endpoint for monitoring
- **Error Handling**: Comprehensive error responses
- **Performance**: Background tasks for heavy operations

## Roadmap

- [ ] JWT authentication and authorization
- [ ] WebSocket support for real-time updates
- [ ] Advanced rate optimization algorithms
- [ ] Multi-broker support
- [ ] Advanced admin dashboard
- [ ] Production deployment automation
- [ ] Comprehensive test suite
- [ ] API rate limiting and caching

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Test individual endpoints for specific issues
4. Check environment variable configuration

## License

This project is part of the Frankie B2B AI-powered loan assistant platform. 