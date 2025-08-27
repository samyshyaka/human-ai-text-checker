# FastAPI Backend - Human-AI Text Checker

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Llama API:
   Create a `.env` file in the server directory with your API credentials:
   ```bash
   # Official Llama API (api.llama.com)
   LLAMA_API_KEY=your_llama_api_key_here
   LLAMA_API_URL=https://api.llama.com/v1/chat/completions
   LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8

   # Alternative: Together AI (if using together.ai)
   # TOGETHER_API_KEY=your_together_api_key_here
   # TOGETHER_API_URL=https://api.together.xyz/v1/chat/completions
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

The backend will be available at http://127.0.0.1:8000/

## API Endpoints

- `POST /analyze` - Analyze text to determine if it's AI or human-generated
- `GET /health` - Check API health status and Llama API configuration

## Llama API Providers

This backend supports multiple Llama API providers:

1. **Together AI** (Recommended)
   - Sign up at https://together.ai/
   - Get API key from dashboard
   - Set `TOGETHER_API_KEY` and `TOGETHER_API_URL`

2. **Hugging Face Inference API**
   - Sign up at https://huggingface.co/
   - Get API token from settings
   - Use model-specific endpoints

3. **OpenAI-compatible endpoints**
   - Any provider that supports OpenAI's chat completions format
   - Set appropriate `LLAMA_API_KEY` and `LLAMA_API_URL`

## Example Usage

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is a sample text to analyze."}'
```

The API will return a JSON response with AI/human probability scores and reasoning. 