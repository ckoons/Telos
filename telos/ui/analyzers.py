"""
Requirement analysis module.

This module provides utilities for analyzing requirements and generating
quality metrics and improvement suggestions.
"""

import logging
from typing import Dict, List, Any

from telos.core.requirement import Requirement

logger = logging.getLogger(__name__)


class RequirementAnalyzer:
    """Analyzes requirements and provides improvement suggestions."""
    
    def __init__(self):
        """Initialize the requirement analyzer."""
        # Load requirement quality criteria
        self.quality_criteria = {
            "clarity": {
                "weight": 0.25,
                "description": "How clear and unambiguous the requirement is"
            },
            "completeness": {
                "weight": 0.25,
                "description": "Whether the requirement contains all necessary information"
            },
            "testability": {
                "weight": 0.20,
                "description": "Whether the requirement can be verified and tested"
            },
            "feasibility": {
                "weight": 0.15,
                "description": "Whether the requirement is technically feasible"
            },
            "consistency": {
                "weight": 0.15,
                "description": "Whether the requirement conflicts with others"
            }
        }
        
        # Quality indicator terms for each criterion
        self.quality_indicators = {
            "clarity": {
                "positive": ["specific", "clear", "precise", "defined", "exact", "explicit"],
                "negative": ["vague", "unclear", "ambiguous", "general", "subjective"]
            },
            "completeness": {
                "positive": ["complete", "comprehensive", "detailed", "thorough", "full"],
                "negative": ["missing", "incomplete", "partial", "lacks", "insufficient"]
            },
            "testability": {
                "positive": ["measurable", "verifiable", "testable", "quantifiable", "observable"],
                "negative": ["unmeasurable", "unverifiable", "subjective", "abstract"]
            },
            "feasibility": {
                "positive": ["achievable", "feasible", "practical", "realistic", "implementable"],
                "negative": ["impossible", "unrealistic", "impractical", "excessive"]
            }
        }
    
    async def analyze_requirement(self, requirement: Requirement) -> Dict[str, Any]:
        """
        Analyze a requirement's quality and provide improvement suggestions.
        
        Args:
            requirement: The requirement to analyze
            
        Returns:
            Analysis results including quality score and suggestions
        """
        # Initialize quality metrics
        quality_metrics = await self._initialize_metrics()
        
        # Analyze title
        quality_metrics = await self._analyze_title(requirement, quality_metrics)
        
        # Analyze description
        quality_metrics = await self._analyze_description(requirement, quality_metrics)
        
        # Analyze testability
        quality_metrics = await self._analyze_testability(requirement, quality_metrics)
        
        # Analyze feasibility
        quality_metrics = await self._analyze_feasibility(requirement, quality_metrics)
        
        # Analyze metadata
        quality_metrics = await self._analyze_metadata(requirement, quality_metrics)
        
        # Calculate overall score
        overall_score = await self._calculate_overall_score(quality_metrics)
        
        # Compile suggestions and improvement areas
        suggestions, improvement_areas = await self._compile_suggestions(requirement, quality_metrics)
        
        # Format detailed feedback
        from .formatters import format_detailed_feedback
        detailed_feedback = format_detailed_feedback(requirement, quality_metrics, overall_score, suggestions)
        
        return {
            "score": overall_score,
            "metrics": quality_metrics,
            "suggestions": suggestions,
            "improvement_areas": improvement_areas,
            "detailed_feedback": detailed_feedback,
            "requirement_id": requirement.requirement_id
        }
    
    async def _initialize_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality metrics for each criterion."""
        quality_metrics = {}
        for criterion, info in self.quality_criteria.items():
            quality_metrics[criterion] = {
                "score": 0.0,
                "description": info["description"],
                "feedback": []
            }
        return quality_metrics
    
    async def _analyze_title(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze the requirement title."""
        if len(requirement.title) < 10:
            metrics["clarity"]["feedback"].append(
                "Title is too short. A good title should briefly summarize what needs to be achieved."
            )
            metrics["clarity"]["score"] = 0.3
        elif len(requirement.title) > 100:
            metrics["clarity"]["feedback"].append(
                "Title is very long. Consider simplifying it for better clarity."
            )
            metrics["clarity"]["score"] = 0.6
        else:
            metrics["clarity"]["score"] = 0.8
        return metrics
    
    async def _analyze_description(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze the requirement description."""
        if len(requirement.description) < 30:
            metrics["completeness"]["feedback"].append(
                "Description is too brief. Provide more details about what, why, and how."
            )
            metrics["completeness"]["score"] = 0.3
        else:
            # Check for completeness indicators
            has_what = "what" in requirement.description.lower()
            has_why = "why" in requirement.description.lower() or "because" in requirement.description.lower()
            has_how = "how" in requirement.description.lower()
            
            completeness_score = 0.4
            if has_what:
                completeness_score += 0.2
            else:
                metrics["completeness"]["feedback"].append(
                    "Add details about WHAT needs to be accomplished"
                )
                
            if has_why:
                completeness_score += 0.2
            else:
                metrics["completeness"]["feedback"].append(
                    "Add context about WHY this requirement matters (business value)"
                )
                
            if has_how:
                completeness_score += 0.2
            else:
                metrics["completeness"]["feedback"].append(
                    "Consider adding guidance on HOW this might be implemented or verified"
                )
                
            metrics["completeness"]["score"] = completeness_score
        return metrics
    
    async def _analyze_testability(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze the requirement testability."""
        testability_words = ["measure", "verify", "test", "validate", "check", "confirm", "demonstrate"]
        testability_count = sum(1 for word in testability_words if word in requirement.description.lower())
        
        if testability_count == 0:
            metrics["testability"]["feedback"].append(
                "Add specific, measurable criteria for verification"
            )
            metrics["testability"]["score"] = 0.3
        else:
            metrics["testability"]["score"] = min(0.3 + (testability_count * 0.15), 1.0)
        return metrics
    
    async def _analyze_feasibility(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze the requirement feasibility."""
        complexity_words = ["complex", "difficult", "challenging", "integrate", "multiple", "all", "every", "always", "never"]
        complexity_count = sum(1 for word in complexity_words if word in requirement.description.lower())
        
        if complexity_count > 3:
            metrics["feasibility"]["feedback"].append(
                "Consider breaking this down into smaller, more manageable requirements"
            )
            metrics["feasibility"]["score"] = 0.5
        else:
            metrics["feasibility"]["score"] = 0.8
            
        # Consistency can't be fully checked without other requirements
        metrics["consistency"]["score"] = 0.7  # Default assumption
        
        return metrics
    
    async def _analyze_metadata(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze requirement metadata (priority, tags, etc.)."""
        if not requirement.priority:
            metrics["completeness"]["feedback"].append(
                "Add a priority level to help with planning"
            )
        
        if not requirement.tags:
            metrics["completeness"]["feedback"].append(
                "Add tags to categorize this requirement"
            )
        
        return metrics
    
    async def _calculate_overall_score(self, metrics: Dict[str, Dict[str, Any]]) -> float:
        """Calculate the overall quality score as a weighted average."""
        overall_score = 0.0
        for criterion, criterion_metrics in metrics.items():
            weight = self.quality_criteria[criterion]["weight"]
            overall_score += criterion_metrics["score"] * weight
        return overall_score
    
    async def _compile_suggestions(self, requirement: Requirement, metrics: Dict[str, Dict[str, Any]]) -> tuple:
        """Compile improvement suggestions and areas from metrics."""
        suggestions = []
        improvement_areas = []
        
        # Extract suggestions from metrics
        for criterion, criterion_metrics in metrics.items():
            if criterion_metrics["score"] < 0.7:
                improvement_areas.append(criterion)
                for feedback in criterion_metrics["feedback"]:
                    suggestions.append(feedback)
        
        # Add best practice suggestions
        if requirement.requirement_type == "functional" and "shall" not in requirement.description.lower():
            suggestions.append(
                "Consider using 'shall' statements for functional requirements (e.g., 'The system shall...')"
            )
        
        # Check for weak words
        weak_words = ["may", "might", "could", "should", "would", "can", "optionally"]
        found_weak_words = [word for word in weak_words if word in requirement.description.lower()]
        if found_weak_words:
            suggestions.append(
                f"Replace weak words ({', '.join(found_weak_words)}) with more definitive terms"
            )
        
        return suggestions, improvement_areas