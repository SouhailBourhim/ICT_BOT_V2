# LLM Provider Guide

This guide explains how to use multiple LLM providers (Ollama, Google Gemini) with your RAG assistant.

## 🚀 Quick Start

### Option 1: Use the Startup Script (Recommended)

```bash
cd inpt-rag-assistant
./start_app.sh
```

This script will:
- Activate the virtual environment
- Check and install dependencies
- Test your LLM providers
- Start the Streamlit app

### Option 2: Manual Start

```bash
cd inpt-rag-assistant
source venv311/bin/activate
python test_llm_integration.py  # Test providers
streamlit run app/chat.py --server.port 8502
```

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Providers

Edit your `.env` file:

```bash
# Primary LLM provider
LLM_PROVIDER="gemini"  # or "ollama"
LLM_FALLBACK_PROVIDER="ollama"

# Google Gemini (API-based, fast)
GOOGLE_API_KEY="your_api_key_here"
GEMINI_MODEL="gemini-1.5-flash"

# Ollama (local, private)
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:3b"
```

### 3. Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API key"
4. Create a new API key
5. Copy it to your `.env` file

### 4. Test the Setup

```bash
python test_llm_integration.py
```

## 🤖 Available Providers

### Google Gemini (Recommended for Speed)

**Pros:**
- ⚡ Very fast responses (API-based)
- 💰 Cost-effective pricing
- 🧠 High-quality outputs
- 📚 Large context window

**Models:**
- `gemini-1.5-flash` - Fast and cheap (recommended)
- `gemini-1.5-pro` - More capable, higher cost
- `gemini-1.0-pro` - Older but reliable

**Pricing (approximate):**
- Flash: ~$0.075 per 1M input tokens
- Pro: ~$3.50 per 1M input tokens

### Ollama (Local)

**Pros:**
- 🔒 Complete privacy (runs locally)
- 💸 No API costs
- 🌐 Works offline
- 🎛️ Full control over models

**Cons:**
- 🐌 Slower than API models
- 💾 Requires local resources
- 🔧 Setup complexity

**Recommended Models:**
- `qwen2.5:3b` - Good balance of speed/quality
- `llama3.2:3b` - Alternative option
- `mistral:7b` - Higher quality, slower

## 🎯 Usage in the App

### Provider Selection

1. Open the Streamlit app
2. Check the sidebar "🤖 Modèle LLM" section
3. Select your preferred provider
4. Status indicators show availability:
   - ✅ Available and working
   - ❌ Not available or error

### Automatic Fallback

The system automatically falls back to secondary providers if the primary fails:

1. **Primary provider** (your selection)
2. **Fallback provider** (configured in settings)
3. **Any available provider**

### Performance Tips

**For Speed (Academic Presentations):**
- Use Gemini Flash as primary
- Set temperature to 0.1-0.3 for consistent results

**For Privacy (Sensitive Data):**
- Use Ollama as primary
- Keep Gemini as fallback for speed when needed

**For Cost Optimization:**
- Use Gemini Flash for most queries
- Use local Ollama for simple questions

## ⚙️ Configuration Options

### Environment Variables

```bash
# Provider Selection
LLM_PROVIDER="gemini"              # Primary provider
LLM_FALLBACK_PROVIDER="ollama"     # Fallback provider

# Gemini Configuration
GOOGLE_API_KEY="your_key"          # Required for Gemini
GEMINI_MODEL="gemini-1.5-flash"   # Model selection

# Ollama Configuration
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:3b"
OLLAMA_TIMEOUT=180

# General Settings
LLM_TEMPERATURE=0.1                # Creativity (0.0-1.0)
LLM_MAX_TOKENS=500                 # Response length
```

### Runtime Selection

You can also change providers during runtime:

```python
# In your code
response = await response_generator.generate_response(
    question="Your question",
    preferred_provider="gemini"  # Override default
)
```

## 🔧 Troubleshooting

### Gemini Issues

**"API key not found"**
- Check your `.env` file has `GOOGLE_API_KEY=your_key`
- Restart the application after adding the key

**"Model not found" or "404 models/gemini-1.5-flash is not found"**
- ✅ **FIXED**: Update to newer model names
- Use `gemini-2.5-flash` instead of `gemini-1.5-flash`
- Use `gemini-2.5-pro` instead of `gemini-1.5-pro`
- The 1.5 models have been deprecated by Google

**"Quota exceeded"**
- You've hit the free tier limit
- Wait for quota reset or upgrade your plan

### Ollama Issues

**"Connection refused"**
- Make sure Ollama is running: `ollama serve`
- Check the URL in `OLLAMA_BASE_URL`

**"Model not found"**
- Pull the model: `ollama pull qwen2.5:3b`
- Check available models: `ollama list`

**Slow responses**
- Try a smaller model: `qwen2.5:1.5b`
- Increase timeout: `OLLAMA_TIMEOUT=300`

### General Issues

**"KeyError: 'ollama'" in chat.py**
- ✅ **FIXED**: Updated to use new LLM manager system
- The system now uses `llm_manager` instead of direct provider access

**"No providers available"**
- Run the test script: `python test_llm_integration.py`
- Check both Ollama and Gemini configurations

**Import errors**
- Install dependencies: `pip install -r requirements.txt`
- Check Python path and virtual environment

## 📊 Performance Comparison

| Provider | Speed | Cost | Privacy | Quality | Setup |
|----------|-------|------|---------|---------|-------|
| Gemini Flash | ⚡⚡⚡ | 💰 | ⚠️ | ⭐⭐⭐ | ✅ |
| Gemini Pro | ⚡⚡ | 💰💰💰 | ⚠️ | ⭐⭐⭐⭐ | ✅ |
| Ollama 3B | ⚡ | 🆓 | 🔒🔒🔒 | ⭐⭐ | 🔧 |
| Ollama 7B | 🐌 | 🆓 | 🔒🔒🔒 | ⭐⭐⭐ | 🔧 |

## 🎓 Academic Use Recommendations

### For Presentations/Demos
- **Primary:** Gemini Flash (fast, reliable)
- **Fallback:** Ollama (backup if internet issues)
- **Temperature:** 0.1-0.3 (consistent results)

### For Development/Testing
- **Primary:** Ollama (no API costs)
- **Fallback:** Gemini (when you need speed)
- **Temperature:** 0.5-0.7 (more creative)

### For Production/Deployment
- **Primary:** Gemini Flash (scalable)
- **Fallback:** Gemini Pro (higher quality when needed)
- **Monitor:** API usage and costs

## 🔄 Migration from Ollama-Only

If you're upgrading from the old Ollama-only system:

1. **Update dependencies:** `pip install -r requirements.txt`
2. **Update .env:** Add the new LLM configuration variables
3. **Test setup:** Run `python test_llm_integration.py`
4. **Restart app:** Your existing conversations will work with new providers

The system is backward compatible - your existing setup will continue working while gaining new capabilities.

## 📞 Support

If you encounter issues:

1. **Run the test script:** `python test_llm_integration.py`
2. **Check logs:** Look for error messages in the console
3. **Verify configuration:** Ensure API keys and URLs are correct
4. **Test providers individually:** Use the Streamlit sidebar to test each provider

The system is designed to be robust with automatic fallbacks, so even if one provider fails, others should continue working.