"""Visualisation de documents"""
import streamlit as st


class DocumentViewer:
    """Visualisation de documents"""
    
    @staticmethod
    def render_document_list(documents: list):
        """Affiche la liste des documents"""
        for doc in documents:
            with st.expander(f"📄 {doc['filename']}"):
                st.write(f"**Taille:** {doc['size']} bytes")
                st.write(f"**Format:** {doc['format']}")
                st.write(f"**Date:** {doc['created_at']}")
