"""Page d'analytics"""
import streamlit as st


def render_analytics_page():
    """Affiche la page d'analytics"""
    st.header("📊 Analytics & Métriques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents indexés", "0")
    
    with col2:
        st.metric("Questions posées", "0")
    
    with col3:
        st.metric("Temps de réponse moyen", "0s")
    
    st.markdown("---")
    st.subheader("Statistiques détaillées")
    st.info("Analytics en cours d'implémentation...")
