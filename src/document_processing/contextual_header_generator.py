"""
Contextual Header Generator for document chunks
Generates hierarchical headers based on document structure
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
from loguru import logger


@dataclass
class StructureInfo:
    """Information about document structure"""
    document_type: str
    has_sections: bool
    has_pages: bool
    section_hierarchy: List[Dict]
    page_breaks: List[int]
    confidence_score: float


class ContextualHeaderGenerator:
    """
    Generates contextual headers for document chunks based on document structure.
    Supports different document formats and hierarchical information.
    """
    
    def __init__(self):
        """Initialize structure detection patterns"""
        # PDF section patterns
        self.pdf_section_patterns = [
            r'^\s*(\d+\.?\d*\.?\d*)\s+([A-Z][^.\n]{10,100})\s*$',  # Numbered sections
            r'^\s*([IVX]+\.?\s+)([A-Z][^.\n]{10,100})\s*$',       # Roman numerals
            r'^\s*(Chapter\s+\d+[:\-\s]+)([A-Z][^.\n]{10,100})\s*$',  # Chapter format
            r'^\s*([A-Z][A-Z\s]{5,50})\s*$',                      # ALL CAPS headers
        ]
        
        # Markdown header patterns
        self.markdown_header_patterns = [
            r'^(#{1,6})\s+(.+)$',  # Standard markdown headers
        ]
        
        # General structured text patterns
        self.structured_text_patterns = [
            r'^\s*(\d+\.)\s+([A-Z][^.\n]{5,100})\s*$',           # 1. Section
            r'^\s*(\d+\.\d+\.?)\s+([A-Z][^.\n]{5,100})\s*$',    # 1.1 Subsection
            r'^\s*(\d+\.\d+\.\d+\.?)\s+([A-Z][^.\n]{5,100})\s*$',  # 1.1.1 Sub-subsection
        ]
        
        # Confidence thresholds
        self.min_confidence = 0.3
        self.high_confidence = 0.7
    
    def generate_header(
        self, 
        chunk_text: str, 
        doc_metadata: Dict, 
        structure_info: Dict,
        chunk_position: int = 0
    ) -> str:
        """
        Generate contextual header for a chunk
        
        Args:
            chunk_text: The text content of the chunk
            doc_metadata: Metadata about the source document
            structure_info: Information about document structure
            chunk_position: Position of chunk in document (for fallback)
            
        Returns:
            Formatted contextual header string
        """
        filename = doc_metadata.get('filename', 'document')
        
        # Extract hierarchical information
        hierarchy_info = self.extract_section_hierarchy(
            chunk_text, 
            structure_info, 
            chunk_position
        )
        
        # Generate header based on available information
        if hierarchy_info['section'] and hierarchy_info['page']:
            # Both section and page available
            header = f"File: {filename} > Page: {hierarchy_info['page']} > Section: {hierarchy_info['section']}"
        elif hierarchy_info['section']:
            # Section available
            header = f"File: {filename} > Section: {hierarchy_info['section']}"
        elif hierarchy_info['page']:
            # Page available
            header = f"File: {filename} > Page: {hierarchy_info['page']}"
        else:
            # Fallback to chunk index
            header = f"File: {filename} > Chunk: {chunk_position + 1}"
        
        return header
    
    def detect_structure(self, text: str, doc_type: str) -> StructureInfo:
        """
        Detect document structure (sections, pages, etc.)
        
        Args:
            text: Full document text
            doc_type: Type of document (pdf, markdown, txt, docx)
            
        Returns:
            StructureInfo object with detected structure
        """
        logger.info(f"Detecting structure for {doc_type} document")
        
        # Initialize structure info
        structure_info = StructureInfo(
            document_type=doc_type,
            has_sections=False,
            has_pages=False,
            section_hierarchy=[],
            page_breaks=[],
            confidence_score=0.0
        )
        
        # Detect page breaks
        page_breaks = self._detect_page_breaks(text, doc_type)
        if page_breaks:
            structure_info.has_pages = True
            structure_info.page_breaks = page_breaks
        
        # Detect sections based on document type
        if doc_type == 'pdf':
            sections = self._detect_pdf_sections(text)
        elif doc_type == 'markdown':
            sections = self._detect_markdown_sections(text)
        else:
            sections = self._detect_structured_text_sections(text)
        
        if sections:
            structure_info.has_sections = True
            structure_info.section_hierarchy = sections
        
        # Calculate confidence score
        structure_info.confidence_score = self._calculate_confidence(structure_info)
        
        logger.info(f"Structure detection complete: sections={structure_info.has_sections}, "
                   f"pages={structure_info.has_pages}, confidence={structure_info.confidence_score:.2f}")
        
        return structure_info
    
    def extract_section_hierarchy(
        self, 
        chunk_text: str, 
        structure_info: Dict,
        chunk_position: int
    ) -> Dict:
        """
        Extract hierarchical position of chunk within document
        
        Args:
            chunk_text: Text content of the chunk
            structure_info: Document structure information
            chunk_position: Position of chunk in document
            
        Returns:
            Dictionary with section and page information
        """
        hierarchy = {
            'section': None,
            'page': None,
            'section_level': 0,
            'section_path': []
        }
        
        # Extract page information if available
        if isinstance(structure_info, dict) and structure_info.get('has_pages'):
            page_num = structure_info.get('page_number')
            if page_num:
                hierarchy['page'] = page_num
        
        # Extract section information from chunk text or structure
        if isinstance(structure_info, dict) and structure_info.get('has_sections'):
            section_info = self._find_relevant_section(chunk_text, structure_info)
            if section_info:
                hierarchy['section'] = section_info['title']
                hierarchy['section_level'] = section_info.get('level', 0)
                hierarchy['section_path'] = section_info.get('path', [])
        
        return hierarchy
    
    def _detect_page_breaks(self, text: str, doc_type: str) -> List[int]:
        """Detect page breaks in document text with enhanced logic"""
        page_breaks = []
        
        if doc_type == 'pdf':
            # Look for page markers inserted by PDF parser
            page_pattern = r'--- Page (\d+) ---'
            matches = list(re.finditer(page_pattern, text))
            page_breaks = [match.start() for match in matches]
            
            # Also detect implicit page breaks (form feeds, large gaps)
            implicit_breaks = self._detect_implicit_page_breaks(text)
            page_breaks.extend(implicit_breaks)
            
        elif doc_type in ['docx', 'txt']:
            # Look for page break indicators in text
            page_break_patterns = [
                r'\f',  # Form feed character
                r'\n\s*\n\s*Page\s+\d+\s*\n',  # "Page N" indicators
                r'\n\s*-{3,}\s*\n',  # Horizontal rules as page separators
            ]
            
            for pattern in page_break_patterns:
                matches = list(re.finditer(pattern, text))
                page_breaks.extend([match.start() for match in matches])
        
        # Remove duplicates and sort
        page_breaks = sorted(list(set(page_breaks)))
        
        return page_breaks
    
    def _detect_pdf_sections(self, text: str) -> List[Dict]:
        """Detect sections in PDF text with enhanced logic"""
        sections = []
        
        # Enhanced PDF section detection
        for pattern in self.pdf_section_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                # Handle patterns with different numbers of groups
                if match.lastindex >= 2:
                    # Pattern has both section number and title
                    section_number = match.group(1).strip()
                    section_title = match.group(2).strip()
                elif match.lastindex == 1:
                    # Pattern has only title (like ALL CAPS headers)
                    section_number = ""
                    section_title = match.group(1).strip()
                else:
                    continue
                
                # Validate section title (avoid false positives)
                if self._is_valid_section_title(section_title):
                    title = f"{section_number} {section_title}".strip()
                    sections.append({
                        'level': self._determine_section_level(section_number) if section_number else 1,
                        'title': title,
                        'start_char': match.start(),
                        'end_char': None,  # Will be set later
                        'section_number': section_number,
                        'raw_title': section_title,
                        'confidence': self._calculate_section_confidence(section_number, section_title)
                    })
        
        # Additional PDF-specific patterns for table of contents and headers
        toc_sections = self._detect_pdf_toc_sections(text)
        sections.extend(toc_sections)
        
        # Remove duplicates and sort by position
        sections = self._deduplicate_sections(sections)
        sections.sort(key=lambda x: x['start_char'])
        
        # Set end positions and build hierarchy
        sections = self._set_section_boundaries(sections, len(text))
        sections = self._build_section_hierarchy(sections)
        
        return sections
    
    def _detect_markdown_sections(self, text: str) -> List[Dict]:
        """Detect sections in Markdown text with enhanced logic"""
        sections = []
        
        for pattern in self.markdown_header_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                header_level = len(match.group(1))  # Number of # symbols
                header_text = match.group(2).strip()
                
                if self._is_valid_section_title(header_text):
                    sections.append({
                        'level': header_level,
                        'title': header_text,
                        'start_char': match.start(),
                        'end_char': None,
                        'header_level': header_level,
                        'raw_title': header_text,
                        'confidence': 0.9,  # Markdown headers are very reliable
                        'source': 'markdown'
                    })
        
        # Sort by position and set end positions
        sections.sort(key=lambda x: x['start_char'])
        sections = self._set_section_boundaries(sections, len(text))
        sections = self._build_section_hierarchy(sections)
        
        return sections
    
    def _detect_structured_text_sections(self, text: str) -> List[Dict]:
        """Detect sections in structured text (numbered sections) with enhanced logic"""
        sections = []
        
        for pattern in self.structured_text_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                section_number = match.group(1).strip()
                section_title = match.group(2).strip()
                
                if self._is_valid_section_title(section_title):
                    sections.append({
                        'level': self._determine_section_level(section_number),
                        'title': f"{section_number} {section_title}",
                        'start_char': match.start(),
                        'end_char': None,
                        'section_number': section_number,
                        'raw_title': section_title,
                        'confidence': self._calculate_section_confidence(section_number, section_title),
                        'source': 'structured_text'
                    })
        
        # Additional patterns for unstructured documents with fallback logic
        if not sections:
            sections = self._detect_fallback_sections(text)
        
        # Sort by position and set end positions
        sections.sort(key=lambda x: x['start_char'])
        sections = self._set_section_boundaries(sections, len(text))
        sections = self._build_section_hierarchy(sections)
        
        return sections
    
    def _determine_section_level(self, section_number: str) -> int:
        """Determine hierarchical level from section number"""
        # Count dots to determine level (1. = level 1, 1.1. = level 2, etc.)
        dots = section_number.count('.')
        if dots == 0:
            return 1
        return dots
    
    def _find_relevant_section(self, chunk_text: str, structure_info: Dict) -> Optional[Dict]:
        """Find the most relevant section for a chunk"""
        sections = structure_info.get('section_hierarchy', [])
        if not sections:
            return None
        
        # For now, use a simple heuristic: find section that contains chunk start
        # In a real implementation, this would use chunk position information
        chunk_start = chunk_text[:100].strip()
        
        for section in sections:
            if section['raw_title'].lower() in chunk_start.lower():
                return section
        
        # Fallback: return first section (this is simplified)
        return sections[0] if sections else None
    
    def _calculate_confidence(self, structure_info: StructureInfo) -> float:
        """Calculate confidence score for structure detection"""
        confidence = 0.0
        
        # Base confidence from having structure
        if structure_info.has_sections:
            confidence += 0.5
        if structure_info.has_pages:
            confidence += 0.3
        
        # Bonus for number of sections found
        section_count = len(structure_info.section_hierarchy)
        if section_count > 0:
            confidence += min(0.2, section_count * 0.05)
        
        # Ensure confidence is between 0 and 1
        return min(1.0, confidence)
    
    def _is_valid_section_title(self, title: str) -> bool:
        """Validate if a detected title is likely a real section header"""
        # Filter out common false positives
        if len(title) < 3 or len(title) > 200:
            return False
        
        # Avoid titles that are mostly numbers or special characters
        alpha_ratio = sum(c.isalpha() for c in title) / len(title)
        if alpha_ratio < 0.3:
            return False
        
        # Avoid common false positives
        false_positives = [
            'page', 'figure', 'table', 'appendix', 'references',
            'bibliography', 'index', 'contents'
        ]
        
        title_lower = title.lower()
        for fp in false_positives:
            if title_lower.startswith(fp) and len(title) < 20:
                return False
        
        return True
    
    def _calculate_section_confidence(self, section_number: str, title: str) -> float:
        """Calculate confidence for a specific section detection"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for well-formatted section numbers
        if re.match(r'^\d+(\.\d+)*\.?$', section_number):
            confidence += 0.3
        
        # Higher confidence for reasonable title length
        if 10 <= len(title) <= 100:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _detect_pdf_toc_sections(self, text: str) -> List[Dict]:
        """Detect sections from table of contents patterns in PDF"""
        toc_sections = []
        
        # Look for table of contents patterns
        toc_patterns = [
            r'(\d+\.?\d*\.?\d*)\s+([A-Z][^.\n]{10,80})\s+\.{3,}\s*(\d+)',  # TOC with dots and page numbers
            r'(\d+\.?\d*\.?\d*)\s+([A-Z][^.\n]{10,80})\s+(\d+)$',          # TOC with page numbers
        ]
        
        for pattern in toc_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                section_number = match.group(1).strip()
                section_title = match.group(2).strip()
                
                if self._is_valid_section_title(section_title):
                    toc_sections.append({
                        'level': self._determine_section_level(section_number),
                        'title': f"{section_number} {section_title}",
                        'start_char': match.start(),
                        'end_char': None,
                        'section_number': section_number,
                        'raw_title': section_title,
                        'confidence': 0.7,  # TOC entries have high confidence
                        'source': 'toc'
                    })
        
        return toc_sections
    
    def _detect_implicit_page_breaks(self, text: str) -> List[int]:
        """Detect implicit page breaks based on text patterns"""
        breaks = []
        
        # Look for large gaps in text (multiple newlines)
        gap_pattern = r'\n\s*\n\s*\n\s*\n'
        matches = list(re.finditer(gap_pattern, text))
        breaks.extend([match.start() for match in matches])
        
        # Look for repeated headers/footers that might indicate page boundaries
        header_footer_pattern = r'\n\s*(Page\s+\d+|Chapter\s+\d+|\d+\s*$)'
        matches = list(re.finditer(header_footer_pattern, text, re.MULTILINE))
        breaks.extend([match.start() for match in matches])
        
        return breaks
    
    def _deduplicate_sections(self, sections: List[Dict]) -> List[Dict]:
        """Remove duplicate section detections"""
        unique_sections = []
        seen_positions = set()
        
        for section in sections:
            # Create a key based on position and title
            key = (section['start_char'] // 100, section['raw_title'][:20])
            
            if key not in seen_positions:
                seen_positions.add(key)
                unique_sections.append(section)
        
        return unique_sections
    
    def _set_section_boundaries(self, sections: List[Dict], text_length: int) -> List[Dict]:
        """Set end boundaries for sections"""
        for i, section in enumerate(sections):
            if i < len(sections) - 1:
                section['end_char'] = sections[i + 1]['start_char']
            else:
                section['end_char'] = text_length
        
        return sections
    
    def _build_section_hierarchy(self, sections: List[Dict]) -> List[Dict]:
        """Build hierarchical relationships between sections"""
        for i, section in enumerate(sections):
            section['parent'] = None
            section['children'] = []
            section['path'] = []
            
            # Find parent (previous section with lower level)
            current_level = section['level']
            for j in range(i - 1, -1, -1):
                if sections[j]['level'] < current_level:
                    section['parent'] = sections[j]['title']
                    sections[j]['children'].append(section['title'])
                    break
            
            # Build path from root to current section
            if section['parent']:
                # Find parent section and copy its path
                for parent_section in sections[:i]:
                    if parent_section['title'] == section['parent']:
                        section['path'] = parent_section['path'] + [parent_section['title']]
                        break
            
            section['path'].append(section['title'])
        
        return sections


    def _detect_fallback_sections(self, text: str) -> List[Dict]:
        """Fallback section detection for unstructured documents"""
        sections = []
        
        # Look for potential headers based on formatting patterns
        fallback_patterns = [
            r'^\s*([A-Z][A-Z\s]{10,60})\s*$',  # ALL CAPS lines
            r'^\s*([A-Z][^.\n]{20,80})\s*$',   # Capitalized lines of reasonable length
            r'^\s*(\*{1,3}\s*[A-Z][^*\n]{10,60}\s*\*{1,3})\s*$',  # Emphasized text
            r'^\s*(-{3,})\s*$',  # Horizontal rules as section separators
        ]
        
        for pattern in fallback_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                title = match.group(1).strip()
                
                # Clean up title (remove emphasis markers)
                title = re.sub(r'[*_-]{1,3}', '', title).strip()
                
                if self._is_valid_section_title(title) and len(title) > 5:
                    sections.append({
                        'level': 1,  # All fallback sections are level 1
                        'title': title,
                        'start_char': match.start(),
                        'end_char': None,
                        'raw_title': title,
                        'confidence': 0.4,  # Lower confidence for fallback detection
                        'source': 'fallback'
                    })
        
        # If still no sections found, create artificial sections based on text length
        if not sections and len(text) > 2000:
            sections = self._create_position_based_sections(text)
        
        return sections
    
    def _create_position_based_sections(self, text: str) -> List[Dict]:
        """Create position-based sections when no structure is detected"""
        sections = []
        section_size = 1500  # Approximate section size
        
        for i in range(0, len(text), section_size):
            section_start = i
            section_end = min(i + section_size, len(text))
            
            # Try to find a good break point (end of sentence or paragraph)
            if section_end < len(text):
                break_point = self._find_good_break_point(text, section_end)
                if break_point > section_start:
                    section_end = break_point
            
            section_num = (i // section_size) + 1
            sections.append({
                'level': 1,
                'title': f"Section {section_num}",
                'start_char': section_start,
                'end_char': section_end,
                'raw_title': f"Section {section_num}",
                'confidence': 0.2,  # Very low confidence for artificial sections
                'source': 'position_based'
            })
        
        return sections
    
    def _find_good_break_point(self, text: str, position: int) -> int:
        """Find a good break point near the given position"""
        # Look for paragraph breaks within 200 characters
        search_start = max(0, position - 100)
        search_end = min(len(text), position + 100)
        search_text = text[search_start:search_end]
        
        # Look for double newlines (paragraph breaks)
        paragraph_breaks = [m.start() + search_start for m in re.finditer(r'\n\s*\n', search_text)]
        if paragraph_breaks:
            # Find the closest paragraph break
            closest = min(paragraph_breaks, key=lambda x: abs(x - position))
            return closest
        
        # Look for sentence endings
        sentence_breaks = [m.end() + search_start for m in re.finditer(r'[.!?]\s+', search_text)]
        if sentence_breaks:
            closest = min(sentence_breaks, key=lambda x: abs(x - position))
            return closest
        
        return position


# Test the contextual header generator
if __name__ == "__main__":
    generator = ContextualHeaderGenerator()
    
    # Test with sample text
    sample_text = """
    1. Introduction to IoT
    
    The Internet of Things (IoT) is revolutionizing how we interact with the world.
    
    1.1 Definition
    IoT refers to the interconnection of physical objects via the Internet.
    
    2. Applications
    Applications are numerous: home automation, health, industry.
    """
    
    structure = generator.detect_structure(sample_text, 'txt')
    print(f"Structure detected: {structure}")
    
    header = generator.generate_header(
        "IoT refers to the interconnection...",
        {'filename': 'iot_guide.txt'},
        structure.__dict__,
        0
    )
    print(f"Generated header: {header}")