import os
import time
import json
import random
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("inference_engine")

class BaseModelAdapter:
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        """
        Returns a dictionary containing:
        - "text": str (generated response)
        - "prompt_tokens": int
        - "completion_tokens": int
        - "latency": float (seconds)
        - "cost": float (USD)
        - "provider_raw": dict (raw response metadata)
        """
        raise NotImplementedError()


class MockAdapter(BaseModelAdapter):
    """
    Generates realistic, high-quality responses mimicking real LLMs on common tasks
    (Math, QA, Code, Agents, RAG, Safety refusals). Helps with zero-cost testing.
    """
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        if seed is not None:
            random.seed(seed)
            
        start_time = time.time()
        # Simulate network latency
        time.sleep(random.uniform(0.15, 0.45))
        
        prompt_lower = prompt.lower()
        response_text = ""
        category = "general"
        
        # 1. Check for Safety/Refusal prompts
        if any(w in prompt_lower for w in ["jailbreak", "unsafe", "bomb", "hack", "bypass", "inject"]):
            response_text = "I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant, and I cannot provide instructions for creating harmful materials or bypassing system security."
            category = "refusal"
        
        # 2. Check for Coding / HumanEval
        elif any(w in prompt_lower for w in ["def ", "write a python", "function", "class ", "return ", "sorting", "implement"]):
            category = "coding"
            response_text = (
                "```python\n"
                "def solve_problem(data):\n"
                "    # Implementation of the requested function\n"
                "    if not data:\n"
                "        return []\n"
                "    # Sort data in place and return\n"
                "    sorted_data = sorted(data, key=lambda x: x)\n"
                "    return sorted_data\n"
                "```"
            )
            
        # 3. Check for Math / GSM8K
        elif any(w in prompt_lower for w in ["calculate", "gsm8k", "solve", "math", "equation", "divided by", "multiplied by"]):
            category = "math"
            val1 = random.randint(10, 100)
            val2 = random.randint(5, 20)
            result = val1 * val2
            response_text = (
                f"Let's solve this step-by-step:\n"
                f"1. First, we identify the main factors: we need to multiply {val1} by {val2}.\n"
                f"2. Performing the calculation: {val1} * {val2} = {result}.\n"
                f"Therefore, the final answer is {result}.\n"
                f"#### {result}"
            )
            
        # 4. Check for RAG / Context QA
        elif "context" in prompt_lower and "question" in prompt_lower:
            category = "rag"
            # Randomly decide if faithful or hallucinated (15% chance of hallucination)
            is_hallucinated = random.random() < 0.15
            if is_hallucinated:
                response_text = "Based on the provided context, the company was founded in 1995 (Note: this is unsupported by context) and its primary product is quantum computers."
            else:
                response_text = "According to the provided text, the system operates under standard pressure conditions, and the reference sensor calibrates automatically every 24 hours."

        # 5. Check for Agent reasoning / tool calls
        elif any(w in prompt_lower for w in ["agent", "tool", "call", "step", "react", "act"]):
            category = "agent"
            response_text = (
                "Thought: I need to search the web for the current status of the project, then use the calculator to sum the items.\n"
                "Action: search_web[status of project X]\n"
                "Observation: Project X is active with a budget of $50,000.\n"
                "Thought: Now I need to calculate the remaining balance after deducting $12,500.\n"
                "Action: calculator[50000 - 12500]\n"
                "Observation: 37500\n"
                "Thought: I have the final answer.\n"
                "Final Answer: The project is active, and the remaining budget balance is $37,500."
            )
            
        # 6. Classification / Sentiment / Toxicity
        elif any(w in prompt_lower for w in ["classify", "toxicity", "sentiment", "toxic", "polite"]):
            category = "classification"
            if any(w in prompt_lower for w in ["bad", "hate", "stupid", "toxic"]):
                response_text = "toxic"
            else:
                response_text = "clean"
                
        # 7. Default QA response
        else:
            response_text = f"This is a simulated high-quality response from {self.model_name} generated for evaluation. The prompt contained {len(prompt)} characters. Let me know if you need any detailed analysis."

        latency = time.time() - start_time
        prompt_tokens = len(prompt.split()) + 10
        completion_tokens = len(response_text.split()) + 5
        
        # Calculate simulated costs (e.g. $0.0015 per 1k input, $0.002 per 1k output)
        cost = (prompt_tokens * 0.0000015) + (completion_tokens * 0.000002)
        
        return {
            "text": response_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency": latency,
            "cost": cost,
            "provider_raw": {
                "mocked": True,
                "category": category,
                "model": self.model_name,
                "seed": seed
            }
        }


class OpenAIAdapter(BaseModelAdapter):
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        if not self.api_key:
            raise ValueError("OpenAI API key missing. Set OPENAI_API_KEY environment variable or pass to adapter.")

        start_time = time.time()
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if seed is not None:
            data["seed"] = seed

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"OpenAI API Error: {error_body}")
            raise Exception(f"OpenAI API Error: {e.code} - {error_body}")

        latency = time.time() - start_time
        choice = response["choices"][0]
        text = choice["message"]["content"]
        
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # Approximate pricing (can be adjusted dynamically)
        input_rate = 0.005 / 1000  # $5.00 per million
        output_rate = 0.015 / 1000  # $15.00 per million
        cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
        
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency": latency,
            "cost": cost,
            "provider_raw": response
        }


class GeminiAdapter(BaseModelAdapter):
    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        if not self.api_key:
            raise ValueError("Gemini API key missing. Set GEMINI_API_KEY environment variable.")

        start_time = time.time()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        contents = [{"parts": [{"text": prompt}]}]
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_prompt:
            data["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"Gemini API Error: {error_body}")
            raise Exception(f"Gemini API Error: {e.code} - {error_body}")

        latency = time.time() - start_time
        
        # Parse content
        try:
            text = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            text = ""
            logger.error(f"Failed to parse Gemini output: {response}")
            
        usage = response.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        
        # Approximate pricing
        input_rate = 0.000075 / 1000
        output_rate = 0.0003 / 1000
        cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
        
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency": latency,
            "cost": cost,
            "provider_raw": response
        }


class AnthropicAdapter(BaseModelAdapter):
    def __init__(self, model_name: str = "claude-3-5-sonnet", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        if not self.api_key:
            raise ValueError("Anthropic API key missing. Set ANTHROPIC_API_KEY environment variable.")

        start_time = time.time()
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            data["system"] = system_prompt

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"Anthropic API Error: {error_body}")
            raise Exception(f"Anthropic API Error: {e.code} - {error_body}")

        latency = time.time() - start_time
        
        text = response["content"][0]["text"]
        usage = response.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        
        input_rate = 0.003 / 1000
        output_rate = 0.015 / 1000
        cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
        
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency": latency,
            "cost": cost,
            "provider_raw": response
        }


class OllamaAdapter(BaseModelAdapter):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        start_time = time.time()
        
        url = f"{self.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model_name,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        if seed is not None:
            data["options"]["seed"] = seed

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read().decode("utf-8"))
        except urllib.error.URLError as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise Exception(f"Ollama connection error. Is Ollama running locally at {self.base_url}? Error: {e}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"Ollama API Error: {error_body}")
            raise Exception(f"Ollama API Error: {e.code} - {error_body}")

        latency = time.time() - start_time
        
        text = response["message"]["content"]
        prompt_tokens = response.get("prompt_eval_count", len(prompt.split()))
        completion_tokens = response.get("eval_count", len(text.split()))
        
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency": latency,
            "cost": 0.0,  # Ollama is local and free
            "provider_raw": response
        }


class InferenceEngine:
    @staticmethod
    def get_adapter(provider: str, model_id: str, api_key: str = None) -> BaseModelAdapter:
        provider_clean = provider.strip().lower()
        
        if provider_clean == "mock":
            return MockAdapter(model_name=model_id)
        elif provider_clean == "openai":
            return OpenAIAdapter(model_name=model_id, api_key=api_key)
        elif provider_clean == "gemini":
            return GeminiAdapter(model_name=model_id, api_key=api_key)
        elif provider_clean == "anthropic":
            return AnthropicAdapter(model_name=model_id, api_key=api_key)
        elif provider_clean == "ollama":
            return OllamaAdapter(model_name=model_id)
        else:
            logger.warning(f"Unknown provider '{provider}', falling back to MockAdapter.")
            return MockAdapter(model_name=model_id)
