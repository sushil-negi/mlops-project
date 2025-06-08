"""
Healthcare AI Engine for Kubernetes Deployment
Production-ready healthcare AI with monitoring and caching
"""

import hashlib
import json
import logging
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthcareAIEngine:
    """Production Healthcare AI Engine for Kubernetes"""

    def __init__(self):
        self.pipeline = None
        self.category_mapping = {}
        self.healthcare_responses = {}
        self.conversation_history = []
        self.response_cache = {}
        self.statistics = {
            "total_requests": 0,
            "cache_hits": 0,
            "model_predictions": 0,
            "contextual_overrides": 0,
        }
        self.knowledge_base = self._load_knowledge_base()
        logger.info("Healthcare AI Engine initialized")

    def _load_knowledge_base(self) -> Dict:
        """Load knowledge base with healthcare responses"""
        knowledge = {
            "category_keywords": {
                "adl": [
                    "mobility",
                    "walking",
                    "transfer",
                    "wheelchair",
                    "balance",
                    "falling",
                    "bathing",
                    "dressing",
                    "eating",
                    "toileting",
                    "daily activities",
                    "independence",
                    "adaptive",
                ],
                "senior_care": [
                    "elderly",
                    "senior",
                    "aging",
                    "parent",
                    "grandfather",
                    "grandmother",
                    "lonely",
                    "isolation",
                    "memory",
                    "medication",
                    "aging in place",
                ],
                "mental_health": [
                    "anxiety",
                    "depression",
                    "stress",
                    "panic",
                    "worried",
                    "sad",
                    "overwhelmed",
                    "mental health",
                    "therapy",
                    "counseling",
                    "emotional",
                    "mood",
                ],
                "respite_care": [
                    "caregiver",
                    "exhausted",
                    "break",
                    "respite",
                    "burnout",
                    "caring for",
                    "relief",
                    "temporary care",
                    "support",
                    "overwhelmed",
                ],
                "disabilities": [
                    "disability",
                    "wheelchair",
                    "adaptive",
                    "accessibility",
                    "accommodation",
                    "assistive",
                    "impairment",
                    "special needs",
                    "inclusion",
                ],
            },
            "responses": {
                "adl": [
                    "For activities of daily living, I recommend consulting with an occupational therapist who can provide personalized assessments and adaptive strategies.",
                    "Mobility aids and adaptive equipment can significantly improve independence in daily activities. Would you like information about specific aids?",
                    "Physical therapy can help improve strength and balance for better performance in daily activities.",
                    "Home modifications like grab bars, ramps, and adapted bathroom fixtures can make daily activities safer and easier.",
                ],
                "senior_care": [
                    "Senior care involves addressing physical, emotional, and social needs. Consider reaching out to local aging services for comprehensive support.",
                    "Regular health monitoring, medication management, and social engagement are crucial aspects of senior care.",
                    "Adult day programs and senior centers offer valuable social interaction and activities for elderly individuals.",
                    "Home health services can provide medical care and assistance while allowing seniors to age in place.",
                ],
                "mental_health": [
                    "Mental health is as important as physical health. Professional counseling and therapy can provide valuable support and coping strategies.",
                    "Support groups, both in-person and online, can connect you with others facing similar challenges.",
                    "Mindfulness practices, regular exercise, and maintaining social connections are important for mental wellbeing.",
                    "If you're experiencing persistent mental health concerns, please reach out to a mental health professional or your primary care provider.",
                ],
                "respite_care": [
                    "Respite care services provide temporary relief for caregivers. Options include in-home care, adult day programs, and short-term facility stays.",
                    "Taking breaks is essential for caregiver wellbeing. Even short periods of respite can help prevent burnout.",
                    "Local caregiver support groups and resources can provide both emotional support and practical assistance.",
                    "Many communities offer volunteer respite programs. Contact your local Area Agency on Aging for information.",
                ],
                "disabilities": [
                    "Disability resources include adaptive technology, accessibility modifications, and vocational rehabilitation services.",
                    "The Americans with Disabilities Act ensures equal access to employment, public services, and accommodations.",
                    "Independent living centers provide resources, advocacy, and peer support for people with disabilities.",
                    "Assistive technology can greatly enhance independence and quality of life for individuals with disabilities.",
                ],
                "general": [
                    "I'm here to help with healthcare-related questions. Could you provide more details about your specific needs?",
                    "Healthcare encompasses many areas. Whether it's about daily living, mental health, or caregiving, I'm here to provide information and support.",
                    "For personalized medical advice, please consult with qualified healthcare professionals.",
                    "What specific healthcare topic or concern would you like to discuss today?",
                ],
            },
        }

        # Try to load additional data if available
        try:
            data_path = "/app/data/test_healthcare_training.json"
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded additional training data from {data_path}")
        except Exception as e:
            logger.warning(f"Could not load additional data: {e}")

        return knowledge

    def _detect_category(self, text: str) -> str:
        """Detect conversation category based on keywords"""
        text_lower = text.lower()

        # Check for crisis first
        crisis_words = [
            "suicide",
            "kill myself",
            "hurt myself",
            "want to die",
            "end it all",
        ]
        if any(word in text_lower for word in crisis_words):
            return "crisis"

        # Score each category
        category_scores = {}
        for category, keywords in self.knowledge_base["category_keywords"].items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score

        # Return highest scoring category or 'general'
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "general"

    def generate_response(self, user_input: str, use_history: bool = True) -> Dict:
        """Generate healthcare response"""
        start_time = time.time()
        self.statistics["total_requests"] += 1

        # Detect category
        category = self._detect_category(user_input)

        # Handle crisis immediately
        if category == "crisis":
            return {
                "response": "🚨 CRISIS SUPPORT NEEDED 🚨\n\nImmediate Resources:\n• Call 911 for emergencies\n• National Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Local emergency services\n\nYou are not alone. Professional help is available 24/7.",
                "category": "crisis",
                "confidence": 1.0,
                "generation_time": time.time() - start_time,
            }

        # Check cache
        input_hash = hashlib.md5(
            user_input.lower().encode(), usedforsecurity=False
        ).hexdigest()
        if input_hash in self.response_cache:
            self.statistics["cache_hits"] += 1
            cached = self.response_cache[input_hash]
            return {
                **cached,
                "cached": True,
                "generation_time": time.time() - start_time,
            }

        # Get response from knowledge base
        responses = self.knowledge_base["responses"].get(
            category, self.knowledge_base["responses"]["general"]
        )
        response = random.choice(responses)

        # Add disclaimer
        response += "\n\n⚠️ This is general health information only. Always consult qualified healthcare professionals for medical advice."

        # Create result
        result = {
            "response": response,
            "category": category,
            "confidence": 0.85,
            "generation_time": time.time() - start_time,
        }

        # Cache response
        self.response_cache[input_hash] = result

        # Add to history
        if use_history:
            self.conversation_history.append(
                {
                    "user": user_input,
                    "assistant": response,
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return result

    def get_conversation_stats(self) -> Dict:
        """Get statistics about the AI engine"""
        return {
            "total_requests": self.statistics["total_requests"],
            "cache_hits": self.statistics["cache_hits"],
            "cache_hit_rate": self.statistics["cache_hits"]
            / max(1, self.statistics["total_requests"]),
            "categories": list(self.knowledge_base["category_keywords"].keys()),
            "conversation_history": len(self.conversation_history),
            "status": "healthy",
        }
