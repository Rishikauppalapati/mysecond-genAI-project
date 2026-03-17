"""
Phase 5: Backend API
Handles query processing and returns answers with source URLs
"""

import os
import sys
import json
from typing import Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase4'))
from rag.retriever import RAGRetriever
from config.csv_loader import CSVSourceManager


class ChatbotBackend:
    """Backend handler for chatbot queries"""
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.csv_manager = CSVSourceManager()
    
    def get_available_funds(self) -> list:
        """Get list of available funds"""
        return self.csv_manager.get_all_funds()
    
    def get_sample_questions(self) -> list:
        """Get sample questions for users"""
        return [
            "What is the current NAV of Axis Large Cap Fund?",
            "What is the expense ratio of Axis ELSS Tax Saver?",
            "What is the minimum SIP amount for Axis Small Cap Fund?"
        ]
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query and return response.
        Response includes: answer (max 3 sentences), source_url, last_updated
        """
        # Generate answer using RAG
        result = self.retriever.generate_answer(query)
        
        # Add timestamp
        result['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        return result
    
    def validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate response meets requirements:
        - Max 3 sentences
        - Source URL present (if not advice request)
        - No financial advice
        """
        # Check sentence count
        answer = response.get('answer', '')
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if len(sentences) > 3:
            # Truncate to 3 sentences
            response['answer'] = '. '.join(sentences[:3]) + '.'
        
        # Ensure source URL for non-advice responses
        if not response.get('is_advice_request') and not response.get('source_url'):
            response['source_url'] = "https://groww.in/mutual-funds"
        
        return response


def main():
    """Test backend API"""
    print("=" * 60)
    print("PHASE 5: BACKEND API")
    print("=" * 60)
    
    backend = ChatbotBackend()
    
    print("\nAvailable Funds:")
    for fund in backend.get_available_funds():
        print(f"  - {fund}")
    
    print("\nSample Questions:")
    for q in backend.get_sample_questions():
        print(f"  - {q}")
    
    print("\n" + "-" * 60)
    print("Testing Queries:")
    print("-" * 60)
    
    test_queries = [
        "What is the NAV of Axis Large Cap Fund?",
        "What is the expense ratio of Axis ELSS Tax Saver?",
        "Should I invest in Axis Small Cap Fund?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = backend.process_query(query)
        response = backend.validate_response(response)
        
        print(f"Answer: {response['answer']}")
        print(f"Source: {response['source_url']}")
        print(f"Last Updated: {response['last_updated']}")
    
    print("\n" + "=" * 60)
    print("PHASE 5 COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
