"""Page de chat"""
import streamlit as st


def render_chat_page():
    """Affiche la page de chat"""
    st.header("💬 Chat avec l'Assistant")
    
    # Initialiser l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Afficher l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input utilisateur
    if prompt := st.chat_input("Posez votre question..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer la réponse (à implémenter)
        with st.chat_message("assistant"):
            response = "Réponse en cours d'implémentation..."
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
