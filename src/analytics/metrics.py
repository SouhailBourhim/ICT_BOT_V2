"""Collecte de métriques de performance"""
from typing import Dict, Any, List
import time


class MetricsCollector:
    """Collecte de métriques"""
    
    def __init__(self):
        self.metrics = []
    
    def record_latency(self, operation: str, duration: float):
        """Enregistre la latence d'une opération"""
        self.metrics.append({
            "type": "latency",
            "operation": operation,
            "duration": duration
        })
    
    def record_retrieval_quality(self, query: str, num_results: int, avg_score: float):
        """Enregistre la qualité de la récupération"""
        self.metrics.append({
            "type": "retrieval_quality",
            "query": query,
            "num_results": num_results,
            "avg_score": avg_score
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Résumé des métriques"""
        latencies = [m["duration"] for m in self.metrics if m["type"] == "latency"]
        
        return {
            "total_operations": len(self.metrics),
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0
        }
