# Confidence Scoring System Guide

## Overview

The INPT RAG Assistant uses a sophisticated confidence scoring system to evaluate the reliability of its responses. This system combines multiple scoring mechanisms to provide users with a clear indication of how trustworthy each answer is.

## Confidence Score Components

### 1. Document Retrieval Scores

The system uses a **hybrid search approach** that combines two complementary scoring methods:

#### Semantic Scoring (70% weight)
- **Method**: Embedding-based similarity using cosine distance
- **Calculation**: 
  ```python
  if distance <= 1.0:
      similarity_score = 1 - distance
  else:
      similarity_score = 1 / (1 + distance)
  ```
- **Purpose**: Measures semantic similarity between the question and document content
- **Range**: 0.0 to 1.0 (higher = more semantically relevant)

#### BM25 Scoring (30% weight)
- **Method**: Traditional keyword-based scoring using BM25 algorithm
- **Factors**: Term frequency, document frequency, document length
- **Purpose**: Measures exact keyword matches and term importance
- **Range**: Variable (normalized to 0.0-1.0 range)

#### Hybrid Score Fusion
```python
final_document_score = (semantic_score × 0.7) + (bm25_score × 0.3)
```

### 2. Overall Confidence Calculation

The final confidence score displayed to users combines multiple factors:

#### Components (with weights):

1. **Average Search Score (60% weight)**
   - Mean score of the top 5 retrieved documents
   - Reflects how well the system found relevant information

2. **Response Length Score (30% weight)**
   - Formula: `min(response_length / 200, 1.0)`
   - Penalizes very short responses that may be incomplete

3. **Citation Bonus (10% boost)**
   - Added when the response contains source citations
   - Indicates the answer is grounded in retrieved documents

4. **Uncertainty Penalty (20% reduction)**
   - Applied when response contains uncertainty phrases:
     - "je ne sais pas" (I don't know)
     - "je n'ai pas" (I don't have)
     - "informations insuffisantes" (insufficient information)
     - "pas dans les documents" (not in the documents)

#### Final Calculation
```python
confidence = (avg_search_score × 0.6 + 
              length_score × 0.3 + 
              citation_bonus - 
              uncertainty_penalty)

# Clamped to [0.0, 1.0] range
confidence = max(0.0, min(1.0, confidence))
```

## Confidence Levels and Display

### Visual Indicators

The system displays confidence using color-coded badges:

| Confidence Range | Badge Color | Label | Meaning |
|-----------------|-------------|-------|---------|
| ≥ 70% | 🟢 Green | "Haute confiance" | High reliability, well-supported answer |
| 40-69% | 🟡 Yellow | "Confiance moyenne" | Moderate reliability, some uncertainty |
| < 40% | 🔴 Red | "Faible confiance" | Low reliability, answer may be incomplete |

### Badge Display Format
```html
<div class="confidence-badge high-confidence">
    🎯 Haute confiance (85%)
</div>
```

## Quality Filtering

### Minimum Confidence Threshold
- **Default**: 0.5 (50%)
- **Purpose**: Documents below this threshold are filtered out before response generation
- **Configurable**: Set via `SIMILARITY_THRESHOLD` in settings

### Source Scoring
Each source document displays its individual score:
```
[1] Document Title
Score: 0.87 • pages 1-3
```

## Configuration Parameters

### Adjustable Settings

| Parameter | Default | Description | Location |
|-----------|---------|-------------|----------|
| `semantic_weight` | 0.7 | Weight for semantic scoring | `HybridSearchEngine` |
| `bm25_weight` | 0.3 | Weight for BM25 scoring | `HybridSearchEngine` |
| `min_confidence` | 0.5 | Minimum document score threshold | `ResponseGenerator` |
| `max_sources` | 3 | Maximum sources in response | `ResponseGenerator` |
| `top_k_retrieval` | 5 | Number of documents to retrieve | `ResponseGenerator` |

### Environment Variables
```bash
# In .env file
SIMILARITY_THRESHOLD=0.5    # Minimum confidence for document inclusion
RERANK_TOP_K=3             # Maximum sources to display
TOP_K_RETRIEVAL=5          # Documents to retrieve initially
```

## Interpreting Confidence Scores

### High Confidence (≥70%)
- **Meaning**: The system found highly relevant documents that closely match your question
- **Reliability**: Answer is well-supported by source material
- **Action**: You can trust this information with high confidence

### Medium Confidence (40-69%)
- **Meaning**: Some relevant information found, but with gaps or partial matches
- **Reliability**: Answer is generally reliable but may need verification
- **Action**: Consider cross-referencing or asking follow-up questions

### Low Confidence (<40%)
- **Meaning**: Limited relevant information found in the document corpus
- **Reliability**: Answer may be incomplete or speculative
- **Action**: Reformulate your question or verify information independently

## Technical Implementation

### Key Classes and Methods

1. **`HybridSearchEngine`** (`src/retrieval/hybrid_search.py`)
   - Combines semantic and BM25 search
   - Normalizes and fuses scores

2. **`ResponseGenerator._calculate_confidence()`** (`src/llm/response_generator.py`)
   - Computes final confidence score
   - Applies penalties and bonuses

3. **`render_sources()`** (`app/chat.py`)
   - Displays confidence badges in UI
   - Shows individual source scores

### Score Flow
```
User Question
    ↓
Hybrid Search (Semantic + BM25)
    ↓
Document Scoring & Filtering
    ↓
Response Generation
    ↓
Confidence Calculation
    ↓
UI Display with Badge
```

## Troubleshooting Low Confidence

### Common Causes
1. **Question too specific**: No documents contain exact information
2. **Terminology mismatch**: Different words used in documents vs. question
3. **Insufficient context**: Question lacks necessary details
4. **Document quality**: Source materials don't cover the topic well

### Improvement Strategies
1. **Rephrase questions**: Use different terminology or broader terms
2. **Add context**: Provide more background information
3. **Check document coverage**: Ensure relevant materials are uploaded
4. **Use follow-up questions**: Break complex queries into smaller parts

## Advanced Features

### Contextual Scoring
- The system considers document structure and headers
- Contextual headers improve relevance scoring
- Clean content extraction enhances BM25 performance

### Conversation History
- Follow-up questions may use conversation context
- History usage is intelligently detected
- Confidence reflects both current and historical relevance

## Monitoring and Analytics

### Available Metrics
- Average confidence scores over time
- Distribution of confidence levels
- Correlation between confidence and user satisfaction
- Document retrieval quality metrics

### Access Analytics
Navigate to the Analytics page in the web interface to view:
- Confidence score trends
- Query performance statistics
- Document usage patterns

## Best Practices

### For Users
1. **Pay attention to confidence levels** when evaluating answers
2. **Ask follow-up questions** for medium/low confidence responses
3. **Provide feedback** to help improve the system
4. **Rephrase questions** if confidence is consistently low

### For Administrators
1. **Monitor confidence distributions** to identify system performance
2. **Adjust thresholds** based on use case requirements
3. **Improve document quality** to increase overall confidence
4. **Regular evaluation** using test question sets

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System overview and components
- [Advanced Analytics Guide](ADVANCED_ANALYTICS_GUIDE.md) - Detailed analytics features
- [API Documentation](API_DOCUMENTATION.md) - Programmatic access to confidence scores
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions