"""
AxisMF.com Scraper Module
Scrapes mutual fund data from AxisMF.com
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.csv_loader import CSVSourceManager


@dataclass
class AxisMFFundData:
    """Data class for storing scraped fund data from AxisMF.com"""
    fund_name: str
    fund_code: str
    source: str
    source_url: str
    csv_reference: str
    last_updated: str
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    faqs: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class AxisMFScraper:
    """Scraper for AxisMF.com mutual fund data"""
    
    def __init__(self, csv_manager: CSVSourceManager = None):
        self.csv_manager = csv_manager or CSVSourceManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_riskometer(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract riskometer/risk level from page"""
        try:
            # Look for riskometer - typically shown as an image or text
            risk_keywords = ['very high', 'high', 'moderately high', 'moderate', 'low', 'very low']
            page_text = soup.get_text().lower()
            
            # Check for riskometer image alt text or nearby text
            risk_selectors = [
                'img[alt*="risk"]',
                '[class*="riskometer"]',
                '[class*="risk"]',
                '[data-testid*="risk"]',
            ]
            
            for selector in risk_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    # Check alt text for images
                    alt_text = elem.get('alt', '').lower()
                    for risk in risk_keywords:
                        if risk in alt_text:
                            return risk.title()
                    
                    # Check element text
                    text = elem.get_text(strip=True).lower()
                    for risk in risk_keywords:
                        if risk in text:
                            return risk.title()
            
            # Search in page text for risk patterns
            for risk in risk_keywords:
                pattern = rf'\b{risk}\s+risk\b'
                if re.search(pattern, page_text, re.IGNORECASE):
                    return risk.title()
            
            return None
        except Exception as e:
            print(f"Error extracting Riskometer: {e}")
            return None
    
    def _extract_benchmark(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract benchmark index from page"""
        try:
            # Look for benchmark information
            benchmark_keywords = ['benchmark', 'index', 'nifty', 'sensex']
            page_text = soup.get_text()
            
            # Try to find benchmark section
            benchmark_selectors = [
                '[class*="benchmark"]',
                '[class*="index"]',
                '[data-testid*="benchmark"]',
            ]
            
            for selector in benchmark_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if any(kw in text.lower() for kw in benchmark_keywords):
                        # Clean up the text
                        return text.strip()
            
            # Search for benchmark in text
            lines = page_text.split('\n')
            for line in lines:
                line_lower = line.lower()
                if 'benchmark' in line_lower:
                    # Extract the benchmark name
                    import re
                    match = re.search(r'benchmark[\s:]*(.+)', line, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
            
            return None
        except Exception as e:
            print(f"Error extracting Benchmark: {e}")
            return None
    
    def _extract_faqs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract FAQs from page"""
        faqs = []
        try:
            # Look for FAQ sections - typically accordion or Q&A format
            faq_selectors = [
                '[class*="faq"]',
                '[class*="accordion"]',
                '[data-testid*="faq"]',
                '.question',
                '.faq-item',
            ]
            
            for selector in faq_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    # Try to find question and answer
                    question = None
                    answer = None
                    
                    # Look for question
                    q_selectors = ['.question', '[class*="question"]', 'h3', 'h4', 'strong']
                    for q_sel in q_selectors:
                        q_elem = elem.select_one(q_sel)
                        if q_elem:
                            text = q_elem.get_text(strip=True)
                            if '?' in text or len(text) > 10:
                                question = text
                                break
                    
                    # Look for answer
                    a_selectors = ['.answer', '[class*="answer"]', 'p', '[class*="content"]']
                    for a_sel in a_selectors:
                        a_elem = elem.select_one(a_sel)
                        if a_elem:
                            text = a_elem.get_text(strip=True)
                            if text and text != question:
                                answer = text
                                break
                    
                    if question and answer:
                        faqs.append({
                            'question': question,
                            'answer': answer
                        })
            
            # Alternative: Look for Q&A patterns in the page
            if not faqs:
                page_text = soup.get_text()
                # Find patterns like "Q: ... A: ..." or "Question: ... Answer: ..."
                qa_pattern = r'(?:Q:|Question:)\s*(.+?)\s*(?:A:|Answer:)\s*(.+?)(?=\n(?:Q:|Question:)|$)'
                matches = re.findall(qa_pattern, page_text, re.DOTALL | re.IGNORECASE)
                for q, a in matches:
                    faqs.append({
                        'question': q.strip(),
                        'answer': a.strip()
                    })
            
            return faqs
        except Exception as e:
            print(f"Error extracting FAQs: {e}")
            return faqs
    
    def scrape_fund(self, fund_name: str) -> Optional[AxisMFFundData]:
        """Scrape all data for a specific fund from AxisMF.com"""
        # Get the URL for this fund (all data types use same URL on AxisMF)
        url = self.csv_manager.get_url(fund_name, "riskometer")
        
        if not url:
            print(f"No URL found for {fund_name}")
            return None
        
        print(f"Scraping {fund_name} from {url}...")
        
        soup = self._get_soup(url)
        if not soup:
            return None
        
        # Extract fund code from URL
        fund_code = url.split('/')[-2] if '/' in url else 'unknown'
        
        # Extract all data points
        fund_data = AxisMFFundData(
            fund_name=fund_name,
            fund_code=fund_code,
            source="axismf.com",
            source_url=url,
            csv_reference=f"sources.csv:{fund_name}",
            last_updated=datetime.now().isoformat(),
            riskometer=self._extract_riskometer(soup),
            benchmark=self._extract_benchmark(soup),
            faqs=self._extract_faqs(soup)
        )
        
        return fund_data
    
    def scrape_all_funds(self) -> Dict[str, AxisMFFundData]:
        """Scrape data for all funds from AxisMF.com"""
        results = {}
        
        # Get unique fund names from AxisMF sources
        axismf_sources = self.csv_manager.get_axismf_sources()
        fund_names = list(set(source.fund_name for source in axismf_sources))
        
        for fund_name in fund_names:
            fund_data = self.scrape_fund(fund_name)
            if fund_data:
                results[fund_name] = fund_data
        
        return results
    
    def save_to_json(self, data: Dict[str, AxisMFFundData], output_path: str = None):
        """Save scraped data to JSON file"""
        if output_path is None:
            # Default to data/raw directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_path = os.path.join(current_dir, "data", "raw", "axismf_data.json")
        
        # Convert to dictionary
        output_data = {
            fund_name: fund_data.to_dict()
            for fund_name, fund_data in data.items()
        }
        
        # Add metadata
        output_data['_metadata'] = {
            'source': 'axismf.com',
            'scraped_at': datetime.now().isoformat(),
            'total_funds': len(data)
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {output_path}")
        return output_path


def main():
    """Main function to test the scraper"""
    scraper = AxisMFScraper()
    
    print("=== Starting AxisMF.com Scraper ===\n")
    
    # Scrape all funds
    results = scraper.scrape_all_funds()
    
    print("\n=== Scraping Results ===")
    for fund_name, fund_data in results.items():
        print(f"\n{fund_name}:")
        print(f"  Riskometer: {fund_data.riskometer}")
        print(f"  Benchmark: {fund_data.benchmark}")
        print(f"  FAQs Count: {len(fund_data.faqs)}")
        if fund_data.faqs:
            print(f"  First FAQ: {fund_data.faqs[0]['question'][:50]}...")
    
    # Save to JSON
    output_path = scraper.save_to_json(results)
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
