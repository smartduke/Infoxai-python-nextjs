import os
from typing import List, Dict, Any, Optional, Union, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
import json
import datetime
import requests
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

# SearxNG Client class for search functionality
class SearxNGClient:
    """
    Client for SearxNG search API
    """
    def __init__(self, base_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """
        Initialize SearxNG client
        
        Args:
            base_url: Base URL of the SearxNG instance
            api_key: API key (if your instance requires it)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def search(self, 
               query: str, 
               category: str = "general", 
               time_range: Optional[str] = None,
               language: str = "en",
               max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using SearxNG API
        
        Args:
            query: The search query
            category: Search category (general, images, news, etc.)
            time_range: Time range for search results
            language: Language code
            max_results: Maximum number of results to return
            
        Returns:
            List of search result dictionaries
        """
        search_url = f"{self.base_url}/search"
        
        params = {
            "q": query,
            "format": "json",
            "categories": category,
            "language": language,
            "pageno": 1,
            "results": max_results
        }
        
        if time_range:
            params["time_range"] = time_range
            
        try:
            response = requests.get(
                search_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Error from SearxNG API: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            
            # Process results into a format similar to Tavily results
            results = []
            if "results" in data:
                for i, result in enumerate(data["results"]):
                    processed_result = {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        # Add equivalent to raw_content if available
                        "raw_content": result.get("content", ""),
                        "score": result.get("score", 0),
                        "source": "searxng",
                        "position": i + 1
                    }
                    results.append(processed_result)
                    
                    # Limit results to max_results
                    if len(results) >= max_results:
                        break
            
            return results
            
        except Exception as e:
            print(f"Error in SearxNG search: {e}")
            return []

# Initialize SearxNG client if URL is provided
SEARXNG_URL = os.getenv("SEARXNG_URL", "")
searxng_client = None
if SEARXNG_URL:
    searxng_client = SearxNGClient(base_url=SEARXNG_URL)

# Search engine options
SEARCH_ENGINES = {
    "tavily": "Tavily Search API",
    "searxng": "SearxNG Search Engine",
    "both": "Both Search Engines (Combined Results)"
}

# Default search engine to use
DEFAULT_SEARCH_ENGINE = os.getenv("DEFAULT_SEARCH_ENGINE", "tavily")
if DEFAULT_SEARCH_ENGINE not in SEARCH_ENGINES:
    DEFAULT_SEARCH_ENGINE = "tavily"

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

# Function to perform a search using the specified search engine
def search_with_engine(
    query: str, 
    search_engine: str = DEFAULT_SEARCH_ENGINE,
    search_depth: str = "basic", 
    max_results: int = 10
) -> List[Dict]:
    """
    Perform a search using the specified search engine
    
    Args:
        query: The search query
        search_engine: Which search engine to use ('tavily', 'searxng', or 'both')
        search_depth: "basic" or "advanced"
        max_results: Maximum number of results to return
        
    Returns:
        List of search result dictionaries
    """
    print(f"Searching for: '{query}' with {search_engine} engine, depth {search_depth}")
    
    results = []
    
    # Determine if we should use Tavily
    use_tavily = search_engine in ["tavily", "both"]
    if use_tavily:
        try:
            if not TAVILY_API_KEY:
                print("Warning: Tavily API key not found. Skipping Tavily search.")
            else:
                # For time-sensitive queries, we want to ensure fresh results
                include_answer = False
                tavily_query = query
                if is_time_sensitive(query):
                    tavily_query = f"{query} (latest information as of {datetime.datetime.now().strftime('%Y-%m-%d')})"
                    include_answer = True
                
                # Call Tavily search API
                search_response = tavily_client.search(
                    query=tavily_query,
                    search_depth=search_depth,
                    include_answer=include_answer,
                    include_raw_content=True,
                    max_results=max_results
                )
                
                if 'results' in search_response:
                    # Add a source tag to Tavily results
                    for result in search_response['results']:
                        result["source"] = "tavily"
                    results.extend(search_response['results'])
        except Exception as e:
            print(f"Error in Tavily search: {e}")
            results.append({
                "title": "Tavily Search API Error",
                "url": "",
                "content": f"Error performing Tavily search: {str(e)}",
                "source": "tavily_error"
            })
    
    # Determine if we should use SearxNG
    use_searxng = search_engine in ["searxng", "both"]
    if use_searxng and searxng_client:
        try:
            # Map search depth to a suitable category for SearxNG
            category = "general"
            if search_depth == "advanced":
                category = "general,news"  # Multiple categories for deeper search
                
            # Set time range if it's a time-sensitive query
            time_range = None
            if is_time_sensitive(query):
                time_range = "day"  # Use 'day' for recent results
                
            # Get results from SearxNG
            searxng_results = searxng_client.search(
                query=query,
                category=category,
                time_range=time_range,
                max_results=max_results
            )
            
            results.extend(searxng_results)
        except Exception as e:
            print(f"Error in SearxNG search: {e}")
            results.append({
                "title": "SearxNG Search Error",
                "url": "",
                "content": f"Error performing SearxNG search: {str(e)}",
                "source": "searxng_error"
            })
    
    # If no results were found from any engine
    if not results:
        results.append({
            "title": "No Search Results",
            "url": "",
            "content": "No results found for your query. Please try a different search term or check search engine settings.",
            "source": "no_results"
        })
    
    # If using both engines, limit to max_results total
    if len(results) > max_results:
        results = results[:max_results]
        
    return results

# Function to get documents from search results
def get_content_from_search(
    query: str, 
    search_engine: str = DEFAULT_SEARCH_ENGINE
) -> List[Document]:
    """
    Get search results and convert them to Document objects
    
    Args:
        query: The search query
        search_engine: Which search engine to use
        
    Returns:
        List of Document objects
    """
    # Determine search depth based on query type
    search_depth = "advanced" if is_time_sensitive(query) else "basic"
    
    # Get search results
    search_results = search_with_engine(
        query, 
        search_engine=search_engine,
        search_depth=search_depth
    )
    
    documents = []
    
    # Add a timestamp document
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    engine_str = SEARCH_ENGINES.get(search_engine, search_engine)
    documents.append(Document(
        page_content=f"Current date and time: {current_date} {current_time}. The following information was retrieved from {engine_str}.",
        metadata={"source": "system", "title": "Current Timestamp"}
    ))
    
    # Add documents from search results
    for i, result in enumerate(search_results):
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        raw_content = result.get("raw_content", "")
        source_engine = result.get("source", "unknown")
        
        # Use raw content if available, otherwise use regular content
        page_content = raw_content if raw_content else content
        
        # Create document from the search result
        documents.append(Document(
            page_content=f"Title: {title}\n\nContent: {page_content[:2000]}\n\nSearch Engine: {source_engine}",
            metadata={
                "source": url, 
                "title": title, 
                "index": i+1,
                "engine": source_engine
            }
        ))
    
    return documents

# Function to generate a response with real-time search results
def generate_response(query: str, search_engine: str = DEFAULT_SEARCH_ENGINE) -> List[Document]:
    """
    Generate a response using real-time web search
    
    Args:
        query: The search query
        search_engine: Which search engine to use
        
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
        web_documents = get_content_from_search(query, search_engine=search_engine)
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
def process_with_date(question, search_engine=DEFAULT_SEARCH_ENGINE):
    """Process a question with date information and search engine selection"""
    # Get current date and time
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Generate response with real-time web search
    docs = generate_response(question, search_engine=search_engine)
    context = format_docs(docs)
    
    # Return all needed variables
    return {
        "context": context,
        "question": question,
        "current_date": current_date,
        "current_time": current_time,
        "search_engine": SEARCH_ENGINES.get(search_engine, search_engine)
    }

# Define the RAG chain 
rag_chain = (
    RunnableLambda(process_with_date)
    | prompt
    | model
    | StrOutputParser()
)

def answer_question(question: str, search_engine: str = DEFAULT_SEARCH_ENGINE) -> str:
    """
    Process a user question and return an answer with citations and follow-up questions.
    
    Args:
        question: The user's question
        search_engine: Which search engine to use
    
    Returns:
        str: Response with answer, citations, and follow-up questions
    """
    try:
        # Validate search engine choice
        if search_engine not in SEARCH_ENGINES:
            search_engine = DEFAULT_SEARCH_ENGINE
            
        # Update the template to include search engine info
        updated_template = template + f"\nSearch performed using: {{search_engine}}\n"
        updated_prompt = PromptTemplate(
            input_variables=["context", "question", "current_date", "current_time", "search_engine"],
            template=updated_template
        )
        
        # Create a temporary chain with the updated prompt
        temp_chain = (
            RunnableLambda(lambda q: process_with_date(q, search_engine))
            | updated_prompt
            | model
            | StrOutputParser()
        )
        
        return temp_chain.invoke(question)
    except Exception as e:
        return f"An error occurred while processing your question: {str(e)}"

def main():
    print("🔍 Web Search RAG Assistant 🔍")
    print("Ask a question to search the web and get a detailed answer with sources")
    print("Available search engines: tavily, searxng, both")
    print("Type 'exit' to quit\n")
    
    # Default search engine
    current_engine = DEFAULT_SEARCH_ENGINE
    print(f"Using search engine: {current_engine}")
    
    while True:
        command = input("\nCommand or question (type 'engine:XXX' to change engine): ")
        
        # Check for exit command
        if command.lower() == 'exit':
            break
            
        # Check for engine change command
        if command.lower().startswith("engine:"):
            new_engine = command.lower().split(":", 1)[1].strip()
            if new_engine in SEARCH_ENGINES:
                current_engine = new_engine
                print(f"Search engine changed to: {current_engine}")
            else:
                print(f"Invalid engine. Available options: {', '.join(SEARCH_ENGINES.keys())}")
            continue
        
        # Process question
        print(f"\nSearching with {current_engine} and generating answer...\n")
        answer = answer_question(command, search_engine=current_engine)
        print("\nAnswer:")
        print(answer)
        print("\n" + "-"*50)

if __name__ == "__main__":
    main()