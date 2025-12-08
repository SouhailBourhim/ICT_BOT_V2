"""
Gestionnaire de conversations avec persistance et historique
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid
from pathlib import Path
from loguru import logger


@dataclass
class Message:
    """Structure d'un message de conversation"""
    role: str  # 'user' ou 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


@dataclass
class Conversation:
    """Structure d'une conversation complète"""
    id: str
    title: str
    messages: List[Message]
    created_at: str
    updated_at: str
    metadata: Dict


class ConversationManager:
    """
    Gestionnaire de conversations avec:
    - Création et gestion de conversations
    - Persistance sur disque (JSON)
    - Recherche dans l'historique
    - Gestion du contexte
    """
    
    def __init__(
        self,
        storage_dir: str = "./data/conversations",
        max_history_length: int = 10
    ):
        """
        Initialise le gestionnaire
        
        Args:
            storage_dir: Répertoire de stockage des conversations
            max_history_length: Nombre max de messages à garder en mémoire
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_history_length = max_history_length
        self.current_conversation: Optional[Conversation] = None
        
        logger.info(f"ConversationManager initialisé: {storage_dir}")
    
    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """
        Crée une nouvelle conversation
        
        Args:
            title: Titre de la conversation (auto-généré si None)
            
        Returns:
            Nouvelle conversation
        """
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        if title is None:
            title = f"Conversation {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        conversation = Conversation(
            id=conv_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            metadata={}
        )
        
        self.current_conversation = conversation
        self._save_conversation(conversation)
        
        logger.info(f"✅ Nouvelle conversation créée: {conv_id}")
        return conversation
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        conversation_id: Optional[str] = None
    ) -> Message:
        """
        Ajoute un message à la conversation
        
        Args:
            role: 'user' ou 'assistant'
            content: Contenu du message
            metadata: Métadonnées additionnelles
            conversation_id: ID de la conversation (utilise current si None)
            
        Returns:
            Message créé
        """
        # Récupérer ou créer une conversation
        if conversation_id:
            conversation = self.load_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} non trouvée, création d'une nouvelle")
                conversation = self.create_conversation()
        else:
            conversation = self.current_conversation
            if not conversation:
                conversation = self.create_conversation()
        
        # Vérification de sécurité
        if not conversation or not hasattr(conversation, 'messages'):
            logger.error("Conversation invalide, création d'une nouvelle")
            conversation = self.create_conversation()
        
        # Créer le message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        # Ajouter à la conversation
        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        
        # Mettre à jour le titre si c'est le premier message user
        if role == 'user' and len(conversation.messages) == 1:
            conversation.title = content[:50] + "..." if len(content) > 50 else content
        
        # Sauvegarder
        self._save_conversation(conversation)
        self.current_conversation = conversation
        
        logger.debug(f"Message ajouté à {conversation.id}")
        
        return message
    
    def get_conversation_history(
        self,
        conversation_id: Optional[str] = None,
        max_messages: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère l'historique d'une conversation
        
        Args:
            conversation_id: ID de la conversation (current si None)
            max_messages: Nombre max de messages (tous si None)
            
        Returns:
            Liste de messages au format dict
        """
        if conversation_id:
            conversation = self.load_conversation(conversation_id)
        else:
            conversation = self.current_conversation
        
        if not conversation:
            return []
        
        messages = conversation.messages
        
        # Limiter le nombre de messages
        if max_messages:
            messages = messages[-max_messages:]
        
        # Conversion en dict pour le LLM
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            }
            for msg in messages
        ]
    
    def get_context_window(
        self,
        conversation_id: Optional[str] = None,
        window_size: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère une fenêtre de contexte récente
        
        Args:
            conversation_id: ID de la conversation
            window_size: Taille de la fenêtre (max_history_length si None)
            
        Returns:
            Liste de messages récents
        """
        if window_size is None:
            window_size = self.max_history_length
        
        return self.get_conversation_history(
            conversation_id=conversation_id,
            max_messages=window_size
        )
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Charge une conversation depuis le disque
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Conversation ou None si introuvable
        """
        file_path = self.storage_dir / f"{conversation_id}.json"
        
        if not file_path.exists():
            logger.warning(f"Conversation {conversation_id} introuvable")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruction des objets
            messages = [Message(**msg) for msg in data['messages']]
            
            conversation = Conversation(
                id=data['id'],
                title=data['title'],
                messages=messages,
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                metadata=data.get('metadata', {})
            )
            
            logger.debug(f"Conversation {conversation_id} chargée")
            return conversation
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return None
    
    def _save_conversation(self, conversation: Conversation):
        """Sauvegarde une conversation sur disque"""
        file_path = self.storage_dir / f"{conversation.id}.json"
        
        try:
            # Conversion en dict
            data = {
                'id': conversation.id,
                'title': conversation.title,
                'messages': [asdict(msg) for msg in conversation.messages],
                'created_at': conversation.created_at,
                'updated_at': conversation.updated_at,
                'metadata': conversation.metadata
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Conversation {conversation.id} sauvegardée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def list_conversations(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Liste toutes les conversations
        
        Args:
            limit: Nombre max de conversations (toutes si None)
            
        Returns:
            Liste de métadonnées de conversations
        """
        conv_files = list(self.storage_dir.glob("*.json"))
        conversations = []
        
        for file_path in conv_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conversations.append({
                    'id': data['id'],
                    'title': data['title'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'message_count': len(data['messages'])
                })
            except Exception as e:
                logger.warning(f"Erreur lecture {file_path}: {e}")
                continue
        
        # Tri par date de mise à jour (plus récent en premier)
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        if limit:
            conversations = conversations[:limit]
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Supprime une conversation
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            True si succès
        """
        file_path = self.storage_dir / f"{conversation_id}.json"
        
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✅ Conversation {conversation_id} supprimée")
                
                # Réinitialiser current si c'était celle-ci
                if self.current_conversation and self.current_conversation.id == conversation_id:
                    self.current_conversation = None
                
                return True
            else:
                logger.warning(f"Conversation {conversation_id} introuvable")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False
    
    def clear_conversation(self, conversation_id: Optional[str] = None):
        """
        Efface les messages d'une conversation
        
        Args:
            conversation_id: ID de la conversation (current si None)
        """
        if conversation_id:
            conversation = self.load_conversation(conversation_id)
        else:
            conversation = self.current_conversation
        
        if conversation:
            conversation.messages = []
            conversation.updated_at = datetime.now().isoformat()
            self._save_conversation(conversation)
            logger.info(f"Conversation {conversation.id} effacée")
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche dans les conversations
        
        Args:
            query: Terme de recherche
            limit: Nombre max de résultats
            
        Returns:
            Conversations correspondantes
        """
        query_lower = query.lower()
        results = []
        
        for conv_file in self.storage_dir.glob("*.json"):
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Recherche dans le titre
                if query_lower in data['title'].lower():
                    results.append({
                        'id': data['id'],
                        'title': data['title'],
                        'match_type': 'title',
                        'updated_at': data['updated_at']
                    })
                    continue
                
                # Recherche dans les messages
                for msg in data['messages']:
                    if query_lower in msg['content'].lower():
                        results.append({
                            'id': data['id'],
                            'title': data['title'],
                            'match_type': 'message',
                            'updated_at': data['updated_at']
                        })
                        break
                
            except Exception as e:
                logger.warning(f"Erreur lors de la recherche: {e}")
                continue
        
        # Tri et limite
        results.sort(key=lambda x: x['updated_at'], reverse=True)
        return results[:limit]
    
    def export_conversation(
        self,
        conversation_id: str,
        format: str = 'json'
    ) -> Optional[str]:
        """
        Exporte une conversation
        
        Args:
            conversation_id: ID de la conversation
            format: 'json', 'txt' ou 'md'
            
        Returns:
            Contenu exporté ou None
        """
        conversation = self.load_conversation(conversation_id)
        if not conversation:
            return None
        
        if format == 'json':
            return json.dumps(asdict(conversation), ensure_ascii=False, indent=2)
        
        elif format == 'txt' or format == 'md':
            lines = [f"# {conversation.title}\n"]
            lines.append(f"Créée le: {conversation.created_at}\n\n")
            
            for msg in conversation.messages:
                role = "👤 Étudiant" if msg.role == 'user' else "🤖 Assistant"
                lines.append(f"{role} ({msg.timestamp}):\n")
                lines.append(f"{msg.content}\n\n")
                lines.append("---\n\n")
            
            return ''.join(lines)
        
        return None


# Test du gestionnaire
if __name__ == "__main__":
    manager = ConversationManager()
    
    # Créer une conversation
    conv = manager.create_conversation(title="Test IoT")
    print(f"✅ Conversation créée: {conv.id}")
    
    # Ajouter des messages
    manager.add_message("user", "Qu'est-ce que l'IoT ?")
    manager.add_message("assistant", "L'IoT (Internet des Objets) désigne...")
    manager.add_message("user", "Quels sont les protocoles utilisés ?")
    
    # Récupérer l'historique
    history = manager.get_conversation_history()
    print(f"\n📜 Historique ({len(history)} messages):")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Lister les conversations
    convs = manager.list_conversations()
    print(f"\n📋 Conversations ({len(convs)}):")
    for c in convs:
        print(f"  - {c['title']} ({c['message_count']} messages)")
    
    # Export
    export_txt = manager.export_conversation(conv.id, format='txt')
    print(f"\n📄 Export TXT:\n{export_txt[:200]}...")