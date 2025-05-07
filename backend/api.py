from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
from typing import List, Dict, Optional

# Add the parent directory to the path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import answer_question

class QuestionRequest(BaseModel):
    question: str

class ReadMoreItem(BaseModel):
    url: str
    title: str

class AnswerResponse(BaseModel):
    main_answer: str
    follow_up_questions: List[str] = []
    read_more: List[Dict[str, str]] = []

app = FastAPI(title="RAG Web Search API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "RAG Web Search API is running"}

@app.post("/api/ask", response_model=AnswerResponse)
async def ask(request: QuestionRequest):
    """Process a question and return an answer with sources and follow-up questions"""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get raw answer from the main module
        raw_answer = answer_question(request.question)
        
        # Format the answer (using the same logic from app.py)
        formatted_answer = format_answer(raw_answer)
        
        return formatted_answer
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_answer(raw_answer: str) -> dict:
    """Format the raw answer into structured sections for better display"""
    import re
    
    # Initialize result structure
    result = {
        'main_answer': '',
        'follow_up_questions': [],
        'read_more': []
    }
    
    # Check for "Follow-up questions" or similar patterns
    follow_up_patterns = [
        r'Follow-up questions(?: to explore next)?:',
        r'Follow-up Questions:',
        r'Additional questions you might be interested in:',
        r'You might also want to know:'
    ]
    
    # Check for "Read more" or similar patterns
    read_more_patterns = [
        r'Read more:',
        r'Read More:',
        r'Sources:',
        r'References:'
    ]
    
    # Combine patterns
    combined_follow_up_pattern = '|'.join(follow_up_patterns)
    combined_read_more_pattern = '|'.join(read_more_patterns)
    
    # Extract main answer, follow-up and read more sections
    main_answer = raw_answer
    
    # Search for follow-up questions section
    follow_up_match = re.search(f'({combined_follow_up_pattern})(.*?)(?:{combined_read_more_pattern}|$)', 
                                raw_answer, re.DOTALL)
    
    read_more_match = re.search(f'({combined_read_more_pattern})(.*?)$', raw_answer, re.DOTALL)
    
    # Extract follow-up questions if found
    if follow_up_match:
        # Update main answer to exclude follow-up
        main_answer_end = follow_up_match.start()
        main_answer = raw_answer[:main_answer_end].strip()
        
        # Extract follow-up questions text
        follow_up_text = follow_up_match.group(2).strip()
        
        # Parse numbered items
        questions = []
        for line in follow_up_text.split('\n'):
            line = line.strip()
            # Match patterns like "1. Question" or "1) Question" or just a question
            if re.match(r'^\d+[\.\)]', line):
                question = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if question:
                    questions.append(question)
        
        result['follow_up_questions'] = questions
    
    # Extract read more links if found
    if read_more_match:
        # If we didn't find follow-up but found read-more
        if not follow_up_match:
            main_answer_end = read_more_match.start()
            main_answer = raw_answer[:main_answer_end].strip()
        
        read_more_text = read_more_match.group(2).strip()
        
        # Parse links - could be URLs or titles
        links = []
        for line in read_more_text.split('\n'):
            line = line.strip()
            if line:
                # Try to extract URLs if present
                url_match = re.search(r'(https?://\S+)', line)
                if url_match:
                    url = url_match.group(1)
                    # Try to extract title
                    title = line.replace(url, '').strip()
                    if not title:
                        title = url
                    
                    # Clean up the title
                    title = title.strip('- []()').strip()
                    
                    links.append({'url': url, 'title': title})
                elif line:  # Just a title without URL
                    links.append({'url': '#', 'title': line})
        
        result['read_more'] = links
    
    # Set the main answer
    result['main_answer'] = main_answer
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)