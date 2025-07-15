# backend-broker

This is the backend API for the broker admin UI. It is built with FastAPI and provides endpoints to:
- List available loan criteria (YAML files in ../criteria/)
- Read and update criteria for each loan type
- (Future) Manage user permissions and broker instances

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pyyaml
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ``` 