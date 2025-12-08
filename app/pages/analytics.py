#!/usr/bin/env python3
"""
Page Analytics - Statistiques et métriques du système RAG
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys

# Ajouter le chemin parent pour les imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.storage.vector_store import VectorStore
from src.conversation.manager import ConversationManager

# Configuration de la page
st.set_page_config(
    page_title="Analytics - INPT RAG Assistant",
    page_icon="📊",
    layout="wide"
)

def load_analytics_data():
    """Charge les données d'analytics"""
    try:
        # Charger toutes les conversations
        conversations = []
        conv_dir = Path("./data/conversations")
        if conv_dir.exists():
            for conv_file in conv_dir.glob("*.json"):
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                        conversations.append(conv_data)
                except Exception:
                    continue
        
        # Initialiser vector store pour les stats de documents
        try:
            vector_store = VectorStore(
                persist_directory=str(settings.CHROMA_PERSIST_DIR),
                collection_name=settings.CHROMA_COLLECTION_NAME
            )
        except Exception:
            vector_store = None
        
        return conversations, vector_store
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return [], None

def render_system_metrics(vector_store):
    """Affiche les métriques système"""
    st.header("🔧 Métriques Système")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if vector_store:
            try:
                doc_count = vector_store.count()
                st.metric("Documents indexés", doc_count)
            except:
                st.metric("Documents indexés", "N/A")
        else:
            st.metric("Documents indexés", "N/A")
    
    with col2:
        st.metric("Modèle LLM", settings.OLLAMA_MODEL)
    
    with col3:
        st.metric("Température", f"{settings.LLM_TEMPERATURE}")
    
    with col4:
        st.metric("Seuil confiance", f"{settings.SIMILARITY_THRESHOLD}")

def render_conversation_analytics(conversations):
    """Affiche les analytics des conversations"""
    st.header("💬 Analytics des Conversations")
    
    if not conversations:
        st.warning("Aucune conversation trouvée. Commencez à utiliser le chat pour voir les statistiques.")
        return
    
    # Métriques générales
    col1, col2, col3, col4 = st.columns(4)
    
    total_conversations = len(conversations)
    total_messages = sum(len(conv.get('messages', [])) for conv in conversations)
    avg_messages_per_conv = total_messages / total_conversations if total_conversations > 0 else 0
    
    # Calculer les conversations actives (dernières 24h)
    now = datetime.now()
    active_conversations = 0
    for conv in conversations:
        if conv.get('messages'):
            last_message = conv['messages'][-1]
            try:
                last_time = datetime.fromisoformat(last_message.get('timestamp', ''))
                if (now - last_time).days < 1:
                    active_conversations += 1
            except:
                continue
    
    with col1:
        st.metric("Total Conversations", total_conversations)
    
    with col2:
        st.metric("Total Messages", total_messages)
    
    with col3:
        st.metric("Moy. Messages/Conv", f"{avg_messages_per_conv:.1f}")
    
    with col4:
        st.metric("Conversations 24h", active_conversations)

def render_usage_charts(conversations):
    """Affiche les graphiques d'utilisation"""
    st.header("📈 Graphiques d'Utilisation")
    
    if not conversations:
        return
    
    # Préparer les données pour les graphiques
    daily_usage = {}
    hourly_usage = {i: 0 for i in range(24)}
    question_types = {}
    
    for conv in conversations:
        for message in conv.get('messages', []):
            if message.get('role') == 'user':
                try:
                    timestamp = datetime.fromisoformat(message.get('timestamp', ''))
                    
                    # Usage quotidien
                    date_key = timestamp.date()
                    daily_usage[date_key] = daily_usage.get(date_key, 0) + 1
                    
                    # Usage horaire
                    hour = timestamp.hour
                    hourly_usage[hour] += 1
                    
                    # Types de questions (basique)
                    content = message.get('content', '').lower()
                    if 'qu\'est-ce que' in content or 'c\'est quoi' in content or 'définition' in content:
                        question_types['Définitions'] = question_types.get('Définitions', 0) + 1
                    elif 'comment' in content or 'expliquer' in content:
                        question_types['Explications'] = question_types.get('Explications', 0) + 1
                    elif 'formule' in content or 'équation' in content or 'calcul' in content:
                        question_types['Formules'] = question_types.get('Formules', 0) + 1
                    elif 'différence' in content or 'comparaison' in content or 'comparer' in content:
                        question_types['Comparaisons'] = question_types.get('Comparaisons', 0) + 1
                    else:
                        question_types['Autres'] = question_types.get('Autres', 0) + 1
                except Exception:
                    continue
    
    # Graphique usage quotidien
    col1, col2 = st.columns(2)
    
    with col1:
        if daily_usage:
            df_daily = pd.DataFrame(list(daily_usage.items()), columns=['Date', 'Messages'])
            df_daily = df_daily.sort_values('Date')
            fig_daily = px.line(df_daily, x='Date', y='Messages', 
                              title='Usage Quotidien',
                              markers=True)
            fig_daily.update_layout(height=400)
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("Pas encore de données d'usage quotidien")
    
    with col2:
        # Graphique usage horaire
        df_hourly = pd.DataFrame(list(hourly_usage.items()), columns=['Heure', 'Messages'])
        fig_hourly = px.bar(df_hourly, x='Heure', y='Messages',
                           title='Usage par Heure de la Journée')
        fig_hourly.update_layout(height=400)
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Graphique types de questions
    if question_types:
        st.subheader("Types de Questions")
        df_types = pd.DataFrame(list(question_types.items()), columns=['Type', 'Nombre'])
        fig_pie = px.pie(df_types, values='Nombre', names='Type',
                        title='Répartition des Types de Questions')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

def render_performance_metrics(conversations):
    """Affiche les métriques de performance"""
    st.header("⚡ Métriques de Performance")
    
    if not conversations:
        return
    
    # Analyser les métadonnées des réponses
    response_times = []
    confidence_scores = []
    chunks_used = []
    
    for conv in conversations:
        for message in conv.get('messages', []):
            if message.get('role') == 'assistant':
                metadata = message.get('metadata', {})
                
                # Temps de réponse (si disponible)
                if 'response_time' in metadata:
                    response_times.append(metadata['response_time'])
                
                # Score de confiance
                if 'confidence' in metadata:
                    confidence_scores.append(metadata['confidence'])
                
                # Nombre de chunks utilisés
                if 'num_chunks_used' in metadata:
                    chunks_used.append(metadata['num_chunks_used'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            st.metric("Confiance Moyenne", f"{avg_confidence:.1%}")
            
            # Histogramme des scores de confiance
            fig_conf = px.histogram(confidence_scores, nbins=20,
                                  title='Distribution des Scores de Confiance',
                                  labels={'value': 'Score de Confiance', 'count': 'Nombre'})
            fig_conf.update_layout(height=300)
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.info("Pas encore de données de confiance")
    
    with col2:
        if chunks_used:
            avg_chunks = sum(chunks_used) / len(chunks_used)
            st.metric("Chunks Utilisés (Moy.)", f"{avg_chunks:.1f}")
            
            # Histogramme des chunks utilisés
            fig_chunks = px.histogram(chunks_used, nbins=10,
                                    title='Distribution des Chunks Utilisés',
                                    labels={'value': 'Nombre de Chunks', 'count': 'Fréquence'})
            fig_chunks.update_layout(height=300)
            st.plotly_chart(fig_chunks, use_container_width=True)
        else:
            st.info("Pas encore de données sur les chunks")
    
    with col3:
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            st.metric("Temps Réponse (Moy.)", f"{avg_time:.1f}s")
            
            # Histogramme des temps de réponse
            fig_time = px.histogram(response_times, nbins=20,
                                  title='Distribution des Temps de Réponse',
                                  labels={'value': 'Temps (s)', 'count': 'Nombre'})
            fig_time.update_layout(height=300)
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Pas encore de données de temps de réponse")

def render_recent_conversations(conversations):
    """Affiche les conversations récentes"""
    st.header("🕒 Conversations Récentes")
    
    if not conversations:
        return
    
    # Trier par dernière activité
    recent_convs = []
    for conv in conversations:
        if conv.get('messages'):
            last_message = conv['messages'][-1]
            try:
                last_time = datetime.fromisoformat(last_message.get('timestamp', ''))
                recent_convs.append({
                    'id': conv.get('id', 'N/A'),
                    'last_activity': last_time,
                    'message_count': len(conv['messages']),
                    'last_message': last_message.get('content', '')[:100] + '...'
                })
            except:
                continue
    
    recent_convs.sort(key=lambda x: x['last_activity'], reverse=True)
    
    # Afficher les 10 plus récentes
    for conv in recent_convs[:10]:
        with st.expander(f"Conversation {conv['id'][:8]}... - {conv['message_count']} messages"):
            st.write(f"**Dernière activité:** {conv['last_activity'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Dernier message:** {conv['last_message']}")

def main():
    """Fonction principale"""
    st.title("📊 Analytics - Assistant RAG INPT")
    st.markdown("---")
    
    # Charger les données
    with st.spinner("Chargement des données d'analytics..."):
        conversations, vector_store = load_analytics_data()
    
    # Afficher les différentes sections
    render_system_metrics(vector_store)
    st.markdown("---")
    
    render_conversation_analytics(conversations)
    st.markdown("---")
    
    render_usage_charts(conversations)
    st.markdown("---")
    
    render_performance_metrics(conversations)
    st.markdown("---")
    
    render_recent_conversations(conversations)
    
    # Footer
    st.markdown("---")
    st.markdown("*Analytics générées automatiquement à partir des données de conversation*")

if __name__ == "__main__":
    main()
