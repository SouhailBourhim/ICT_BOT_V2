"""Composants de l'interface de chat"""
import streamlit as st


class ChatInterface:
    """Interface de chat réutilisable"""
    
    @staticmethod
    def render_message(role: str, content: str):
        """Affiche un message"""
        with st.chat_message(role):
            st.markdown(content)
    
    @staticmethod
    def render_sources(sources: list):
        """Affiche les sources"""
        with st.expander("📚 Sources"):
            for i, source in enumerate(sources, 1):
                st.markdown(f"**{i}. {source['filename']}**")
                st.text(source['content'][:200] + "...")
