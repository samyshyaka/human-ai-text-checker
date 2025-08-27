from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for Llama API
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.llama.com/v1/chat/completions")

class AnalyzeRequest(BaseModel):
    text: str

class LlamaAPIClient:
    def __init__(self):
        self.api_key = LLAMA_API_KEY
        self.api_url = LLAMA_API_URL
        
        if not self.api_key:
            raise ValueError("No API key found. Please set LLAMA_API_KEY environment variable.")
    
    async def analyze_text_with_llama(self, text: str, context: str) -> Dict:
        """Send text to Llama API for human vs AI analysis"""
        # Create a more robust prompt that handles multi-paragraph text
        prompt = f"""Context: {context}

Analyze the following text and determine the probability that it was written by AI versus a human.

Consider factors like:
- Writing patterns and consistency across paragraphs
- Vocabulary usage and complexity
- Sentence structure and flow
- Creative elements and personal touches
- Error patterns typical of AI or human writing
- Paragraph transitions and coherence
- Personal anecdotes or experiences
- Emotional authenticity

Text to analyze:
---
{text}
---

Respond with a JSON object containing:
- ai_probability: float between 0 and 1
- human_probability: float between 0 and 1  
- reasoning: brief explanation of your analysis

Format your response as valid JSON only."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert AI detector that can analyze text and determine if it was written by AI or humans. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Debug: Print the full response structure
                        print(f"🔍 Full API Response: {result}")
                        
                        # Try multiple response formats
                        content = None
                        
                        # Format 1: Llama API specific format with completion_message
                        if "completion_message" in result:
                            completion_msg = result["completion_message"]
                            # Handle nested structure: completion_message.content.text
                            if isinstance(completion_msg, dict) and "content" in completion_msg:
                                if isinstance(completion_msg["content"], dict) and "text" in completion_msg["content"]:
                                    content = completion_msg["content"]["text"]
                                else:
                                    content = completion_msg["content"]
                            else:
                                content = completion_msg
                        
                        # Format 2: OpenAI-style response with choices
                        elif "choices" in result and len(result["choices"]) > 0:
                            if "message" in result["choices"][0]:
                                content = result["choices"][0]["message"]["content"]
                            elif "text" in result["choices"][0]:
                                content = result["choices"][0]["text"]
                        
                        # Format 3: Direct content response
                        elif "content" in result:
                            content = result["content"]
                        
                        # Format 4: Direct text response
                        elif "text" in result:
                            content = result["text"]
                        
                        # Format 5: Response field
                        elif "response" in result:
                            content = result["response"]
                        
                        if content:
                            # Ensure content is a string before slicing
                            content_str = str(content)
                            print(f"📝 Extracted content: {content_str[:200]}...")
                            
                            # Try to parse the JSON response from Llama
                            try:
                                import json
                                import re
                                
                                print(f"🔧 Attempting JSON parsing...")
                                print(f"📝 Content type: {type(content)}")
                                print(f"📝 Content preview: {str(content)[:500]}...")
                                
                                # Ensure content is a string before JSON parsing
                                if isinstance(content, str):
                                    # Remove markdown code block formatting if present
                                    content_clean = content.strip()
                                    print(f"🧹 Content after strip: {content_clean[:200]}...")
                                    
                                    if content_clean.startswith("```json") and content_clean.endswith("```"):
                                        # Extract JSON from markdown code block
                                        content_clean = re.sub(r'^```json\s*\n?', '', content_clean)
                                        content_clean = re.sub(r'\n?```$', '', content_clean)
                                        print(f"📦 Removed ```json markers: {content_clean[:200]}...")
                                    elif content_clean.startswith("```") and content_clean.endswith("```"):
                                        # Handle generic code block
                                        content_clean = re.sub(r'^```[a-zA-Z]*\s*\n?', '', content_clean)
                                        content_clean = re.sub(r'\n?```$', '', content_clean)
                                        print(f"📦 Removed generic markers: {content_clean[:200]}...")
                                    
                                    print(f"🧹 Final cleaned content: {content_clean[:200]}...")
                                    analysis = json.loads(content_clean.strip())
                                    print(f"✅ JSON parsing successful!")
                                    print(f"📊 Parsed analysis keys: {list(analysis.keys())}")
                                    print(f"📊 Full parsed analysis: {analysis}")
                                elif isinstance(content, dict):
                                    # Content is already a dictionary
                                    print(f"✅ Content is already a dict with keys: {list(content.keys())}")
                                    analysis = content
                                else:
                                    # Convert to string and try parsing
                                    content_str = str(content)
                                    print(f"🔄 Converting to string: {content_str[:200]}...")
                                    analysis = json.loads(content_str)
                                    print(f"✅ JSON parsing successful after conversion!")
                                
                                # Get the exact probabilities from Llama's response
                                print(f"🎯 Extracting probabilities from analysis...")
                                ai_prob = float(analysis.get("ai_probability", 0.5))
                                human_prob = float(analysis.get("human_probability", 0.5))
                                
                                print(f"📊 Raw extracted values - AI: {ai_prob}, Human: {human_prob}")
                                
                                # Only normalize if both values are provided
                                if "ai_probability" in analysis and "human_probability" in analysis:
                                    # Use Llama's exact values
                                    print(f"✅ Both probabilities found in analysis - using exact values")
                                    pass
                                elif "ai_probability" in analysis:
                                    # Only ai_probability provided, calculate human_probability
                                    human_prob = 1.0 - ai_prob
                                    print(f"⚠️ Only AI probability found - calculated human: {human_prob}")
                                elif "human_probability" in analysis:
                                    # Only human_probability provided, calculate ai_probability
                                    ai_prob = 1.0 - human_prob
                                    print(f"⚠️ Only human probability found - calculated AI: {ai_prob}")
                                else:
                                    # Neither provided, use defaults
                                    print(f"❌ No probabilities found in analysis - using defaults")
                                    ai_prob = 0.5
                                    human_prob = 0.5
                                
                                print(f"🎯 Final probabilities - AI: {ai_prob}, Human: {human_prob}")
                                
                                print(f"🎯 FINAL RESULT - Using JSON parsing success path")
                                print(f"🎯 Final probabilities - AI: {ai_prob}, Human: {human_prob}")
                                print(f"🎯 Source: Direct from Llama JSON response")
                                
                                return {
                                    "ai_probability": ai_prob,
                                    "human_probability": human_prob,
                                    "reasoning": analysis.get("reasoning", "Analysis completed"),
                                    "raw_response": content,
                                    "debug_api_response": result,
                                    "llama_analysis": analysis,  # Include the full parsed analysis
                                    "source": "llama_json_parsing",
                                    "extraction_method": "json_success"
                                }
                            except json.JSONDecodeError:
                                # Fallback if JSON parsing fails - try to extract info from text
                                print(f"⚠️  JSON parsing failed, using text analysis fallback")
                                
                                # Text analysis fallback - try to extract meaningful information
                                content_str = str(content)
                                content_lower = content_str.lower()
                                
                                # Look for probability indicators in the text
                                ai_prob = 0.5  # Default neutral
                                human_prob = 0.5
                                
                                # Try to find probability numbers in the text
                                import re
                                
                                # Debug: Print what we're searching in
                                print(f"🔍 Searching for numbers in: {content_str[:300]}...")
                                
                                # Look for various number formats
                                prob_matches = re.findall(r'(\d+(?:\.\d+)?)', content_str)
                                print(f"📊 Found number matches: {prob_matches}")
                                
                                # Also look for JSON-like patterns - more aggressive extraction
                                json_pattern = r'"ai_probability":\s*(\d+(?:\.\d+)?)'
                                ai_match = re.search(json_pattern, content_str)
                                human_match = re.search(r'"human_probability":\s*(\d+(?:\.\d+)?)', content_str)
                                
                                # Also try without quotes (in case of different formatting)
                                ai_match_no_quotes = re.search(r'ai_probability:\s*(\d+(?:\.\d+)?)', content_str, re.IGNORECASE)
                                human_match_no_quotes = re.search(r'human_probability:\s*(\d+(?:\.\d+)?)', content_str, re.IGNORECASE)
                                
                                # Try to find any decimal numbers that look like probabilities
                                prob_pattern = r'\b(?:ai|human)?\s*probability\s*[=:]\s*(\d+(?:\.\d+)?)'
                                prob_matches = re.findall(prob_pattern, content_str, re.IGNORECASE)
                                print(f"🔍 Probability pattern matches: {prob_matches}")
                                
                                if ai_match and human_match:
                                    # Both probabilities found
                                    ai_prob = float(ai_match.group(1))
                                    human_prob = float(human_match.group(1))
                                    print(f"✅ Extracted both from JSON: AI={ai_prob}, Human={human_prob}")
                                elif ai_match_no_quotes and human_match_no_quotes:
                                    # Both probabilities found without quotes
                                    ai_prob = float(ai_match_no_quotes.group(1))
                                    human_prob = float(human_match_no_quotes.group(1))
                                    print(f"✅ Extracted both from JSON (no quotes): AI={ai_prob}, Human={human_prob}")
                                elif ai_match or ai_match_no_quotes:
                                    # Only AI probability found
                                    match = ai_match if ai_match else ai_match_no_quotes
                                    ai_prob = float(match.group(1))
                                    human_prob = 1.0 - ai_prob
                                    print(f"✅ Extracted AI from JSON: AI={ai_prob}, Human={human_prob}")
                                elif human_match or human_match_no_quotes:
                                    # Only human probability found
                                    match = human_match if human_match else human_match_no_quotes
                                    human_prob = float(match.group(1))
                                    ai_prob = 1.0 - human_prob
                                    print(f"✅ Extracted Human from JSON: AI={ai_prob}, Human={human_prob}")
                                elif prob_matches:
                                    try:
                                        # Look for the first probability number
                                        first_prob = float(prob_matches[0])
                                        if 0 <= first_prob <= 1:
                                            ai_prob = first_prob
                                            human_prob = 1.0 - first_prob
                                            print(f"✅ Extracted from number pattern: AI={ai_prob}, Human={human_prob}")
                                    except ValueError:
                                        print(f"❌ Could not convert {first_prob} to float")
                                        pass
                                
                                # If we still don't have valid probabilities, try to extract from the raw content
                                if ai_prob == 0.5:
                                    print(f"🔍 Attempting to extract probabilities from raw content...")
                                    # Look for any decimal numbers in the content
                                    decimal_pattern = r'\b0\.\d+\b'
                                    decimal_matches = re.findall(decimal_pattern, content_str)
                                    print(f"📊 Found decimal matches: {decimal_matches}")
                                    
                                    if len(decimal_matches) >= 2:
                                        try:
                                            # Use the first two decimal numbers found
                                            ai_prob = float(decimal_matches[0])
                                            human_prob = float(decimal_matches[1])
                                            print(f"✅ Extracted from decimal pattern: AI={ai_prob}, Human={human_prob}")
                                        except ValueError:
                                            print(f"❌ Could not convert decimals to float")
                                    elif len(decimal_matches) == 1:
                                        try:
                                            ai_prob = float(decimal_matches[0])
                                            human_prob = 1.0 - ai_prob
                                            print(f"✅ Extracted single decimal: AI={ai_prob}, Human={human_prob}")
                                        except ValueError:
                                            print(f"❌ Could not convert decimal to float")
                                
                                print(f"🎯 FINAL RESULT - Using fallback path")
                                print(f"🎯 Final probabilities - AI: {ai_prob}, Human: {human_prob}")
                                print(f"🎯 Source: Text analysis fallback (JSON parsing failed)")
                                
                                return {
                                    "ai_probability": ai_prob,
                                    "human_probability": human_prob,
                                    "reasoning": f"Text analysis fallback - JSON parsing failed. Extracted probabilities from text: AI={ai_prob}, Human={human_prob}",
                                    "raw_response": content,
                                    "debug_api_response": result,
                                    "fallback_method": "text_analysis",
                                    "note": "This is a fallback response. Check server logs to see why JSON parsing failed.",
                                    "source": "fallback_text_analysis",
                                    "extraction_method": "fallback"
                                }
                        else:
                            print(f"❌ Could not extract content from response: {result}")
                            raise HTTPException(
                                status_code=500, 
                                detail=f"Could not extract content from API response. Response keys: {list(result.keys())}"
                            )
                    else:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status, 
                            detail=f"Llama API error: {error_text}"
                        )
                        
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Initialize the Llama API client
try:
    llama_client = LlamaAPIClient()
except ValueError as e:
    print(f"Warning: {e}")
    llama_client = None

# Real RAG Implementation
import chromadb
from sentence_transformers import SentenceTransformer
import json
import os

class RAGSystem:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "ai_detection_knowledge"
        self.setup_collection()
        self.initialize_knowledge_base()
    
    def setup_collection(self):
        """Setup ChromaDB collection for AI detection knowledge"""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI detection knowledge base"}
            )
    
    def initialize_knowledge_base(self):
        """Initialize with real AI detection knowledge"""
        if self.collection.count() == 0:
            knowledge_items = [
                {
                    "text": "AI-generated text often exhibits repetitive patterns, overly consistent sentence structures, and lacks natural variation in writing style. The vocabulary tends to be more uniform and predictable.",
                    "metadata": {"category": "ai_patterns", "source": "research"}
                },
                {
                    "text": "Human writing typically shows more natural variation in sentence length, vocabulary diversity, and emotional expression. Personal anecdotes and unique experiences are common indicators of human authorship.",
                    "metadata": {"category": "human_patterns", "source": "research"}
                },
                {
                    "text": "AI text often has perfect grammar and punctuation, while human writing may contain minor errors, contractions, and informal language patterns that reflect natural communication.",
                    "metadata": {"category": "grammar_patterns", "source": "research"}
                },
                {
                    "text": "Human writers tend to use more context-specific references, cultural nuances, and personal opinions that reflect individual experiences and background knowledge.",
                    "metadata": {"category": "context_patterns", "source": "research"}
                },
                {
                    "text": "AI-generated content may show sudden topic shifts without natural transitions, while human writing typically flows more organically between related ideas.",
                    "metadata": {"category": "flow_patterns", "source": "research"}
                }
            ]
            
            # Add documents to collection
            texts = [item["text"] for item in knowledge_items]
            metadatas = [item["metadata"] for item in knowledge_items]
            ids = [f"doc_{i}" for i in range(len(knowledge_items))]
            
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Initialized knowledge base with {len(knowledge_items)} items")
    
    def retrieve_relevant_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context using semantic search"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search for similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if results['documents'] and results['documents'][0]:
                # Combine relevant contexts
                contexts = results['documents'][0]
                combined_context = "\n\n".join(contexts)
                print(f"🔍 Retrieved {len(contexts)} relevant contexts")
                return combined_context
            else:
                return "AI detection patterns and human writing characteristics."
                
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}")
            return "AI detection patterns and human writing characteristics."

# Initialize RAG system
rag_system = RAGSystem()

def rag_retrieve(query: str) -> str:
    """Enhanced RAG retrieval using real semantic search"""
    return rag_system.retrieve_relevant_context(query)

@app.post("/analyze")
async def analyze_text(request: AnalyzeRequest) -> Dict:
    text = request.text
    
    # Validate input
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # RAG: retrieve context
    context = rag_retrieve(text)
    
    # Check if Llama client is available
    if llama_client is None:
        # Fallback to dummy data if no API key is configured
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "context": context,
            "reasoning": "No API key configured - using fallback response",
            "status": "fallback"
        }
    
    try:
        # Use Llama API for analysis
        analysis_result = await llama_client.analyze_text_with_llama(text, context)
        
        # Add context to the response
        analysis_result["context"] = context
        analysis_result["status"] = "success"
        
        return analysis_result
        
    except Exception as e:
        # Fallback to dummy data if API call fails
        print(f"Llama API call failed: {e}")
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "context": context,
            "reasoning": f"API call failed: {str(e)}",
            "status": "error_fallback"
        }

@app.get("/rag/test")
async def test_rag():
    """Test RAG system with sample queries"""
    test_queries = [
        "How can I detect AI-generated text?",
        "What are the characteristics of human writing?",
        "Tell me about grammar patterns in AI vs human text"
    ]
    
    results = {}
    for query in test_queries:
        context = rag_system.retrieve_relevant_context(query)
        results[query] = {
            "retrieved_context": context[:200] + "..." if len(context) > 200 else context,
            "context_length": len(context)
        }
    
    return {
        "status": "RAG test completed",
        "collection_count": rag_system.collection.count(),
        "test_results": results
    }

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API status"""
    api_status = "configured" if llama_client is not None else "not_configured"
    
    debug_info = {
        "status": "healthy",
        "llama_api": api_status,
        "message": "Human-AI Text Checker API is running"
    }
    
    if llama_client is not None:
        debug_info.update({
            "api_url": llama_client.api_url,
            "api_key_preview": f"{llama_client.api_key[:10]}...{llama_client.api_key[-4:] if len(llama_client.api_key) > 14 else '***'}",
            "model": os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8")
        })
    
    debug_info["app_name"] = "AI vs Human Text Checker"
    
    return debug_info

@app.get("/debug/test-simple")
async def test_simple():
    """Simple test to see exact API response format"""
    if llama_client is None:
        return {"error": "No API client configured"}
    
    headers = {
        "Authorization": f"Bearer {llama_client.api_key}",
        "Content-Type": "application/json"
    }
    
    simple_payload = {
        "model": os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 20
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(llama_client.api_url, json=simple_payload, headers=headers) as response:
                status = response.status
                
                if status == 200:
                    response_json = await response.json()
                    return {
                        "status_code": status,
                        "success": True,
                        "full_response": response_json,
                        "response_keys": list(response_json.keys()),
                        "api_url": llama_client.api_url,
                        "model": simple_payload["model"]
                    }
                else:
                    response_text = await response.text()
                    return {
                        "status_code": status,
                        "success": False,
                        "error_response": response_text,
                        "api_url": llama_client.api_url,
                        "model": simple_payload["model"]
                    }
    except Exception as e:
        return {
            "error": str(e),
            "api_url": llama_client.api_url,
            "model": simple_payload["model"]
        } 