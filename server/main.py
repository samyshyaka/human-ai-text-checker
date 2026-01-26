from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import os
import aiohttp
import json
import re
from dotenv import load_dotenv

# LangChain imports
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import LlamaCpp
from langchain_openai import ChatOpenAI
import chromadb

# Load environment variables
load_dotenv()

app = FastAPI(title="Human-AI Text Checker API")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.llama.com/v1/chat/completions")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8")

class AnalyzeRequest(BaseModel):
    text: str

class LlamaAPIClient:
    def __init__(self):
        self.api_key = LLAMA_API_KEY
        self.api_url = LLAMA_API_URL
        self.model = LLAMA_MODEL
        
        if not self.api_key:
            raise ValueError("No API key found. Please set LLAMA_API_KEY environment variable.")
    
    async def analyze_text(self, text: str) -> Dict:
        """Analyze text using Llama API for AI vs Human detection"""
        
        prompt = f"""Analyze the following text and determine the probability that it was written by AI versus a human.

Consider factors like:
- Writing patterns and consistency
- Vocabulary usage and complexity
- Sentence structure and flow
- Creative elements and personal touches
- Error patterns typical of AI or human writing
- Paragraph transitions and coherence
- Personal anecdotes or experiences
- Emotional authenticity

Text to analyze:
{text}

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
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert AI detector. Always respond with valid JSON."
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
                        return self._parse_response(result)
                    else:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status, 
                            detail=f"API error: {error_text}"
                        )
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    def _parse_response(self, result: dict) -> Dict:
        """Parse API response and extract analysis results"""
        
        # Extract content from various response formats
        content = self._extract_content(result)
        
        if not content:
            raise HTTPException(
                status_code=500, 
                detail="Could not extract content from API response"
            )
        
        try:
            # Clean and parse JSON response
            analysis = self._parse_json_content(content)
            return self._format_analysis_result(analysis, content)
            
        except json.JSONDecodeError:
            # Fallback: extract probabilities from text
            return self._extract_from_text(content)
    
    def _extract_content(self, result: dict) -> Optional[str]:
        """Extract content from API response in various formats"""
        
        # Format 1: Llama API with completion_message
        if "completion_message" in result:
            completion_msg = result["completion_message"]
            if isinstance(completion_msg, dict) and "content" in completion_msg:
                if isinstance(completion_msg["content"], dict) and "text" in completion_msg["content"]:
                    return completion_msg["content"]["text"]
                else:
                    return str(completion_msg["content"])
        
        # Format 2: OpenAI-style response with choices
        elif "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        
        # Format 3: Direct content/text fields
        elif "content" in result:
            return str(result["content"])
        elif "text" in result:
            return str(result["text"])
        elif "response" in result:
            return str(result["response"])
        
        return None
    
    def _parse_json_content(self, content: str) -> dict:
        """Parse JSON content, handling various formatting issues"""
        
        # Clean content
        content_clean = content.strip()
        
        # Remove markdown code blocks if present
        if content_clean.startswith("```json") and content_clean.endswith("```"):
            content_clean = re.sub(r'^```json\s*\n?', '', content_clean)
            content_clean = re.sub(r'\n?```$', '', content_clean)
        elif content_clean.startswith("```") and content_clean.endswith("```"):
            content_clean = re.sub(r'^```[a-zA-Z]*\s*\n?', '', content_clean)
            content_clean = re.sub(r'\n?```$', '', content_clean)
        
        return json.loads(content_clean.strip())
    
    def _format_analysis_result(self, analysis: dict, raw_content: str) -> Dict:
        """Format the analysis result with proper probabilities"""
        
        ai_prob = float(analysis.get("ai_probability", 0.5))
        human_prob = float(analysis.get("human_probability", 0.5))
        
        # Normalize probabilities if only one is provided
        if "ai_probability" in analysis and "human_probability" not in analysis:
            human_prob = 1.0 - ai_prob
        elif "human_probability" in analysis and "ai_probability" not in analysis:
            ai_prob = 1.0 - human_prob
        elif "ai_probability" not in analysis and "human_probability" not in analysis:
            ai_prob = 0.5
            human_prob = 0.5
        
        return {
            "ai_probability": ai_prob,
            "human_probability": human_prob,
            "reasoning": analysis.get("reasoning", "Analysis completed"),
            "raw_response": raw_content,
            "source": "llama_api"
        }
    
    def _extract_from_text(self, content: str) -> Dict:
        """Fallback: extract probabilities from text using regex"""
        
        content_lower = content.lower()
        ai_prob = 0.5
        human_prob = 0.5
        
        # Try to find probability numbers in the text
        ai_match = re.search(r'"ai_probability":\s*(\d+(?:\.\d+)?)', content)
        human_match = re.search(r'"human_probability":\s*(\d+(?:\.\d+)?)', content)
        
        if ai_match and human_match:
            ai_prob = float(ai_match.group(1))
            human_prob = float(human_match.group(1))
        elif ai_match:
            ai_prob = float(ai_match.group(1))
            human_prob = 1.0 - ai_prob
        elif human_match:
            human_prob = float(human_match.group(1))
            ai_prob = 1.0 - human_prob
        
        return {
            "ai_probability": ai_prob,
            "human_probability": human_prob,
            "reasoning": "Extracted from text analysis (JSON parsing failed)",
            "raw_response": content,
            "source": "text_fallback"
        }

# Initialize the Llama API client
try:
    llama_client = LlamaAPIClient()
except ValueError as e:
    print(f"Warning: {e}")
    llama_client = None

class LangChainRAGSystem:
    """LangChain RAG system for enhanced text analysis with vector search"""
    
    def __init__(self):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize vector store
        self.vectorstore = None
        self.setup_vectorstore()
        self.initialize_knowledge_base()
        
        # Initialize LLM (using OpenAI-compatible interface)
        self.llm = None
        self.setup_llm()
    
    def setup_vectorstore(self):
        """Setup ChromaDB vectorstore through LangChain"""
        try:
            # Try to load existing vectorstore
            self.vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings,
                collection_name="ai_detection_knowledge"
            )
            print("✅ Loaded existing LangChain vectorstore")
        except Exception as e:
            print(f"Creating new vectorstore: {e}")
            # Create new vectorstore
            self.vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings,
                collection_name="ai_detection_knowledge"
            )
            print("✅ Created new LangChain vectorstore")
    
    def setup_llm(self):
        """Setup LLM for LangChain analysis"""
        try:
            # Use OpenAI-compatible interface with Llama API
            if LLAMA_API_KEY and LLAMA_API_URL:
                self.llm = ChatOpenAI(
                    model=LLAMA_MODEL,
                    openai_api_key=LLAMA_API_KEY,
                    openai_api_base=LLAMA_API_URL,
                    temperature=0.3,
                    max_tokens=500
                )
                print("✅ Initialized LangChain LLM with Llama API")
            else:
                print("⚠️ No API credentials for LangChain LLM")
        except Exception as e:
            print(f"⚠️ Failed to setup LangChain LLM: {e}")
            self.llm = None
    
    def initialize_knowledge_base(self):
        """Initialize knowledge base with AI detection patterns"""
        try:
            if self.vectorstore._collection.count() == 0:
                knowledge_items = [
                    {
                        "text": "AI-generated text often exhibits repetitive patterns, overly consistent sentence structures, and lacks natural variation in writing style. The vocabulary tends to be more uniform and predictable, with fewer colloquialisms or personal expressions.",
                        "metadata": {"category": "ai_patterns", "source": "research", "type": "style"}
                    },
                    {
                        "text": "Human writing typically shows more natural variation in sentence length, vocabulary diversity, and emotional expression. Personal anecdotes, unique experiences, and individual voice are common indicators of human authorship.",
                        "metadata": {"category": "human_patterns", "source": "research", "type": "style"}
                    },
                    {
                        "text": "AI text often has perfect grammar and punctuation, while human writing may contain minor errors, contractions, informal language patterns, and natural speech rhythms that reflect authentic communication.",
                        "metadata": {"category": "grammar_patterns", "source": "research", "type": "grammar"}
                    },
                    {
                        "text": "Human writers tend to use more context-specific references, cultural nuances, personal opinions, and domain-specific knowledge that reflect individual experiences and background.",
                        "metadata": {"category": "context_patterns", "source": "research", "type": "context"}
                    },
                    {
                        "text": "AI-generated content may show sudden topic shifts without natural transitions, while human writing typically flows more organically between related ideas with smoother paragraph transitions.",
                        "metadata": {"category": "flow_patterns", "source": "research", "type": "flow"}
                    },
                    {
                        "text": "Human writing often contains emotional authenticity, personal stakes, and genuine reactions to events, while AI text may feel more detached or lack emotional depth.",
                        "metadata": {"category": "emotional_patterns", "source": "research", "type": "emotion"}
                    },
                    {
                        "text": "AI text tends to be more verbose and may include unnecessary details or repetitive explanations, while human writing is typically more concise and focused.",
                        "metadata": {"category": "verbosity_patterns", "source": "research", "type": "verbosity"}
                    },
                    {
                        "text": "Human writers often use specific examples, personal experiences, and unique perspectives that reflect their individual background and expertise.",
                        "metadata": {"category": "specificity_patterns", "source": "research", "type": "specificity"}
                    }
                ]
                
                # Split and add documents to vectorstore
                for item in knowledge_items:
                    chunks = self.text_splitter.split_text(item["text"])
                    for chunk in chunks:
                        self.vectorstore.add_texts(
                            texts=[chunk],
                            metadatas=[item["metadata"]]
                        )
                
                self.vectorstore.persist()
                print(f"✅ Initialized LangChain knowledge base with {len(knowledge_items)} knowledge items")
        except Exception as e:
            print(f"⚠️ Failed to initialize knowledge base: {e}")
    
    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant context using semantic search"""
        try:
            # Search for similar documents
            docs = self.vectorstore.similarity_search(query, k=top_k)
            
            if docs:
                # Combine relevant contexts
                contexts = [doc.page_content for doc in docs]
                combined_context = "\n\n".join(contexts)
                print(f"🔍 Retrieved {len(contexts)} relevant contexts for LangChain analysis")
                return combined_context
            else:
                return "AI detection patterns and human writing characteristics."
                
        except Exception as e:
            print(f"⚠️ LangChain RAG retrieval failed: {e}")
            return "AI detection patterns and human writing characteristics."
    
    def analyze_with_langchain(self, text: str, context: str) -> Dict:
        """Analyze text using LangChain with structured prompt and LLM"""
        
        if not self.llm:
            return {
                "ai_probability": 0.5,
                "human_probability": 0.5,
                "reasoning": "LangChain LLM not available",
                "key_indicators": ["LLM not configured"],
                "confidence": 0.0,
                "method": "langchain_fallback"
            }
        
        # Create structured prompt template
        prompt_template = PromptTemplate(
            input_variables=["text", "context"],
            template="""You are an expert AI text detector. Analyze the following text to determine if it was written by a human or generated by AI.

Context about AI vs Human text patterns:
{context}

Text to analyze:
{text}

Please provide your analysis in the following JSON format:
{{
    "ai_probability": <float between 0.0 and 1.0>,
    "human_probability": <float between 0.0 and 1.0>,
    "reasoning": "<detailed explanation of your analysis>",
    "key_indicators": ["<indicator1>", "<indicator2>", "<indicator3>"],
    "confidence": <float between 0.0 and 1.0>
}}

Focus on:
- Writing style consistency and natural variation
- Vocabulary diversity and complexity
- Grammar patterns and error types
- Emotional expression and authenticity
- Context awareness and personal touches
- Natural flow and transitions
- Specificity of examples and references

Analysis:"""
        )
        
        try:
            # Create LLM chain
            llm_chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template,
                verbose=False
            )
            
            # Run the analysis
            result = llm_chain.run(text=text, context=context)
            
            # Parse the result
            try:
                # Clean the result
                result_clean = result.strip()
                if result_clean.startswith("```json"):
                    result_clean = re.sub(r'^```json\s*\n?', '', result_clean)
                    result_clean = re.sub(r'\n?```$', '', result_clean)
                elif result_clean.startswith("```"):
                    result_clean = re.sub(r'^```[a-zA-Z]*\s*\n?', '', result_clean)
                    result_clean = re.sub(r'\n?```$', '', result_clean)
                
                analysis = json.loads(result_clean)
                
                # Ensure probabilities are valid
                ai_prob = float(analysis.get("ai_probability", 0.5))
                human_prob = float(analysis.get("human_probability", 0.5))
                
                # Normalize if needed
                if "ai_probability" in analysis and "human_probability" not in analysis:
                    human_prob = 1.0 - ai_prob
                elif "human_probability" in analysis and "ai_probability" not in analysis:
                    ai_prob = 1.0 - human_prob
                
                return {
                    "ai_probability": ai_prob,
                    "human_probability": human_prob,
                    "reasoning": analysis.get("reasoning", "LangChain analysis completed"),
                    "key_indicators": analysis.get("key_indicators", ["LangChain analysis"]),
                    "confidence": float(analysis.get("confidence", 0.8)),
                    "method": "langchain_rag",
                    "context_used": context[:200] + "..." if len(context) > 200 else context
                }
                
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_langchain_fallback(result, context)
                
        except Exception as e:
            print(f"⚠️ LangChain analysis failed: {e}")
            return {
                "ai_probability": 0.5,
                "human_probability": 0.5,
                "reasoning": f"LangChain analysis failed: {str(e)}",
                "key_indicators": ["Error occurred"],
                "confidence": 0.0,
                "method": "langchain_error"
            }
    
    def _parse_langchain_fallback(self, result: str, context: str) -> Dict:
        """Fallback parsing for LangChain results"""
        
        # Try to extract probabilities using regex
        ai_match = re.search(r'"ai_probability":\s*(\d+(?:\.\d+)?)', result)
        human_match = re.search(r'"human_probability":\s*(\d+(?:\.\d+)?)', result)
        
        ai_prob = 0.5
        human_prob = 0.5
        
        if ai_match and human_match:
            ai_prob = float(ai_match.group(1))
            human_prob = float(human_match.group(1))
        elif ai_match:
            ai_prob = float(ai_match.group(1))
            human_prob = 1.0 - ai_prob
        elif human_match:
            human_prob = float(human_match.group(1))
            ai_prob = 1.0 - human_prob
        
        return {
            "ai_probability": ai_prob,
            "human_probability": human_prob,
            "reasoning": f"LangChain analysis with context-aware RAG: {context[:100]}...",
            "key_indicators": ["RAG-enhanced", "Context-aware", "LangChain-powered"],
            "confidence": 0.7,
            "method": "langchain_rag_fallback",
            "raw_result": result
        }

# Initialize LangChain RAG system
try:
    rag_system = LangChainRAGSystem()
    print("✅ LangChain RAG system initialized successfully")
except Exception as e:
    print(f"⚠️ Failed to initialize LangChain RAG system: {e}")
    rag_system = None

def rag_retrieve(query: str) -> str:
    """Enhanced RAG retrieval using LangChain"""
    if rag_system:
        return rag_system.retrieve_relevant_context(query)
    return "AI detection patterns and human writing characteristics."

@app.post("/analyze")
async def analyze_text(request: AnalyzeRequest) -> Dict:
    """Main endpoint for text analysis with RAG enhancement"""
    
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Get relevant context using RAG
    context = rag_retrieve(text)
    
    if llama_client is None:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": "No API key configured - using fallback response",
            "context": context,
            "source": "fallback"
        }
    
    try:
        result = await llama_client.analyze_text(text)
        result["context"] = context
        return result
    except Exception as e:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": f"Analysis failed: {str(e)}",
            "context": context,
            "source": "error_fallback"
        }

@app.post("/analyze/langchain")
async def analyze_text_langchain(request: AnalyzeRequest) -> Dict:
    """Analyze text using LangChain RAG system"""
    
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if rag_system is None:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": "LangChain RAG system not available",
            "source": "langchain_fallback"
        }
    
    try:
        # Get relevant context using LangChain RAG
        context = rag_system.retrieve_relevant_context(text)
        
        # Analyze using LangChain
        result = rag_system.analyze_with_langchain(text, context)
        result["context"] = context
        result["source"] = "langchain_rag"
        
        return result
        
    except Exception as e:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": f"LangChain analysis failed: {str(e)}",
            "source": "langchain_error"
        }

@app.get("/rag/test")
async def test_rag_system():
    """Test RAG system with sample queries"""
    
    if rag_system is None:
        return {
            "status": "error",
            "message": "LangChain RAG system not available"
        }
    
    test_queries = [
        "How can I detect AI-generated text?",
        "What are the characteristics of human writing?",
        "Tell me about grammar patterns in AI vs human text",
        "What makes writing sound natural and human-like?",
        "How do emotional expressions differ between AI and human text?"
    ]
    
    results = {}
    for query in test_queries:
        try:
            context = rag_system.retrieve_relevant_context(query)
            results[query] = {
                "retrieved_context": context[:200] + "..." if len(context) > 200 else context,
                "context_length": len(context),
                "status": "success"
            }
        except Exception as e:
            results[query] = {
                "error": str(e),
                "status": "failed"
            }
    
    return {
        "status": "RAG test completed",
        "collection_count": rag_system.vectorstore._collection.count() if rag_system.vectorstore else 0,
        "test_results": results,
        "system_status": "healthy" if rag_system else "unavailable"
    }

@app.get("/rag/status")
async def rag_status():
    """Get RAG system status and statistics"""
    
    if rag_system is None:
        return {
            "status": "unavailable",
            "message": "LangChain RAG system not initialized"
        }
    
    try:
        collection_count = rag_system.vectorstore._collection.count() if rag_system.vectorstore else 0
        llm_status = "available" if rag_system.llm else "unavailable"
        
        return {
            "status": "healthy",
            "collection_count": collection_count,
            "llm_status": llm_status,
            "embeddings_model": "all-MiniLM-L6-v2",
            "vectorstore_type": "ChromaDB",
            "knowledge_base_initialized": collection_count > 0,
            "rag_system": "LangChain"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking RAG status: {str(e)}"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive system status"""
    
    api_status = "configured" if llama_client is not None else "not_configured"
    rag_status = "healthy" if rag_system is not None else "unavailable"
    
    health_info = {
        "status": "healthy",
        "llama_api": api_status,
        "langchain_rag": rag_status,
        "message": "Human-AI Text Checker API is running"
    }
    
    if llama_client is not None:
        health_info.update({
            "api_url": llama_client.api_url,
            "model": llama_client.model,
            "api_key_configured": bool(llama_client.api_key)
        })
    
    if rag_system is not None:
        try:
            collection_count = rag_system.vectorstore._collection.count() if rag_system.vectorstore else 0
            health_info.update({
                "rag_collection_count": collection_count,
                "rag_llm_available": rag_system.llm is not None,
                "rag_embeddings": "all-MiniLM-L6-v2"
            })
        except Exception as e:
            health_info["rag_error"] = str(e)
    
    return health_info

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Human-AI Text Checker API",
        "version": "1.0.0",
        "features": [
            "Direct Llama API text analysis",
            "LangChain RAG-enhanced analysis",
            "Vector-based context retrieval",
            "AI vs Human authorship detection"
        ],
        "endpoints": {
            "analyze": "POST /analyze - Analyze text with RAG enhancement",
            "analyze_langchain": "POST /analyze/langchain - Pure LangChain RAG analysis",
            "rag_test": "GET /rag/test - Test RAG system functionality",
            "rag_status": "GET /rag/status - Get RAG system statistics",
            "health": "GET /health - Check comprehensive API status"
        }
    }