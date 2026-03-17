"""
Phase 4: RAG Retrieval & Generation
Retrieves relevant context and generates answers using Groq LLM
"""

import json
import os
import sys
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase3'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase3', 'embeddings'))

from embeddings.vector_store import VectorStore, GroqRAGPipeline
from config.csv_loader import CSVSourceManager


class RAGRetriever:
    """
    RAG Retriever - Main interface for question answering.
    Combines vector store search with Groq LLM for responses.
    """
    
    def __init__(self):
        self.pipeline = GroqRAGPipeline()
        self.csv_manager = CSVSourceManager()
        
        # Load data automatically
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'data')
        chunks_path = os.path.join(base_dir, 'processed', 'chunks.json')
        
        if os.path.exists(chunks_path):
            self.pipeline.load_data(chunks_path)
    
    def get_available_funds(self) -> List[str]:
        """Get list of available funds"""
        return self.csv_manager.get_all_funds()
    
    def get_fund_info(self, fund_name: str) -> Dict[str, Any]:
        """Get information about a specific fund"""
        sources = self.csv_manager.get_fund_sources(fund_name)
        return {
            'fund_name': fund_name,
            'sources': sources,
            'data_types': list(sources.keys()) if sources else []
        }
    
    def answer(self, query: str) -> Dict[str, Any]:
        """
        Main method to answer user queries.
        Returns structured response with answer, source URL, and metadata.
        """
        result = self.pipeline.answer_query(query)
        
        # Ensure response has all required fields
        response = {
            'answer': result.get('answer', ''),
            'source_url': result.get('source_url'),
            'fund_name': result.get('fund_name'),
            'is_advice_request': result.get('is_advice_request', False),
            'is_out_of_scope': result.get('is_out_of_scope', False),
            'reason': result.get('reason'),
            'last_updated': result.get('last_updated', datetime.now().strftime("%Y-%m-%d")),
            'query': query
        }
        
        return response
    
    def get_sample_questions(self) -> List[Dict[str, str]]:
        """Get sample questions for users"""
        return [
            {
                'question': 'What is the current NAV of Axis Large Cap Fund?',
                'category': 'NAV',
                'fund': 'Axis Large Cap Fund'
            },
            {
                'question': 'What is the expense ratio of Axis ELSS Tax Saver?',
                'category': 'Expense Ratio',
                'fund': 'Axis ELSS Tax Saver'
            },
            {
                'question': 'What is the minimum SIP amount for Axis Small Cap Fund?',
                'category': 'SIP',
                'fund': 'Axis Small Cap Fund'
            },
            {
                'question': 'What is the risk level of Axis Nifty 500 Index Fund?',
                'category': 'Risk',
                'fund': 'Axis Nifty 500 Index Fund'
            }
        ]
    
    def validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate response meets all requirements:
        - Max 3 sentences
        - Source URL present for factual queries
        - Proper handling of advice/out-of-scope
        """
        # Check sentence count
        answer = response.get('answer', '')
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if len(sentences) > 3:
            # Truncate to 3 sentences
            response['answer'] = '. '.join(sentences[:3]) + '.'
            response['truncated'] = True
        
        # Ensure source URL for factual responses
        if (not response.get('is_advice_request') and 
            not response.get('is_out_of_scope') and 
            not response.get('source_url')):
            # Try to get a default source
            fund = response.get('fund_name')
            if fund:
                response['source_url'] = self.csv_manager.get_source_for_answer(fund, 'NAV')
        
        return response


def main():
    """Test RAG retriever"""
    print("=" * 70)
    print("PHASE 4: RAG RETRIEVER & GENERATION")
    print("=" * 70)
    
    retriever = RAGRetriever()
    
    print("\n📊 Available Funds:")
    for fund in retriever.get_available_funds():
        print(f"   • {fund}")
    
    print("\n💡 Sample Questions:")
    for q in retriever.get_sample_questions():
        print(f"   • {q['question']}")
    
    print("\n" + "-" * 70)
    print("Testing Queries:")
    print("-" * 70)
    
    test_queries = [
        "What is the NAV of Axis Large Cap Fund?",
        "What is the expense ratio of Axis ELSS Tax Saver?",
        "Should I invest in Axis Small Cap Fund?",
        "What is my account balance?",
        "Tell me about the weather"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = retriever.answer(query)
        result = retriever.validate_response(result)
        
        print(f"💬 Answer: {result['answer']}")
        print(f"🔗 Source: {result.get('source_url', 'N/A')}")
        
        if result.get('is_advice_request'):
            print("⚠️  Type: Investment Advice (Rejected)")
        elif result.get('is_out_of_scope'):
            print(f"⚠️  Type: Out of Scope ({result.get('reason')})")
        else:
            print(f"✅ Type: Factual Response")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 4 COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
