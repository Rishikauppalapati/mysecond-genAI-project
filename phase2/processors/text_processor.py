"""
Phase 2: Document Processing
Cleans and chunks scraped data for vector storage
"""

import json
import os
import sys
import re
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add shared config to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from config.csv_loader import CSVSourceManager


@dataclass
class DocumentChunk:
    """Represents a processed chunk of document"""
    chunk_id: str
    fund_name: str
    data_type: str
    content: str
    source_url: str  # URL from CSV for citation
    source_domain: str
    last_updated: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class TextProcessor:
    """Processes and chunks raw scraped data"""
    
    def __init__(self, csv_manager: CSVSourceManager = None):
        self.csv_manager = csv_manager or CSVSourceManager()
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        - Remove HTML tags
        - Normalize whitespace
        - Handle special characters
        - Standardize currency formats
        - Normalize date formats
        """
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation and currency symbols
        text = re.sub(r'[^\w\s\.\,\₹\%\-\(\)\:]', ' ', text)
        
        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def normalize_currency(self, text: str) -> str:
        """Standardize currency formats"""
        # Replace Rs. with ₹
        text = re.sub(r'Rs\.?\s*', '₹', text)
        # Replace INR with ₹
        text = re.sub(r'INR\s*', '₹', text)
        return text
    
    def chunk_nav_data(self, nav_data: Dict, fund_name: str, source_url: str, last_updated: str) -> Optional[DocumentChunk]:
        """Create chunk for NAV data"""
        if not nav_data or not isinstance(nav_data, dict):
            return None
        
        current_nav = nav_data.get('current')
        nav_date = nav_data.get('date', '')
        
        if not current_nav:
            return None
        
        content = f"The current NAV of {fund_name} is ₹{current_nav}"
        if nav_date:
            content += f" as of {nav_date}"
        content += "."
        
        return DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            fund_name=fund_name,
            data_type='NAV',
            content=self.clean_text(content),
            source_url=source_url,
            source_domain='groww.in',
            last_updated=last_updated,
            metadata={
                'nav_value': current_nav,
                'nav_date': nav_date,
                'raw_data': nav_data
            }
        )
    
    def chunk_simple_field(self, value: str, fund_name: str, data_type: str, source_url: str, last_updated: str) -> Optional[DocumentChunk]:
        """Create chunk for simple text fields (MIN SIP, Expense Ratio, Exit Load)"""
        if not value:
            return None
        
        # Clean the value
        cleaned_value = self.clean_text(value)
        cleaned_value = self.normalize_currency(cleaned_value)
        
        # Create descriptive content based on data type
        if data_type == 'min_sip':
            content = f"The minimum SIP amount for {fund_name} is {cleaned_value}."
        elif data_type == 'expense_ratio':
            content = f"The expense ratio of {fund_name} is {cleaned_value}."
        elif data_type == 'exit_load':
            content = f"The exit load for {fund_name}: {cleaned_value}."
        else:
            content = f"{fund_name} {data_type}: {cleaned_value}"
        
        return DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            fund_name=fund_name,
            data_type=data_type.upper(),
            content=content,
            source_url=source_url,
            source_domain='groww.in',
            last_updated=last_updated,
            metadata={'raw_value': value}
        )
    
    def chunk_riskometer(self, risk_level: str, fund_name: str, source_url: str, last_updated: str) -> Optional[DocumentChunk]:
        """Create chunk for riskometer data"""
        if not risk_level:
            return None
        
        content = f"{fund_name} has a {self.clean_text(risk_level)} risk level."
        
        return DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            fund_name=fund_name,
            data_type='RISKOMETER',
            content=content,
            source_url=source_url,
            source_domain='axismf.com',
            last_updated=last_updated,
            metadata={'risk_level': risk_level}
        )
    
    def chunk_benchmark(self, benchmark: str, fund_name: str, source_url: str, last_updated: str) -> Optional[DocumentChunk]:
        """Create chunk for benchmark data"""
        if not benchmark:
            return None
        
        cleaned_benchmark = self.clean_text(benchmark)
        content = f"The benchmark for {fund_name} is {cleaned_benchmark}."
        
        return DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            fund_name=fund_name,
            data_type='BENCHMARK',
            content=content,
            source_url=source_url,
            source_domain='axismf.com',
            last_updated=last_updated,
            metadata={'benchmark': benchmark}
        )
    
    def chunk_faq(self, faq: Dict, fund_name: str, index: int, source_url: str, last_updated: str) -> Optional[DocumentChunk]:
        """Create chunk for FAQ data"""
        if not faq or not isinstance(faq, dict):
            return None
        
        question = faq.get('question', '')
        answer = faq.get('answer', '')
        
        if not question or not answer:
            return None
        
        cleaned_question = self.clean_text(question)
        cleaned_answer = self.clean_text(answer)
        
        content = f"Q: {cleaned_question} A: {cleaned_answer}"
        
        return DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            fund_name=fund_name,
            data_type='FAQ',
            content=content,
            source_url=source_url,
            source_domain='axismf.com',
            last_updated=last_updated,
            metadata={
                'faq_index': index,
                'question': cleaned_question,
                'answer': cleaned_answer
            }
        )
    
    def process_groww_data(self, raw_data_path: str) -> List[DocumentChunk]:
        """
        Process Groww.in scraped data into chunks.
        Data types: NAV, MIN SIP, Expense Ratio, Exit Load
        """
        chunks = []
        
        print(f"Processing Groww data from: {raw_data_path}")
        
        if not os.path.exists(raw_data_path):
            print(f"Warning: File not found: {raw_data_path}")
            return chunks
        
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for fund_name, fund_data in data.items():
            if fund_name.startswith('_'):
                continue
            
            print(f"  Processing {fund_name}...")
            
            last_updated = fund_data.get('last_updated', datetime.now().isoformat())
            
            # Process NAV
            nav_data = fund_data.get('nav')
            if nav_data:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'NAV')
                chunk = self.chunk_nav_data(nav_data, fund_name, source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
            
            # Process MIN SIP
            min_sip = fund_data.get('min_sip')
            if min_sip:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'MIN SIP')
                chunk = self.chunk_simple_field(min_sip, fund_name, 'min_sip', source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
            
            # Process Expense Ratio
            expense_ratio = fund_data.get('expense_ratio')
            if expense_ratio:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'expense_ratio')
                chunk = self.chunk_simple_field(expense_ratio, fund_name, 'expense_ratio', source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
            
            # Process Exit Load
            exit_load = fund_data.get('exit_load')
            if exit_load:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'exit_load')
                chunk = self.chunk_simple_field(exit_load, fund_name, 'exit_load', source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
        
        print(f"Created {len(chunks)} chunks from Groww data")
        return chunks
    
    def process_axismf_data(self, raw_data_path: str) -> List[DocumentChunk]:
        """
        Process AxisMF.com scraped data into chunks.
        Data types: Riskometer, Benchmark, FAQs
        """
        chunks = []
        
        print(f"Processing AxisMF data from: {raw_data_path}")
        
        if not os.path.exists(raw_data_path):
            print(f"Warning: File not found: {raw_data_path}")
            return chunks
        
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for fund_name, fund_data in data.items():
            if fund_name.startswith('_'):
                continue
            
            print(f"  Processing {fund_name}...")
            
            last_updated = fund_data.get('last_updated', datetime.now().isoformat())
            
            # Process Riskometer
            riskometer = fund_data.get('riskometer')
            if riskometer:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'riskometer')
                chunk = self.chunk_riskometer(riskometer, fund_name, source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
            
            # Process Benchmark
            benchmark = fund_data.get('benchmark')
            if benchmark:
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'benchmark')
                chunk = self.chunk_benchmark(benchmark, fund_name, source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
            
            # Process FAQs
            faqs = fund_data.get('faqs', [])
            for i, faq in enumerate(faqs):
                source_url = self.csv_manager.get_source_for_answer(fund_name, 'FAQs')
                chunk = self.chunk_faq(faq, fund_name, i, source_url, last_updated)
                if chunk:
                    chunks.append(chunk)
        
        print(f"Created {len(chunks)} chunks from AxisMF data")
        return chunks
    
    def save_chunks(self, chunks: List[DocumentChunk], output_path: str):
        """Save processed chunks to JSON"""
        output_data = {
            'chunks': [
                {
                    'chunk_id': chunk.chunk_id,
                    'fund_name': chunk.fund_name,
                    'data_type': chunk.data_type,
                    'content': chunk.content,
                    'source_url': chunk.source_url,  # This is the URL returned in chatbot answers
                    'source_domain': chunk.source_domain,
                    'last_updated': chunk.last_updated,
                    'metadata': chunk.metadata
                }
                for chunk in chunks
            ],
            '_metadata': {
                'processed_at': datetime.now().isoformat(),
                'total_chunks': len(chunks),
                'funds': list(set(chunk.fund_name for chunk in chunks)),
                'data_types': list(set(chunk.data_type for chunk in chunks))
            }
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Processed chunks saved to {output_path}")
        return output_path
    
    def get_chunking_stats(self, chunks: List[DocumentChunk]) -> Dict:
        """Get statistics about processed chunks"""
        stats = {
            'total_chunks': len(chunks),
            'by_fund': {},
            'by_data_type': {},
            'by_domain': {}
        }
        
        for chunk in chunks:
            # By fund
            stats['by_fund'][chunk.fund_name] = stats['by_fund'].get(chunk.fund_name, 0) + 1
            
            # By data type
            stats['by_data_type'][chunk.data_type] = stats['by_data_type'].get(chunk.data_type, 0) + 1
            
            # By domain
            stats['by_domain'][chunk.source_domain] = stats['by_domain'].get(chunk.source_domain, 0) + 1
        
        return stats


def main():
    """Run Phase 2 processing"""
    print("=" * 70)
    print("PHASE 2: DOCUMENT PROCESSING")
    print("=" * 70)
    
    processor = TextProcessor()
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'data')
    
    # Process Groww data
    print("\n[1/3] Processing Groww.in data...")
    groww_chunks = processor.process_groww_data(
        os.path.join(base_dir, 'raw', 'groww_data.json')
    )
    
    # Process AxisMF data
    print("\n[2/3] Processing AxisMF.com data...")
    axismf_chunks = processor.process_axismf_data(
        os.path.join(base_dir, 'raw', 'axismf_data.json')
    )
    
    # Combine and save
    print("\n[3/3] Saving processed chunks...")
    all_chunks = groww_chunks + axismf_chunks
    output_path = processor.save_chunks(
        all_chunks, 
        os.path.join(base_dir, 'processed', 'chunks.json')
    )
    
    # Display statistics
    print("\n" + "-" * 70)
    print("PROCESSING STATISTICS")
    print("-" * 70)
    
    stats = processor.get_chunking_stats(all_chunks)
    
    print(f"\nTotal Chunks: {stats['total_chunks']}")
    
    print("\nBy Fund:")
    for fund, count in sorted(stats['by_fund'].items()):
        print(f"  {fund}: {count} chunks")
    
    print("\nBy Data Type:")
    for data_type, count in sorted(stats['by_data_type'].items()):
        print(f"  {data_type}: {count} chunks")
    
    print("\nBy Domain:")
    for domain, count in sorted(stats['by_domain'].items()):
        print(f"  {domain}: {count} chunks")
    
    # Show sample chunks
    print("\n" + "-" * 70)
    print("SAMPLE CHUNKS")
    print("-" * 70)
    
    for i, chunk in enumerate(all_chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"  Fund: {chunk.fund_name}")
        print(f"  Type: {chunk.data_type}")
        print(f"  Content: {chunk.content[:100]}...")
        print(f"  Source URL: {chunk.source_url}")
    
    print("\n" + "=" * 70)
    print(f"PHASE 2 COMPLETE! Total chunks: {len(all_chunks)}")
    print(f"Output: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
