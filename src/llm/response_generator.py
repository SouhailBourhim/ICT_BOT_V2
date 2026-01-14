"""
Générateur de réponses RAG combinant recherche et LLM
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
from loguru import logger

from ..config.settings import settings
from ..utils.query_enhancement import QueryEnhancer
from ..retrieval.professor_query_handler import ProfessorQueryHandler


@dataclass
class RAGResponse:
    """Structure d'une réponse RAG complète"""
    answer: str
    sources: List[Dict]
    confidence: float
    retrieved_chunks: List[Dict]
    metadata: Dict


class ResponseGenerator:
    """
    Générateur de réponses RAG
    Orchestre: Recherche -> Filtrage -> Génération -> Post-traitement
    """
    
    def __init__(
        self,
        hybrid_search,
        ollama_client,
        prompt_builder,
        min_confidence: float = 0.5,
        max_sources: int = 3,
        top_k_retrieval: int = 5
    ):
        """
        Initialise le générateur de réponses
        
        Args:
            hybrid_search: Instance de HybridSearchEngine
            ollama_client: Instance de OllamaClient
            prompt_builder: Instance de PromptBuilder
            min_confidence: Score minimum pour utiliser un chunk
            max_sources: Nombre max de sources dans la réponse
            top_k_retrieval: Nombre de chunks à récupérer
        """
        self.hybrid_search = hybrid_search
        self.ollama_client = ollama_client
        self.prompt_builder = prompt_builder
        self.min_confidence = min_confidence
        self.max_sources = max_sources
        self.top_k_retrieval = top_k_retrieval
        
        # Initialize professor query handler
        self.professor_handler = ProfessorQueryHandler(
            vector_store=hybrid_search.vector_store,
            hybrid_search=hybrid_search
        )
        
        logger.info("ResponseGenerator initialisé")
    
    def _is_follow_up_question(self, question: str, conversation_history: List[Dict]) -> bool:
        """
        Détecte si la question est une question de suivi liée au contexte précédent
        
        Args:
            question: Question actuelle
            conversation_history: Historique de conversation
            
        Returns:
            True si c'est une question de suivi, False sinon
        """
        if not conversation_history or len(conversation_history) < 2:
            return False
        
        question_lower = question.lower().strip()
        
        # 1. Indicateurs de question de suivi (pronoms, références)
        follow_up_indicators = [
            # Pronoms démonstratifs
            r'\b(cela|ça|ce|cette|cet|ces)\b',
            # Pronoms personnels en début
            r'^(il|elle|ils|elles|le|la|les|lui|leur)\b',
            # Questions courtes de clarification
            r'^(et|mais|donc|alors|aussi|également)\b',
            # Références directes
            r'\b(même|aussi|également|pareil)\b',
            # Questions très courtes (< 4 mots souvent des suivis)
            r'^\w+\s+\w+\s*\??$',
            # "Et pour..." / "Et le..."
            r'^et\s+(pour|le|la|les)\b',
            # "Plus de détails" / "Explique plus"
            r'\b(plus|davantage|encore|autre)\s+(de|d\'|sur)\b',
            # Questions avec "?" seulement
            r'^\w+\s*\?$'
        ]
        
        for pattern in follow_up_indicators:
            if re.search(pattern, question_lower):
                logger.info(f"🔗 Question de suivi détectée (pattern: {pattern})")
                return True
        
        # 2. Extraire les mots-clés de la dernière question
        if len(conversation_history) >= 2:
            last_user_msg = None
            for msg in reversed(conversation_history):
                if msg.get('role') == 'user':
                    last_user_msg = msg.get('content', '')
                    break
            
            if last_user_msg:
                # Extraire les noms propres et termes techniques (mots en majuscules ou avec acronymes)
                last_keywords = set(re.findall(r'\b[A-Z]{2,}\b|\b[A-Z][a-z]+\b', last_user_msg))
                current_keywords = set(re.findall(r'\b[A-Z]{2,}\b|\b[A-Z][a-z]+\b', question))
                
                # Si partage des mots-clés importants
                if last_keywords and current_keywords:
                    overlap = last_keywords.intersection(current_keywords)
                    if overlap:
                        logger.info(f"🔗 Question de suivi détectée (mots-clés communs: {overlap})")
                        return True
        
        # 3. Question complète et indépendante (contient verbe + sujet complet)
        # Si la question est longue et bien formée, c'est probablement une nouvelle question
        if len(question.split()) > 6:
            # Vérifier si contient des mots interrogatifs complets
            complete_question_patterns = [
                r'\b(qu\'est-ce que|c\'est quoi|quelle est|quel est|quels sont|quelles sont)\b',
                r'\b(comment|pourquoi|où|quand|combien)\b.*\b(le|la|les|un|une|des)\b',
                r'\b(expliquer|définir|décrire|présenter)\b.*\b(le|la|les)\b'
            ]
            
            for pattern in complete_question_patterns:
                if re.search(pattern, question_lower):
                    logger.info(f"❌ Question indépendante détectée (question complète)")
                    return False
        
        # Par défaut, si aucun indicateur fort, considérer comme indépendante
        return False
    
    def generate_response(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        filters: Optional[Dict] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> RAGResponse:
        """
        Génère une réponse complète à une question
        
        Args:
            question: Question de l'utilisateur
            conversation_history: Historique de conversation
            filters: Filtres sur les documents
            temperature: Température du LLM
            stream: Mode streaming
            
        Returns:
            RAGResponse avec réponse et métadonnées
        """
        logger.info(f"🎯 Génération de réponse pour: '{question[:50]}...'")

        # 0. Query enhancement (optional)
        search_query = question
        word_count = len(question.split())
        if (
            settings.ENABLE_QUERY_EXPANSION
            or settings.ENABLE_SPELLING_CORRECTION
        ) and (
            word_count <= settings.QUERY_ENHANCEMENT_MAX_WORDS
            or len(question) <= settings.QUERY_ENHANCEMENT_MIN_CHARS
        ):
            enhancer = QueryEnhancer(ollama_client=self.ollama_client)
            enhanced_query = enhancer.enhance(question)
            if enhanced_query:
                search_query = enhanced_query
        
        # 1. Détection intelligente de question de suivi
        use_history = False
        if conversation_history:
            use_history = self._is_follow_up_question(question, conversation_history)
            if not use_history:
                logger.info("🆕 Question indépendante détectée - historique ignoré")
        
        # 2. Recherche hybride
        search_results = self.hybrid_search.search(
            query=search_query,
            top_k=self.top_k_retrieval,
            filters=filters
        )
        # 2. Recherche hybride avec gestion spécialisée pour les requêtes professeur
        if self.professor_handler.is_professor_query(question):
            logger.info("🎓 Requête professeur détectée - utilisation du handler spécialisé")
            search_results_raw = self.professor_handler.handle_professor_query(
                query=search_query,
                top_k=self.top_k_retrieval,
                filters=filters
            )
            # Convert to SearchResult objects for compatibility
            from ..retrieval.hybrid_search import SearchResult
            search_results = []
            for result in search_results_raw:
                search_results.append(SearchResult(
                    doc_id=result['doc_id'],
                    text=result['text'],
                    metadata=result['metadata'],
                    score=result['score'],
                    semantic_score=result.get('semantic_score', result['score']),
                    bm25_score=result.get('bm25_score', 0.0),
                    rank=result['rank']
                ))
        else:
            search_results = self.hybrid_search.search(
                query=search_query,
                top_k=self.top_k_retrieval,
                filters=filters
            )
        
        if not search_results:
            return self._generate_no_context_response(question)
        
        # 3. Filtrage par confiance
        relevant_chunks = self._filter_by_confidence(search_results)
        
        if not relevant_chunks:
            return self._generate_low_confidence_response(question, search_results)
        
        # 4. Construction du prompt (avec ou sans historique selon détection)
        if self.professor_handler.is_professor_query(question):
            # Check if it's specifically asking for contact information
            if self.professor_handler.is_professor_contact_query(question):
                # Utiliser le prompt spécialisé pour les informations de contact
                system_prompt, user_prompt = self.prompt_builder.build_professor_contact_prompt(
                    question=question,
                    context_chunks=relevant_chunks
                )
            else:
                # Utiliser le prompt spécialisé pour les requêtes professeur générales
                system_prompt, user_prompt = self.prompt_builder.build_professor_prompt(
                    question=question,
                    context_chunks=relevant_chunks
                )
        elif use_history:
            system_prompt, user_prompt = self.prompt_builder.build_conversation_prompt(
                question=question,
                context_chunks=relevant_chunks,
                conversation_history=conversation_history
            )
        else:
            system_prompt, user_prompt = self.prompt_builder.build_rag_prompt(
                question=question,
                context_chunks=relevant_chunks
            )
        
        # 4. Génération de la réponse
        try:
            if stream:
                answer = self._generate_streaming(system_prompt, user_prompt, temperature)
            else:
                answer = self.ollama_client.generate(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=temperature,
                    max_tokens=2000
                )
            
            logger.success("✅ Réponse générée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return self._generate_error_response(question, str(e))
        
        # 5. Post-traitement
        answer = self._post_process_answer(answer)
        
        # 6. Extraction des sources
        sources = self._extract_sources(relevant_chunks[:self.max_sources])
        
        # 7. Calcul de confiance
        confidence, confidence_breakdown = self._calculate_confidence(
            search_results, answer, question, relevant_chunks
        )
        
        # 8. Construction de la réponse finale
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            retrieved_chunks=relevant_chunks,
            metadata={
                'num_chunks_retrieved': len(search_results),
                'num_chunks_used': len(relevant_chunks),
                'question': question,
                'search_query': search_query,
                'has_conversation_history': conversation_history is not None,
                'used_conversation_history': use_history,
                'confidence_breakdown': confidence_breakdown
            }
        )
    
    def generate_response_with_citations(
        self,
        question: str,
        **kwargs
    ) -> RAGResponse:
        """
        Génère une réponse avec citations inline
        Format: "L'IoT est... [1] Les capteurs... [2]"
        """
        response = self.generate_response(question, **kwargs)
        
        # Ajouter les numéros de citation
        answer_with_citations = self._add_inline_citations(
            response.answer,
            response.sources
        )
        
        response.answer = answer_with_citations
        return response
    
    def _filter_by_confidence(self, results: List) -> List[Dict]:
        """Filtre les résultats par score de confiance"""
        filtered = []
        
        for result in results:
            if result.score >= self.min_confidence:
                clean_content = ""
                if isinstance(result.metadata, dict):
                    clean_content = result.metadata.get('clean_content', '')
                display_text = result.text
                chunk_text = clean_content or display_text
                filtered.append({
                    'text': chunk_text,
                    'clean_content': clean_content,
                    'raw_text': display_text,
                    'metadata': result.metadata,
                    'score': result.score
                })
        
        logger.info(f"📊 {len(filtered)}/{len(results)} chunks retenus (seuil: {self.min_confidence})")
        return filtered
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extrait les sources uniques des chunks"""
        sources = {}
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            source_name = metadata.get('filename', 'Source inconnue')
            
            if source_name not in sources:
                sources[source_name] = {
                    'name': source_name,
                    'pages': set(),
                    'score': chunk.get('score', 0)
                }
            
            # Ajouter le numéro de page s'il existe
            if 'page_number' in metadata:
                sources[source_name]['pages'].add(metadata['page_number'])
        
        # Conversion en liste
        sources_list = []
        for source_name, info in sources.items():
            pages = sorted(list(info['pages']))
            sources_list.append({
                'name': source_name,
                'pages': pages,
                'score': info['score']
            })
        
        # Tri par pertinence
        sources_list.sort(key=lambda x: x['score'], reverse=True)
        
        return sources_list
    
    def _calculate_confidence(
        self,
        search_results: List,
        answer: str,
        question: str,
        relevant_chunks: List[Dict]
    ) -> tuple[float, Dict[str, float]]:
        """
        Calcule un score de confiance global
        Basé sur: scores de recherche, couverture des mots-clés, longueur réponse
        """
        if not search_results:
            return 0.0, {"retrieval_strength": 0.0, "coverage": 0.0, "length_score": 0.0}

        normalized_semantic = self._normalize_component_scores(
            [r.semantic_score or r.score for r in search_results]
        )
        normalized_bm25 = self._normalize_component_scores(
            [r.bm25_score for r in search_results]
        )

        combined_scores = []
        for semantic_score, bm25_score in zip(normalized_semantic, normalized_bm25):
            if bm25_score > 0:
                combined = (semantic_score + bm25_score) / 2
            else:
                combined = semantic_score
            combined_scores.append(combined)

        top_k = min(5, len(combined_scores))
        retrieval_strength = sum(combined_scores[:top_k]) / top_k if top_k else 0.0
        coverage = self._compute_query_coverage(question, relevant_chunks)
        length_score = min(len(answer) / 300, 1.0)

        # Pénalité si "je ne sais pas" dans la réponse
        uncertainty_penalty = 0.2 if any(phrase in answer.lower() for phrase in [
            "je ne sais pas",
            "je n'ai pas",
            "informations insuffisantes",
            "pas dans les documents"
        ]) else 0.0

        confidence = (
            retrieval_strength * 0.5
            + coverage * 0.3
            + length_score * 0.2
            - uncertainty_penalty
        )

        return max(0.0, min(1.0, confidence)), {
            "retrieval_strength": retrieval_strength,
            "coverage": coverage,
            "length_score": length_score,
            "uncertainty_penalty": uncertainty_penalty
        }

    def _normalize_component_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores between 0 and 1."""
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score - min_score <= 0:
            return [0.0 for _ in scores]
        return [(score - min_score) / (max_score - min_score) for score in scores]

    def _compute_query_coverage(self, question: str, chunks: List[Dict]) -> float:
        """Compute how many query keywords appear in retrieved chunks."""
        keywords = [w for w in re.findall(r"\w+", question.lower()) if len(w) > 3]
        if not keywords:
            return 0.0
        corpus_text = " ".join(
            chunk.get('clean_content')
            or chunk.get('metadata', {}).get('clean_content')
            or chunk.get('text', '')
            for chunk in chunks
        ).lower()
        if not corpus_text:
            return 0.0
        matched = sum(1 for word in set(keywords) if word in corpus_text)
        return matched / len(set(keywords))
    
    def _post_process_answer(self, answer: str) -> str:
        """Post-traitement de la réponse"""
        # Nettoyer les espaces multiples
        answer = re.sub(r'\s+', ' ', answer)
        
        # Nettoyer les sauts de ligne multiples
        answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer)
        
        # Trim
        answer = answer.strip()
        
        return answer
    
    def _add_inline_citations(self, answer: str, sources: List[Dict]) -> str:
        """Ajoute des citations inline numérotées"""
        # Créer la liste de références
        references = "\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            pages = f" (pages {', '.join(map(str, source['pages']))})" if source['pages'] else ""
            references += f"[{i}] {source['name']}{pages}\n"
        
        return answer + references
    
    def _generate_streaming(self, system: str, user: str, temperature: float):
        """Génération en mode streaming (non implémenté ici, voir interface)"""
        # Pour le streaming, utiliser directement dans l'UI Streamlit
        return self.ollama_client.generate(
            prompt=user,
            system=system,
            temperature=temperature,
            stream=False
        )
    
    def _generate_no_context_response(self, question: str) -> RAGResponse:
        """Réponse quand aucun contexte n'est trouvé"""
        answer = f"""Je n'ai pas trouvé d'informations pertinentes dans les documents disponibles pour répondre à votre question: "{question}".

Suggestions:
- Reformulez votre question différemment
- Vérifiez l'orthographe
- Assurez-vous que le sujet est couvert dans les documents chargés

Si vous pensez que cette information devrait être disponible, contactez votre enseignant."""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            confidence=0.0,
            retrieved_chunks=[],
            metadata={'error': 'no_context_found'}
        )
    
    def _generate_low_confidence_response(self, question: str, results: List) -> RAGResponse:
        """Réponse quand la confiance est trop faible"""
        answer = f"""J'ai trouvé quelques informations mais elles ne semblent pas suffisamment pertinentes pour répondre avec certitude à: "{question}".

Les documents consultés traitent de sujets connexes mais pas exactement de votre question. Pourriez-vous reformuler ou préciser ce que vous recherchez ?"""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            confidence=0.3,
            retrieved_chunks=[],
            metadata={'error': 'low_confidence'}
        )
    
    def _generate_error_response(self, question: str, error: str) -> RAGResponse:
        """Réponse en cas d'erreur"""
        answer = f"""Une erreur s'est produite lors de la génération de la réponse.

Erreur: {error}

Veuillez réessayer ou contacter le support technique."""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            confidence=0.0,
            retrieved_chunks=[],
            metadata={'error': error}
        )
    
    def generate_follow_up_questions(self, question: str, answer: str) -> List[str]:
        """Génère des questions de suivi pertinentes"""
        template = self.prompt_builder.templates.FOLLOW_UP_QUESTIONS
        system, user = template.format(question=question, answer=answer)
        
        try:
            response = self.ollama_client.generate(
                prompt=user,
                system=system,
                temperature=0.8,
                max_tokens=300
            )
            
            # Extraction des questions (format numéroté)
            questions = re.findall(r'\d+\.\s*(.+?)(?:\n|$)', response)
            return questions[:3]
            
        except Exception as e:
            logger.error(f"Erreur génération questions suivi: {e}")
            return []


# Test du générateur
if __name__ == "__main__":
    from hybrid_search import HybridSearchEngine
    from ollama_client import OllamaClient
    from prompt_templates import PromptBuilder
    from vector_store import VectorStore
    
    # Setup (simulé)
    print("Initialisation du système RAG...")
    
    # Note: Nécessite un setup complet pour fonctionner
    # Voir script d'intégration principal
