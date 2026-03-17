"""
Phase 2: Document Processing Runner
Processes and chunks scraped data from Phase 1
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'processors'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from processors.text_processor import TextProcessor


def main():
    """Run Phase 2 document processing"""
    print("=" * 70)
    print("PHASE 2: DOCUMENT PROCESSING - GROWW RAG CHATBOT")
    print("=" * 70)
    
    processor = TextProcessor()
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'shared', 'data')
    
    # Check if Phase 1 data exists
    groww_path = os.path.join(base_dir, 'raw', 'groww_data.json')
    axismf_path = os.path.join(base_dir, 'raw', 'axismf_data.json')
    
    if not os.path.exists(groww_path):
        print(f"\n⚠️  Warning: Groww data not found at {groww_path}")
        print("Please run Phase 1 first: cd phase1 && python run_phase1.py")
        return
    
    if not os.path.exists(axismf_path):
        print(f"\n⚠️  Warning: AxisMF data not found at {axismf_path}")
        print("Please run Phase 1 first: cd phase1 && python run_phase1.py")
        return
    
    # Process Groww data
    print("\n[1/3] Processing Groww.in data...")
    print("-" * 70)
    groww_chunks = processor.process_groww_data(groww_path)
    
    # Process AxisMF data
    print("\n[2/3] Processing AxisMF.com data...")
    print("-" * 70)
    axismf_chunks = processor.process_axismf_data(axismf_path)
    
    # Combine and save
    print("\n[3/3] Saving processed chunks...")
    print("-" * 70)
    all_chunks = groww_chunks + axismf_chunks
    output_path = processor.save_chunks(
        all_chunks, 
        os.path.join(base_dir, 'processed', 'chunks.json')
    )
    
    # Display statistics
    print("\n" + "=" * 70)
    print("PROCESSING STATISTICS")
    print("=" * 70)
    
    stats = processor.get_chunking_stats(all_chunks)
    
    print(f"\n📊 Total Chunks: {stats['total_chunks']}")
    
    print("\n📁 By Fund:")
    for fund, count in sorted(stats['by_fund'].items()):
        print(f"   • {fund}: {count} chunks")
    
    print("\n📋 By Data Type:")
    for data_type, count in sorted(stats['by_data_type'].items()):
        print(f"   • {data_type}: {count} chunks")
    
    print("\n🌐 By Source Domain:")
    for domain, count in sorted(stats['by_domain'].items()):
        print(f"   • {domain}: {count} chunks")
    
    # Show sample chunks with source URLs
    print("\n" + "=" * 70)
    print("SAMPLE CHUNKS (with Source URLs)")
    print("=" * 70)
    
    for i, chunk in enumerate(all_chunks[:5]):
        print(f"\n{i+1}. {chunk.fund_name} - {chunk.data_type}")
        print(f"   Content: {chunk.content[:80]}...")
        print(f"   Source: {chunk.source_url}")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 2 COMPLETE!")
    print(f"   Total chunks created: {len(all_chunks)}")
    print(f"   Output: {output_path}")
    print("=" * 70)
    
    print("\n📝 Next Steps:")
    print("   1. Run Phase 3: cd phase3 && python embeddings/vector_store.py")
    print("   2. Or run full pipeline: cd phase7 && python scheduler/refresh_scheduler.py")


if __name__ == "__main__":
    main()
