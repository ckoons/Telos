#\!/usr/bin/env python3
"""
LLM Adapter for Telos Requirements Management System

This module implements an adapter for interacting with the Tekton LLM service,
providing a unified interface for LLM capabilities across the system.
"""

import os
import json
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("telos.llm_adapter")

class LLMAdapter:
    """
    Client for interacting with LLMs through the Tekton LLM Adapter.
    
    This class provides a unified interface for LLM operations, connecting
    to the centralized Tekton LLM adapter service.
    """
    
    def __init__(self, adapter_url: Optional[str] = None):
        """
        Initialize the LLM Adapter client.
        
        Args:
            adapter_url: URL for the LLM adapter service
        """
        # Default to environment variable or standard port
        rhetor_port = os.environ.get("RHETOR_PORT", "8003")
        default_adapter_url = f"http://localhost:{rhetor_port}"
        
        self.adapter_url = adapter_url or os.environ.get("LLM_ADAPTER_URL", default_adapter_url)
        self.default_provider = os.environ.get("LLM_PROVIDER", "anthropic")
        self.default_model = os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        self.ws_url = self.adapter_url.replace("http://", "ws://").replace("https://", "wss://")
        
        # For WebSocket streaming
        self.ws_port = os.environ.get("LLM_ADAPTER_WS_PORT", "8301")
        if ":" in self.ws_url:
            # Replace the port in the URL
            base_url = self.ws_url.split(":")[0] + ":" + self.ws_url.split(":")[1]
            self.ws_url = f"{base_url}:{self.ws_port}"
        else:
            # Append the port
            self.ws_url = f"{self.ws_url}:{self.ws_port}"
            
        logger.info(f"LLM Adapter initialized with URL: {self.adapter_url}")
        logger.info(f"WebSocket URL for streaming: {self.ws_url}")
    
    async def chat(self, 
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  stream: bool = False,
                  system_prompt: Optional[str] = None) -> Union[str, Callable]:
        """
        Send a chat request to the LLM adapter.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: LLM model to use (defaults to configured default)
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            system_prompt: Optional system prompt
            
        Returns:
            If stream=False, returns the complete response as a string
            If stream=True, returns a streaming generator
        """
        if stream:
            return self._stream_chat(messages, model, temperature, max_tokens, system_prompt)
        
        # Standard synchronous request
        payload = {
            "provider": self.default_provider,
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(
                f"{self.adapter_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )
            
            if response.status_code \!= 200:
                logger.error(f"LLM request failed: {response.status_code}, {response.text}")
                return f"Error: Failed to get LLM response (Status: {response.status_code})"
                
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except requests.RequestException as e:
            logger.error(f"LLM request exception: {str(e)}")
            return self._get_fallback_response()
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _stream_chat(self, 
                         messages: List[Dict[str, str]],
                         model: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None,
                         system_prompt: Optional[str] = None):
        """
        Stream a chat response from the LLM adapter via WebSocket.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: LLM model to use (defaults to configured default)
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Yields:
            Response chunks as they arrive
        """
        payload = {
            "provider": self.default_provider,
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"{self.ws_url}/v1/chat/completions/stream") as ws:
                    await ws.send_json(payload)
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                if data.get("type") == "content":
                                    yield data.get("content", "")
                                elif data.get("type") == "error":
                                    logger.error(f"Streaming error: {data.get('error')}")
                                    yield f"Error: {data.get('error')}"
                                    break
                                elif data.get("type") == "done":
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON in stream: {msg.data}")
                                continue
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break
                            
        except aiohttp.ClientError as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            yield self._get_fallback_response()
        except Exception as e:
            logger.error(f"Unexpected error in streaming: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def analyze_requirement(self, 
                                requirement: Dict[str, Any], 
                                context: Optional[str] = None, 
                                model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a requirement using the LLM adapter to evaluate quality and suggest improvements.
        
        Args:
            requirement: The requirement dictionary with id, title, description, etc.
            context: Optional additional context about the project
            model: LLM model to use (defaults to configured default)
            
        Returns:
            Dictionary with analysis results
        """
        # Format requirement as text for the LLM
        req_text = f"Requirement ID: {requirement.get('id', 'N/A')}\n"
        req_text += f"Title: {requirement.get('title', 'N/A')}\n"
        req_text += f"Description: {requirement.get('description', 'N/A')}\n"
        req_text += f"Type: {requirement.get('type', 'N/A')}\n"
        req_text += f"Priority: {requirement.get('priority', 'N/A')}\n"
        
        if requirement.get('acceptance_criteria'):
            req_text += "Acceptance Criteria:\n"
            for idx, criteria in enumerate(requirement['acceptance_criteria']):
                req_text += f"- {criteria}\n"
        
        system_prompt = """
        You are an AI assistant specialized in requirements engineering. 
        Analyze the requirement and evaluate it based on the following quality criteria:
        
        1. Clarity: Is the requirement clear and unambiguous?
        2. Completeness: Does the requirement include all necessary information?
        3. Testability: Can the requirement be verified or tested objectively?
        4. Feasibility: Is the requirement technically and practically achievable?
        5. Consistency: Is the requirement free from contradictions?
        
        Provide a score from 1-5 for each criterion, where 1 is poor and 5 is excellent.
        Also provide specific suggestions for improvement and potential issues to address.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please analyze this requirement:\n\n{req_text}"}
        ]
        
        if context:
            messages.append({
                "role": "user", 
                "content": f"Consider this additional project context:\n\n{context}"
            })
            
        try:
            response = await self.chat(messages, model=model, temperature=0.3)
            
            # Try to extract structured data from response
            analysis = self._parse_requirement_analysis(response)
            
            return {
                "success": True,
                "analysis": analysis,
                "raw_response": response
            }
        except Exception as e:
            logger.error(f"Requirement analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": ""
            }
    
    async def refine_requirement(self,
                               requirement: Dict[str, Any],
                               feedback: str,
                               model: Optional[str] = None) -> Dict[str, Any]:
        """
        Refine a requirement based on feedback using the LLM adapter.
        
        Args:
            requirement: The requirement dictionary with id, title, description, etc.
            feedback: User feedback to incorporate into the refinement
            model: LLM model to use (defaults to configured default)
            
        Returns:
            Dictionary with refined requirement
        """
        # Format requirement as text for the LLM
        req_text = f"Requirement ID: {requirement.get('id', 'N/A')}\n"
        req_text += f"Title: {requirement.get('title', 'N/A')}\n"
        req_text += f"Description: {requirement.get('description', 'N/A')}\n"
        req_text += f"Type: {requirement.get('type', 'N/A')}\n"
        req_text += f"Priority: {requirement.get('priority', 'N/A')}\n"
        
        if requirement.get('acceptance_criteria'):
            req_text += "Acceptance Criteria:\n"
            for idx, criteria in enumerate(requirement['acceptance_criteria']):
                req_text += f"- {criteria}\n"
        
        system_prompt = """
        You are an AI assistant specialized in requirements engineering.
        Your task is to refine a requirement based on feedback provided by the user.
        
        Ensure the refined requirement is:
        1. Clear and unambiguous
        2. Complete with all necessary information
        3. Testable and verifiable
        4. Feasible and realistic
        5. Consistent and non-contradictory
        
        Return the refined requirement in the same format it was provided, with improved content.
        Do not invent technical details that aren't at least implied by the original requirement or feedback.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the requirement to refine:\n\n{req_text}"},
            {"role": "user", "content": f"Here is the feedback to incorporate:\n\n{feedback}"}
        ]
        
        try:
            response = await self.chat(messages, model=model)
            
            # Parse the response to extract refined requirement
            refined = self._parse_refined_requirement(response, requirement)
            
            return {
                "success": True,
                "refined_requirement": refined,
                "raw_response": response
            }
        except Exception as e:
            logger.error(f"Requirement refinement error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": ""
            }
    
    def _parse_requirement_analysis(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM's response to extract structured analysis data.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            Dictionary with structured analysis data
        """
        try:
            # Initialize default analysis structure
            analysis = {
                "scores": {
                    "clarity": 0,
                    "completeness": 0,
                    "testability": 0,
                    "feasibility": 0,
                    "consistency": 0
                },
                "suggestions": [],
                "issues": []
            }
            
            # Try to extract scores using regex patterns
            import re
            
            # Extract scores
            score_patterns = {
                "clarity": r"clarity:?\s*(\d+)[/\s]*5",
                "completeness": r"completeness:?\s*(\d+)[/\s]*5",
                "testability": r"testability:?\s*(\d+)[/\s]*5",
                "feasibility": r"feasibility:?\s*(\d+)[/\s]*5",
                "consistency": r"consistency:?\s*(\d+)[/\s]*5"
            }
            
            for category, pattern in score_patterns.items():
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    analysis["scores"][category] = int(match.group(1))
            
            # Extract suggestions
            suggestions_pattern = r"suggestions?:(.*?)(?:issues:|$)"
            suggestions_match = re.search(suggestions_pattern, response, re.IGNORECASE | re.DOTALL)
            if suggestions_match:
                # Split by bullet points and clean up
                suggestions_text = suggestions_match.group(1).strip()
                suggestions = re.findall(r"[-*]\s*(.*?)(?:\n|$)", suggestions_text)
                analysis["suggestions"] = [s.strip() for s in suggestions if s.strip()]
            
            # Extract issues
            issues_pattern = r"issues?:(.*?)(?:suggestions?:|$)"
            issues_match = re.search(issues_pattern, response, re.IGNORECASE | re.DOTALL)
            if issues_match:
                # Split by bullet points and clean up
                issues_text = issues_match.group(1).strip()
                issues = re.findall(r"[-*]\s*(.*?)(?:\n|$)", issues_text)
                analysis["issues"] = [i.strip() for i in issues if i.strip()]
            
            # Calculate overall score
            scores = analysis["scores"].values()
            analysis["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing requirement analysis: {str(e)}")
            return {
                "scores": {},
                "suggestions": [],
                "issues": [],
                "parsing_error": str(e)
            }
    
    def _parse_refined_requirement(self, response: str, original_requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the LLM's response to extract refined requirement data.
        
        Args:
            response: The raw response from the LLM
            original_requirement: The original requirement dictionary
            
        Returns:
            Dictionary with refined requirement data
        """
        try:
            # Create a copy of the original requirement
            refined = original_requirement.copy()
            
            # Extract title
            import re
            title_match = re.search(r"title:?\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
            if title_match:
                refined["title"] = title_match.group(1).strip()
            
            # Extract description
            description_pattern = r"description:?\s*(.*?)(?:type:|priority:|acceptance criteria:|$)"
            description_match = re.search(description_pattern, response, re.IGNORECASE | re.DOTALL)
            if description_match:
                refined["description"] = description_match.group(1).strip()
            
            # Extract type
            type_match = re.search(r"type:?\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
            if type_match:
                refined["type"] = type_match.group(1).strip()
            
            # Extract priority
            priority_match = re.search(r"priority:?\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
            if priority_match:
                refined["priority"] = priority_match.group(1).strip()
            
            # Extract acceptance criteria
            criteria_pattern = r"acceptance criteria:?(.*?)(?:$)"
            criteria_match = re.search(criteria_pattern, response, re.IGNORECASE | re.DOTALL)
            if criteria_match:
                criteria_text = criteria_match.group(1).strip()
                criteria = re.findall(r"[-*]\s*(.*?)(?:\n|$)", criteria_text)
                if criteria:
                    refined["acceptance_criteria"] = [c.strip() for c in criteria if c.strip()]
            
            return refined
            
        except Exception as e:
            logger.error(f"Error parsing refined requirement: {str(e)}")
            return original_requirement
    
    def _get_fallback_response(self) -> str:
        """
        Provide a fallback response when the LLM service is unavailable.
        
        Returns:
            A helpful error message
        """
        return (
            "I apologize, but I'm currently unable to connect to the LLM service. "
            "This could be due to network issues or the service being offline. "
            "Please try again later or contact your administrator if the problem persists."
        )
    
    def get_available_models(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get the list of available models from the LLM adapter.
        
        Returns:
            Dictionary mapping providers to their available models
        """
        try:
            response = requests.get(f"{self.adapter_url}/v1/models")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get models: {response.status_code}, {response.text}")
                return {
                    "anthropic": [
                        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"}
                    ]
                }
        except requests.RequestException as e:
            logger.error(f"Error getting models: {str(e)}")
            return {
                "anthropic": [
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"}
                ]
            }
EOF < /dev/null