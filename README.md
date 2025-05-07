# RAG Web Search Assistant

This application uses Retrieval Augmented Generation (RAG) to provide comprehensive, up-to-date answers from web search results. The application is split into two parts:

1. A FastAPI backend using LangChain for RAG functionality
2. A Next.js frontend for the user interface

## Project Structure

```
rag-app/
├── backend/
│   └── api.py             # FastAPI backend
├── frontend/
│   ├── app/
│   │   ├── layout.tsx     # Next.js app layout
│   │   └── page.tsx       # Main page component
│   ├── components/
│   │   ├── Answer.tsx     # Answer display component
│   │   └── Search.tsx     # Search input component
│   ├── styles/
│   │   └── globals.css    # Global styles
│   └── package.json       # Frontend dependencies
├── main.py                # Core RAG functionality
└── .env                   # Environment variables (create this file)
```

## Prerequisites

- Python 3.8+ with pip
- Node.js and npm/yarn
- OpenAI API key
- Tavily API key (for web search capabilities)

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the root directory with the following:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
MODEL_NAME=gpt-4o
TEMPERATURE=0
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn langchain langchain_openai python-dotenv tavily-python

# Run the FastAPI backend
cd backend
uvicorn api:app --reload --port 8000
```

The backend API will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Run the development server
npm run dev
# or
yarn dev
```

The frontend application will be available at: http://localhost:3000

## API Endpoints

- `GET /` - Health check endpoint
- `POST /api/ask` - Processes a question and returns an answer with sources

## Environment Configuration

For production deployment, you should:

1. Set up proper CORS restrictions in the backend
2. Configure environment variables securely
3. Set up a production-ready server for FastAPI
4. Build and deploy the Next.js frontend to a static hosting service

## Technologies Used

- **Backend**: FastAPI, LangChain, Tavily API, OpenAI
- **Frontend**: Next.js, React, TypeScript, CSS