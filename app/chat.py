"""
Interface Streamlit principale pour l'Assistant RAG INPT
"""
import streamlit as st
from pathlib import Path
import sys

# Ajout du path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.document_processing.parser import DocumentParser
from src.document_processing.chunker import SemanticChunker
from src.document_processing.embedding_generator import EmbeddingGenerator
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import PromptBuilder
from src.llm.response_generator import ResponseGenerator
from src.conversation.manager import ConversationManager
from app.components.math_renderer import render_math_content

from datetime import datetime
from loguru import logger
import re


def render_math_content_old(text: str):
    """
    Rend le contenu avec support LaTeX pour les formules mathématiques.
    Détecte plusieurs formats et nettoie les erreurs de formatage.
    """
    # 0. Nettoyer les caractères Unicode bizarres et doublons
    text = re.sub(r'Y\^iY\^i​', r'\\hat{Y}_i', text)
    text = re.sub(r'YiYi​', r'Y_i', text)
    text = re.sub(r'nnest', r'$n$ est', text)
    
    # 1. Remplacer les formules entre crochets [ ... ] par $$ ... $$
    text = re.sub(r'\[\s*([^\]]+?)\s*\]', r'$$\1$$', text)
    
    # 2. Remplacer \( ... \) et \[ ... \] par $$ ... $$
    text = re.sub(r'\\\(\s*([^)]+?)\s*\\\)', r'$$\1$$', text)
    text = re.sub(r'\\\[\s*([^\]]+?)\s*\\\]', r'$$\1$$', text)
    
    # 3. Détecter les formules qui commencent par \text{ ou \frac{ avec =
    # Pattern plus agressif pour capturer toutes les formules
    latex_equation_pattern = r'(\\(?:text|frac|sum|int|sqrt|hat)\{[^}]*\}[^a-zA-Z\n]*?(?:=|\\sum|\\int|\\frac)[^\n]*?)(?=\s*(?:où|Où|Cette|Pour|La|Le|\.|,|\n|$))'
    
    def wrap_latex(match):
        formula = match.group(1).strip()
        if not formula.startswith('$$'):
            return f'$$\n{formula}\n$$'
        return formula
    
    text = re.sub(latex_equation_pattern, wrap_latex, text, flags=re.MULTILINE)
    
    # 4. Diviser le texte en parties: texte normal et formules
    parts = re.split(r'(\$\$.*?\$\$)', text, flags=re.DOTALL)
    
    for part in parts:
        if part.startswith('$$') and part.endswith('$$'):
            # C'est une formule LaTeX
            formula = part[2:-2].strip()
            # Nettoyer la formule
            formula = formula.replace('\\', '\\')  # Normaliser les backslashes
            try:
                st.latex(formula)
            except Exception as e:
                # Si erreur LaTeX, afficher comme code
                st.code(formula, language='latex')
        elif part.strip():
            # C'est du texte normal
            st.markdown(part)


# Configuration de la page
st.set_page_config(
    page_title=settings.STREAMLIT_PAGE_TITLE,
    page_icon=settings.STREAMLIT_PAGE_ICON,
    layout=settings.STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded"
)


# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .source-card {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .high-confidence { background-color: #90EE90; color: #006400; }
    .medium-confidence { background-color: #FFD700; color: #8B6914; }
    .low-confidence { background-color: #FFB6C1; color: #8B0000; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_system():
    """Initialise tous les composants du système (avec cache)"""
    logger.info("🚀 Initialisation du système RAG...")
    
    try:
        # 1. Vector Store
        vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        # 2. Embedding Generator
        embedder = EmbeddingGenerator(
            model_name=settings.EMBEDDING_MODEL,
            batch_size=settings.BATCH_SIZE
        )
        
        # 3. Hybrid Search
        hybrid_search = HybridSearchEngine(
            vector_store=vector_store,
            semantic_weight=settings.SEMANTIC_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT
        )
        
        # Indexer tous les documents pour BM25
        doc_count = vector_store.count()
        if doc_count > 0:
            logger.info(f"Indexation BM25 de {doc_count} documents...")
            all_docs = vector_store.peek(limit=doc_count)
            if all_docs and all_docs.get('documents'):
                documents = [
                    {
                        'id': doc_id,
                        'text': text,
                        'metadata': meta
                    }
                    for doc_id, text, meta in zip(
                        all_docs['ids'],
                        all_docs['documents'],
                        all_docs['metadatas']
                    )
                ]
                hybrid_search.index_documents(documents)
                logger.success(f"✅ Index BM25 créé avec {len(documents)} documents")
        
        # 4. Ollama Client
        ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        
        # 5. Prompt Builder
        prompt_builder = PromptBuilder()
        
        # 6. Response Generator
        response_gen = ResponseGenerator(
            hybrid_search=hybrid_search,
            ollama_client=ollama,
            prompt_builder=prompt_builder,
            min_confidence=settings.SIMILARITY_THRESHOLD,
            max_sources=settings.RERANK_TOP_K,
            top_k_retrieval=settings.TOP_K_RETRIEVAL
        )
        
        # 7. Conversation Manager
        conv_manager = ConversationManager(
            storage_dir="./data/conversations",
            max_history_length=settings.MAX_CONVERSATION_HISTORY
        )
        
        logger.success("✅ Système initialisé avec succès")
        
        return {
            'vector_store': vector_store,
            'embedder': embedder,
            'hybrid_search': hybrid_search,
            'ollama': ollama,
            'response_gen': response_gen,
            'conv_manager': conv_manager
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation: {e}")
        st.error(f"Erreur d'initialisation: {e}")
        return None


def render_sidebar(system):
    """Rendu de la barre latérale"""
    with st.sidebar:
        st.markdown("## 🎓 Assistant RAG INPT")
        st.markdown("**Smart ICT - Système d'aide éducative**")
        st.markdown("---")
        
        # Gestion des conversations
        st.markdown("### 💬 Conversations")
        
        if st.button("➕ Nouvelle Conversation", use_container_width=True):
            conv = system['conv_manager'].create_conversation()
            st.session_state.current_conv_id = conv.id
            st.rerun()
        
        # Liste des conversations récentes
        conversations = system['conv_manager'].list_conversations(limit=10)
        
        if conversations:
            st.markdown("**Récentes:**")
            for conv in conversations:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"📝 {conv['title'][:30]}...",
                        key=f"load_{conv['id']}",
                        use_container_width=True
                    ):
                        st.session_state.current_conv_id = conv['id']
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}"):
                        system['conv_manager'].delete_conversation(conv['id'])
                        st.rerun()
        
        st.markdown("---")
        
        # Bouton pour effacer le cache
        if st.button("🔄 Effacer le cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache effacé ! Rechargez la page.")
            st.rerun()
        
        st.markdown("---")
        
        # Paramètres
        with st.expander("⚙️ Paramètres", expanded=False):
            temperature = st.slider(
                "Créativité (Temperature)",
                min_value=0.0,
                max_value=1.0,
                value=settings.LLM_TEMPERATURE,
                step=0.1
            )
            st.session_state.temperature = temperature
            
            top_k = st.slider(
                "Nombre de sources",
                min_value=1,
                max_value=10,
                value=settings.RERANK_TOP_K,
                step=1
            )
            st.session_state.top_k = top_k


def render_main_chat(system):
    """Rendu de l'interface de chat principale"""
    # Header
    st.markdown('<div class="main-header">🎓 Assistant Éducatif Smart ICT</div>', unsafe_allow_html=True)
    
    # Initialiser la session
    if 'current_conv_id' not in st.session_state:
        conv = system['conv_manager'].create_conversation()
        st.session_state.current_conv_id = conv.id
        st.session_state.messages = []
    
    # Charger les messages de la conversation actuelle
    if 'messages' not in st.session_state or 'last_loaded_conv_id' not in st.session_state or st.session_state.last_loaded_conv_id != st.session_state.current_conv_id:
        # Charger l'historique de la conversation
        conv = system['conv_manager'].load_conversation(st.session_state.current_conv_id)
        if conv and conv.messages:
            st.session_state.messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "sources": msg.metadata.get('sources', []) if hasattr(msg, 'metadata') and msg.metadata else [],
                    "confidence": msg.metadata.get('confidence', 0.0) if hasattr(msg, 'metadata') and msg.metadata else 0.0
                }
                for msg in conv.messages
            ]
        else:
            st.session_state.messages = []
        st.session_state.last_loaded_conv_id = st.session_state.current_conv_id
    
    # Afficher l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_math_content(message["content"])
            
            # Afficher les sources si présentes
            if "sources" in message and message["sources"]:
                render_sources(message["sources"], message.get("confidence", 0.0))
    
    # Input utilisateur
    if prompt := st.chat_input("Posez votre question sur les cours..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            render_math_content(prompt)
        
        # Générer la réponse
        with st.chat_message("assistant"):
            with st.spinner("🤔 Recherche et génération de la réponse..."):
                # Récupérer l'historique
                history = system['conv_manager'].get_context_window(
                    conversation_id=st.session_state.current_conv_id
                )
                
                # Générer la réponse
                response = system['response_gen'].generate_response(
                    question=prompt,
                    conversation_history=history,
                    temperature=st.session_state.get('temperature', 0.7)
                )
                
                # Afficher la réponse
                render_math_content(response.answer)
                
                # Afficher les sources
                if response.sources:
                    render_sources(response.sources, response.confidence)
                
                # Sauvegarder dans l'historique
                system['conv_manager'].add_message(
                    role='user',
                    content=prompt,
                    conversation_id=st.session_state.current_conv_id
                )
                
                system['conv_manager'].add_message(
                    role='assistant',
                    content=response.answer,
                    metadata={
                        'confidence': response.confidence,
                        'num_sources': len(response.sources)
                    },
                    conversation_id=st.session_state.current_conv_id
                )
                
                # Ajouter à l'état de session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources,
                    "confidence": response.confidence
                })


def render_sources(sources, confidence):
    """
    Affiche les sources et le niveau de confiance avec support de compatibilité
    
    Args:
        sources: Liste des sources (format ancien ou nouveau)
        confidence: Niveau de confiance global
    """
    st.markdown("---")
    
    # Badge de confiance
    if confidence >= 0.7:
        badge_class = "high-confidence"
        label = "Haute confiance"
    elif confidence >= 0.4:
        badge_class = "medium-confidence"
        label = "Confiance moyenne"
    else:
        badge_class = "low-confidence"
        label = "Faible confiance"
    
    st.markdown(
        f'<div class="confidence-badge {badge_class}">🎯 {label} ({confidence:.0%})</div>',
        unsafe_allow_html=True
    )
    
    # Sources avec support de compatibilité
    st.markdown("**📚 Sources consultées:**")
    
    if not sources:
        st.info("Aucune source trouvée.")
        return
    
    # Detect if we have enhanced source format
    has_enhanced_sources = any(
        isinstance(source, dict) and source.get('chunk_format') in ['enhanced', 'legacy']
        for source in sources
    )
    
    if has_enhanced_sources:
        # Use enhanced rendering with compatibility support
        render_enhanced_sources_inline(sources)
    else:
        # Fallback to original rendering for legacy format
        render_legacy_sources(sources)


def render_enhanced_sources_inline(sources):
    """
    Render sources with enhanced compatibility information inline
    
    Args:
        sources: List of source dictionaries with compatibility info
    """
    # Show format statistics
    format_counts = {}
    for source in sources:
        chunk_format = source.get('chunk_format', 'unknown')
        format_counts[chunk_format] = format_counts.get(chunk_format, 0) + 1
    
    # Display format info if mixed
    if len(format_counts) > 1:
        format_info = []
        for fmt, count in format_counts.items():
            if fmt == 'enhanced':
                format_info.append(f"🟢 {count} enrichi(s)")
            elif fmt == 'legacy':
                format_info.append(f"🟡 {count} ancien(s)")
            else:
                format_info.append(f"🔴 {count} inconnu(s)")
        
        st.caption(f"Formats: {', '.join(format_info)}")
    
    # Render individual sources
    for i, source in enumerate(sources, 1):
        # Extract display information
        display_title = get_source_display_title(source)
        content = get_source_display_content(source)
        score = source.get('score', 0.0)
        chunk_format = source.get('chunk_format', 'unknown')
        
        # Format indicator
        format_indicator = ""
        if chunk_format == 'enhanced':
            format_indicator = "🟢"
        elif chunk_format == 'legacy':
            format_indicator = "🟡"
        else:
            format_indicator = "🔴"
        
        # Contextual header info
        contextual_info = ""
        if source.get('has_contextual_header', False):
            contextual_header = source.get('contextual_header', '')
            if contextual_header:
                contextual_info = f"<br><small>📍 {contextual_header}</small>"
        
        st.markdown(f"""
        <div class="source-card">
            <strong>[{i}] {format_indicator}</strong> {display_title}<br>
            <small>Score: {score:.2f}</small>{contextual_info}
        </div>
        """, unsafe_allow_html=True)
        
        # Show content preview
        content_preview = content[:150] + "..." if len(content) > 150 else content
        st.text(content_preview)


def render_legacy_sources(sources):
    """
    Render sources in legacy format (backward compatibility)
    
    Args:
        sources: List of sources in legacy format
    """
    for i, source in enumerate(sources, 1):
        # Handle different legacy formats
        if isinstance(source, dict):
            # Dictionary format
            name = source.get('name', source.get('filename', f'Document {i}'))
            pages = source.get('pages', [])
            score = source.get('score', 0.0)
            
            pages_text = f"pages {', '.join(map(str, pages))}" if pages else "page inconnue"
            
            st.markdown(f"""
            <div class="source-card">
                <strong>[{i}]</strong> {name}<br>
                <small>📄 {pages_text} • Score: {score:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            # String or other format
            st.markdown(f"""
            <div class="source-card">
                <strong>[{i}]</strong> {str(source)[:100]}...
            </div>
            """, unsafe_allow_html=True)


def get_source_display_title(source):
    """
    Get appropriate display title for a source
    
    Args:
        source: Source dictionary
        
    Returns:
        Display title string
    """
    # Try display_title first (from compatibility layer)
    if source.get('display_title'):
        return source['display_title']
    
    # Try contextual_header
    if source.get('contextual_header'):
        return source['contextual_header']
    
    # Try legacy name field
    if source.get('name'):
        return source['name']
    
    # Try filename from metadata
    metadata = source.get('metadata', {})
    filename = metadata.get('filename') or metadata.get('source')
    if filename:
        return filename
    
    # Fallback
    return f"Document {source.get('id', 'Unknown')}"


def get_source_display_content(source):
    """
    Get appropriate display content for a source
    
    Args:
        source: Source dictionary
        
    Returns:
        Content string for display
    """
    # Use clean_content if available
    clean_content = source.get('clean_content')
    if clean_content:
        return clean_content
    
    # Fallback to regular content
    content = source.get('content', '')
    
    # If content starts with contextual header, try to extract clean part
    contextual_header = source.get('contextual_header', '')
    if contextual_header and content.startswith(contextual_header):
        # Remove header and leading newlines
        clean_part = content[len(contextual_header):].lstrip('\n')
        return clean_part if clean_part else content
    
    return content


def main():
    """Fonction principale de l'application"""
    # Initialisation
    system = initialize_system()
    
    if system is None:
        st.error("❌ Impossible d'initialiser le système. Vérifiez la configuration.")
        st.stop()
    
    # Vérifier qu'Ollama est disponible
    if not system['ollama']._check_connection():
        st.warning("""
        ⚠️ **Ollama n'est pas accessible**
        
        Assurez-vous que:
        1. Ollama est installé: `curl -fsSL https://ollama.ai/install.sh | sh`
        2. Le service est lancé: `ollama serve`
        3. Le modèle est téléchargé: `ollama pull llama3.2:3b`
        """)
        st.stop()
    
    # Rendu de l'interface
    render_sidebar(system)
    render_main_chat(system)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Assistant RAG développé pour l'INPT Smart ICT • Version 1.0.0<br>
        Propulsé par Ollama + ChromaDB + Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()