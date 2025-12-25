"""
Découpage sémantique de documents avec support du français
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from loguru import logger

# Import contextual header generator
from .contextual_header_generator import ContextualHeaderGenerator

# Import enhanced chunk model
from ..storage.models import EnhancedChunk

# LangChain imports for semantic chunking
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_experimental.text_splitter import SemanticChunker as LangChainSemanticChunker
    from langchain.text_splitter import TextSplitter
    from sentence_transformers import SentenceTransformer
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain text splitters not available: {e}")
    LANGCHAIN_AVAILABLE = False
    LangChainSemanticChunker = None


@dataclass
class Chunk:
    """Structure pour un chunk de texte - Legacy compatibility"""
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
    
    Now uses LangChain's SemanticChunker for improved semantic awareness.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        respect_sentence_boundaries: bool = True,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sentence_boundaries = respect_sentence_boundaries
        self.embeddings_model = embeddings_model
        
        # Initialize LangChain SemanticChunker if available
        self._langchain_chunker = None
        self._fallback_chunker = None
        
        if LANGCHAIN_AVAILABLE and LangChainSemanticChunker:
            try:
                # Initialize embeddings model for semantic chunking
                embeddings = SentenceTransformer(embeddings_model)
                
                # Create LangChain SemanticChunker with custom embeddings wrapper
                class EmbeddingsWrapper:
                    def __init__(self, model):
                        self.model = model
                    
                    def embed_documents(self, texts):
                        return self.model.encode(texts).tolist()
                    
                    def embed_query(self, text):
                        return self.model.encode([text])[0].tolist()
                
                embeddings_wrapper = EmbeddingsWrapper(embeddings)
                
                self._langchain_chunker = LangChainSemanticChunker(
                    embeddings=embeddings_wrapper,
                    buffer_size=1,  # Number of sentences to group together
                    add_start_index=True
                )
                logger.info("✅ LangChain SemanticChunker initialized successfully")
                
            except Exception as e:
                logger.warning(f"Failed to initialize LangChain SemanticChunker: {e}")
                self._langchain_chunker = None
        
        # Initialize fallback chunker (RecursiveCharacterTextSplitter)
        if LANGCHAIN_AVAILABLE:
            self._fallback_chunker = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        
        # Initialize contextual header generator
        self.header_generator = ContextualHeaderGenerator()
        
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
    ) -> List[EnhancedChunk]:
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
        
        # Detect document structure for contextual headers
        doc_type = self._determine_document_type(doc_metadata)
        structure_info = self.header_generator.detect_structure(text, doc_type)
        
        # Use LangChain SemanticChunker if available
        if self._langchain_chunker:
            try:
                chunks = self._chunk_with_langchain(text, doc_metadata, preserve_structure, structure_info)
                logger.info(f"✅ Créé {len(chunks)} chunks avec LangChain SemanticChunker (moyenne: {sum(c.metadata.get('token_count', 0) for c in chunks) / len(chunks):.0f} tokens)")
                return chunks
            except Exception as e:
                logger.warning(f"LangChain chunking failed, falling back to custom implementation: {e}")
        
        # Fallback to original implementation
        if preserve_structure:
            # Découpage basé sur la structure
            chunks = self._chunk_by_structure(text, doc_metadata, structure_info)
        else:
            # Découpage simple avec overlap
            chunks = self._chunk_with_overlap(text, doc_metadata, structure_info)
        
        # Enrichissement des métadonnées
        chunks = self._enrich_chunks(chunks, text, doc_metadata)
        
        logger.info(f"✅ Créé {len(chunks)} chunks (moyenne: {sum(c.metadata.get('token_count', 0) for c in chunks) / len(chunks):.0f} tokens)")
        
        return chunks
    
    def _determine_document_type(self, doc_metadata: Dict) -> str:
        """
        Determine document type from metadata
        
        Args:
            doc_metadata: Document metadata
            
        Returns:
            Document type string (pdf, markdown, txt, docx)
        """
        filename = doc_metadata.get('filename', '')
        filepath = doc_metadata.get('filepath', '')
        format_type = doc_metadata.get('format', '')
        
        # Check format field first
        if format_type:
            return format_type.lower()
        
        # Check file extension
        if filename:
            if filename.lower().endswith('.pdf'):
                return 'pdf'
            elif filename.lower().endswith(('.md', '.markdown')):
                return 'markdown'
            elif filename.lower().endswith('.docx'):
                return 'docx'
            elif filename.lower().endswith('.txt'):
                return 'txt'
        
        if filepath:
            if filepath.lower().endswith('.pdf'):
                return 'pdf'
            elif filepath.lower().endswith(('.md', '.markdown')):
                return 'markdown'
            elif filepath.lower().endswith('.docx'):
                return 'docx'
            elif filepath.lower().endswith('.txt'):
                return 'txt'
        
        # Default to txt if unknown
        return 'txt'
    
    def _chunk_with_langchain(
        self, 
        text: str, 
        doc_metadata: Dict, 
        preserve_structure: bool = True,
        structure_info = None
    ) -> List[EnhancedChunk]:
        """
        Use LangChain's SemanticChunker for text splitting
        
        Args:
            text: Text to chunk
            doc_metadata: Document metadata
            preserve_structure: Whether to preserve document structure
            structure_info: Document structure information for contextual headers
            
        Returns:
            List of chunks created by LangChain SemanticChunker
        """
        try:
            # Use LangChain SemanticChunker to split text
            langchain_docs = self._langchain_chunker.create_documents([text])
            
            chunks = []
            for i, doc in enumerate(langchain_docs):
                chunk_text = doc.page_content
                
                # Skip chunks that are too small
                if len(chunk_text) < self.min_chunk_size:
                    continue
                
                # Get start index from metadata if available
                start_char = doc.metadata.get('start_index', i * self.chunk_size)
                end_char = start_char + len(chunk_text)
                
                # Generate contextual header
                contextual_header = ""
                if structure_info:
                    try:
                        contextual_header = self.header_generator.generate_header(
                            chunk_text,
                            doc_metadata,
                            structure_info.__dict__ if hasattr(structure_info, '__dict__') else structure_info,
                            i
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate contextual header: {e}")
                        contextual_header = f"File: {doc_metadata.get('filename', 'document')} > Chunk: {i + 1}"
                
                # Prepend contextual header to chunk text
                if contextual_header:
                    enhanced_text = f"{contextual_header}\n\n{chunk_text}"
                else:
                    enhanced_text = chunk_text
                
                # Create enhanced chunk with proper metadata structure
                enhanced_metadata = {
                    **doc_metadata,
                    'chunk_method': 'langchain_semantic',
                    'original_text': chunk_text,
                    'langchain_metadata': doc.metadata,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'token_count': self._estimate_tokens(enhanced_text)
                }
                
                # Extract hierarchy path from structure info - simplified version
                hierarchy_path = []
                if structure_info and hasattr(structure_info, '__dict__'):
                    structure_dict = structure_info.__dict__
                elif structure_info:
                    structure_dict = dict(structure_info)
                else:
                    structure_dict = {}
                
                # Build simple hierarchy path from document structure
                filename = doc_metadata.get('filename', 'document')
                hierarchy_path = [filename]
                
                # Add section information if available
                if doc_metadata.get('section'):
                    hierarchy_path.append(doc_metadata['section'])
                
                # Simplify structure metadata to avoid complex nested objects
                simple_structure_metadata = {
                    'document_type': structure_dict.get('document_type', 'unknown'),
                    'has_sections': structure_dict.get('has_sections', False),
                    'has_pages': structure_dict.get('has_pages', False),
                    'confidence_score': structure_dict.get('confidence_score', 0.0)
                }
                
                # Create enhanced chunk
                chunk = EnhancedChunk(
                    id=f"{doc_metadata.get('filename', 'doc')}_langchain_{i}",
                    document_id=doc_metadata.get('filepath', ''),
                    chunk_id=i,
                    content=enhanced_text,
                    embedding=None,  # Will be set later
                    metadata=enhanced_metadata,
                    contextual_header=contextual_header,
                    hierarchy_path=hierarchy_path,
                    structure_metadata=simple_structure_metadata
                )
                chunks.append(chunk)
            
            # If no valid chunks were created, fall back to RecursiveCharacterTextSplitter
            if not chunks and self._fallback_chunker:
                logger.info("LangChain SemanticChunker produced no valid chunks, using fallback")
                return self._chunk_with_fallback_langchain(text, doc_metadata, structure_info)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in LangChain chunking: {e}")
            # Fall back to RecursiveCharacterTextSplitter
            if self._fallback_chunker:
                return self._chunk_with_fallback_langchain(text, doc_metadata, structure_info)
            else:
                # Ultimate fallback to original implementation
                return self._chunk_with_overlap(text, doc_metadata, structure_info)
    
    def _chunk_with_fallback_langchain(self, text: str, doc_metadata: Dict, structure_info = None) -> List[EnhancedChunk]:
        """
        Use LangChain's RecursiveCharacterTextSplitter as fallback
        
        Args:
            text: Text to chunk
            doc_metadata: Document metadata
            structure_info: Document structure information for contextual headers
            
        Returns:
            List of chunks created by RecursiveCharacterTextSplitter
        """
        try:
            langchain_docs = self._fallback_chunker.create_documents([text])
            
            chunks = []
            for i, doc in enumerate(langchain_docs):
                chunk_text = doc.page_content
                
                # Skip chunks that are too small
                if len(chunk_text) < self.min_chunk_size:
                    continue
                
                start_char = i * (self.chunk_size - self.chunk_overlap)
                end_char = start_char + len(chunk_text)
                
                # Generate contextual header
                contextual_header = ""
                if structure_info:
                    try:
                        contextual_header = self.header_generator.generate_header(
                            chunk_text,
                            doc_metadata,
                            structure_info.__dict__ if hasattr(structure_info, '__dict__') else structure_info,
                            i
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate contextual header: {e}")
                        contextual_header = f"File: {doc_metadata.get('filename', 'document')} > Chunk: {i + 1}"
                
                # Prepend contextual header to chunk text
                if contextual_header:
                    enhanced_text = f"{contextual_header}\n\n{chunk_text}"
                else:
                    enhanced_text = chunk_text
                
                # Create enhanced chunk with proper metadata structure
                enhanced_metadata = {
                    **doc_metadata,
                    'chunk_method': 'langchain_recursive',
                    'original_text': chunk_text,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'token_count': self._estimate_tokens(enhanced_text)
                }
                
                # Extract hierarchy path from structure info - simplified version
                hierarchy_path = []
                if structure_info and hasattr(structure_info, '__dict__'):
                    structure_dict = structure_info.__dict__
                elif structure_info:
                    structure_dict = dict(structure_info)
                else:
                    structure_dict = {}
                
                # Build simple hierarchy path from document structure
                filename = doc_metadata.get('filename', 'document')
                hierarchy_path = [filename]
                
                # Add section information if available
                if doc_metadata.get('section'):
                    hierarchy_path.append(doc_metadata['section'])
                
                # Simplify structure metadata to avoid complex nested objects
                simple_structure_metadata = {
                    'document_type': structure_dict.get('document_type', 'unknown'),
                    'has_sections': structure_dict.get('has_sections', False),
                    'has_pages': structure_dict.get('has_pages', False),
                    'confidence_score': structure_dict.get('confidence_score', 0.0)
                }
                
                chunk = EnhancedChunk(
                    id=f"{doc_metadata.get('filename', 'doc')}_recursive_{i}",
                    document_id=doc_metadata.get('filepath', ''),
                    chunk_id=i,
                    content=enhanced_text,
                    embedding=None,  # Will be set later
                    metadata=enhanced_metadata,
                    contextual_header=contextual_header,
                    hierarchy_path=hierarchy_path,
                    structure_metadata=simple_structure_metadata
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in fallback LangChain chunking: {e}")
            # Ultimate fallback to original implementation
            return self._chunk_with_overlap(text, doc_metadata, structure_info)
    
    def _chunk_by_structure(self, text: str, doc_metadata: Dict, structure_info = None) -> List[EnhancedChunk]:
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
                    {**doc_metadata, 'section': section['title']},
                    structure_info
                )
                chunks.extend(sub_chunks)
            else:
                # Generate contextual header for the section
                contextual_header = ""
                if structure_info:
                    try:
                        contextual_header = self.header_generator.generate_header(
                            section_text,
                            doc_metadata,
                            structure_info.__dict__ if hasattr(structure_info, '__dict__') else structure_info,
                            section_idx
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate contextual header: {e}")
                        contextual_header = f"File: {doc_metadata.get('filename', 'document')} > Section: {section['title']}"
                
                # Prepend contextual header to section text
                if contextual_header:
                    enhanced_text = f"{contextual_header}\n\n{section_text}"
                else:
                    enhanced_text = section_text
                
                # Create enhanced chunk for the section
                enhanced_metadata = {
                    **doc_metadata,
                    'section': section['title'],
                    'section_index': section_idx,
                    'original_text': section_text,
                    'char_count': len(section_text),
                    'word_count': len(section_text.split()),
                    'token_count': self._estimate_tokens(enhanced_text)
                }
                
                # Extract hierarchy path from structure info - simplified version
                hierarchy_path = []
                if structure_info and hasattr(structure_info, '__dict__'):
                    structure_dict = structure_info.__dict__
                elif structure_info:
                    structure_dict = dict(structure_info)
                else:
                    structure_dict = {}
                
                # Build simple hierarchy path from document structure
                filename = doc_metadata.get('filename', 'document')
                hierarchy_path = [filename]
                
                # Add section title to hierarchy
                if section['title'] not in hierarchy_path:
                    hierarchy_path.append(section['title'])
                
                # Simplify structure metadata to avoid complex nested objects
                simple_structure_metadata = {
                    'document_type': structure_dict.get('document_type', 'unknown'),
                    'has_sections': structure_dict.get('has_sections', False),
                    'has_pages': structure_dict.get('has_pages', False),
                    'confidence_score': structure_dict.get('confidence_score', 0.0)
                }
                
                # Créer un chunk pour la section entière
                chunk = EnhancedChunk(
                    id=f"{doc_metadata.get('filename', 'doc')}_{section_idx}",
                    document_id=doc_metadata.get('filepath', ''),
                    chunk_id=section_idx,
                    content=enhanced_text,
                    embedding=None,  # Will be set later
                    metadata=enhanced_metadata,
                    contextual_header=contextual_header,
                    hierarchy_path=hierarchy_path,
                    structure_metadata=simple_structure_metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_with_overlap(self, text: str, metadata: Dict, structure_info = None) -> List[EnhancedChunk]:
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
                # Generate contextual header
                contextual_header = ""
                if structure_info:
                    try:
                        contextual_header = self.header_generator.generate_header(
                            chunk_text,
                            metadata,
                            structure_info.__dict__ if hasattr(structure_info, '__dict__') else structure_info,
                            chunk_idx
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate contextual header: {e}")
                        contextual_header = f"File: {metadata.get('filename', 'document')} > Chunk: {chunk_idx + 1}"
                
                # Prepend contextual header to chunk text
                if contextual_header:
                    enhanced_text = f"{contextual_header}\n\n{chunk_text}"
                else:
                    enhanced_text = chunk_text
                
                # Create enhanced chunk with proper metadata structure
                enhanced_metadata = {
                    **metadata,
                    'original_text': chunk_text,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'token_count': self._estimate_tokens(enhanced_text)
                }
                
                # Extract hierarchy path from structure info - simplified version
                hierarchy_path = []
                if structure_info and hasattr(structure_info, '__dict__'):
                    structure_dict = structure_info.__dict__
                elif structure_info:
                    structure_dict = dict(structure_info)
                else:
                    structure_dict = {}
                
                # Build simple hierarchy path from document structure
                filename = metadata.get('filename', 'document')
                hierarchy_path = [filename]
                
                # Add section information if available
                if metadata.get('section'):
                    hierarchy_path.append(metadata['section'])
                
                # Simplify structure metadata to avoid complex nested objects
                simple_structure_metadata = {
                    'document_type': structure_dict.get('document_type', 'unknown'),
                    'has_sections': structure_dict.get('has_sections', False),
                    'has_pages': structure_dict.get('has_pages', False),
                    'confidence_score': structure_dict.get('confidence_score', 0.0)
                }
                
                chunk = EnhancedChunk(
                    id=f"{metadata.get('filename', 'doc')}_chunk_{chunk_idx}",
                    document_id=metadata.get('filepath', ''),
                    chunk_id=chunk_idx,
                    content=enhanced_text,
                    embedding=None,  # Will be set later
                    metadata=enhanced_metadata,
                    contextual_header=contextual_header,
                    hierarchy_path=hierarchy_path,
                    structure_metadata=simple_structure_metadata
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
    
    def _enrich_chunks(self, chunks: List[EnhancedChunk], full_text: str, doc_metadata: Dict) -> List[EnhancedChunk]:
        """Enrichit les chunks avec des métadonnées supplémentaires"""
        for chunk in chunks:
            # Ajouter la position relative
            chunk.metadata['relative_position'] = 0.0  # Will be calculated based on chunk position
            
            # Ajouter le contexte (chunk précédent et suivant)
            chunk.metadata['has_overlap'] = self.chunk_overlap > 0
            
            # Ensure char_count, word_count are in metadata if not already set
            if 'char_count' not in chunk.metadata:
                chunk.metadata['char_count'] = len(chunk.content)
            if 'word_count' not in chunk.metadata:
                chunk.metadata['word_count'] = len(chunk.content.split())
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Estime le nombre de tokens (approximation)"""
        # Approximation: 1 token ≈ 4 caractères pour le français
        return len(text) // 4
    
    def chunk_with_pages(self, pages_data: List[Dict], doc_metadata: Dict) -> List[EnhancedChunk]:
        """Découpe un document structuré en pages (ex: PDF)"""
        all_chunks = []
        
        # Detect document structure for the entire document
        full_text = "\n".join([page['content'] for page in pages_data])
        doc_type = self._determine_document_type(doc_metadata)
        structure_info = self.header_generator.detect_structure(full_text, doc_type)
        
        for page in pages_data:
            page_text = page['content']
            page_num = page['page_number']
            
            # Métadonnées enrichies avec le numéro de page
            page_metadata = {
                **doc_metadata,
                'page_number': page_num
            }
            
            # Create structure info for this specific page
            page_structure_info = structure_info
            if hasattr(structure_info, '__dict__'):
                page_structure_dict = structure_info.__dict__.copy()
                page_structure_dict['page_number'] = page_num
            else:
                page_structure_dict = dict(structure_info) if structure_info else {}
                page_structure_dict['page_number'] = page_num
            
            # Chunker le texte de la page
            page_chunks = self.chunk_text(
                page_text,
                page_metadata,
                preserve_structure=True
            )
            
            # Update chunk metadata to include page-specific contextual headers
            for chunk in page_chunks:
                # If chunk doesn't already have a contextual header, generate one
                if 'contextual_header' not in chunk.metadata or not chunk.metadata['contextual_header']:
                    try:
                        contextual_header = self.header_generator.generate_header(
                            chunk.metadata.get('original_text', chunk.text),
                            page_metadata,
                            page_structure_dict,
                            len(all_chunks)
                        )
                        
                        # Update chunk text with new header if needed
                        if contextual_header and not chunk.text.startswith(contextual_header):
                            original_text = chunk.metadata.get('original_text', chunk.text)
                            chunk.content = f"{contextual_header}\n\n{original_text}"
                            chunk.metadata['contextual_header'] = contextual_header
                            chunk.metadata['token_count'] = self._estimate_tokens(chunk.content)
                            
                    except Exception as e:
                        logger.warning(f"Failed to generate page-based contextual header: {e}")
            
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
        print(f"Texte: {chunk.content[:100]}...")
        print(f"Tokens: {chunk.metadata.get('token_count', 0)}")
        print(f"Contextual Header: {chunk.contextual_header}")
        print(f"Hierarchy Path: {chunk.hierarchy_path}")