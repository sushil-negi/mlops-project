#!/usr/bin/env python3
"""
Create test data for MLOps pipeline demonstration
"""

import json
import random

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
        test_data.append({
            "query": test_query,
            "category": category,
            "response": f"Professional healthcare guidance for {category}"
        })

# Save test data
with open("data/test_healthcare_training.json", "w") as f:
    json.dump(test_data, f, indent=2)

print(f"Created {len(test_data)} test samples")
print("Categories:", set(item['category'] for item in test_data))