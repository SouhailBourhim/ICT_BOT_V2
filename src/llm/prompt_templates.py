"""
Templates de prompts en français pour le système RAG INPT
"""
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Structure d'un template de prompt"""
    system: str
    user: str
    
    def format(self, **kwargs) -> tuple[str, str]:
        """Formate le template avec les variables"""
        return (
            self.system.format(**kwargs),
            self.user.format(**kwargs)
        )


class PromptTemplates:
    """Collection de templates pour différents cas d'usage"""
    
    # Template principal RAG
    RAG_QA = PromptTemplate(
        system="""Tu es un assistant qui extrait des informations UNIQUEMENT du contexte fourni.

RÈGLES STRICTES:
1. Cite UNIQUEMENT les informations présentes dans le contexte
2. Si le contexte mentionne des noms (algorithmes, méthodes, techniques), liste-les
3. N'invente JAMAIS d'exemples d'application (prix, photos, transport, etc.)
4. Si tu ne trouves pas l'info, dis "Information non trouvée dans le document"
5. Maximum 3-4 phrases courtes

DISTINCTION IMPORTANTE:
- Noms d'algorithmes/méthodes dans le contexte → CITE-LES
- Exemples d'application non dans le contexte → N'INVENTE PAS

ABSOLUMENT INTERDIT:
- Inventer des cas d'usage (prédire prix, classifier photos, etc.)
- Utiliser tes connaissances générales
- Ajouter des détails non présents dans le contexte""",
        
        user="""CONTEXTE EXTRAIT DU COURS:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Réponds DIRECTEMENT à la question
- Si c'est une liste/énumération, donne une brève description de chaque élément
- Si c'est une définition, donne 3-4 phrases complètes
- Mentionne toujours les concepts clés
- Ne mentionne PAS les numéros de documents
- Format clair et structuré

RÉPONSE DIRECTE:"""
    )
    
    # Template pour conversations avec historique
    RAG_CONVERSATION = PromptTemplate(
        system="""Tu es un assistant éducatif pour les étudiants Smart ICT de l'INPT.

Tu maintiens une conversation cohérente en tenant compte de l'historique.

Directives:
- Reste dans le contexte de la conversation
- Fais référence aux échanges précédents si pertinent
- Utilise les documents fournis comme base de connaissance
- Cite toujours tes sources
- Sois pédagogique et encourageant""",
        
        user="""Historique de conversation:
{conversation_history}

Contexte (documents pertinents):
{context}

Question actuelle: {question}

Réponse:"""
    )
    
    # Template pour synthèse de documents
    DOCUMENT_SUMMARY = PromptTemplate(
        system="""Tu es un expert en synthèse de documents académiques pour l'INPT.

Ton rôle est de créer des résumés clairs et structurés.""",
        
        user="""Document à résumer:
{document_text}

Métadonnées:
- Titre: {title}
- Source: {source}
- Pages: {pages}

Crée un résumé structuré avec:
1. Idées principales (3-5 points)
2. Concepts clés
3. Applications pratiques

Résumé:"""
    )
    
    # Template pour extraction de concepts
    CONCEPT_EXTRACTION = PromptTemplate(
        system="""Tu es un expert en extraction de concepts académiques.

Identifie les concepts clés, définitions et relations dans le texte fourni.""",
        
        user="""Texte:
{text}

Extrais:
1. Concepts principaux (liste)
2. Définitions importantes
3. Relations entre concepts
4. Mots-clés techniques

Format JSON:
{
  "concepts": [...],
  "definitions": {...},
  "keywords": [...]
}

Résultat:"""
    )
    
    # Template pour questions de suivi
    FOLLOW_UP_QUESTIONS = PromptTemplate(
        system="""Tu es un assistant pédagogique qui génère des questions de suivi pertinentes.""",
        
        user="""Question initiale: {question}
Réponse donnée: {answer}

Génère 3 questions de suivi pertinentes qui approfondiraient la compréhension de l'étudiant.

Questions:
1.
2.
3."""
    )
    
    # Template pour reformulation de requêtes
    QUERY_REFINEMENT = PromptTemplate(
        system="""Tu es un expert en reformulation de requêtes pour améliorer la recherche.""",
        
        user="""Requête originale: {query}

Reformule cette requête pour la rendre plus précise et efficace pour une recherche documentaire.
Génère 2-3 variantes qui capturent différents aspects de la question.

Variantes:
1.
2.
3."""
    )
    
    # Template pour vérification de pertinence
    RELEVANCE_CHECK = PromptTemplate(
        system="""Tu évalues la pertinence d'un passage par rapport à une question.""",
        
        user="""Question: {question}

Passage:
{passage}

Ce passage est-il pertinent pour répondre à la question?
Réponds par OUI ou NON suivi d'une brève justification.

Évaluation:"""
    )
    
    # Template pour explication étape par étape
    STEP_BY_STEP = PromptTemplate(
        system="""Tu es un tuteur pédagogique qui explique les concepts étape par étape.

Décompose les explications complexes en étapes simples et progressives.""",
        
        user="""Concept à expliquer: {concept}

Contexte:
{context}

Fournis une explication étape par étape adaptée au niveau {level} (débutant/intermédiaire/avancé).

Explication:

Étape 1:
...

Étape 2:
...

Conclusion:
..."""
    )
    
    # Template pour génération d'exercices
    EXERCISE_GENERATION = PromptTemplate(
        system="""Tu es un enseignant qui crée des exercices pratiques basés sur le contenu du cours.""",
        
        user="""Contenu du cours:
{content}

Sujet: {topic}

Génère 3 exercices pratiques de difficulté progressive (facile, moyen, difficile).
Pour chaque exercice, fournis:
- L'énoncé
- Des indices
- La solution attendue

Exercices:"""
    )
    
    # Template pour correction/feedback
    FEEDBACK_GENERATION = PromptTemplate(
        system="""Tu es un enseignant bienveillant qui donne du feedback constructif.""",
        
        user="""Question: {question}
Réponse correcte attendue: {correct_answer}
Réponse de l'étudiant: {student_answer}

Fournis un feedback:
1. Ce qui est correct
2. Ce qui doit être amélioré
3. Suggestions pour progresser

Feedback:"""
    )


class PromptBuilder:
    """Constructeur de prompts avec gestion du contexte"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict],
        max_context_length: int = 2000
    ) -> tuple[str, str]:
        """
        Construit un prompt RAG avec contexte
        
        Args:
            question: Question de l'utilisateur
            context_chunks: Liste de chunks pertinents
            max_context_length: Longueur max du contexte
            
        Returns:
            (system_prompt, user_prompt)
        """
        # Construction du contexte
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('text', '')
            chunk_metadata = chunk.get('metadata', {})
            
            # Formatage du chunk avec métadonnées
            source = chunk_metadata.get('filename', 'Document inconnu')
            page = chunk_metadata.get('page_number', '')
            page_info = f", page {page}" if page else ""
            
            chunk_formatted = f"\n[Document {i}: {source}{page_info}]\n{chunk_text}\n"
            
            # Vérifier la longueur
            if current_length + len(chunk_formatted) > max_context_length:
                break
            
            context_parts.append(chunk_formatted)
            current_length += len(chunk_formatted)
        
        context = "\n---\n".join(context_parts)
        
        # Formater le template
        return self.templates.RAG_QA.format(
            context=context,
            question=question
        )
    
    def build_conversation_prompt(
        self,
        question: str,
        context_chunks: List[Dict],
        conversation_history: List[Dict],
        max_history: int = 5
    ) -> tuple[str, str]:
        """
        Construit un prompt avec historique de conversation
        
        Args:
            question: Question actuelle
            context_chunks: Chunks pertinents
            conversation_history: Historique [{role, content}]
            max_history: Nombre max de messages d'historique
            
        Returns:
            (system_prompt, user_prompt)
        """
        # Formater l'historique (derniers messages)
        history_text = ""
        for msg in conversation_history[-max_history:]:
            role = "Étudiant" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n\n"
        
        # Contexte documentaire
        context = self._format_context(context_chunks, max_length=2000)
        
        return self.templates.RAG_CONVERSATION.format(
            conversation_history=history_text,
            context=context,
            question=question
        )
    
    def _format_context(self, chunks: List[Dict], max_length: int) -> str:
        """Formate les chunks en contexte"""
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            text = chunk.get('text', '')
            if current_length + len(text) > max_length:
                break
            context_parts.append(text)
            current_length += len(text)
        
        return "\n\n---\n\n".join(context_parts)


# Test des templates
if __name__ == "__main__":
    builder = PromptBuilder()
    
    # Exemple de chunks
    chunks = [
        {
            'text': "L'IoT (Internet des Objets) désigne l'interconnexion d'objets physiques via Internet.",
            'metadata': {'filename': 'cours_iot.pdf', 'page_number': 1}
        },
        {
            'text': "Les capteurs IoT collectent des données environnementales en temps réel.",
            'metadata': {'filename': 'cours_iot.pdf', 'page_number': 2}
        }
    ]
    
    # Construction d'un prompt RAG
    system, user = builder.build_rag_prompt(
        question="Qu'est-ce que l'IoT ?",
        context_chunks=chunks
    )
    
    print("=== SYSTEM PROMPT ===")
    print(system)
    print("\n=== USER PROMPT ===")
    print(user)