# 📖 Guide d'Utilisation - Assistant RAG INPT

## Comment Poser de Bonnes Questions

### ✅ Questions Efficaces

Le système fonctionne mieux avec des questions **claires et spécifiques** sur les concepts du cours:

#### 1. Définitions
- ✅ "Qu'est-ce que le clustering ?"
- ✅ "Définis l'apprentissage supervisé"
- ✅ "C'est quoi K-means ?"

#### 2. Explications
- ✅ "Comment fonctionne l'algorithme K-means ?"
- ✅ "Explique la différence entre supervisé et non-supervisé"
- ✅ "Quel est le principe de la régression linéaire ?"

#### 3. Types et Catégories
- ✅ "Quels sont les types d'apprentissage supervisé ?"
- ✅ "Quelles sont les méthodes de clustering ?"
- ✅ "Liste les algorithmes de classification"

#### 4. Caractéristiques
- ✅ "Quels sont les avantages de K-means ?"
- ✅ "Quelles sont les limites du SVM ?"
- ✅ "Quand utiliser la régression ?"

### ⚠️ Questions Problématiques

#### Exemples Concrets Non Présents dans le Cours

Si le cours ne contient pas d'exemples d'application concrets, le système dira honnêtement:
> "Le document ne donne pas d'exemples spécifiques"

**Exemples de questions qui peuvent ne pas avoir de réponse:**
- ❌ "Donne des exemples d'apprentissage supervisé" 
  - → Le cours mentionne les **types** (classification, régression) mais pas forcément des **exemples concrets** (prédire prix maison, etc.)
  
- ❌ "Donne un exemple d'application du clustering"
  - → Sauf si le cours contient des cas d'usage spécifiques

**Solution:** Reformulez pour demander les types/catégories:
- ✅ "Quels sont les types d'apprentissage supervisé ?"
- ✅ "Quelles sont les applications du clustering mentionnées dans le cours ?"

#### Questions Trop Vagues

- ❌ "Parle-moi du machine learning"
  - → Trop large, la réponse sera générique

- ✅ "Qu'est-ce que le machine learning selon le cours ?"
  - → Plus spécifique

#### Questions Hors Sujet

- ❌ "Comment installer Python ?"
- ❌ "Quelle est la différence entre Python et Java ?"
- ❌ "Explique les réseaux de neurones" (si pas dans le cours)

Le système répondra:
> "Information non trouvée dans le document"

## Comprendre les Réponses

### Réponses Courtes et Précises

Le système est configuré pour donner des réponses **concises** (2-3 phrases, ~200-300 caractères).

**Exemple:**
> "Clustering est une technique d'exploration des données qui consiste à partitionner les données en groupes homogènes, c'est-à-dire que les données dans le même groupe sont similaires."

### Citations des Sources

Chaque réponse cite le document source:
> [Source: Algo_ML1_v2.pdf, page 29]

### Quand le Système Ne Sait Pas

Le système est honnête quand il ne trouve pas l'information:
- "Le document ne donne pas d'exemples spécifiques"
- "Information non trouvée dans le document"

**C'est une bonne chose !** Cela évite les hallucinations.

## Stratégies pour Obtenir de Meilleures Réponses

### 1. Commencez par les Bases

Posez d'abord des questions de définition:
1. "Qu'est-ce que X ?"
2. "Comment fonctionne X ?"
3. "Quels sont les types de X ?"

### 2. Soyez Spécifique

Au lieu de:
- ❌ "Parle-moi du clustering"

Demandez:
- ✅ "Qu'est-ce que le clustering ?"
- ✅ "Quels sont les algorithmes de clustering ?"
- ✅ "Quels sont les avantages du clustering ?"

### 3. Reformulez si Nécessaire

Si la réponse est "Information non trouvée", essayez:
- Reformuler avec d'autres mots
- Poser une question plus générale
- Diviser en plusieurs questions simples

**Exemple:**
- ❌ "Donne des exemples d'apprentissage supervisé" → Pas d'exemples concrets
- ✅ "Quels sont les types d'apprentissage supervisé ?" → Classification et Régression ✓

### 4. Questions de Suivi

Utilisez les réponses pour poser des questions plus précises:

1. "Qu'est-ce que l'apprentissage supervisé ?"
   → Réponse: utilise des données avec labels...

2. "Quels sont les types d'apprentissage supervisé ?"
   → Réponse: Classification et Régression

3. "Qu'est-ce que la classification ?"
   → Réponse détaillée sur la classification

## Limitations du Système

### Ce que le Système PEUT Faire

✅ Répondre aux questions sur le contenu du cours
✅ Définir les concepts mentionnés dans les documents
✅ Expliquer les algorithmes décrits
✅ Comparer des concepts présents dans le cours
✅ Citer les sources avec précision

### Ce que le Système NE PEUT PAS Faire

❌ Inventer des exemples non présents dans le cours
❌ Utiliser des connaissances externes au document
❌ Répondre à des questions hors sujet
❌ Donner des opinions personnelles
❌ Faire des calculs complexes
❌ Générer du code (sauf si dans le cours)

## Exemples de Bonnes Sessions

### Session 1: Apprentissage du Clustering

```
Q: Qu'est-ce que le clustering ?
R: Technique d'exploration des données qui partitionne en groupes homogènes...

Q: Quels sont les algorithmes de clustering ?
R: K-means, DBSCAN, Hierarchical clustering...

Q: Comment fonctionne K-means ?
R: Spécifier K clusters, initialiser centroïdes, affecter points...

Q: Quels sont les avantages de K-means ?
R: Simple à implémenter, s'adapte aux grands datasets, garantit convergence...
```

### Session 2: Apprentissage Supervisé

```
Q: Qu'est-ce que l'apprentissage supervisé ?
R: Type d'apprentissage qui utilise des données avec labels...

Q: Quels sont les types d'apprentissage supervisé ?
R: Classification (variable qualitative) et Régression (variable quantitative)

Q: Qu'est-ce que la classification ?
R: Prédiction d'une catégorie ou classe à partir de caractéristiques...

Q: Quels algorithmes de classification existent ?
R: SVM, Random Forest, Decision Trees...
```

## Conseils Finaux

1. **Soyez patient**: Le système prend 10-20 secondes pour générer une réponse

2. **Lisez attentivement**: Les réponses sont concises mais précises

3. **Vérifiez les sources**: Chaque réponse cite le document source

4. **Reformulez si besoin**: Si "Information non trouvée", essayez une autre formulation

5. **Posez des questions simples**: Une question = un concept

6. **Utilisez le contexte**: Référez-vous aux réponses précédentes dans la conversation

## Support

Si vous rencontrez des problèmes:
- Le système invente des informations → Signalez-le (c'est un bug)
- Les réponses sont hors sujet → Reformulez votre question
- Pas de réponse après 30s → Rechargez la page

---

**Bon apprentissage ! 🎓**
