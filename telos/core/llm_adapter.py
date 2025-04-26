"""
LLM adapter for Telos.

This module provides a client for interacting with LLMs through the Tekton LLM Adapter.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

class LLMAdapter:
    """Client for interacting with LLMs through the Tekton LLM Adapter."""
    
    def __init__(self, adapter_url: Optional[str] = None):
        """
        Initialize the LLM adapter.
        
        Args:
            adapter_url: URL for the LLM adapter service
        """
        # Default to the environment variable or standard port from the Single Port Architecture
        rhetor_port = os.environ.get("RHETOR_PORT", "8003")
        default_adapter_url = f"http://localhost:{rhetor_port}"
        
        self.adapter_url = adapter_url or os.environ.get("LLM_ADAPTER_URL", default_adapter_url)
        self.default_provider = os.environ.get("LLM_PROVIDER", "anthropic")
        self.default_model = os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        
    async def get_available_providers(self) -> Dict[str, Any]:
        """
        Get available LLM providers.
        
        Returns:
            Dict of available providers and their models
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.adapter_url}/providers", timeout=5.0) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get providers: {response.status}")
        except Exception as e:
            logger.error(f"Error getting providers: {e}")
        
        # Return default providers if the API call fails
        return {
            self.default_provider: {
                "available": True,
                "models": [
                    {"id": self.default_model, "name": "Default Model"},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
                ]
            }
        }
    
    def get_current_provider_and_model(self) -> Tuple[str, str]:
        """
        Get the current provider and model.
        
        Returns:
            Tuple of (provider_id, model_id)
        """
        return (self.default_provider, self.default_model)
    
    def set_provider_and_model(self, provider_id: str, model_id: str) -> None:
        """
        Set the provider and model to use.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
        """
        self.default_provider = provider_id
        self.default_model = model_id
    
    async def analyze_requirement(self, requirement_text: str) -> Dict[str, Any]:
        """
        Analyze a requirement using LLM.
        
        Args:
            requirement_text: Requirement text
            
        Returns:
            Analysis results
        """
        try:
            # Try to use the LLM adapter service
            prompt = """
            Analyze the following software requirement. Evaluate it for:
            1. Clarity - Is the requirement clear and unambiguous?
            2. Completeness - Does it contain all necessary information?
            3. Testability - Can it be verified by testing?
            4. Feasibility - Can it be implemented with available resources?
            
            For each criterion, provide a score from 0 to 10 and explain your reasoning.
            Then provide specific suggestions for improvement.
            
            Requirement:
            """
            
            message_data = {
                "message": f"{prompt}\n\n{requirement_text}",
                "context_id": "telos:requirement_analysis",
                "task_type": "analysis",
                "component": "telos",
                "streaming": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/message", 
                    json=message_data,
                    timeout=30.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_analysis_response(result)
                    else:
                        logger.warning(f"Failed to analyze requirement: {response.status}")
                        
            # If we get here, the request failed
            return {
                "score": 0.5,
                "analysis": "Failed to connect to LLM service.",
                "suggestions": ["Ensure the requirement is clear and testable."]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing requirement: {e}")
            return {
                "score": 0.5,
                "analysis": f"Error analyzing requirement: {str(e)}",
                "suggestions": ["Review the requirement manually."]
            }
    
    async def refine_requirement(
        self, 
        requirement_text: str, 
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine a requirement based on feedback.
        
        Args:
            requirement_text: Original requirement text
            feedback: User feedback
            
        Returns:
            Refined requirement
        """
        try:
            # Try to use the LLM adapter service
            prompt = """
            I have a software requirement that needs refinement based on feedback.
            
            Original requirement:
            """
            
            feedback_prompt = """
            Feedback received:
            """
            
            task_prompt = """
            Please create an improved version of the requirement that addresses the feedback.
            Your response should be in the following format:
            
            Improved Requirement: [improved requirement text]
            
            Changes Made:
            - [list of specific changes]
            
            Additional Notes:
            [any additional notes or explanations]
            """
            
            message_data = {
                "message": f"{prompt}\n\n{requirement_text}\n\n{feedback_prompt}\n\n{feedback}\n\n{task_prompt}",
                "context_id": "telos:requirement_refinement",
                "task_type": "refinement",
                "component": "telos",
                "streaming": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/message", 
                    json=message_data,
                    timeout=30.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_refinement_response(result)
                    else:
                        logger.warning(f"Failed to refine requirement: {response.status}")
                        
            # If we get here, the request failed
            return {
                "refined_text": requirement_text,
                "changes": [],
                "notes": "Failed to connect to LLM service."
            }
            
        except Exception as e:
            logger.error(f"Error refining requirement: {e}")
            return {
                "refined_text": requirement_text,
                "changes": [],
                "notes": f"Error refining requirement: {str(e)}"
            }
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM analysis response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed analysis
        """
        message = response.get("message", "")
        
        # Simple parsing of key elements from the response
        # A more robust implementation would use structured output or better parsing
        
        # Extract scores
        clarity_score = self._extract_score(message, "Clarity")
        completeness_score = self._extract_score(message, "Completeness")
        testability_score = self._extract_score(message, "Testability")
        feasibility_score = self._extract_score(message, "Feasibility")
        
        # Calculate overall score
        avg_score = (clarity_score + completeness_score + testability_score + feasibility_score) / 40.0
        
        # Extract suggestions
        suggestions = []
        if "suggestion" in message.lower() or "improve" in message.lower():
            for line in message.split("\n"):
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    suggestions.append(line.strip()[1:].strip())
        
        return {
            "score": avg_score,
            "analysis": message,
            "suggestions": suggestions,
            "scores": {
                "clarity": clarity_score,
                "completeness": completeness_score,
                "testability": testability_score,
                "feasibility": feasibility_score
            }
        }
    
    def _parse_refinement_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM refinement response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed refinement
        """
        message = response.get("message", "")
        
        # Extract the improved requirement
        refined_text = ""
        changes = []
        notes = ""
        
        # Simple parser for the response
        in_requirement = False
        in_changes = False
        in_notes = False
        
        for line in message.split("\n"):
            line = line.strip()
            
            if line.startswith("Improved Requirement:"):
                in_requirement = True
                in_changes = False
                in_notes = False
                # Get the text after the colon
                if ":" in line:
                    refined_text = line.split(":", 1)[1].strip()
                continue
            
            if line.startswith("Changes Made:"):
                in_requirement = False
                in_changes = True
                in_notes = False
                continue
            
            if line.startswith("Additional Notes:"):
                in_requirement = False
                in_changes = False
                in_notes = True
                continue
            
            if in_requirement:
                if line and not line.startswith("-"):
                    refined_text += "\n" + line if refined_text else line
            
            if in_changes:
                if line.startswith("-"):
                    changes.append(line[1:].strip())
            
            if in_notes:
                notes += "\n" + line if notes else line
        
        return {
            "refined_text": refined_text,
            "changes": changes,
            "notes": notes
        }
    
    def _extract_score(self, text: str, criterion: str) -> float:
        """
        Extract a score from text.
        
        Args:
            text: Text containing score
            criterion: Criterion name to look for
            
        Returns:
            Score value (0-10)
        """
        try:
            # Look for patterns like "Clarity: 7/10" or "Clarity - 7"
            import re
            patterns = [
                rf"{criterion}:\s*(\d+)(?:/10)?",
                rf"{criterion}\s*-\s*(\d+)(?:/10)?",
                rf"{criterion} score:?\s*(\d+)(?:/10)?"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            
            return 5.0  # Default middle score
        except:
            return 5.0