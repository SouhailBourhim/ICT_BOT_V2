"""
Client Ollama pour intégration LLM locale
Support des modèles Llama, Mistral, etc.
"""
from typing import List, Dict, Optional, Generator
import requests
import json
from loguru import logger
import time


class OllamaClient:
    """
    Client pour interagir avec Ollama API
    Gère la génération de réponses, le streaming, etc.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout: int = 120
    ):
        """
        Initialise le client Ollama
        
        Args:
            base_url: URL de l'API Ollama
            model: Nom du modèle à utiliser
            timeout: Timeout des requêtes (secondes)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        
        logger.info(f"Client Ollama initialisé: {model} @ {base_url}")
        
        # Vérification de la connexion
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """Vérifie que Ollama est accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.success(f"✅ Ollama connecté ({len(models)} modèles disponibles)")
                return True
            else:
                logger.warning(f"⚠️ Ollama répond mais avec code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter à Ollama: {e}")
            logger.info("Assurez-vous qu'Ollama est lancé: ollama serve")
            return False
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> str:
        """
        Génère une réponse avec Ollama
        
        Args:
            prompt: Prompt utilisateur
            system: Prompt système (instructions)
            temperature: Créativité [0-1]
            max_tokens: Nombre max de tokens
            stop: Séquences d'arrêt
            stream: Mode streaming
            
        Returns:
            Texte généré
        """
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            if stream:
                return self._generate_stream(endpoint, payload)
            else:
                return self._generate_complete(endpoint, payload)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            raise
    
    def _generate_complete(self, endpoint: str, payload: Dict) -> str:
        """Génération complète (non-streaming)"""
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
        
        result = response.json()
        generated_text = result.get('response', '')
        
        # Métriques
        elapsed = time.time() - start_time
        total_duration = result.get('total_duration', 0) / 1e9  # nanosecondes -> secondes
        
        logger.info(f"✅ Génération complète en {elapsed:.2f}s (model: {total_duration:.2f}s)")
        
        return generated_text
    
    def _generate_stream(self, endpoint: str, payload: Dict) -> Generator[str, None, None]:
        """Génération en mode streaming"""
        response = requests.post(
            endpoint,
            json=payload,
            stream=True,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if 'response' in chunk:
                    yield chunk['response']
                
                if chunk.get('done', False):
                    break
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Mode chat avec historique de conversation
        
        Args:
            messages: Liste de messages [{"role": "user/assistant", "content": "..."}]
            temperature: Créativité
            max_tokens: Tokens max
            stream: Mode streaming
            
        Returns:
            Réponse du modèle
        """
        endpoint = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            if stream:
                return self._chat_stream(endpoint, payload)
            else:
                return self._chat_complete(endpoint, payload)
                
        except Exception as e:
            logger.error(f"Erreur lors du chat: {e}")
            raise
    
    def _chat_complete(self, endpoint: str, payload: Dict) -> str:
        """Chat mode complet"""
        response = requests.post(
            endpoint,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        message = result.get('message', {})
        
        return message.get('content', '')
    
    def _chat_stream(self, endpoint: str, payload: Dict) -> Generator[str, None, None]:
        """Chat mode streaming"""
        response = requests.post(
            endpoint,
            json=payload,
            stream=True,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                message = chunk.get('message', {})
                if 'content' in message:
                    yield message['content']
                
                if chunk.get('done', False):
                    break
    
    def create_embeddings(self, text: str) -> List[float]:
        """
        Génère des embeddings avec Ollama
        (Nécessite un modèle compatible comme nomic-embed-text)
        """
        endpoint = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            return result.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embeddings: {e}")
            raise
    
    def list_models(self) -> List[Dict]:
        """Liste tous les modèles disponibles"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                return response.json().get('models', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Télécharge un modèle Ollama
        
        Args:
            model_name: Nom du modèle (ex: "llama3.2:3b")
            
        Returns:
            True si succès
        """
        endpoint = f"{self.base_url}/api/pull"
        
        payload = {"name": model_name}
        
        logger.info(f"Téléchargement du modèle {model_name}...")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=600  # 10 minutes pour le téléchargement
            )
            
            for line in response.iter_lines():
                if line:
                    status = json.loads(line)
                    if 'status' in status:
                        logger.info(status['status'])
            
            logger.success(f"✅ Modèle {model_name} téléchargé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            return False
    
    def delete_model(self, model_name: str) -> bool:
        """Supprime un modèle"""
        endpoint = f"{self.base_url}/api/delete"
        
        payload = {"name": model_name}
        
        try:
            response = requests.delete(endpoint, json=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Informations sur le modèle actuel"""
        models = self.list_models()
        
        for model in models:
            if model.get('name') == self.model:
                return model
        
        return {}


# Test du client
if __name__ == "__main__":
    # Initialisation
    client = OllamaClient(model="llama3.2:3b")
    
    # Liste des modèles
    print("\n📋 Modèles disponibles:")
    models = client.list_models()
    for model in models:
        print(f"  - {model['name']} ({model.get('size', 'N/A')})")
    
    # Test de génération simple
    print("\n🤖 Test de génération:")
    prompt = "Explique brièvement ce qu'est l'IoT en français."
    response = client.generate(
        prompt=prompt,
        system="Tu es un assistant éducatif pour les étudiants de l'INPT.",
        temperature=0.7,
        max_tokens=200
    )
    print(f"\nPrompt: {prompt}")
    print(f"Réponse: {response}")
    
    # Test du mode chat
    print("\n💬 Test du mode chat:")
    messages = [
        {"role": "system", "content": "Tu es un assistant éducatif spécialisé en IoT."},
        {"role": "user", "content": "Qu'est-ce qu'un capteur IoT ?"},
    ]
    
    chat_response = client.chat(messages, temperature=0.7)
    print(f"Réponse chat: {chat_response}")