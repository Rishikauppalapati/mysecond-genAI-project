"""
Phase 3: Vector Store, Embeddings & Groq LLM Integration
Generates embeddings and uses Groq LLM for responses
"""

import json
import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Groq
try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: groq package not installed. Install with: pip install groq")


@dataclass
class SearchResult:
    """Represents a search result from vector store"""
    chunk: Dict[str, Any]
    score: float


class VectorStore:
    """Vector store with keyword-based search (placeholder for embedding-based search)"""
    
    def __init__(self):
        self.chunks = []
        self.embeddings_available = False
    
    def load_chunks(self, chunks_path: str):
        """Load processed chunks from Phase 2"""
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.chunks = data.get('chunks', [])
        
        print(f"✅ Loaded {len(self.chunks)} chunks into vector store")
        return len(self.chunks)
    
    def search(self, query: str, fund_name: str = None, top_k: int = 3) -> List[SearchResult]:
        """
        Search for relevant chunks using keyword matching.
        In production, this would use embedding similarity search.
        """
        results = []
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        for chunk in self.chunks:
            # Filter by fund if specified
            if fund_name and chunk.get('fund_name') != fund_name:
                continue
            
            content_lower = chunk.get('content', '').lower()
            score = 0
            
            # Keyword matching
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            # Boost for exact fund name match
            if chunk.get('fund_name', '').lower() in query_lower:
                score += 3
            
            # Boost for data type match
            data_type = chunk.get('data_type', '').lower()
            if data_type in query_lower:
                score += 2
            elif data_type == 'nav' and ('nav' in query_lower or 'price' in query_lower):
                score += 2
            elif data_type == 'expense_ratio' and 'expense' in query_lower:
                score += 2
            elif data_type == 'min_sip' and 'sip' in query_lower:
                score += 2
            elif data_type == 'riskometer' and 'risk' in query_lower:
                score += 2
            
            if score > 0:
                results.append(SearchResult(chunk=chunk, score=score))
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Get a specific chunk by ID"""
        for chunk in self.chunks:
            if chunk.get('chunk_id') == chunk_id:
                return chunk
        return None


class GroqRAGPipeline:
    """RAG Pipeline using Groq LLM"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.client = None
        self.model = "llama-3.3-70b-versatile"
        
        # Initialize Groq client
        if GROQ_AVAILABLE:
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                self.client = groq.Groq(api_key=api_key)
                print("✅ Groq client initialized")
            else:
                print("⚠️  Warning: GROQ_API_KEY not found in environment")
        else:
            print("⚠️  Warning: groq package not available")
    
    def load_data(self, chunks_path: str):
        """Load processed chunks"""
        return self.vector_store.load_chunks(chunks_path)
    
    def detect_fund(self, query: str) -> Optional[str]:
        """Detect which fund the query is about"""
        funds = [
            "Axis Large Cap Fund",
            "Axis Small Cap Fund",
            "Axis Nifty 500 Index Fund",
            "Axis ELSS Tax Saver"
        ]
        
        query_lower = query.lower()
        
        for fund in funds:
            if fund.lower() in query_lower:
                return fund
        
        # Check for partial matches
        if 'large cap' in query_lower:
            return "Axis Large Cap Fund"
        elif 'small cap' in query_lower:
            return "Axis Small Cap Fund"
        elif 'nifty 500' in query_lower or 'nifty500' in query_lower:
            return "Axis Nifty 500 Index Fund"
        elif 'elss' in query_lower or 'tax saver' in query_lower:
            return "Axis ELSS Tax Saver"
        
        return None
    
    def is_advice_request(self, query: str) -> bool:
        """Detect if user is asking for investment advice"""
        advice_keywords = [
            'should i', 'should we', 'recommend', 'suggestion',
            'buy or sell', 'good investment', 'bad investment',
            'invest in', 'put money', 'worth buying', 'worth investing',
            'advice', 'advise', 'better option', 'which is better'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in advice_keywords)
    
    def is_personal_info_request(self, query: str) -> bool:
        """Detect if user is asking for personal information (out of scope)"""
        personal_keywords = [
            'my account', 'my investment', 'my portfolio', 'my details',
            'personal information', 'my name', 'my email', 'my phone',
            'my address', 'my pan', 'my kyc', 'login', 'password',
            'account balance', 'my holdings', 'my units', 'my returns'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in personal_keywords)
    
    def is_out_of_scope(self, query: str) -> Tuple[bool, str]:
        """
        Check if query is out of scope.
        Returns (is_out_of_scope, reason)
        """
        if self.is_advice_request(query):
            return True, "investment_advice"
        
        if self.is_personal_info_request(query):
            return True, "personal_information"
        
        # Check if query is about mutual funds
        fund_related_keywords = [
            'nav', 'expense', 'sip', 'fund', 'axis', 'large cap', 'small cap',
            'nifty', 'elss', 'tax saver', 'risk', 'benchmark', 'exit load',
            'mutual fund', 'investment', 'return', 'growth', 'direct'
        ]
        
        query_lower = query.lower()
        is_fund_related = any(keyword in query_lower for keyword in fund_related_keywords)
        
        if not is_fund_related:
            return True, "out_of_scope"
        
        return False, ""
    
    def build_context(self, search_results: List[SearchResult]) -> str:
        """Build context string from search results"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            chunk = result.chunk
            content = chunk.get('content', '')
            fund = chunk.get('fund_name', '')
            data_type = chunk.get('data_type', '')
            
            context_parts.append(f"[{i}] {fund} - {data_type}: {content}")
        
        return "\n\n".join(context_parts)
    
    def generate_response_with_groq(self, context: str, question: str) -> Dict[str, Any]:
        """
        Generate response using Groq LLM.
        ONLY uses information from provided context (embeddings).
        """
        if not self.client:
            return {
                "answer": "Error: Groq client not initialized. Please check GROQ_API_KEY.",
                "source_url": None,
                "error": "groq_not_initialized"
            }
        
        prompt = f"""You are a factual mutual fund information assistant for Groww.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. Use ONLY the provided context below to answer - DO NOT use any external knowledge
2. If information is not in the context, say "I don't have that information in my database"
3. NEVER use your pre-trained knowledge - only use the context provided
4. Answer in MAXIMUM 3 sentences
5. Do NOT provide investment advice
6. Be factual and specific with numbers when available
7. If NAV value is mentioned, include it in the format "₹XX.XX"

Context from database (USE ONLY THIS INFORMATION):
{context}

User Question: {question}

Provide a factual answer using ONLY the context above (max 3 sentences):"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a factual assistant that ONLY uses provided context. You must NOT use external knowledge."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for factual responses
                max_tokens=200
            )
            
            return {
                "answer": response.choices[0].message.content.strip(),
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "source_url": None,
                "error": str(e)
            }
    
    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point: Process user query and return answer.
        Returns dict with: answer, source_url, fund_name, is_advice_request, etc.
        """
        # Check if out of scope
        is_out, reason = self.is_out_of_scope(query)
        
        if is_out:
            if reason == "investment_advice":
                return {
                    "answer": "I can only provide factual information about mutual funds, not investment advice. Please consult a financial advisor for personalized recommendations.",
                    "source_url": None,
                    "fund_name": None,
                    "is_advice_request": True,
                    "is_out_of_scope": True,
                    "reason": reason,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            elif reason == "personal_information":
                return {
                    "answer": "I cannot access personal account information or investment details. This chatbot provides general fund information only. Please check your Groww app for personal account details.",
                    "source_url": None,
                    "fund_name": None,
                    "is_advice_request": False,
                    "is_out_of_scope": True,
                    "reason": reason,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            else:
                return {
                    "answer": "I can only answer questions about Axis Mutual Funds (NAV, expense ratio, SIP, risk level, etc.). Please ask about fund-specific information.",
                    "source_url": None,
                    "fund_name": None,
                    "is_advice_request": False,
                    "is_out_of_scope": True,
                    "reason": reason,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
        
        # Detect fund
        fund_name = self.detect_fund(query)
        
        # Search vector store
        search_results = self.vector_store.search(query, fund_name=fund_name, top_k=3)
        
        if not search_results:
            return {
                "answer": "I don't have information about that specific query. Please ask about NAV, expense ratio, minimum SIP, risk level, or benchmark for the available funds.",
                "source_url": None,
                "fund_name": fund_name,
                "is_advice_request": False,
                "is_out_of_scope": False,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
        
        # Build context from search results
        context = self.build_context(search_results)
        
        # Get source URL from most relevant chunk
        source_url = search_results[0].chunk.get('source_url', '')
        
        # Generate response with Groq
        groq_response = self.generate_response_with_groq(context, query)
        
        # Validate response length (max 3 sentences)
        answer = groq_response.get('answer', '')
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        if len(sentences) > 3:
            answer = '. '.join(sentences[:3]) + '.'
        
        return {
            "answer": answer,
            "source_url": source_url,
            "fund_name": fund_name,
            "is_advice_request": False,
            "is_out_of_scope": False,
            "context_chunks": [r.chunk.get('chunk_id') for r in search_results],
            "model_used": groq_response.get('model'),
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }


def main():
    """Run Phase 3"""
    print("=" * 70)
    print("PHASE 3: VECTOR STORE & GROQ LLM INTEGRATION")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = GroqRAGPipeline()
    
    # Load data
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'data')
    chunks_path = os.path.join(base_dir, 'processed', 'chunks.json')
    
    print(f"\n[1/2] Loading chunks from Phase 2...")
    try:
        num_chunks = pipeline.load_data(chunks_path)
        print(f"✅ Loaded {num_chunks} chunks")
    except FileNotFoundError:
        print(f"❌ Error: {chunks_path} not found. Run Phase 2 first.")
        return
    
    # Test queries
    print(f"\n[2/2] Testing queries with Groq LLM...")
    print("-" * 70)
    
    test_queries = [
        "What is the NAV of Axis Large Cap Fund?",
        "What is the expense ratio of Axis ELSS Tax Saver?",
        "What is the minimum SIP amount for Axis Small Cap Fund?",
        "Should I invest in Axis Nifty 500 Index Fund?",
        "What is my account balance?",
        "Tell me about the weather today"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = pipeline.answer_query(query)
        
        print(f"💬 Answer: {result['answer']}")
        print(f"🔗 Source: {result.get('source_url', 'N/A')}")
        
        if result.get('is_advice_request'):
            print("⚠️  Type: Investment Advice Request (Rejected)")
        elif result.get('is_out_of_scope'):
            print(f"⚠️  Type: Out of Scope ({result.get('reason')})")
        else:
            print(f"✅ Type: Factual Query")
            if result.get('fund_name'):
                print(f"📊 Fund: {result['fund_name']}")
        
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✅ PHASE 3 COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
