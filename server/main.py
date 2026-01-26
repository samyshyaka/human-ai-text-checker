"""
Human-AI Text Checker - FastAPI Inference Server
=================================================
This server is dedicated to ML inference using LangChain RAG.
It handles text analysis for AI vs Human detection.

The Node.js API server proxies requests to this inference server.
"""

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
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Human-AI Text Checker - Inference Server",
    description="FastAPI inference server with LangChain RAG for AI/Human text detection",
    version="1.0.0"
)

# CORS middleware - allow both Node.js API and direct access for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:3001",  # Node.js API
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.llama.com/v1/chat/completions")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8")


class AnalyzeRequest(BaseModel):
    """Request model for text analysis"""
    text: str


class LlamaInferenceClient:
    """Client for Llama API inference calls"""
    
    def __init__(self):
        self.api_key = LLAMA_API_KEY
        self.api_url = LLAMA_API_URL
        self.model = LLAMA_MODEL
        
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY environment variable not set")
    
    async def analyze_text(self, text: str, context: str = "") -> Dict:
        """
        Analyze text using Llama API for AI vs Human detection.
        
        Args:
            text: The text to analyze
            context: Optional RAG context to enhance analysis
            
        Returns:
            Analysis result with probabilities and reasoning
        """
        
        # Build enhanced prompt with RAG context
        context_section = ""
        if context:
            context_section = f"""
Reference knowledge about AI vs Human text patterns:
{context}

Use this knowledge to inform your analysis.
"""
        
        prompt = f"""{context_section}Analyze the following text and determine the probability that it was written by AI versus a human.

Consider these factors carefully:
- Writing patterns and consistency
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
- reasoning: detailed explanation of your analysis
- key_indicators: array of specific patterns found

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
                    "content": "You are an expert AI text detector. Analyze text carefully and provide accurate probability assessments. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 800,
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
                            detail=f"Llama API error: {error_text}"
                        )
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    
    def _parse_response(self, result: dict) -> Dict:
        """Parse and validate API response"""
        
        content = self._extract_content(result)
        
        if not content:
            raise HTTPException(
                status_code=500, 
                detail="Could not extract content from API response"
            )
        
        try:
            analysis = self._parse_json_content(content)
            return self._format_result(analysis, content)
        except json.JSONDecodeError:
            return self._extract_from_text(content)
    
    def _extract_content(self, result: dict) -> Optional[str]:
        """Extract content from various API response formats"""
        
        # Llama API format with completion_message
        if "completion_message" in result:
            completion_msg = result["completion_message"]
            if isinstance(completion_msg, dict) and "content" in completion_msg:
                if isinstance(completion_msg["content"], dict) and "text" in completion_msg["content"]:
                    return completion_msg["content"]["text"]
                else:
                    return str(completion_msg["content"])
        
        # OpenAI-style format with choices
        elif "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        
        # Direct content fields
        elif "content" in result:
            return str(result["content"])
        elif "text" in result:
            return str(result["text"])
        elif "response" in result:
            return str(result["response"])
        
        return None
    
    def _parse_json_content(self, content: str) -> dict:
        """Parse JSON content, handling markdown code blocks"""
        
        content_clean = content.strip()
        
        # Remove markdown code blocks
        if content_clean.startswith("```json"):
            content_clean = re.sub(r'^```json\s*\n?', '', content_clean)
            content_clean = re.sub(r'\n?```$', '', content_clean)
        elif content_clean.startswith("```"):
            content_clean = re.sub(r'^```[a-zA-Z]*\s*\n?', '', content_clean)
            content_clean = re.sub(r'\n?```$', '', content_clean)
        
        return json.loads(content_clean.strip())
    
    def _format_result(self, analysis: dict, raw_content: str) -> Dict:
        """Format analysis result with validated probabilities"""
        
        ai_prob = float(analysis.get("ai_probability", 0.5))
        human_prob = float(analysis.get("human_probability", 0.5))
        
        # Normalize probabilities
        if "ai_probability" in analysis and "human_probability" not in analysis:
            human_prob = 1.0 - ai_prob
        elif "human_probability" in analysis and "ai_probability" not in analysis:
            ai_prob = 1.0 - human_prob
        
        # Clamp values
        ai_prob = max(0.0, min(1.0, ai_prob))
        human_prob = max(0.0, min(1.0, human_prob))
        
        return {
            "ai_probability": ai_prob,
            "human_probability": human_prob,
            "reasoning": analysis.get("reasoning", "Analysis completed"),
            "key_indicators": analysis.get("key_indicators", []),
            "raw_response": raw_content,
            "source": "llama_api"
        }
    
    def _extract_from_text(self, content: str) -> Dict:
        """Fallback: extract probabilities from text using regex"""
        
        ai_prob = 0.5
        human_prob = 0.5
        
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
            "reasoning": "Analysis extracted from text (JSON parsing fallback)",
            "key_indicators": [],
            "raw_response": content,
            "source": "text_fallback"
        }


class LangChainRAGSystem:
    """
    LangChain RAG system for enhanced text analysis.
    
    Uses ChromaDB for vector storage and HuggingFace embeddings
    for semantic search over AI detection knowledge base.
    """
    
    def __init__(self):
        print("🚀 Initializing LangChain RAG System...")
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ HuggingFace embeddings initialized (all-MiniLM-L6-v2)")
        
        # Initialize text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize vector store
        self.vectorstore = None
        self._setup_vectorstore()
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
        
        # Initialize LLM
        self.llm = None
        self._setup_llm()
        
        print("✅ LangChain RAG System ready")
    
    def _setup_vectorstore(self):
        """Setup ChromaDB vector store through LangChain"""
        try:
            self.vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings,
                collection_name="ai_detection_knowledge"
            )
            count = self.vectorstore._collection.count()
            print(f"✅ ChromaDB vectorstore loaded ({count} documents)")
        except Exception as e:
            print(f"⚠️ Creating new vectorstore: {e}")
            self.vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings,
                collection_name="ai_detection_knowledge"
            )
            print("✅ New ChromaDB vectorstore created")
    
    def _setup_llm(self):
        """Setup LangChain LLM with Llama API"""
        try:
            if LLAMA_API_KEY and LLAMA_API_URL:
                self.llm = ChatOpenAI(
                    model=LLAMA_MODEL,
                    openai_api_key=LLAMA_API_KEY,
                    openai_api_base=LLAMA_API_URL.replace("/chat/completions", ""),
                    temperature=0.3,
                    max_tokens=800
                )
                print("✅ LangChain LLM initialized with Llama API")
            else:
                print("⚠️ No API credentials - LangChain LLM disabled")
        except Exception as e:
            print(f"⚠️ Failed to setup LangChain LLM: {e}")
            self.llm = None
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base with AI detection patterns"""
        try:
            if self.vectorstore._collection.count() == 0:
                knowledge_items = self._get_knowledge_items()
                
                for item in knowledge_items:
                    chunks = self.text_splitter.split_text(item["text"])
                    for chunk in chunks:
                        self.vectorstore.add_texts(
                            texts=[chunk],
                            metadatas=[item["metadata"]]
                        )
                
                self.vectorstore.persist()
                print(f"✅ Knowledge base initialized ({len(knowledge_items)} items)")
        except Exception as e:
            print(f"⚠️ Knowledge base initialization failed: {e}")
    
    def _get_knowledge_items(self) -> List[Dict]:
        """Get knowledge items for AI detection"""
        return [
            {
                "text": "AI-generated text often exhibits repetitive patterns, overly consistent sentence structures, and lacks natural variation in writing style. The vocabulary tends to be more uniform and predictable, with fewer colloquialisms or personal expressions. AI text frequently uses generic phrases and avoids specific, concrete examples.",
                "metadata": {"category": "ai_patterns", "type": "style", "confidence": "high"}
            },
            {
                "text": "Human writing typically shows more natural variation in sentence length, vocabulary diversity, and emotional expression. Personal anecdotes, unique experiences, and individual voice are common indicators of human authorship. Humans often include specific details, make cultural references, and show emotional investment in their writing.",
                "metadata": {"category": "human_patterns", "type": "style", "confidence": "high"}
            },
            {
                "text": "AI text often has perfect grammar and punctuation, while human writing may contain minor errors, contractions, informal language patterns, and natural speech rhythms that reflect authentic communication. Typos, self-corrections, and colloquial expressions are strong indicators of human authorship.",
                "metadata": {"category": "grammar_patterns", "type": "grammar", "confidence": "high"}
            },
            {
                "text": "Human writers tend to use more context-specific references, cultural nuances, personal opinions, and domain-specific knowledge that reflect individual experiences and background. They often express uncertainty, ask rhetorical questions, and share subjective viewpoints.",
                "metadata": {"category": "context_patterns", "type": "context", "confidence": "high"}
            },
            {
                "text": "AI-generated content may show sudden topic shifts without natural transitions, while human writing typically flows more organically between related ideas with smoother paragraph transitions. AI often structures content in predictable patterns like numbered lists or rigid outlines.",
                "metadata": {"category": "flow_patterns", "type": "flow", "confidence": "medium"}
            },
            {
                "text": "Human writing often contains emotional authenticity, personal stakes, and genuine reactions to events, while AI text may feel more detached or lack emotional depth. Humans express frustration, excitement, humor, and vulnerability in ways that AI struggles to replicate authentically.",
                "metadata": {"category": "emotional_patterns", "type": "emotion", "confidence": "high"}
            },
            {
                "text": "AI text tends to be more verbose and may include unnecessary details or repetitive explanations, while human writing is typically more concise and focused. AI often hedges with phrases like 'it is important to note' or 'it should be mentioned that'.",
                "metadata": {"category": "verbosity_patterns", "type": "verbosity", "confidence": "medium"}
            },
            {
                "text": "Human writers often use specific examples, personal experiences, and unique perspectives that reflect their individual background and expertise. They reference real events, specific people, particular locations, and concrete situations rather than generic abstractions.",
                "metadata": {"category": "specificity_patterns", "type": "specificity", "confidence": "high"}
            },
            {
                "text": "AI text often follows predictable structural patterns: introduction, body paragraphs with topic sentences, conclusion. Human writing is more varied, sometimes starting mid-thought, using stream of consciousness, or organizing ideas in unexpected ways.",
                "metadata": {"category": "structure_patterns", "type": "structure", "confidence": "medium"}
            },
            {
                "text": "Indicators of AI text include: excessive use of transitional phrases, overly balanced arguments presenting 'both sides', generic examples, lack of personal pronouns in appropriate contexts, and conclusions that summarize rather than provide genuine insight.",
                "metadata": {"category": "ai_indicators", "type": "indicators", "confidence": "high"}
            }
        ]
    
    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant context using semantic search.
        
        Args:
            query: Text to find relevant context for
            top_k: Number of results to retrieve
            
        Returns:
            Combined relevant context as string
        """
        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            
            if docs:
                contexts = [doc.page_content for doc in docs]
                combined = "\n\n".join(contexts)
                print(f"🔍 Retrieved {len(contexts)} relevant contexts")
                return combined
            else:
                return self._get_default_context()
                
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}")
            return self._get_default_context()
    
    def _get_default_context(self) -> str:
        """Return default context when retrieval fails"""
        return """AI text patterns include: repetitive structures, perfect grammar, generic examples, 
verbose explanations, and predictable organization. Human text patterns include: natural variation, 
personal anecdotes, emotional expression, specific references, and authentic voice."""
    
    async def analyze_with_rag(self, text: str) -> Dict:
        """
        Full RAG analysis using LangChain.
        
        Args:
            text: Text to analyze
            
        Returns:
            Complete analysis result with context
        """
        # Retrieve relevant context
        context = self.retrieve_context(text)
        
        if not self.llm:
            return {
                "ai_probability": 0.5,
                "human_probability": 0.5,
                "reasoning": "LangChain LLM not configured",
                "key_indicators": [],
                "confidence": 0.0,
                "method": "langchain_fallback",
                "context_used": context[:200] + "..."
            }
        
        # Create analysis prompt
        prompt_template = PromptTemplate(
            input_variables=["text", "context"],
            template="""You are an expert AI text detector using RAG-enhanced analysis.

Knowledge Base Context:
{context}

Analyze this text to determine if it was written by a human or AI:
---
{text}
---

Provide your analysis as JSON:
{{
    "ai_probability": <0.0-1.0>,
    "human_probability": <0.0-1.0>,
    "reasoning": "<detailed analysis>",
    "key_indicators": ["<indicator1>", "<indicator2>", ...],
    "confidence": <0.0-1.0>
}}

Consider:
- Writing style and natural variation
- Vocabulary diversity and specificity
- Grammar patterns (perfection vs natural errors)
- Emotional authenticity and personal voice
- Structural organization
- Use of specific vs generic examples

Analysis:"""
        )
        
        try:
            chain = LLMChain(llm=self.llm, prompt=prompt_template, verbose=False)
            result = chain.run(text=text, context=context)
            
            return self._parse_chain_result(result, context)
            
        except Exception as e:
            print(f"⚠️ LangChain analysis failed: {e}")
            return {
                "ai_probability": 0.5,
                "human_probability": 0.5,
                "reasoning": f"Analysis error: {str(e)}",
                "key_indicators": [],
                "confidence": 0.0,
                "method": "langchain_error",
                "context_used": context[:200] + "..."
            }
    
    def _parse_chain_result(self, result: str, context: str) -> Dict:
        """Parse LangChain result into structured output"""
        try:
            # Clean markdown formatting
            result_clean = result.strip()
            if result_clean.startswith("```json"):
                result_clean = re.sub(r'^```json\s*\n?', '', result_clean)
                result_clean = re.sub(r'\n?```$', '', result_clean)
            elif result_clean.startswith("```"):
                result_clean = re.sub(r'^```[a-zA-Z]*\s*\n?', '', result_clean)
                result_clean = re.sub(r'\n?```$', '', result_clean)
            
            analysis = json.loads(result_clean)
            
            ai_prob = float(analysis.get("ai_probability", 0.5))
            human_prob = float(analysis.get("human_probability", 0.5))
            
            # Normalize if needed
            if "ai_probability" in analysis and "human_probability" not in analysis:
                human_prob = 1.0 - ai_prob
            elif "human_probability" in analysis and "ai_probability" not in analysis:
                ai_prob = 1.0 - human_prob
            
            return {
                "ai_probability": max(0.0, min(1.0, ai_prob)),
                "human_probability": max(0.0, min(1.0, human_prob)),
                "reasoning": analysis.get("reasoning", "LangChain RAG analysis completed"),
                "key_indicators": analysis.get("key_indicators", []),
                "confidence": float(analysis.get("confidence", 0.8)),
                "method": "langchain_rag",
                "context_used": context[:300] + "..." if len(context) > 300 else context
            }
            
        except json.JSONDecodeError:
            # Fallback parsing
            return self._parse_fallback(result, context)
    
    def _parse_fallback(self, result: str, context: str) -> Dict:
        """Fallback parsing when JSON parsing fails"""
        ai_match = re.search(r'"ai_probability":\s*(\d+(?:\.\d+)?)', result)
        human_match = re.search(r'"human_probability":\s*(\d+(?:\.\d+)?)', result)
        
        ai_prob = 0.5
        human_prob = 0.5
        
        if ai_match:
            ai_prob = float(ai_match.group(1))
            human_prob = 1.0 - ai_prob if not human_match else float(human_match.group(1))
        elif human_match:
            human_prob = float(human_match.group(1))
            ai_prob = 1.0 - human_prob
        
        return {
            "ai_probability": ai_prob,
            "human_probability": human_prob,
            "reasoning": "LangChain RAG analysis (fallback parsing)",
            "key_indicators": ["RAG-enhanced", "Context-aware"],
            "confidence": 0.7,
            "method": "langchain_rag_fallback",
            "context_used": context[:200] + "...",
            "raw_result": result
        }


# Initialize services
print("\n" + "="*60)
print("   Human-AI Text Checker - Inference Server")
print("="*60 + "\n")

# Initialize Llama client
try:
    llama_client = LlamaInferenceClient()
    print("✅ Llama API client initialized")
except ValueError as e:
    print(f"⚠️ Llama API client disabled: {e}")
    llama_client = None

# Initialize LangChain RAG system
try:
    rag_system = LangChainRAGSystem()
except Exception as e:
    print(f"⚠️ RAG system initialization failed: {e}")
    rag_system = None

print("\n" + "="*60 + "\n")


# ============================================================
# API Endpoints
# ============================================================

@app.post("/analyze")
async def analyze_text(request: AnalyzeRequest) -> Dict:
    """
    Main inference endpoint for text analysis.
    Uses RAG context to enhance Llama API analysis.
    """
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Get RAG context
    context = ""
    if rag_system:
        context = rag_system.retrieve_context(text)
    
    # Perform inference
    if llama_client is None:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": "Llama API not configured - returning neutral result",
            "key_indicators": [],
            "context": context[:200] + "..." if len(context) > 200 else context,
            "source": "fallback"
        }
    
    try:
        result = await llama_client.analyze_text(text, context)
        result["context"] = context[:200] + "..." if len(context) > 200 else context
        return result
    except HTTPException:
        raise
    except Exception as e:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": f"Analysis error: {str(e)}",
            "key_indicators": [],
            "context": context[:200] + "..." if len(context) > 200 else context,
            "source": "error_fallback"
        }


@app.post("/analyze/langchain")
async def analyze_langchain(request: AnalyzeRequest) -> Dict:
    """
    LangChain RAG-powered analysis endpoint.
    Uses full LangChain pipeline with vector retrieval.
    """
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if rag_system is None:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": "LangChain RAG system not available",
            "key_indicators": [],
            "source": "langchain_unavailable"
        }
    
    try:
        result = await rag_system.analyze_with_rag(text)
        result["source"] = "langchain_rag"
        return result
    except Exception as e:
        return {
            "ai_probability": 0.5,
            "human_probability": 0.5,
            "reasoning": f"LangChain error: {str(e)}",
            "key_indicators": [],
            "source": "langchain_error"
        }


@app.get("/rag/status")
async def get_rag_status() -> Dict:
    """Get RAG system status and statistics"""
    
    if rag_system is None:
        return {
            "status": "unavailable",
            "message": "LangChain RAG system not initialized"
        }
    
    try:
        collection_count = rag_system.vectorstore._collection.count()
        
        return {
            "status": "healthy",
            "collection_count": collection_count,
            "llm_status": "available" if rag_system.llm else "unavailable",
            "embeddings_model": "all-MiniLM-L6-v2",
            "vectorstore": "ChromaDB",
            "knowledge_base_initialized": collection_count > 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Status check failed: {str(e)}"
        }


@app.get("/rag/test")
async def test_rag() -> Dict:
    """Test RAG retrieval with sample queries"""
    
    if rag_system is None:
        return {"status": "error", "message": "RAG system unavailable"}
    
    test_queries = [
        "How to detect AI-generated text?",
        "What are human writing characteristics?",
        "Grammar patterns in AI vs human text"
    ]
    
    results = {}
    for query in test_queries:
        try:
            context = rag_system.retrieve_context(query, top_k=3)
            results[query] = {
                "context_preview": context[:150] + "...",
                "context_length": len(context),
                "status": "success"
            }
        except Exception as e:
            results[query] = {"status": "error", "error": str(e)}
    
    return {
        "status": "RAG test completed",
        "collection_count": rag_system.vectorstore._collection.count(),
        "results": results
    }


@app.get("/health")
async def health_check() -> Dict:
    """Inference server health check"""
    
    health = {
        "status": "healthy",
        "service": "inference",
        "llama_api": "configured" if llama_client else "not_configured",
        "langchain_rag": "healthy" if rag_system else "unavailable"
    }
    
    if llama_client:
        health["model"] = llama_client.model
        health["api_configured"] = True
    
    if rag_system:
        try:
            health["rag_documents"] = rag_system.vectorstore._collection.count()
            health["rag_llm"] = "available" if rag_system.llm else "unavailable"
        except:
            health["rag_documents"] = "unknown"
    
    return health


@app.get("/")
async def root() -> Dict:
    """Inference server info"""
    return {
        "service": "Human-AI Text Checker - Inference Server",
        "version": "1.0.0",
        "description": "FastAPI inference server with LangChain RAG",
        "endpoints": {
            "POST /analyze": "Standard analysis with RAG context",
            "POST /analyze/langchain": "Full LangChain RAG analysis",
            "GET /rag/status": "RAG system status",
            "GET /rag/test": "Test RAG retrieval",
            "GET /health": "Health check"
        }
    }
