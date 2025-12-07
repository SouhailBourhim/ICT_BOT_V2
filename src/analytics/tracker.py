"""Tracking des interactions utilisateur"""
from typing import Dict, Any
from datetime import datetime
import json


class InteractionTracker:
    """Tracking des interactions"""
    
    def __init__(self, log_file: str = "interactions.jsonl"):
        self.log_file = log_file
    
    def track(self, event_type: str, data: Dict[str, Any]):
        """Enregistre une interaction"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    def track_query(self, query: str, response: str, retrieved_docs: int):
        """Track une requête"""
        self.track("query", {
            "query": query,
            "response_length": len(response),
            "retrieved_docs": retrieved_docs
        })
    
    def track_document_upload(self, filename: str, size: int):
        """Track un upload de document"""
        self.track("document_upload", {
            "filename": filename,
            "size": size
        })
