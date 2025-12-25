#!/usr/bin/env python3
"""
Système d'évaluation RAG complet
Mesure: Retrieval, Generation, et End-to-End metrics
"""

import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import PromptBuilder
from src.llm.response_generator import ResponseGenerator
import time
from typing import Dict, List
import re


class RAGEvaluator:
    """Évaluateur de système RAG"""
    
    def __init__(self, response_gen, test_dataset_path: str):
        self.response_gen = response_gen
        with open(test_dataset_path, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
        self.results = []
    
    def evaluate_all(self):
        """Évalue tous les cas de test"""
        print(f"\n{'='*80}")
        print(f"🧪 ÉVALUATION RAG - {settings.OLLAMA_MODEL}")
        print(f"{'='*80}\n")
        print(f"📊 {len(self.test_data['test_cases'])} cas de test\n")
        
        for test_case in self.test_data['test_cases']:
            result = self.evaluate_single(test_case)
            self.results.append(result)
            self.print_result(result)
        
        self.print_summary()
    
    def evaluate_single(self, test_case: Dict) -> Dict:
        """Évalue un cas de test"""
        question = test_case['question']
        
        # Génération de la réponse
        start = time.time()
        response = self.response_gen.generate_response(
            question=question,
            temperature=settings.LLM_TEMPERATURE
        )
        duration = time.time() - start
        
        answer = response.answer.lower()
        
        # Métriques
        metrics = {
            'test_id': test_case['id'],
            'question': question,
            'category': test_case['category'],
            'answer': response.answer,
            'duration': duration,
            'confidence': response.confidence,
            'chunks_used': response.metadata['num_chunks_used'],
            
            # Keyword Coverage
            'keyword_coverage': self._calculate_keyword_coverage(
                answer, test_case['expected_keywords']
            ),
            
            # Concept Coverage
            'concept_coverage': self._calculate_concept_coverage(
                answer, test_case['expected_concepts']
            ),
            
            # Hallucination Check
            'has_hallucinations': self._check_hallucinations(
                answer, test_case['should_not_contain']
            ),
            
            # Answer Length
            'answer_length': len(response.answer),
            
            # Response Quality Score
            'quality_score': 0.0
        }
        
        # Calcul du score de qualité global
        metrics['quality_score'] = self._calculate_quality_score(metrics)
        
        return metrics
    
    def _calculate_keyword_coverage(self, answer: str, keywords: List[str]) -> float:
        """% de mots-clés attendus présents dans la réponse"""
        if not keywords:
            return 1.0
        found = sum(1 for kw in keywords if kw.lower() in answer)
        return found / len(keywords)
    
    def _calculate_concept_coverage(self, answer: str, concepts: List[str]) -> float:
        """% de concepts attendus présents dans la réponse"""
        if not concepts:
            return 1.0
        found = sum(1 for concept in concepts if concept.lower() in answer)
        return found / len(concepts)
    
    def _check_hallucinations(self, answer: str, forbidden_words: List[str]) -> bool:
        """Vérifie la présence de mots interdits (hallucinations)"""
        return any(word.lower() in answer for word in forbidden_words)
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Score de qualité global (0-100)"""
        score = 0.0
        
        # Keyword coverage (30%)
        score += metrics['keyword_coverage'] * 30
        
        # Concept coverage (30%)
        score += metrics['concept_coverage'] * 30
        
        # No hallucinations (20%)
        if not metrics['has_hallucinations']:
            score += 20
        
        # Confidence (10%)
        score += metrics['confidence'] * 10
        
        # Answer length penalty (10%)
        # Optimal: 150-400 caractères
        length = metrics['answer_length']
        if 150 <= length <= 400:
            score += 10
        elif 100 <= length < 150 or 400 < length <= 600:
            score += 5
        
        return round(score, 1)
    
    def print_result(self, result: Dict):
        """Affiche le résultat d'un test"""
        print(f"\n{'─'*80}")
        print(f"Test #{result['test_id']}: {result['question']}")
        print(f"Catégorie: {result['category']}")
        print(f"{'─'*80}")
        
        print(f"\n💬 Réponse ({result['answer_length']} chars):")
        print(f"   {result['answer'][:200]}{'...' if len(result['answer']) > 200 else ''}")
        
        print(f"\n📊 Métriques:")
        print(f"   • Score qualité: {result['quality_score']}/100")
        print(f"   • Keyword coverage: {result['keyword_coverage']:.0%}")
        print(f"   • Concept coverage: {result['concept_coverage']:.0%}")
        print(f"   • Hallucinations: {'❌ OUI' if result['has_hallucinations'] else '✅ NON'}")
        print(f"   • Confiance: {result['confidence']:.0%}")
        print(f"   • Temps: {result['duration']:.1f}s")
        print(f"   • Chunks: {result['chunks_used']}")
    
    def print_summary(self):
        """Affiche le résumé global"""
        print(f"\n{'='*80}")
        print(f"📈 RÉSUMÉ GLOBAL")
        print(f"{'='*80}\n")
        
        # Score moyen
        avg_quality = sum(r['quality_score'] for r in self.results) / len(self.results)
        print(f"🎯 Score qualité moyen: {avg_quality:.1f}/100")
        
        # Keyword coverage moyen
        avg_keyword = sum(r['keyword_coverage'] for r in self.results) / len(self.results)
        print(f"📝 Keyword coverage moyen: {avg_keyword:.0%}")
        
        # Concept coverage moyen
        avg_concept = sum(r['concept_coverage'] for r in self.results) / len(self.results)
        print(f"🧠 Concept coverage moyen: {avg_concept:.0%}")
        
        # Taux d'hallucinations
        hallucination_rate = sum(1 for r in self.results if r['has_hallucinations']) / len(self.results)
        print(f"⚠️  Taux d'hallucinations: {hallucination_rate:.0%}")
        
        # Confiance moyenne
        avg_confidence = sum(r['confidence'] for r in self.results) / len(self.results)
        print(f"💪 Confiance moyenne: {avg_confidence:.0%}")
        
        # Temps moyen
        avg_time = sum(r['duration'] for r in self.results) / len(self.results)
        print(f"⏱️  Temps moyen: {avg_time:.1f}s")
        
        # Longueur moyenne
        avg_length = sum(r['answer_length'] for r in self.results) / len(self.results)
        print(f"📏 Longueur moyenne: {avg_length:.0f} caractères")
        
        # Par catégorie
        print(f"\n📊 Par catégorie:")
        categories = {}
        for r in self.results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r['quality_score'])
        
        for cat, scores in categories.items():
            avg = sum(scores) / len(scores)
            print(f"   • {cat}: {avg:.1f}/100 ({len(scores)} tests)")
        
        # Grade final
        print(f"\n{'='*80}")
        grade = self._get_grade(avg_quality)
        print(f"🏆 NOTE FINALE: {grade} ({avg_quality:.1f}/100)")
        print(f"{'='*80}\n")
    
    def _get_grade(self, score: float) -> str:
        """Convertit le score en note"""
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Très bien)"
        elif score >= 70:
            return "B (Bien)"
        elif score >= 60:
            return "C (Acceptable)"
        elif score >= 50:
            return "D (Passable)"
        else:
            return "F (Insuffisant)"
    
    def save_results(self, output_path: str):
        """Sauvegarde les résultats en JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'model': settings.OLLAMA_MODEL,
                'temperature': settings.LLM_TEMPERATURE,
                'results': self.results,
                'summary': {
                    'avg_quality_score': sum(r['quality_score'] for r in self.results) / len(self.results),
                    'avg_keyword_coverage': sum(r['keyword_coverage'] for r in self.results) / len(self.results),
                    'avg_concept_coverage': sum(r['concept_coverage'] for r in self.results) / len(self.results),
                    'hallucination_rate': sum(1 for r in self.results if r['has_hallucinations']) / len(self.results),
                    'avg_confidence': sum(r['confidence'] for r in self.results) / len(self.results),
                    'avg_duration': sum(r['duration'] for r in self.results) / len(self.results),
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ Résultats sauvegardés: {output_path}")


def main():
    """Point d'entrée principal"""
    # Init système RAG
    print("📦 Initialisation du système RAG...")
    
    vector_store = VectorStore(
        persist_directory=str(settings.CHROMA_PERSIST_DIR),
        collection_name=settings.CHROMA_COLLECTION_NAME
    )
    
    hybrid_search = HybridSearchEngine(
        vector_store=vector_store,
        semantic_weight=settings.SEMANTIC_WEIGHT,
        bm25_weight=settings.BM25_WEIGHT
    )
    
    # Index BM25
    doc_count = vector_store.count()
    all_docs = vector_store.peek(limit=doc_count)
    if all_docs and all_docs.get('documents'):
        documents = [
            {'id': doc_id, 'text': text, 'metadata': meta}
            for doc_id, text, meta in zip(
                all_docs['ids'], all_docs['documents'], all_docs['metadatas']
            )
        ]
        hybrid_search.index_documents(documents)
    
    ollama = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT
    )
    
    prompt_builder = PromptBuilder()
    
    response_gen = ResponseGenerator(
        hybrid_search=hybrid_search,
        ollama_client=ollama,
        prompt_builder=prompt_builder,
        min_confidence=settings.SIMILARITY_THRESHOLD,
        max_sources=settings.RERANK_TOP_K,
        top_k_retrieval=settings.TOP_K_RETRIEVAL
    )
    
    # Évaluation
    test_dataset_path = Path(__file__).parent / "test_dataset.json"
    evaluator = RAGEvaluator(response_gen, str(test_dataset_path))
    evaluator.evaluate_all()
    
    # Sauvegarde
    output_path = Path(__file__).parent / f"evaluation_results_{settings.OLLAMA_MODEL.replace(':', '_')}.json"
    evaluator.save_results(str(output_path))


if __name__ == "__main__":
    main()
