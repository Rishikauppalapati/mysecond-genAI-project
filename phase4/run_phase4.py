"""
Phase 4: Backend & Frontend Runner
Runs both backend API and frontend UI
"""

import sys
import os
import argparse

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))


def run_backend():
    """Run backend API server"""
    print("=" * 70)
    print("PHASE 4: BACKEND API")
    print("=" * 70)
    
    try:
        from backend.api import main as backend_main
        backend_main()
        
        print("\n🚀 To start the API server:")
        print("   uvicorn phase4.backend.api:app --reload --port 8000")
        print("\n📚 API Documentation:")
        print("   Swagger UI: http://localhost:8000/docs")
        print("   ReDoc: http://localhost:8000/redoc")
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("Install required packages:")
        print("   pip install fastapi uvicorn")


def run_frontend():
    """Run frontend Streamlit app"""
    print("=" * 70)
    print("PHASE 4: FRONTEND UI")
    print("=" * 70)
    
    print("\n🎨 Starting FundWise AI - Professional Mutual Fund Assistant")
    print("\nTo launch the UI:")
    print("   streamlit run phase4/frontend/streamlit_app.py")
    print("\nThe app will open in your browser at http://localhost:8501")


def run_tests():
    """Run integration tests"""
    print("=" * 70)
    print("PHASE 4: INTEGRATION TESTS")
    print("=" * 70)
    
    try:
        from backend.api import ChatbotBackend
        
        backend = ChatbotBackend()
        
        print("\n📊 Available Funds:")
        for fund in backend.get_available_funds():
            print(f"   • {fund}")
        
        print("\n💡 Sample Questions:")
        for q in backend.get_sample_questions():
            print(f"   • {q['question']}")
        
        print("\n" + "-" * 70)
        print("Testing Backend Integration:")
        print("-" * 70)
        
        test_cases = [
            "What is the NAV of Axis Large Cap Fund?",
            "What is the expense ratio of Axis ELSS Tax Saver?",
            "Should I invest in Axis Small Cap Fund?",
            "What is my account balance?",
        ]
        
        for query in test_cases:
            print(f"\n📝 Query: {query}")
            response = backend.process_query(query)
            
            print(f"💬 Answer: {response['answer'][:100]}...")
            print(f"🔗 Source: {response.get('source_url', 'N/A')}")
            
            if response.get('is_advice_request'):
                print("⚠️  Type: Advice Request (Rejected)")
            elif response.get('is_out_of_scope'):
                print("⚠️  Type: Out of Scope")
            else:
                print("✅ Type: Factual Response")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Phase 4: Backend & Frontend')
    parser.add_argument(
        '--mode',
        choices=['backend', 'frontend', 'test', 'all'],
        default='all',
        help='Run mode: backend, frontend, test, or all'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PHASE 4: BACKEND & FRONTEND - FUNDWISE AI")
    print("=" * 70)
    
    if args.mode in ['backend', 'all']:
        run_backend()
        print()
    
    if args.mode in ['frontend', 'all']:
        run_frontend()
        print()
    
    if args.mode in ['test', 'all']:
        run_tests()
        print()
    
    print("=" * 70)
    print("PHASE 4 COMPLETE!")
    print("=" * 70)
    print("\n🎯 Quick Start:")
    print("   1. Backend: uvicorn phase4.backend.api:app --reload")
    print("   2. Frontend: streamlit run phase4/frontend/streamlit_app.py")
    print("   3. Tests: python phase4/run_phase4.py --mode test")


if __name__ == "__main__":
    main()
