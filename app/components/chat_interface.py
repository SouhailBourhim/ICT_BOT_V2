"""Composants de l'interface de chat"""
import streamlit as st
from typing import List, Dict, Any, Optional


class ChatInterface:
    """Interface de chat réutilisable avec support de compatibilité pour les chunks"""
    
    @staticmethod
    def render_message(role: str, content: str):
        """Affiche un message"""
        with st.chat_message(role):
            st.markdown(content)
    
    @staticmethod
    def render_sources(sources: List[Dict[str, Any]]):
        """
        Affiche les sources avec support pour les formats de chunks anciens et nouveaux
        
        Args:
            sources: Liste de sources avec métadonnées potentiellement mixtes
        """
        if not sources:
            return
            
        with st.expander("📚 Sources"):
            for i, source in enumerate(sources, 1):
                # Handle both old and new chunk formats
                ChatInterface._render_single_source(i, source)
    
    @staticmethod
    def _render_single_source(index: int, source: Dict[str, Any]):
        """
        Render a single source with backward compatibility
        
        Args:
            index: Source index for display
            source: Source data dictionary
        """
        # Extract display information with fallbacks
        display_title = ChatInterface._get_source_title(source)
        content = ChatInterface._get_source_content(source)
        metadata = source.get('metadata', {})
        
        # Display source header
        st.markdown(f"**{index}. {display_title}**")
        
        # Show chunk format indicator if available
        chunk_format = source.get('chunk_format', 'unknown')
        if chunk_format != 'unknown':
            format_color = "🟢" if chunk_format == 'enhanced' else "🟡"
            st.caption(f"{format_color} Format: {chunk_format}")
        
        # Display contextual header if available
        if source.get('has_contextual_header', False):
            contextual_header = source.get('contextual_header', '')
            if contextual_header:
                st.info(f"📍 {contextual_header}")
        
        # Display content preview
        content_preview = content[:200] + "..." if len(content) > 200 else content
        st.text(content_preview)
        
        # Display additional metadata in expandable section
        if metadata:
            with st.expander(f"Métadonnées source {index}"):
                ChatInterface._render_source_metadata(metadata, source)
    
    @staticmethod
    def _get_source_title(source: Dict[str, Any]) -> str:
        """
        Extract appropriate title for source display
        
        Args:
            source: Source data dictionary
            
        Returns:
            Display title string
        """
        # Try display_title first (from compatibility layer)
        if source.get('display_title'):
            return source['display_title']
        
        # Try contextual_header
        if source.get('contextual_header'):
            return source['contextual_header']
        
        # Fallback to metadata-based title
        metadata = source.get('metadata', {})
        
        # Try filename
        filename = metadata.get('filename') or metadata.get('source')
        if filename:
            # Add page/section info if available
            page_num = metadata.get('page_number') or metadata.get('page')
            section = metadata.get('section')
            
            title_parts = [filename]
            if page_num:
                title_parts.append(f"Page {page_num}")
            if section:
                title_parts.append(f"Section: {section}")
            
            return " - ".join(title_parts)
        
        # Ultimate fallback
        return f"Document {source.get('id', 'Unknown')}"
    
    @staticmethod
    def _get_source_content(source: Dict[str, Any]) -> str:
        """
        Extract appropriate content for display
        
        Args:
            source: Source data dictionary
            
        Returns:
            Content string for display
        """
        # Use clean_content for better readability if available
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
    
    @staticmethod
    def _render_source_metadata(metadata: Dict[str, Any], source: Dict[str, Any]):
        """
        Render source metadata in a structured way
        
        Args:
            metadata: Metadata dictionary
            source: Full source data for additional context
        """
        # Core metadata
        core_fields = ['filename', 'page_number', 'section', 'char_count', 'word_count', 'token_count']
        
        # Display core fields
        st.write("**Informations principales:**")
        for field in core_fields:
            value = metadata.get(field)
            if value is not None:
                field_label = {
                    'filename': 'Fichier',
                    'page_number': 'Page',
                    'section': 'Section',
                    'char_count': 'Caractères',
                    'word_count': 'Mots',
                    'token_count': 'Tokens'
                }.get(field, field)
                st.write(f"- {field_label}: {value}")
        
        # Enhanced chunk information
        if source.get('chunk_format') == 'enhanced':
            st.write("**Informations enrichies:**")
            
            hierarchy_path = source.get('hierarchy_path', [])
            if hierarchy_path:
                st.write(f"- Hiérarchie: {' > '.join(hierarchy_path)}")
            
            structure_metadata = source.get('structure_metadata', {})
            if structure_metadata:
                doc_type = structure_metadata.get('document_type', 'unknown')
                has_sections = structure_metadata.get('has_sections', False)
                has_pages = structure_metadata.get('has_pages', False)
                confidence = structure_metadata.get('confidence_score', 0.0)
                
                st.write(f"- Type de document: {doc_type}")
                st.write(f"- Sections détectées: {'Oui' if has_sections else 'Non'}")
                st.write(f"- Pages détectées: {'Oui' if has_pages else 'Non'}")
                if confidence > 0:
                    st.write(f"- Confiance structure: {confidence:.2%}")
        
        # Additional metadata
        other_metadata = {k: v for k, v in metadata.items() 
                         if k not in core_fields and not k.startswith('_')}
        
        if other_metadata:
            st.write("**Métadonnées supplémentaires:**")
            for key, value in other_metadata.items():
                # Handle complex values
                if isinstance(value, (list, dict)):
                    st.write(f"- {key}: {str(value)[:100]}...")
                else:
                    st.write(f"- {key}: {value}")
    
    @staticmethod
    def render_enhanced_sources(sources: List[Dict[str, Any]], show_format_stats: bool = False):
        """
        Render sources with enhanced display and optional format statistics
        
        Args:
            sources: List of source dictionaries
            show_format_stats: Whether to show format compatibility statistics
        """
        if not sources:
            st.info("Aucune source trouvée.")
            return
        
        # Show format statistics if requested
        if show_format_stats:
            ChatInterface._render_format_statistics(sources)
        
        # Render sources
        ChatInterface.render_sources(sources)
    
    @staticmethod
    def _render_format_statistics(sources: List[Dict[str, Any]]):
        """
        Render format compatibility statistics
        
        Args:
            sources: List of source dictionaries
        """
        if not sources:
            return
        
        # Count formats
        format_counts = {}
        for source in sources:
            chunk_format = source.get('chunk_format', 'unknown')
            format_counts[chunk_format] = format_counts.get(chunk_format, 0) + 1
        
        # Display statistics
        with st.expander("📊 Statistiques de compatibilité"):
            total = len(sources)
            
            for format_type, count in format_counts.items():
                percentage = (count / total) * 100
                
                if format_type == 'enhanced':
                    st.success(f"🟢 Chunks enrichis: {count}/{total} ({percentage:.1f}%)")
                elif format_type == 'legacy':
                    st.warning(f"🟡 Chunks anciens: {count}/{total} ({percentage:.1f}%)")
                else:
                    st.error(f"🔴 Format inconnu: {count}/{total} ({percentage:.1f}%)")
            
            # Show compatibility message
            if format_counts.get('enhanced', 0) > 0 and format_counts.get('legacy', 0) > 0:
                st.info("ℹ️ Mode de compatibilité mixte actif - Les deux formats sont supportés.")
            elif format_counts.get('enhanced', 0) == total:
                st.success("✅ Tous les chunks utilisent le nouveau format enrichi.")
            elif format_counts.get('legacy', 0) == total:
                st.info("📋 Tous les chunks utilisent l'ancien format (compatibilité assurée).")
