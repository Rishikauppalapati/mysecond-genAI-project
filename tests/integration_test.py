"""
Integration Tests for Groww RAG Chatbot
Tests all phases together: Phase 1 → Phase 2 → Phase 3
"""

import sys
import os

# Add all phase paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1', 'scrapers'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase2', 'processors'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase3', 'embeddings'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config.csv_loader import CSVSourceManager
from phase1.scrapers.groww_scraper import GrowwScraper
from phase1.scrapers.axismf_scraper import AxisMFScraper
from phase2.processors.text_processor import TextProcessor
from phase3.embeddings.vector_store import GroqRAGPipeline


class IntegrationTest:
    """End-to-end integration test for all phases"""
    
    def __init__(self):
        self.csv_manager = CSVSourceManager()
        self.results = {
            'phase1': {'status': 'pending', 'chunks_created': 0},
            'phase2': {'status': 'pending', 'chunks_created': 0},
            'phase3': {'status': 'pending', 'tests_passed': 0, 'tests_failed': 0}
        }
    
    def run_phase1(self):
        """Run Phase 1: Data Ingestion"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST - PHASE 1: DATA INGESTION")
        print("=" * 70)
        
        try:
            # Scrape Groww.in
            print("\n[Phase 1] Scraping Groww.in...")
            groww_scraper = GrowwScraper(self.csv_manager, use_selenium=False)
            groww_data = groww_scraper.scrape_all_funds()
            groww_scraper.save_to_json(groww_data)
            print(f"✅ Scraped {len(groww_data)} funds from Groww.in")
            
            # Scrape AxisMF.com
            print("\n[Phase 1] Scraping AxisMF.com...")
            axismf_scraper = AxisMFScraper(self.csv_manager)
            axismf_data = axismf_scraper.scrape_all_funds()
            axismf_scraper.save_to_json(axismf_data)
            print(f"✅ Scraped {len(axismf_data)} funds from AxisMF.com")
            
            self.results['phase1'] = {
                'status': 'passed',
                'groww_funds': len(groww_data),
                'axismf_funds': len(axismf_data)
            }
            return True
            
        except Exception as e:
            print(f"❌ Phase 1 Failed: {e}")
            self.results['phase1'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def run_phase2(self):
        """Run Phase 2: Document Processing"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST - PHASE 2: DOCUMENT PROCESSING")
        print("=" * 70)
        
        try:
            processor = TextProcessor(self.csv_manager)
            base_dir = os.path.join(os.path.dirname(__file__), '..', 'shared', 'data')
            
            # Process Groww data
            print("\n[Phase 2] Processing Groww.in data...")
            groww_chunks = processor.process_groww_data(
                os.path.join(base_dir, 'raw', 'groww_data.json')
            )
            
            # Process AxisMF data
            print("\n[Phase 2] Processing AxisMF.com data...")
            axismf_chunks = processor.process_axismf_data(
                os.path.join(base_dir, 'raw', 'axismf_data.json')
            )
            
            # Save combined chunks
            all_chunks = groww_chunks + axismf_chunks
            processor.save_chunks(
                all_chunks,
                os.path.join(base_dir, 'processed', 'chunks.json')
            )
            
            print(f"✅ Created {len(all_chunks)} total chunks")
            
            self.results['phase2'] = {
                'status': 'passed',
                'chunks_created': len(all_chunks),
                'groww_chunks': len(groww_chunks),
                'axismf_chunks': len(axismf_chunks)
            }
            return True
            
        except Exception as e:
            print(f"❌ Phase 2 Failed: {e}")
            self.results['phase2'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def run_phase3(self):
        """Run Phase 3: Vector Store & Groq LLM"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST - PHASE 3: VECTOR STORE & GROQ LLM")
        print("=" * 70)
        
        try:
            # Initialize pipeline
            print("\n[Phase 3] Initializing Groq RAG Pipeline...")
            pipeline = GroqRAGPipeline()
            
            # Load data
            base_dir = os.path.join(os.path.dirname(__file__), '..', 'shared', 'data')
            chunks_path = os.path.join(base_dir, 'processed', 'chunks.json')
            
            num_chunks = pipeline.load_data(chunks_path)
            print(f"✅ Loaded {num_chunks} chunks into vector store")
            
            # Run test cases
            print("\n[Phase 3] Running test queries...")
            test_cases = self.get_test_cases()
            
            passed = 0
            failed = 0
            
            for test in test_cases:
                result = pipeline.answer_query(test['query'])
                is_valid = self.validate_test_case(test, result)
                
                if is_valid:
                    passed += 1
                    print(f"✅ PASS: {test['name']}")
                else:
                    failed += 1
                    print(f"❌ FAIL: {test['name']}")
                
                # Print details
                print(f"   Query: {test['query']}")
                print(f"   Answer: {result['answer'][:100]}...")
                print(f"   Source: {result.get('source_url', 'N/A')}")
                print()
            
            self.results['phase3'] = {
                'status': 'passed',
                'tests_passed': passed,
                'tests_failed': failed,
                'total_tests': len(test_cases)
            }
            
            return failed == 0
            
        except Exception as e:
            print(f"❌ Phase 3 Failed: {e}")
            self.results['phase3'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def get_test_cases(self):
        """Get comprehensive test cases"""
        return [
            # Factual queries - should return answer with source URL
            {
                'name': 'NAV Query - Axis Large Cap',
                'query': 'What is the NAV of Axis Large Cap Fund?',
                'expected_type': 'factual',
                'expected_fund': 'Axis Large Cap Fund',
                'should_have_source': True,
                'max_sentences': 3
            },
            {
                'name': 'Expense Ratio Query - ELSS',
                'query': 'What is the expense ratio of Axis ELSS Tax Saver?',
                'expected_type': 'factual',
                'expected_fund': 'Axis ELSS Tax Saver',
                'should_have_source': True,
                'max_sentences': 3
            },
            {
                'name': 'SIP Query - Small Cap',
                'query': 'What is the minimum SIP amount for Axis Small Cap Fund?',
                'expected_type': 'factual',
                'expected_fund': 'Axis Small Cap Fund',
                'should_have_source': True,
                'max_sentences': 3
            },
            {
                'name': 'Risk Query - Nifty 500',
                'query': 'What is the risk level of Axis Nifty 500 Index Fund?',
                'expected_type': 'factual',
                'expected_fund': 'Axis Nifty 500 Index Fund',
                'should_have_source': True,
                'max_sentences': 3
            },
            
            # Advice queries - should be rejected
            {
                'name': 'Investment Advice - Should Invest',
                'query': 'Should I invest in Axis Large Cap Fund?',
                'expected_type': 'advice_rejected',
                'should_have_source': False
            },
            {
                'name': 'Investment Advice - Buy or Sell',
                'query': 'Is it a good time to buy Axis ELSS Tax Saver?',
                'expected_type': 'advice_rejected',
                'should_have_source': False
            },
            
            # Personal information queries - should be rejected
            {
                'name': 'Personal Info - Account Balance',
                'query': 'What is my account balance?',
                'expected_type': 'personal_info_rejected',
                'should_have_source': False
            },
            {
                'name': 'Personal Info - My Portfolio',
                'query': 'Show me my portfolio holdings',
                'expected_type': 'personal_info_rejected',
                'should_have_source': False
            },
            
            # Out of scope queries - should be rejected
            {
                'name': 'Out of Scope - Weather',
                'query': 'What is the weather today?',
                'expected_type': 'out_of_scope',
                'should_have_source': False
            },
            {
                'name': 'Out of Scope - General Knowledge',
                'query': 'Who is the Prime Minister of India?',
                'expected_type': 'out_of_scope',
                'should_have_source': False
            }
        ]
    
    def validate_test_case(self, test, result):
        """Validate a test case result"""
        expected_type = test.get('expected_type')
        
        if expected_type == 'factual':
            # Should NOT be rejected
            if result.get('is_advice_request') or result.get('is_out_of_scope'):
                return False
            
            # Should have correct fund
            if test.get('expected_fund') and result.get('fund_name') != test['expected_fund']:
                return False
            
            # Should have source URL
            if test.get('should_have_source') and not result.get('source_url'):
                return False
            
            # Should be max 3 sentences
            if test.get('max_sentences'):
                sentences = [s for s in result['answer'].split('.') if s.strip()]
                if len(sentences) > test['max_sentences']:
                    return False
            
            return True
        
        elif expected_type == 'advice_rejected':
            return result.get('is_advice_request') == True
        
        elif expected_type == 'personal_info_rejected':
            return result.get('is_out_of_scope') == True and result.get('reason') == 'personal_information'
        
        elif expected_type == 'out_of_scope':
            return result.get('is_out_of_scope') == True
        
        return False
    
    def run_all(self):
        """Run all phases and tests"""
        print("=" * 70)
        print("GROWW RAG CHATBOT - FULL INTEGRATION TEST")
        print("=" * 70)
        
        # Run Phase 1
        p1_success = self.run_phase1()
        if not p1_success:
            print("\n❌ Integration test stopped at Phase 1")
            return False
        
        # Run Phase 2
        p2_success = self.run_phase2()
        if not p2_success:
            print("\n❌ Integration test stopped at Phase 2")
            return False
        
        # Run Phase 3
        p3_success = self.run_phase3()
        
        # Final summary
        print("\n" + "=" * 70)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        for phase, result in self.results.items():
            status = result.get('status', 'unknown')
            symbol = "✅" if status == 'passed' else "❌"
            print(f"\n{symbol} {phase.upper()}: {status.upper()}")
            
            if 'chunks_created' in result:
                print(f"   Chunks created: {result['chunks_created']}")
            if 'tests_passed' in result:
                print(f"   Tests passed: {result['tests_passed']}/{result.get('total_tests', 0)}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        overall = all(r.get('status') == 'passed' for r in self.results.values())
        
        print("\n" + "=" * 70)
        if overall:
            print("✅ ALL INTEGRATION TESTS PASSED!")
        else:
            print("❌ SOME INTEGRATION TESTS FAILED")
        print("=" * 70)
        
        return overall


def main():
    """Run integration tests"""
    test = IntegrationTest()
    success = test.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
