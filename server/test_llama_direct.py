#!/usr/bin/env python3
"""
Direct test of the Llama API to verify connectivity
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llama_api_direct():
    """Test the Llama API directly using your curl command format"""
    
    api_key = os.getenv("LLAMA_API_KEY")
    if not api_key:
        print("❌ No LLAMA_API_KEY found in environment variables")
        print("Please create a .env file with your API key:")
        print("LLAMA_API_KEY=your_actual_api_key_here")
        return False
    
    url = "https://api.llama.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {"role": "user", "content": "Hello Llama! Can you give me a quick intro?"}
        ]
    }
    
    print("Testing Llama API connection...")
    print(f"URL: {url}")
    print(f"Model: {payload['model']}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print("-" * 50)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print("\nResponse:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print("Response:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_text_analysis():
    """Test the text analysis use case"""
    
    api_key = os.getenv("LLAMA_API_KEY")
    if not api_key:
        print("❌ No LLAMA_API_KEY found")
        return False
    
    url = "https://api.llama.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    analysis_prompt = """
    Analyze the following text and determine the probability that it was written by AI versus a human.
    Consider factors like:
    - Writing patterns and consistency
    - Vocabulary usage and complexity  
    - Sentence structure and flow
    - Creative elements and personal touches
    - Error patterns typical of AI or human writing
    
    Text to analyze: "This comprehensive analysis demonstrates that artificial intelligence technologies have significantly enhanced operational efficiency across multiple industry sectors through systematic implementation of machine learning algorithms."
    
    Respond with a JSON object containing:
    - ai_probability: float between 0 and 1
    - human_probability: float between 0 and 1  
    - reasoning: brief explanation of your analysis
    
    Format your response as valid JSON only.
    """
    
    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {
                "role": "system", 
                "content": "You are an expert AI detector that can analyze text and determine if it was written by AI or humans. Always respond with valid JSON."
            },
            {
                "role": "user", 
                "content": analysis_prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }
    
    print("\nTesting text analysis functionality...")
    print("-" * 50)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text analysis successful!")
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("\nAI Analysis Response:")
                print(content)
                
                # Try to parse as JSON
                try:
                    analysis = json.loads(content)
                    print("\n✅ JSON parsing successful!")
                    print(f"AI Probability: {analysis.get('ai_probability', 'N/A')}")
                    print(f"Human Probability: {analysis.get('human_probability', 'N/A')}")
                    print(f"Reasoning: {analysis.get('reasoning', 'N/A')}")
                except json.JSONDecodeError:
                    print("⚠️  Response is not valid JSON, but API call worked")
                
            return True
        else:
            print(f"❌ Analysis failed with status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        return False

if __name__ == "__main__":
    print("🦙 Testing Llama API Integration")
    print("=" * 50)
    
    # Test basic connectivity
    basic_test = test_llama_api_direct()
    
    if basic_test:
        # Test text analysis functionality
        analysis_test = test_text_analysis()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"Basic API: {'✅ PASS' if basic_test else '❌ FAIL'}")
        print(f"Text Analysis: {'✅ PASS' if analysis_test else '❌ FAIL'}")
        
        if basic_test and analysis_test:
            print("\n🎉 Llama API is ready for integration!")
            print("You can now start your FastAPI server and test with Postman.")
        else:
            print("\n⚠️  Some tests failed. Check your API key and model access.")
    else:
        print("\n❌ Basic API test failed. Please check your configuration.")
