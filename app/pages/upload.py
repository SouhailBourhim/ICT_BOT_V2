"""Page d'upload de documents"""
import streamlit as st


def render_upload_page():
    """Affiche la page d'upload"""
    st.header("📤 Upload de Documents")
    
    st.markdown("""
    Uploadez vos documents pour enrichir la base de connaissances.
    Formats supportés: PDF, TXT, Markdown
    """)
    
    uploaded_file = st.file_uploader(
        "Choisissez un fichier",
        type=["pdf", "txt", "md"]
    )
    
    if uploaded_file:
        st.success(f"Fichier uploadé: {uploaded_file.name}")
        
        if st.button("Traiter le document"):
            with st.spinner("Traitement en cours..."):
                # Traitement à implémenter
                st.success("Document traité avec succès!")
