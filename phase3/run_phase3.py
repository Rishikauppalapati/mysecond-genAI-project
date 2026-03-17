"""
Phase 3: Vector Store & Groq LLM Runner
Loads processed chunks and tests RAG pipeline
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'embeddings'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from embeddings.vector_store import GroqRAGPipeline


def main():
    """Run Phase 3"""
    print("=" * 70)
    print("PHASE 3: VECTOR STORE & GROQ LLM INTEGRATION")
    print("=" * 70)
    
    # Initialize pipeline
    print("\n[1/3] Initializing Groq RAG Pipeline...")
    pipeline = GroqRAGPipeline()
    
    # Load data
    print("\n[2/3] Loading processed chunks from Phase 2...")
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'shared', 'data')
    chunks_path = os.path.join(base_dir, 'processed', 'chunks.json')
    
    if not os.path.exists(chunks_path):
        print(f"❌ Error: {chunks_path} not found.")
        print("Please run Phase 2 first: cd phase2 && python run_phase2.py")
        return
    
    try:
        num_chunks = pipeline.load_data(chunks_path)
        print(f"✅ Loaded {num_chunks} chunks into vector store")
    except Exception as e:
        print(f"❌ Error loading chunks: {e}")
        return
    
    # Test queries
    print("\n[3/3] Running test queries...")
    print("=" * 70)
    
    test_cases = [
        {
            "query": "What is the NAV of Axis Large Cap Fund?",
            "expected_fund": "Axis Large Cap Fund",
            "expected_type": "factual"
        },
        {
            "query": "What is the expense ratio of Axis ELSS Tax Saver?",
            "expected_fund": "Axis ELSS Tax Saver",
            "expected_type": "factual"
        },
        {
            "query": "What is the minimum SIP amount for Axis Small Cap Fund?",
            "expected_fund": "Axis Small Cap Fund",
            "expected_type": "factual"
        },
        {
            "query": "Should I invest in Axis Nifty 500 Index Fund?",
            "expected_type": "advice_rejected"
        },
        {
            "query": "What is my account balance?",
            "expected_type": "personal_info_rejected"
        },
        {
            "query": "Tell me about the weather today",
            "expected_type": "out_of_scope"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        print(f"\nTest {i}: {query}")
        print("-" * 70)
        
        result = pipeline.answer_query(query)
        
        print(f"💬 Answer: {result['answer']}")
        print(f"🔗 Source URL: {result.get('source_url', 'N/A')}")
        print(f"📅 Last Updated: {result.get('last_updated')}")
        
        # Validate response
        is_valid = True
        
        if test.get('expected_type') == 'factual':
            if result.get('is_advice_request') or result.get('is_out_of_scope'):
                print("❌ FAIL: Expected factual response but got rejection")
                is_valid = False
            elif test.get('expected_fund') and result.get('fund_name') != test['expected_fund']:
                print(f"❌ FAIL: Expected fund {test['expected_fund']} but got {result.get('fund_name')}")
                is_valid = False
            elif not result.get('source_url'):
                print("❌ FAIL: Missing source URL")
                is_valid = False
            else:
                print("✅ PASS: Valid factual response with source")
        
        elif test.get('expected_type') == 'advice_rejected':
            if not result.get('is_advice_request'):
                print("❌ FAIL: Expected advice rejection")
                is_valid = False
            else:
                print("✅ PASS: Correctly rejected advice request")
        
        elif test.get('expected_type') == 'personal_info_rejected':
            if not result.get('is_out_of_scope') or result.get('reason') != 'personal_information':
                print("❌ FAIL: Expected personal info rejection")
                is_valid = False
            else:
                print("✅ PASS: Correctly rejected personal info request")
        
        elif test.get('expected_type') == 'out_of_scope':
            if not result.get('is_out_of_scope'):
                print("❌ FAIL: Expected out of scope rejection")
                is_valid = False
            else:
                print("✅ PASS: Correctly rejected out of scope query")
        
        if is_valid:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 3 COMPLETE!")
    print("=" * 70)
    
    print("\n📝 Next Steps:")
    print("   1. Run Phase 4: cd phase4 && python rag/retriever.py")
    print("   2. Run full integration: cd phase7 && python scheduler/refresh_scheduler.py")


if __name__ == "__main__":
    main()
