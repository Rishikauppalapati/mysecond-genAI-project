"""
Phase 4: Backend API
FastAPI-based backend for the RAG Chatbot
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rag'))

from rag.retriever import RAGRetriever

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("Warning: FastAPI not installed. Install with: pip install fastapi uvicorn")


# Pydantic models for API
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    source_url: Optional[str] = None
    fund_name: Optional[str] = None
    is_advice_request: bool = False
    is_out_of_scope: bool = False
    last_updated: str


class FundInfo(BaseModel):
    fund_name: str
    data_types: List[str]


class SampleQuestion(BaseModel):
    question: str
    category: str
    fund: str


# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="FundWise AI API",
        description="Professional mutual fund information assistant for Axis Mutual Funds",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None

# Initialize retriever
retriever = RAGRetriever()


if FASTAPI_AVAILABLE:
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "FundWise AI API",
            "version": "1.0.0",
            "description": "Professional mutual fund information assistant",
            "status": "active"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "funds_available": len(retriever.get_available_funds())
        }
    
    @app.get("/funds", response_model=List[FundInfo])
    async def get_funds():
        """Get list of available funds"""
        funds = []
        for fund_name in retriever.get_available_funds():
            info = retriever.get_fund_info(fund_name)
            funds.append(FundInfo(
                fund_name=fund_name,
                data_types=info.get('data_types', [])
            ))
        return funds
    
    @app.get("/sample-questions", response_model=List[SampleQuestion])
    async def get_sample_questions():
        """Get sample questions for users"""
        questions = retriever.get_sample_questions()
        return [SampleQuestion(**q) for q in questions]
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """
        Main chat endpoint.
        Process user query and return AI-generated response.
        """
        try:
            # Get answer from RAG retriever
            result = retriever.answer(request.query)
            result = retriever.validate_response(result)
            
            return ChatResponse(
                answer=result['answer'],
                source_url=result.get('source_url'),
                fund_name=result.get('fund_name'),
                is_advice_request=result.get('is_advice_request', False),
                is_out_of_scope=result.get('is_out_of_scope', False),
                last_updated=result.get('last_updated', datetime.now().strftime("%Y-%m-%d"))
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


class ChatbotBackend:
    """
    Backend handler for chatbot queries.
    Can be used directly or via FastAPI.
    """
    
    def __init__(self):
        self.retriever = RAGRetriever()
    
    def get_available_funds(self) -> List[str]:
        """Get list of available funds"""
        return self.retriever.get_available_funds()
    
    def get_sample_questions(self) -> List[Dict[str, str]]:
        """Get sample questions for users"""
        return self.retriever.get_sample_questions()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query and return response.
        Response includes: answer (max 3 sentences), source_url, last_updated
        """
        result = self.retriever.answer(query)
        result = self.retriever.validate_response(result)
        return result


def main():
    """Run backend API"""
    print("=" * 70)
    print("PHASE 4: BACKEND API")
    print("=" * 70)
    
    if not FASTAPI_AVAILABLE:
        print("\n❌ FastAPI not installed.")
        print("Install with: pip install fastapi uvicorn")
        return
    
    backend = ChatbotBackend()
    
    print("\n📊 Available Funds:")
    for fund in backend.get_available_funds():
        print(f"   • {fund}")
    
    print("\n💡 Sample Questions:")
    for q in backend.get_sample_questions():
        print(f"   • {q['question']}")
    
    print("\n" + "-" * 70)
    print("Testing Backend:")
    print("-" * 70)
    
    test_queries = [
        "What is the NAV of Axis Large Cap Fund?",
        "What is the expense ratio of Axis ELSS Tax Saver?",
        "Should I invest in Axis Small Cap Fund?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        response = backend.process_query(query)
        
        print(f"💬 Answer: {response['answer']}")
        print(f"🔗 Source: {response.get('source_url', 'N/A')}")
        print(f"📅 Last Updated: {response.get('last_updated')}")
    
    print("\n" + "=" * 70)
    print("✅ BACKEND API READY!")
    print("=" * 70)
    print("\nTo start server:")
    print("   uvicorn phase4.backend.api:app --reload --port 8000")


if __name__ == "__main__":
    main()
