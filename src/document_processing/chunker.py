"""
Découpage sémantique de documents avec support du français
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from loguru import logger


@dataclass
class Chunk:
    """Structure pour un chunk de texte"""
    text: str
    metadata: Dict
    chunk_id: str
    start_char: int
    end_char: int
    token_count: int


class SemanticChunker:
    """
    Chunker sémantique qui découpe le texte de manière intelligente
    en respectant la structure du document (paragraphes, sections, etc.)
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        respect_sentence_boundaries: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sentence_boundaries = respect_sentence_boundaries
        
        # Patterns pour détecter les frontières sémantiques (français)
        self.section_patterns = [
            r'\n#{1,6}\s+.+\n',  # Markdown headers
            r'\n[A-Z][^.!?]*:',  # Titres suivis de ":"
            r'\n\d+\.\s+[A-Z]',  # Listes numérotées comme titres
            r'\n[IVX]+\.\s+',    # Numérotation romaine
        ]
        
        # Pattern pour détecter les fins de phrases (français)
        self.sentence_end_pattern = r'[.!?]\s+'
    
    def chunk_text(
        self, 
        text: str, 
        doc_metadata: Dict,
        preserve_structure: bool = True
    ) -> List[Chunk]:
        """
        Découpe un texte en chunks sémantiques
        
        Args:
            text: Texte à découper
            doc_metadata: Métadonnées du document source
            preserve_structure: Si True, respecte la structure du document
            
        Returns:
            Liste de chunks
        """
        if not text or len(text) < self.min_chunk_size:
            logger.warning("Texte trop court pour être chunké")
            return []
        
        if preserve_structure:
            # Découpage basé sur la structure
            chunks = self._chunk_by_structure(text, doc_metadata)
        else:
            # Découpage simple avec overlap
            chunks = self._chunk_with_overlap(text, doc_metadata)
        
        # Enrichissement des métadonnées
        chunks = self._enrich_chunks(chunks, text, doc_metadata)
        
        logger.info(f"✅ Créé {len(chunks)} chunks (moyenne: {sum(c.token_count for c in chunks) / len(chunks):.0f} tokens)")
        
        return chunks
    
    def _chunk_by_structure(self, text: str, doc_metadata: Dict) -> List[Chunk]:
        """Découpe en respectant la structure sémantique"""
        chunks = []
        
        # Détection des sections principales
        sections = self._detect_sections(text)
        
        if not sections:
            # Pas de structure détectée, découpage classique
            return self._chunk_with_overlap(text, doc_metadata)
        
        for section_idx, section in enumerate(sections):
            section_text = section['text']
            
            # Si la section est trop grande, la découper
            if len(section_text) > self.chunk_size:
                sub_chunks = self._chunk_with_overlap(
                    section_text,
                    {**doc_metadata, 'section': section['title']}
                )
                chunks.extend(sub_chunks)
            else:
                # Créer un chunk pour la section entière
                chunk = Chunk(
                    text=section_text,
                    metadata={
                        **doc_metadata,
                        'section': section['title'],
                        'section_index': section_idx
                    },
                    chunk_id=f"{doc_metadata.get('filename', 'doc')}_{section_idx}",
                    start_char=section['start'],
                    end_char=section['end'],
                    token_count=self._estimate_tokens(section_text)
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_with_overlap(self, text: str, metadata: Dict) -> List[Chunk]:
        """Découpage avec overlap en respectant les phrases"""
        chunks = []
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            # Déterminer la fin du chunk
            end = start + self.chunk_size
            
            # Ajuster pour respecter les frontières de phrases
            if self.respect_sentence_boundaries and end < len(text):
                end = self._find_sentence_boundary(text, end)
            
            # Extraire le chunk
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunk = Chunk(
                    text=chunk_text,
                    metadata=metadata.copy(),
                    chunk_id=f"{metadata.get('filename', 'doc')}_chunk_{chunk_idx}",
                    start_char=start,
                    end_char=end,
                    token_count=self._estimate_tokens(chunk_text)
                )
                chunks.append(chunk)
                chunk_idx += 1
            
            # Avancer avec overlap
            start = end - self.chunk_overlap
            
            # Éviter les boucles infinies
            if start >= len(text):
                break
        
        return chunks
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """Détecte les sections du document"""
        sections = []
        
        # Chercher tous les patterns de section
        matches = []
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.group().strip()))
        
        # Trier par position
        matches.sort(key=lambda x: x[0])
        
        if not matches:
            return []
        
        # Créer les sections
        for i, (start, title) in enumerate(matches):
            # Déterminer la fin de la section
            if i < len(matches) - 1:
                end = matches[i + 1][0]
            else:
                end = len(text)
            
            section_text = text[start:end].strip()
            
            sections.append({
                'title': title,
                'text': section_text,
                'start': start,
                'end': end
            })
        
        return sections
    
    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Trouve la frontière de phrase la plus proche"""
        # Chercher la prochaine fin de phrase après la position
        search_text = text[position:position + 200]  # Chercher dans les 200 prochains caractères
        
        match = re.search(self.sentence_end_pattern, search_text)
        
        if match:
            return position + match.end()
        
        # Si pas trouvé, chercher en arrière
        search_text = text[max(0, position - 200):position]
        matches = list(re.finditer(self.sentence_end_pattern, search_text))
        
        if matches:
            last_match = matches[-1]
            return max(0, position - 200) + last_match.end()
        
        # Par défaut, retourner la position originale
        return position
    
    def _enrich_chunks(self, chunks: List[Chunk], full_text: str, doc_metadata: Dict) -> List[Chunk]:
        """Enrichit les chunks avec des métadonnées supplémentaires"""
        for chunk in chunks:
            # Ajouter la position relative
            chunk.metadata['relative_position'] = chunk.start_char / len(full_text)
            
            # Ajouter le contexte (chunk précédent et suivant)
            chunk.metadata['has_overlap'] = self.chunk_overlap > 0
            
            # Informations statistiques
            chunk.metadata['char_count'] = len(chunk.text)
            chunk.metadata['word_count'] = len(chunk.text.split())
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Estime le nombre de tokens (approximation)"""
        # Approximation: 1 token ≈ 4 caractères pour le français
        return len(text) // 4
    
    def chunk_with_pages(self, pages_data: List[Dict], doc_metadata: Dict) -> List[Chunk]:
        """Découpe un document structuré en pages (ex: PDF)"""
        all_chunks = []
        
        for page in pages_data:
            page_text = page['content']
            page_num = page['page_number']
            
            # Métadonnées enrichies avec le numéro de page
            page_metadata = {
                **doc_metadata,
                'page_number': page_num
            }
            
            # Chunker le texte de la page
            page_chunks = self.chunk_text(
                page_text,
                page_metadata,
                preserve_structure=True
            )
            
            all_chunks.extend(page_chunks)
        
        return all_chunks


# Test du chunker
if __name__ == "__main__":
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=100)
    
    sample_text = """
    Introduction à l'IoT
    
    L'Internet des Objets (IoT) révolutionne notre façon d'interagir avec le monde.
    
    1. Définition
    L'IoT désigne l'interconnexion des objets physiques via Internet.
    
    2. Applications
    Les applications sont nombreuses: domotique, santé, industrie.
    """
    
    chunks = chunker.chunk_text(sample_text, {'filename': 'test.md'})
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Texte: {chunk.text[:100]}...")
        print(f"Tokens: {chunk.token_count}")