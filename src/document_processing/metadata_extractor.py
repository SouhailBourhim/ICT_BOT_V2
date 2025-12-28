"""Extraction des métadonnées des documents"""
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class MetadataExtractor:
    """Extraction des métadonnées"""
    
    @staticmethod
    def extract(file_path: Path, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les métadonnées d'un document"""
        stat = file_path.stat()
        
        metadata = {
            "filename": file_path.name,
            "filepath": str(file_path),
            "format": parsed_data.get("format"),
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "processed_at": datetime.now().isoformat()
        }
        
        # Métadonnées spécifiques au format
        if parsed_data.get("format") == "pdf":
            metadata["pages"] = parsed_data.get("pages")
        
        return metadata
