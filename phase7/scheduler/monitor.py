# -*- coding: utf-8 -*-
"""
Phase 7: Scheduler Monitor
Monitors scheduler status and logs refresh operations
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class SchedulerMonitor:
    """Monitor for scheduler operations"""
    
    def __init__(self):
        self.log_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'shared', 'data', 'scheduler_log.json'
        )
        self.max_log_entries = 100
    
    def _load_logs(self) -> List[Dict]:
        """Load scheduler logs"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading scheduler logs: {e}")
        return []
    
    def _save_logs(self, logs: List[Dict]):
        """Save scheduler logs"""
        try:
            # Keep only last N entries
            logs = logs[-self.max_log_entries:]
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving scheduler logs: {e}")
    
    def log_refresh_status(self, job_id: str, status: str, details: str = ""):
        """Log refresh job status"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job_id,
            'status': status,
            'details': details
        }
        
        logs = self._load_logs()
        logs.append(log_entry)
        self._save_logs(logs)
        
        logger.info(f"Scheduler job {job_id}: {status} - {details}")
    
    def notify_on_failure(self, job_id: str, error: str):
        """Log failure notification"""
        self.log_refresh_status(job_id, 'FAILED', error)
        logger.error(f"Scheduler job {job_id} failed: {error}")
    
    def get_recent_logs(self, count: int = 10) -> List[Dict]:
        """Get recent scheduler logs"""
        logs = self._load_logs()
        return logs[-count:]
    
    def get_job_statistics(self) -> Dict:
        """Get statistics for all jobs"""
        logs = self._load_logs()
        
        stats = {}
        for log in logs:
            job_id = log.get('job_id', 'unknown')
            status = log.get('status', 'unknown')
            
            if job_id not in stats:
                stats[job_id] = {'success': 0, 'failed': 0, 'total': 0}
            
            stats[job_id]['total'] += 1
            if status == 'SUCCESS':
                stats[job_id]['success'] += 1
            elif status == 'FAILED':
                stats[job_id]['failed'] += 1
        
        return stats
