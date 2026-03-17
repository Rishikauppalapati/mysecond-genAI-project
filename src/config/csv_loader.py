"""
CSV Source Loader Module
Loads and manages URLs from the sources.csv file
"""

import csv
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FundSource:
    """Represents a single data source for a fund"""
    fund_name: str
    data_type: str
    url: str


class CSVSourceManager:
    """Manages loading and retrieval of URLs from sources.csv"""
    
    def __init__(self, csv_path: str = None):
        if csv_path is None:
            # Default to the config directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, "sources.csv")
        
        self.csv_path = csv_path
        self.sources: List[FundSource] = []
        self._load_sources()
    
    def _load_sources(self) -> None:
        """Load all sources from CSV file"""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = FundSource(
                    fund_name=row['fund_name'].strip(),
                    data_type=row['data_type'].strip(),
                    url=row['url'].strip()
                )
                self.sources.append(source)
    
    def get_all_funds(self) -> List[str]:
        """Get list of all unique fund names"""
        return list(set(source.fund_name for source in self.sources))
    
    def get_data_types(self) -> List[str]:
        """Get list of all unique data types"""
        return list(set(source.data_type for source in self.sources))
    
    def get_url(self, fund_name: str, data_type: str) -> Optional[str]:
        """Get URL for a specific fund and data type"""
        for source in self.sources:
            if source.fund_name == fund_name and source.data_type == data_type:
                return source.url
        return None
    
    def get_fund_sources(self, fund_name: str) -> Dict[str, str]:
        """Get all URLs for a specific fund"""
        return {
            source.data_type: source.url
            for source in self.sources
            if source.fund_name == fund_name
        }
    
    def get_sources_by_domain(self, domain: str) -> List[FundSource]:
        """Get all sources for a specific domain (e.g., 'groww.in', 'axismf.com')"""
        return [source for source in self.sources if domain in source.url]
    
    def get_groww_sources(self) -> List[FundSource]:
        """Get all sources from Groww.in"""
        return self.get_sources_by_domain('groww.in')
    
    def get_axismf_sources(self) -> List[FundSource]:
        """Get all sources from AxisMF.com"""
        return self.get_sources_by_domain('axismf.com')
    
    def get_fund_url_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get complete mapping of all funds and their data sources"""
        mapping = {}
        for fund in self.get_all_funds():
            mapping[fund] = self.get_fund_sources(fund)
        return mapping


# Singleton instance for global use
_source_manager = None


def get_source_manager(csv_path: str = None) -> CSVSourceManager:
    """Get or create singleton instance of CSVSourceManager"""
    global _source_manager
    if _source_manager is None:
        _source_manager = CSVSourceManager(csv_path)
    return _source_manager


if __name__ == "__main__":
    # Test the loader
    manager = CSVSourceManager()
    
    print("=== All Funds ===")
    print(manager.get_all_funds())
    
    print("\n=== All Data Types ===")
    print(manager.get_data_types())
    
    print("\n=== Axis Large Cap Fund Sources ===")
    print(manager.get_fund_sources("Axis Large Cap Fund"))
    
    print("\n=== URL for Axis Large Cap Fund NAV ===")
    print(manager.get_url("Axis Large Cap Fund", "NAV"))
    
    print("\n=== Groww.in Sources ===")
    for source in manager.get_groww_sources():
        print(f"{source.fund_name} - {source.data_type}: {source.url}")
    
    print("\n=== AxisMF.com Sources ===")
    for source in manager.get_axismf_sources():
        print(f"{source.fund_name} - {source.data_type}: {source.url}")
