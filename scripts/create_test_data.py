#!/usr/bin/env python3
"""
Create test data for MLOps pipeline demonstration
"""

import json
import random


def generate_response(category, query=""):
    """Generate appropriate response based on category"""
    
    # Crisis response must include emergency resources
    if category == "crisis_mental_health" or any(word in query.lower() for word in ["suicide", "kill", "hurt myself", "end my life"]):
        return (
            "🚨 CRISIS SUPPORT NEEDED 🚨\n\n"
            "If you're having thoughts of suicide or self-harm, please reach out for help immediately:\n\n"
            "• National Suicide Prevention Lifeline: 988\n"
            "• Crisis Text Line: Text HOME to 741741\n"
            "• Emergency Services: 911\n\n"
            "You matter, and help is available 24/7. Please don't hesitate to reach out to a mental health professional, "
            "trusted friend, or family member. Consider contacting your healthcare provider for additional support."
        )
    
    # Medical-related responses should include disclaimers
    medical_categories = ["senior_medication", "mental_health_anxiety", "mental_health_depression"]
    if category in medical_categories or any(word in query.lower() for word in ["medication", "medical", "treatment", "symptoms"]):
        return (
            f"Here's guidance for {category.replace('_', ' ')}:\n\n"
            "• Establish a consistent routine\n"
            "• Use medication reminders or pill organizers\n"
            "• Keep a symptom journal\n"
            "• Stay connected with support systems\n\n"
            "Please consult with your healthcare provider or medical professional for personalized advice. "
            "This information is for educational purposes only and should not replace professional medical guidance."
        )
    
    # ADL and mobility responses
    if "adl" in category:
        return (
            f"For assistance with {category.replace('_', ' ')}:\n\n"
            "• Consider adaptive equipment like grab bars or transfer boards\n"
            "• Break tasks into smaller, manageable steps\n"
            "• Ensure proper lighting and clear pathways\n"
            "• Practice exercises to maintain strength and flexibility\n\n"
            "Consult with an occupational therapist or healthcare provider for personalized recommendations."
        )
    
    # Caregiver support responses
    if "caregiver" in category:
        return (
            f"Caregiver support for {category.replace('_', ' ')}:\n\n"
            "• Take regular breaks to prevent burnout\n"
            "• Join caregiver support groups\n"
            "• Use respite care services when available\n"
            "• Practice self-care activities\n\n"
            "Remember: caring for yourself enables you to better care for others. "
            "Consider consulting with a healthcare professional for additional support resources."
        )
    
    # Disability support responses
    if "disability" in category:
        return (
            f"Support for {category.replace('_', ' ')}:\n\n"
            "• Research available assistive technologies\n"
            "• Connect with disability advocacy organizations\n"
            "• Understand your rights under the ADA\n"
            "• Explore community resources and support programs\n\n"
            "Contact disability services or a healthcare provider for personalized assistance and resources."
        )
    
    # Senior/social responses
    if "senior" in category and "medication" not in category:
        return (
            f"Guidance for {category.replace('_', ' ')}:\n\n"
            "• Join senior community centers or groups\n"
            "• Use technology to stay connected with family\n"
            "• Participate in activities that interest you\n"
            "• Consider volunteer opportunities\n\n"
            "Consult with your healthcare provider about programs and services available in your area."
        )
    
    # Default response with disclaimer
    return (
        f"Healthcare guidance for {category.replace('_', ' ')}:\n\n"
        "• Maintain regular communication with healthcare providers\n"
        "• Follow prescribed treatment plans\n"
        "• Keep detailed health records\n"
        "• Stay informed about your condition\n\n"
        "Please consult with a qualified healthcare professional for personalized medical advice."
    )


# Create mock healthcare training data
test_data = []

# Sample queries and categories
healthcare_samples = [
    ("My elderly father has trouble getting out of bed", "adl_mobility"),
    ("I need help with medication reminders", "senior_medication"),
    ("I feel overwhelmed caring for my mother", "caregiver_burnout"),
    ("What exercises are safe for seniors?", "senior_social"),
    ("I can't stop feeling anxious", "mental_health_anxiety"),
    ("I feel sad and hopeless", "mental_health_depression"),
    ("I want to hurt myself", "crisis_mental_health"),
    ("Need help with wheelchair transfers", "disability_equipment"),
    ("How do I get disability accommodations?", "disability_rights"),
    ("I need a break from caregiving", "caregiver_respite"),
    ("Help with bathing elderly parent", "adl_self_care"),
]

# Generate more samples
for query, category in healthcare_samples:
    # Create variations
    for i in range(20):
        variations = [
            query,
            f"Can you help with {query.lower()}?",
            f"I need advice about {query.lower()}",
            f"What should I do about {query.lower()}?",
            f"Looking for help with {query.lower()}",
        ]

        test_query = random.choice(variations)
        test_data.append(
            {
                "query": test_query,
                "category": category,
                "response": generate_response(category, test_query),
            }
        )

# Save test data
with open("data/test_healthcare_training.json", "w") as f:
    json.dump(test_data, f, indent=2)

print(f"Created {len(test_data)} test samples")
print("Categories:", set(item["category"] for item in test_data))
