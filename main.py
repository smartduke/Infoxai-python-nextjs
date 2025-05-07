import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
import json
import datetime
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "") # You'll need to set this in your .env file

# Initialize the model
model = ChatOpenAI(
    model_name=os.getenv("MODEL_NAME", "gpt-4o"),
    temperature=float(os.getenv("TEMPERATURE", "0")),
    openai_api_key=OPENAI_API_KEY
)

# Initialize Tavily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Function to detect if a query is time-sensitive
def is_time_sensitive(query: str) -> bool:
    """Determine if a query is about current events or time-sensitive information."""
    time_keywords = [
        "today", "current", "latest", "recent", "now", "ongoing", 
        "live", "update", "breaking", "news", "match", "game",
        "score", "weather", "forecast", "price", "stock", "crypto",
        "election", "tournament", "ipl", "playoff", "result"
    ]
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Check for time-sensitive keywords
    return any(keyword in query_lower for keyword in time_keywords)

# Function to perform a search using Tavily API
def tavily_search(query: str, search_depth="basic", max_results=10) -> List[Dict]:
    """
    Perform a web search using Tavily API
    
    Args:
        query: The search query
        search_depth: "basic" or "deep"
        max_results: Maximum number of results to return
        
    Returns:
        List of search result dictionaries
    """
    print(f"Searching for: {query} with depth {search_depth}")
    try:
        if not TAVILY_API_KEY:
            print("Warning: Tavily API key not found. Using fallback approach.")
            return [{
                "title": "API Key Missing",
                "url": "",
                "content": "Please set up a Tavily API key in your .env file to enable web search."
            }]
        
        # For time-sensitive queries, we want to ensure fresh results
        include_answer = False
        if is_time_sensitive(query):
            query = f"{query} (latest information as of {datetime.datetime.now().strftime('%Y-%m-%d')})"
            include_answer = True
        
        # Call Tavily search API
        search_response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=True,
            max_results=max_results
        )
        
        if 'results' in search_response:
            return search_response['results']
        return []
    except Exception as e:
        print(f"Error in Tavily search: {e}")
        return [{
            "title": "Search API Error",
            "url": "",
            "content": f"Error performing search: {str(e)}"
        }]

# Function to get documents from search results
def get_content_from_search(query: str) -> List[Document]:
    """
    Get search results and convert them to Document objects
    
    Args:
        query: The search query
        
    Returns:
        List of Document objects
    """
    # Determine search depth based on query type - use 'advanced' instead of 'deep'
    search_depth = "advanced" if is_time_sensitive(query) else "basic"
    
    # Get search results
    search_results = tavily_search(query, search_depth=search_depth)
    documents = []
    
    # Add a timestamp document
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    documents.append(Document(
        page_content=f"Current date and time: {current_date} {current_time}. The following information was retrieved from web search results.",
        metadata={"source": "system", "title": "Current Timestamp"}
    ))
    
    # Add documents from search results
    for i, result in enumerate(search_results):
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        raw_content = result.get("raw_content", "")
        
        # Use raw content if available, otherwise use regular content
        page_content = raw_content if raw_content else content
        
        # Create document from the search result
        documents.append(Document(
            page_content=f"Title: {title}\n\nContent: {page_content[:2000]}",
            metadata={
                "source": url, 
                "title": title, 
                "index": i+1
            }
        ))
    
    return documents

# Function to generate a response with real-time search results
def generate_response(query: str) -> List[Document]:
    """
    Generate a response using real-time web search
    
    Args:
        query: The search query
        
    Returns:
        List of Document objects with response content
    """
    documents = []
    
    # Get current date information
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Get content from search
    try:
        web_documents = get_content_from_search(query)
        if web_documents:
            documents.extend(web_documents)
    except Exception as e:
        print(f"Error fetching web content: {e}")
        documents.append(Document(
            page_content=f"Error retrieving web information: {str(e)}",
            metadata={"source": "error", "title": "Web Search Error"}
        ))
    
    # If it's a time-sensitive query, add a note
    if is_time_sensitive(query):
        documents.append(Document(
            page_content=f"Note: This query appears to be about time-sensitive information. " +
                       f"The web search results above should contain current information as of {current_date}.",
            metadata={"source": "system", "title": "Time Sensitivity Note"}
        ))
    
    return documents

# Format documents function
def format_docs(docs):
    return "\n\n".join([f"Source {doc.metadata.get('index', i+1)}:\n{doc.page_content}\nURL: {doc.metadata.get('source', 'No URL')}" for i, doc in enumerate(docs)])

# Prompt for generating final answers
template = """
You are an AI research assistant that provides accurate and helpful information.
Answer the question using ONLY the following information from web search results. If you cannot answer the question with the provided information,
state that you don't have enough information and suggest what else to search for.

Current Date: {current_date}
Current Time: {current_time}

Information from web search:
{context}

Question: {question}

Provide a comprehensive answer that:
1. Directly answers the question based ONLY on the information in the search results
2. Includes specific facts from the provided information 
3. Cites your sources with [Source X] notation after each fact (where X is the number of the source)
4. If the question is about current events or time-sensitive information, explicitly mention the date of the information
5. At the end, list 3 follow-up questions that would be interesting to explore next
6. At the end, include a "Read More" section with the most relevant source URLs from the search results

Follow these special instructions:
- Don't make up information that's not in the search results
- Don't rely on your general knowledge or training data
- If the search results contain contradictory information, acknowledge this and present multiple perspectives
- Be clear about which information comes from which source

Answer:
"""

# Create prompt from template
prompt = PromptTemplate(
    input_variables=["context", "question", "current_date", "current_time"],
    template=template
)

# Updated chain with current date and time information
def process_with_date(question):
    # Get current date and time
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Generate response with real-time web search
    docs = generate_response(question)
    context = format_docs(docs)
    
    # Return all needed variables
    return {
        "context": context,
        "question": question,
        "current_date": current_date,
        "current_time": current_time
    }

# Define the RAG chain 
rag_chain = (
    RunnableLambda(process_with_date)
    | prompt
    | model
    | StrOutputParser()
)

def answer_question(question: str) -> str:
    """
    Process a user question and return an answer with citations and follow-up questions.
    
    Args:
        question: The user's question
    
    Returns:
        str: Response with answer, citations, and follow-up questions
    """
    try:
        return rag_chain.invoke(question)
    except Exception as e:
        return f"An error occurred while processing your question: {str(e)}"

def main():
    print("🔍 Web Search RAG Assistant 🔍")
    print("Ask a question to search the web and get a detailed answer with sources")
    print("Type 'exit' to quit\n")
    
    while True:
        question = input("\nQuestion: ")
        if question.lower() == 'exit':
            break
        
        print("\nSearching and generating answer...\n")
        answer = answer_question(question)
        print("\nAnswer:")
        print(answer)
        print("\n" + "-"*50)

if __name__ == "__main__":
    main()