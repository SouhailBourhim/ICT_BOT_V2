"""
Specialized handler for professor-related queries that ensures first page content is retrieved
"""
from typing import List, Dict, Optional, Tuple
import re
from loguru import logger
from ..storage.compatibility import compatibility_layer


class ProfessorQueryHandler:
    """
    Handles professor-related queries by ensuring first page content is always retrieved
    and given priority in the search results.
    """
    
    def __init__(self, vector_store, hybrid_search):
        """
        Initialize the professor query handler
        
        Args:
            vector_store: Vector store instance
            hybrid_search: Hybrid search engine instance
        """
        self.vector_store = vector_store
        self.hybrid_search = hybrid_search
        
        # Patterns to detect professor-related queries
        self.professor_patterns = [
            r'\b(professor|professeur|enseignant|teacher|instructor)\b',
            r'\b(nom\s+du\s+professeur|name\s+of\s+professor)\b',
            r'\b(qui\s+enseigne|who\s+teaches)\b',
            r'\b(responsable\s+du\s+cours|course\s+instructor)\b',
            r'\b(prof\s+de|prof\s+du)\b',
            
            # Follow-up questions about professor information
            r'\b(son\s+email|his\s+email|her\s+email)\b',
            r'\b(son\s+adresse|his\s+address|her\s+address)\b',
            r'\b(contact\s+du\s+professeur|professor\s+contact)\b',
            r'\b(email\s+du\s+prof|prof\s+email)\b',
            r'\b(coordonnées|contact\s+info|contact\s+information)\b',
            r'\b(comment\s+le\s+contacter|how\s+to\s+contact)\b',
            r'\b(bureau\s+du\s+professeur|professor\s+office)\b'
        ]
        
        # Common professor title patterns
        self.professor_title_patterns = [
            r'\b(?:Prof\.?\s+|Professeur\s+)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'\b(?:Dr\.?\s+)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'\b(?:M\.?\s+|Mme\.?\s+)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'(?:Enseignant|Responsable|Instructor):\s*(?:Prof\.?|Dr\.?|M\.?|Mme\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'(?:Par|By):\s*(?:Prof\.?|Dr\.?|M\.?|Mme\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            
            # INPT specific patterns - name followed by credentials
            r'(?:^|\s)([A-Z][a-z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',  # IyadLAHSEN CHERIF, PhDPA
            r'(?:^|\s)([A-Z][a-z]+\s+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',  # Name with spaces
            
            # Name before email pattern (common in INPT documents)
            r'(?:^|\s)([A-Z][a-z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),?\s*[^,]*@',
            r'(?:^|\s)([A-Z][a-z]+\s+[A-Z][A-Z]+\s+[A-Z][A-Z]+),?\s*[^,]*@'
        ]
        
        logger.info("ProfessorQueryHandler initialized")
    
    def is_professor_query(self, query: str) -> bool:
        """
        Check if the query is asking about professor information
        
        Args:
            query: User query
            
        Returns:
            True if query is professor-related, False otherwise
        """
        query_lower = query.lower()
        
        for pattern in self.professor_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.info(f"Professor query detected: {pattern}")
                return True
        
        return False
    
    def is_professor_contact_query(self, query: str) -> bool:
        """
        Check if the query is asking for professor contact information
        
        Args:
            query: User query
            
        Returns:
            True if query is asking for professor contact info, False otherwise
        """
        query_lower = query.lower()
        
        # Contact-specific patterns
        contact_patterns = [
            r'\b(email|mail|adresse|address)\b',
            r'\b(contact|coordonnées|téléphone|phone)\b',
            r'\b(bureau|office|où\s+le\s+trouver)\b',
            r'\b(comment\s+le\s+contacter|how\s+to\s+contact)\b',
            r'\b(son\s+email|his\s+email|her\s+email)\b'
        ]
        
        # Check if it's a contact query
        is_contact = False
        for pattern in contact_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.info(f"Professor contact query detected: {pattern}")
                is_contact = True
                break
        
        # If it's a contact query, also check if it could be professor-related
        # (either explicitly mentions professor or uses pronouns that could refer to professor)
        if is_contact:
            # Check for explicit professor mentions
            if self.is_professor_query(query):
                return True
            
            # Check for pronoun references that could refer to professor in context
            pronoun_patterns = [
                r'\b(his|her|son|sa|ses|lui|le|la)\b',
                r'\b(where\s+is\s+he|où\s+est-il)\b'
            ]
            
            for pattern in pronoun_patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"Contact query with pronoun reference detected: {pattern}")
                    return True
        
        return False
    
    def handle_professor_query(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Handle professor-related queries with specialized retrieval strategy
        
        Args:
            query: User query about professor
            top_k: Number of results to return
            filters: Optional filters
            
        Returns:
            List of search results with first page content prioritized
        """
        logger.info(f"Handling professor query: {query}")
        
        # Check if this is a contact query - if so, search more broadly
        is_contact_query = self.is_professor_contact_query(query)
        
        if is_contact_query:
            logger.info("Contact query detected - searching all pages for contact information")
            # For contact queries, search more broadly and look for email patterns
            contact_results = self._search_for_contact_info(query, top_k)
            if contact_results:
                logger.info(f"Found {len(contact_results)} contact-related results")
                return contact_results
        
        # Step 1: Get first page chunks from all documents
        first_page_results = self._get_first_page_chunks()
        
        # Step 2: Regular hybrid search
        regular_results = self.hybrid_search.search(
            query=query,
            top_k=top_k,
            filters=filters
        )
        
        # Step 3: Merge and prioritize first page content
        merged_results = self._merge_and_prioritize_results(
            first_page_results,
            regular_results,
            query,
            top_k
        )
        
        logger.info(f"Professor query handled: {len(merged_results)} results")
        return merged_results
    
    def _search_for_contact_info(self, query: str, top_k: int) -> List[Dict]:
        """
        Search specifically for contact information across all document pages
        
        Args:
            query: Contact-related query
            top_k: Number of results to return
            
        Returns:
            List of results containing contact information
        """
        try:
            # Get all chunks from vector store
            all_results = self.vector_store.get_all_with_metadata()
            
            contact_chunks = []
            
            if 'normalized_results' in all_results:
                # Use compatibility layer results
                for result_data in all_results['normalized_results']:
                    metadata = result_data.get('metadata', {})
                    clean_content = result_data.get('clean_content', result_data.get('content', ''))
                    display_content = result_data.get('content', '')
                    
                    # Check if this chunk contains contact information
                    contact_score = self._calculate_contact_relevance(clean_content or display_content)
                    
                    if contact_score > 0.1:  # Lower threshold for contact info
                        contact_chunks.append({
                            'doc_id': result_data.get('id', ''),
                            'text': display_content,
                            'metadata': {
                                **metadata,
                                'clean_content': clean_content,
                                'contact_score': contact_score,
                                'is_contact_result': True
                            },
                            'score': contact_score + 1.0,  # Boost contact results
                            'semantic_score': contact_score,
                            'bm25_score': 0.0,
                            'rank': 0
                        })
            
            # Sort by contact relevance
            contact_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Also do regular search and merge
            regular_results = self.hybrid_search.search(
                query=query,
                top_k=top_k,
                filters=None
            )
            
            # Convert regular results to dict format
            regular_dict = {}
            for result in regular_results:
                regular_dict[result.doc_id] = {
                    'doc_id': result.doc_id,
                    'text': result.text,
                    'metadata': result.metadata,
                    'score': result.score,
                    'semantic_score': result.semantic_score,
                    'bm25_score': result.bm25_score,
                    'rank': result.rank
                }
            
            # Merge contact chunks with regular results
            merged_results = {}
            
            # Add contact chunks first (higher priority)
            for contact_chunk in contact_chunks[:top_k]:
                doc_id = contact_chunk['doc_id']
                merged_results[doc_id] = contact_chunk
            
            # Add regular results that aren't already included
            for doc_id, result in regular_dict.items():
                if doc_id not in merged_results and len(merged_results) < top_k:
                    merged_results[doc_id] = result
            
            # Sort by score and return
            sorted_results = sorted(
                merged_results.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:top_k]
            
            # Update ranks
            for i, result in enumerate(sorted_results):
                result['rank'] = i + 1
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error searching for contact info: {e}")
            return []
    
    def _calculate_contact_relevance(self, text: str) -> float:
        """
        Calculate how relevant a text chunk is for contact information
        
        Args:
            text: Text content to analyze
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not text:
            return 0.0
            
        relevance_score = 0.0
        text_lower = text.lower()
        
        # Check for email addresses (highest priority)
        email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Standard email
            r'inpt[a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # INPT emails
        ]
        
        for pattern in email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                relevance_score += 0.8  # Very high score for emails
                logger.info(f"Found email addresses: {matches[:2]}")  # Log first 2
        
        # Check for phone numbers
        phone_patterns = [
            r'\b\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}\b',  # French format
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                relevance_score += 0.4
                logger.info(f"Found phone numbers: {matches[:2]}")
        
        # Check for office/bureau information
        office_patterns = [
            r'\b(bureau|office|salle|room)\s*[:\-]?\s*[A-Z]?\d+[A-Z]?\b',
            r'\b(bâtiment|building|bloc)\s*[:\-]?\s*[A-Z]?\d*[A-Z]?\b',
        ]
        
        for pattern in office_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                relevance_score += 0.3
                logger.info(f"Found office info: {matches[:2]}")
        
        # Check for contact keywords
        contact_keywords = [
            'contact', 'coordonnées', 'téléphone', 'phone', 'email', 'mail',
            'adresse', 'address', 'bureau', 'office'
        ]
        
        for keyword in contact_keywords:
            if keyword in text_lower:
                relevance_score += 0.1
        
        # Check for professor names (to ensure it's about the right person)
        professor_names = ['iyad', 'lahsen', 'cherif']
        name_found = any(name in text_lower for name in professor_names)
        if name_found:
            relevance_score += 0.2
        
        return min(relevance_score, 1.0)

    def _get_first_page_chunks(self) -> List[Dict]:
        """
        Retrieve all chunks from first pages of documents
        
        Returns:
            List of first page chunks
        """
        try:
            # Query for page 1 chunks specifically
            results = self.vector_store.get_all_with_metadata()
            
            first_page_chunks = []
            
            if 'normalized_results' in results:
                # Use compatibility layer results
                for result_data in results['normalized_results']:
                    metadata = result_data.get('metadata', {})
                    page_number = metadata.get('page_number')
                    
                    # Include chunks from page 1 or chunks without page info (might be from first page)
                    if page_number == 1 or page_number is None:
                        clean_content = result_data.get('clean_content', result_data.get('content', ''))
                        display_content = result_data.get('content', '')
                        
                        first_page_chunks.append({
                            'doc_id': result_data.get('id', ''),
                            'text': display_content,
                            'metadata': {
                                **metadata,
                                'clean_content': clean_content,
                                'is_first_page': True,
                                'priority_boost': 0.3  # Boost score for first page content
                            },
                            'score': 1.0,  # High base score for first page
                            'semantic_score': 1.0,
                            'bm25_score': 0.0,
                            'rank': 0
                        })
            else:
                # Fallback to original format
                all_results = self.vector_store.get_all()
                
                for i, (doc_id, text, metadata) in enumerate(zip(
                    all_results.get('ids', []),
                    all_results.get('documents', []),
                    all_results.get('metadatas', [])
                )):
                    page_number = metadata.get('page_number')
                    
                    if page_number == 1 or page_number is None:
                        first_page_chunks.append({
                            'doc_id': doc_id,
                            'text': text,
                            'metadata': {
                                **metadata,
                                'is_first_page': True,
                                'priority_boost': 0.3
                            },
                            'score': 1.0,
                            'semantic_score': 1.0,
                            'bm25_score': 0.0,
                            'rank': 0
                        })
            
            logger.info(f"Retrieved {len(first_page_chunks)} first page chunks")
            return first_page_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving first page chunks: {e}")
            return []
    
    def _merge_and_prioritize_results(
        self,
        first_page_results: List[Dict],
        regular_results: List,
        query: str,
        top_k: int
    ) -> List[Dict]:
        """
        Merge first page results with regular results, prioritizing first page content
        
        Args:
            first_page_results: Results from first pages
            regular_results: Regular search results
            query: Original query
            top_k: Number of results to return
            
        Returns:
            Merged and prioritized results
        """
        # Convert regular results to dict format
        regular_dict = {}
        for result in regular_results:
            regular_dict[result.doc_id] = {
                'doc_id': result.doc_id,
                'text': result.text,
                'metadata': result.metadata,
                'score': result.score,
                'semantic_score': result.semantic_score,
                'bm25_score': result.bm25_score,
                'rank': result.rank
            }
        
        # Merge results, prioritizing first page content
        merged_results = {}
        
        # Add first page results with boosted scores
        for fp_result in first_page_results:
            doc_id = fp_result['doc_id']
            
            # Check if this chunk contains professor information
            professor_relevance = self._calculate_professor_relevance(
                fp_result['text'], 
                query
            )
            
            # Boost score if professor information is found
            boosted_score = fp_result['score'] + professor_relevance
            
            merged_results[doc_id] = {
                **fp_result,
                'score': boosted_score,
                'professor_relevance': professor_relevance,
                'is_prioritized': True
            }
        
        # Add regular results that aren't already included
        for doc_id, result in regular_dict.items():
            if doc_id not in merged_results:
                merged_results[doc_id] = result
        
        # Sort by score (descending) and return top_k
        sorted_results = sorted(
            merged_results.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]
        
        # Update ranks
        for i, result in enumerate(sorted_results):
            result['rank'] = i + 1
        
        return sorted_results
    
    def _calculate_professor_relevance(self, text: str, query: str) -> float:
        """
        Calculate how relevant a text chunk is for professor queries
        
        Args:
            text: Text content to analyze
            query: Original query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        relevance_score = 0.0
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Check for professor title patterns
        for pattern in self.professor_title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                relevance_score += 0.5  # High boost for professor titles
                logger.info(f"Found professor title pattern: {matches}")
        
        # Check for course-related keywords
        course_keywords = [
            'cours', 'course', 'module', 'enseignement', 'teaching',
            'responsable', 'instructor', 'animé par', 'taught by'
        ]
        
        for keyword in course_keywords:
            if keyword in text_lower:
                relevance_score += 0.1
        
        # Check for contact information (emails, phone numbers, addresses)
        contact_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
            r'\b(email|mail|contact|bureau|office|téléphone|phone)\b',  # Contact keywords
            r'\b(coordonnées|contact\s+info)\b'  # Contact information keywords
        ]
        
        for pattern in contact_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                relevance_score += 0.2  # Boost for contact information
                logger.info(f"Found contact information: {matches[:3]}")  # Log first 3 matches
        
        # IMPORTANT: Check for specific course context in query
        # If query mentions specific course, boost relevance for matching course
        course_context_patterns = {
            'machine learning': ['machine learning', 'ml', 'apprentissage automatique'],
            'hadoop': ['hadoop', 'mapreduce'],
            'big data': ['big data', 'données massives'],
            'spark': ['spark', 'apache spark']
        }
        
        for course_name, course_terms in course_context_patterns.items():
            # Check if query mentions this course
            query_mentions_course = any(term in query_lower for term in course_terms)
            # Check if text is about this course
            text_about_course = any(term in text_lower for term in course_terms)
            
            if query_mentions_course and text_about_course:
                # Strong boost for matching course context
                relevance_score += 0.8
                logger.info(f"Course context match: query mentions {course_name}, text contains relevant content")
            elif query_mentions_course and not text_about_course:
                # Penalty for non-matching course context
                relevance_score -= 0.3
                logger.info(f"Course context mismatch: query mentions {course_name}, but text is about different course")
        
        # Check for query keywords
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2 and word in text_lower:
                relevance_score += 0.05
        
        # Normalize score to [0, 1]
        return max(0.0, min(relevance_score, 1.0))
    
    def extract_professor_names(self, text: str) -> List[str]:
        """
        Extract potential professor names from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of potential professor names
        """
        names = []
        
        for pattern in self.professor_title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the name (add spaces if needed for INPT format)
                clean_name = match.strip()
                if clean_name and len(clean_name) > 3:
                    # Handle names like "IyadLAHSEN" -> "Iyad LAHSEN"
                    if re.match(r'^[A-Z][a-z]+[A-Z][A-Z]+', clean_name):
                        # Find where lowercase ends and uppercase begins
                        for i in range(1, len(clean_name)):
                            if clean_name[i].isupper() and clean_name[i-1].islower():
                                clean_name = clean_name[:i] + ' ' + clean_name[i:]
                                break
                    names.append(clean_name)
        
        # Clean and deduplicate names
        cleaned_names = []
        for name in names:
            name = name.strip()
            if name and name not in cleaned_names and len(name) > 2:
                cleaned_names.append(name)
        
        return cleaned_names


# Test the professor query handler
if __name__ == "__main__":
    # This would require actual vector store and hybrid search instances
    print("ProfessorQueryHandler module loaded successfully")
    
    # Test pattern matching
    handler = ProfessorQueryHandler(None, None)
    
    test_queries = [
        "What is the name of this course's professor?",
        "Quel est le nom du professeur de ce cours?",
        "Who teaches this course?",
        "Qui enseigne ce module?",
        "What is machine learning?"  # Non-professor query
    ]
    
    for query in test_queries:
        is_prof_query = handler.is_professor_query(query)
        print(f"Query: '{query}' -> Professor query: {is_prof_query}")