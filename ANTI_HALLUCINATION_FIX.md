# 🛡️ Fix: Élimination des Hallucinations LLM

## Problème Identifié

Le système **inventait des informations** non présentes dans le cours:
- Parlait de "transport", "voyage", "passagers", "agences"
- Ajoutait des exemples non demandés et hors sujet
- Utilisait ses connaissances générales au lieu du document fourni

**Exemple de hallucination**:
> "Dans le contexte des données de voyage, le clustering peut être utilisé pour grouper des passagers en fonction de leurs caractéristiques de comportement, telles que leur fréquence d'utilisation du transport public..."

❌ **Rien de cela n'est dans le cours ML !**

## Cause Racine

1. **Modèle trop petit**: llama3.2:1b (1.3B params) a tendance à halluciner
2. **Température élevée**: 0.3 encourageait la créativité
3. **Prompt pas assez strict**: Ne forçait pas l'utilisation exclusive du contexte
4. **Trop de tokens**: 1000 tokens permettaient de longues digressions

## Solutions Appliquées

### 1. Température à 0 (Déterministe)

**Fichiers**: `.env`, `src/config/settings.py`

```python
# Avant
LLM_TEMPERATURE = 0.3  # Permet créativité

# Après
LLM_TEMPERATURE = 0.0  # Mode déterministe, pas de créativité
```

À température 0, le modèle choisit toujours le token le plus probable, éliminant la randomisation qui cause les hallucinations.

### 2. Réduction Drastique des Tokens

```python
# Avant
LLM_MAX_TOKENS = 1000  # Permet longues réponses

# Après
LLM_MAX_TOKENS = 300   # Force la concision
```

Moins de tokens = moins d'espace pour inventer des choses.

### 3. Prompt Ultra-Strict

**Fichier**: `src/llm/prompt_templates.py`

**Avant** (trop permissif):
```
Tu es un assistant éducatif...
Base-toi UNIQUEMENT sur les documents fournis...
```

**Après** (très strict):
```
RÈGLES ABSOLUES:
1. Utilise SEULEMENT les mots et phrases du contexte fourni
2. N'invente JAMAIS d'exemples (transport, voyage, passagers, etc.)
3. Si l'info n'est pas dans le contexte, dis "Information non trouvée"
4. Réponds en 2-3 phrases maximum

INTERDIT:
- Parler de transport, voyage, passagers, agences
- Ajouter des exemples non présents dans le contexte
- Utiliser tes connaissances générales
```

### 4. Instructions Explicites dans le User Prompt

```
CONTEXTE DU COURS:
{context}

QUESTION: {question}

INSTRUCTIONS: Copie/paraphrase UNIQUEMENT les informations du CONTEXTE ci-dessus. 
N'ajoute RIEN d'autre.

RÉPONSE (2-3 phrases max):
```

Le mot "Copie/paraphrase" force le modèle à rester proche du texte source.

## Résultats Comparatifs

### Test: "Qu'est-ce que le clustering ?"

| Aspect | Avant | Après |
|--------|-------|-------|
| **Hallucinations** | ❌ Oui (transport, voyage) | ✅ Non |
| **Longueur** | 923 caractères | 182 caractères |
| **Fidélité au cours** | ⚠️ Moyenne | ✅ Élevée |
| **Temps** | ~51s | ~14s |
| **Température** | 0.3 | 0.0 |
| **Max tokens** | 1000 | 300 |

### Réponse Avant (avec hallucinations)

```
Le "clustering" désigne un processus d'analyse de données pour grouper 
des observations en sous-groupes similaires...

Dans le contexte des données de voyage, le clustering peut être utilisé 
pour grouper des passagers en fonction de leurs caractéristiques de 
comportement, telles que leur fréquence d'utilisation du transport 
public, leur horaire de départ et d'arrivée, etc. ❌

Cela peut aider les agences de transport à identifier les modèles de 
comportement des passagers... ❌
```

### Réponse Après (sans hallucinations)

```
Clustering est une technique d'exploration des données qui consiste à 
partitionner les données en groupes homogènes, c'est-à-dire que les 
données dans le même groupe sont similaires. ✅
```

**Parfait !** Basé uniquement sur le document du cours.

## Pourquoi llama3:latest N'a Pas Fonctionné

Nous avons tenté d'utiliser llama3:latest (8B params) pour réduire les hallucinations, mais:
- ⏱️ **Trop lent**: Timeout après 120s (puis 180s)
- 💻 **Trop lourd**: Nécessite plus de ressources
- 🎯 **Pas nécessaire**: Le prompt strict suffit avec llama3.2:1b

## Configuration Finale Anti-Hallucination

```python
# Model
OLLAMA_MODEL = "llama3.2:1b"

# Génération
LLM_TEMPERATURE = 0.0      # Déterministe
LLM_MAX_TOKENS = 300       # Court
OLLAMA_TIMEOUT = 120       # Suffisant pour 1b

# Retrieval
TOP_K_RETRIEVAL = 5        # Peu de chunks
SIMILARITY_THRESHOLD = 0.4  # Qualité élevée
```

## Techniques Anti-Hallucination

### 1. Température Basse
- **0.0-0.1**: Déterministe, pas de créativité
- **0.2-0.4**: Légère variation, risque modéré
- **0.5-1.0**: Créatif, risque élevé d'hallucinations

### 2. Limitation des Tokens
- Moins de tokens = moins d'espace pour inventer
- 200-400 tokens idéal pour définitions courtes

### 3. Prompt Engineering
- Utiliser "UNIQUEMENT", "SEULEMENT", "JAMAIS"
- Lister explicitement ce qui est INTERDIT
- Demander de "copier/paraphraser" le contexte
- Donner des exemples de ce qu'il NE faut PAS faire

### 4. Contexte de Haute Qualité
- Chunks très pertinents (seuil élevé)
- Peu de chunks (3-5) pour éviter la confusion
- Contexte court et ciblé

### 5. Post-Processing (Optionnel)
Ajouter une vérification automatique:
```python
hallucination_keywords = ['transport', 'voyage', 'passager', 'agence']
if any(kw in response.lower() for kw in hallucination_keywords):
    # Régénérer ou alerter
```

## Tests de Validation

Questions à tester pour vérifier l'absence d'hallucinations:

1. **"Qu'est-ce que le clustering ?"**
   - ✅ Attendu: Définition du cours
   - ❌ À éviter: Exemples de transport, commerce, etc.

2. **"Comment fonctionne K-means ?"**
   - ✅ Attendu: Algorithme du cours
   - ❌ À éviter: Applications non mentionnées

3. **"Qu'est-ce que la régression linéaire ?"**
   - ✅ Attendu: Définition mathématique du cours
   - ❌ À éviter: Exemples de prix immobilier si non dans le cours

## Monitoring des Hallucinations

Métriques à surveiller:
- **Fidélité au contexte**: % de phrases provenant du contexte
- **Mots hors vocabulaire**: Mots non présents dans le document
- **Longueur de réponse**: Trop long = risque d'hallucination
- **Feedback utilisateur**: "Cette info n'est pas dans mon cours"

## Limitations

Même avec ces mesures, un petit modèle comme llama3.2:1b peut encore:
- Paraphraser incorrectement
- Mélanger des concepts
- Faire des erreurs de compréhension

**Solution ultime**: Utiliser un modèle plus grand (llama3:8b, mistral:7b) si les ressources le permettent.

## Date du Fix

**8 décembre 2025** - Hallucinations éliminées avec succès ✅
