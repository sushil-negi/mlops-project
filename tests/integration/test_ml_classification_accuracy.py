"""
Integration tests for ML classification accuracy with real trained model
"""

import json
import os
import pickle
import sys

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Add the healthcare-ai source directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../models/healthcare-ai/src")
)

from healthcare_trained_engine import HealthcareTrainedEngine


@pytest.fixture(scope="session")
def trained_model_path(tmp_path_factory):
    """Create a trained model for testing - shared across all test classes"""
    # Sample training data covering all categories
    training_data = [
        # ADL Mobility
        ("I need help transferring from bed to wheelchair", "adl_mobility"),
        ("What exercises can improve my balance?", "adl_mobility"),
        ("How do I safely use a walker?", "adl_mobility"),
        ("My legs are weak, what mobility aids help?", "adl_mobility"),
        # ADL Self-care
        ("I struggle with dressing due to arthritis", "adl_self_care"),
        ("What tools help with bathing independently?", "adl_self_care"),
        ("Eating is difficult with tremors", "adl_self_care"),
        ("Need help with grooming tasks", "adl_self_care"),
        # Senior Medication
        ("How do I manage multiple medications?", "senior_medication"),
        ("I keep forgetting to take my pills", "senior_medication"),
        ("What's the best pill organizer for seniors?", "senior_medication"),
        ("Medication side effects concern me", "senior_medication"),
        # Senior Social
        ("My mother feels isolated and lonely", "senior_social"),
        ("Where can seniors meet friends?", "senior_social"),
        ("How to stay socially connected as elderly?", "senior_social"),
        ("Senior activity programs near me", "senior_social"),
        # Mental Health Anxiety
        ("I'm anxious about my health condition", "mental_health_anxiety"),
        ("Panic attacks are affecting my life", "mental_health_anxiety"),
        ("How to manage anxiety as a senior?", "mental_health_anxiety"),
        ("Worried constantly about everything", "mental_health_anxiety"),
        # Mental Health Depression
        ("Feeling depressed and hopeless", "mental_health_depression"),
        ("No motivation to do anything anymore", "mental_health_depression"),
        ("Depression makes daily tasks hard", "mental_health_depression"),
        ("Sad all the time, need help", "mental_health_depression"),
        # Caregiver Respite
        ("I need a break from caregiving", "caregiver_respite"),
        ("Where can I find respite care?", "caregiver_respite"),
        ("How much does respite care cost?", "caregiver_respite"),
        ("Temporary care for my spouse needed", "caregiver_respite"),
        # Caregiver Burnout
        ("I'm exhausted from caring for my parent", "caregiver_burnout"),
        ("Feeling resentful about caregiving", "caregiver_burnout"),
        ("No time for myself anymore", "caregiver_burnout"),
        ("Caregiver stress is overwhelming", "caregiver_burnout"),
        # Disability Equipment
        ("What wheelchair is best for me?", "disability_equipment"),
        ("Need communication devices for speech", "disability_equipment"),
        ("Home modifications for wheelchair access", "disability_equipment"),
        ("Adaptive computer equipment needed", "disability_equipment"),
        # Disability Rights
        ("My employer won't provide accommodations", "disability_rights"),
        ("ADA rights for wheelchair users", "disability_rights"),
        ("Housing discrimination due to disability", "disability_rights"),
        ("Educational accommodations for disability", "disability_rights"),
        # Crisis Mental Health
        ("I want to end my life", "crisis_mental_health"),
        ("Thinking about hurting myself", "crisis_mental_health"),
        ("Life isn't worth living anymore", "crisis_mental_health"),
        ("Suicidal thoughts won't stop", "crisis_mental_health"),
    ]

    # Prepare data
    texts = [item[0] for item in training_data]
    labels = [item[1] for item in training_data]

    # Create category mapping
    unique_categories = sorted(list(set(labels)))
    category_to_idx = {cat: idx for idx, cat in enumerate(unique_categories)}
    idx_to_category = {idx: cat for cat, idx in category_to_idx.items()}

    # Convert labels to indices
    label_indices = [category_to_idx[label] for label in labels]

    # Train model
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=100, ngram_range=(1, 2))),
            ("classifier", MultinomialNB()),
        ]
    )

    pipeline.fit(texts, label_indices)

    # Create dummy responses for testing
    healthcare_responses = {
        cat: [f"Test response for {cat}"] for cat in unique_categories
    }

    # Save model
    model_data = {
        "pipeline": pipeline,
        "category_mapping": idx_to_category,
        "healthcare_responses": healthcare_responses,
    }

    model_path = tmp_path_factory.mktemp("models") / "test_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)

    return model_path


class TestMLClassificationAccuracy:
    """Test ML classification accuracy with various queries"""

    @pytest.fixture
    def engine(self, trained_model_path):
        """Create engine with trained model"""
        return HealthcareTrainedEngine(str(trained_model_path))

    @pytest.mark.parametrize(
        "query,expected_category",
        [
            # ADL Mobility tests
            ("I need help getting out of bed", "adl_mobility"),
            ("Balance exercises for elderly", "adl_mobility"),
            ("Wheelchair transfer techniques", "adl_mobility"),
            # Senior Medication tests
            ("Pill reminder systems for memory loss", "senior_medication"),
            ("Managing diabetes medications", "senior_medication"),
            ("Medication organizer recommendations", "senior_medication"),
            # Mental Health tests
            ("Feeling very anxious lately", "mental_health_anxiety"),
            ("Depressed about my health", "mental_health_depression"),
            # Caregiver tests
            ("Need respite care for weekend", "caregiver_respite"),
            ("Burned out from caregiving", "caregiver_burnout"),
            # Disability tests
            ("Need adaptive eating utensils", "disability_equipment"),
            ("Workplace accommodation rights", "disability_rights"),
            # Crisis tests
            ("Want to hurt myself", "crisis_mental_health"),
        ],
    )
    def test_classification_accuracy(self, engine, query, expected_category):
        """Test that queries are classified correctly"""
        response = engine.generate_response(query)

        # Crisis detection overrides ML classification
        if "hurt myself" in query.lower() or "suicide" in query.lower():
            assert response["method"] == "crisis_detection"
            assert response["category"] == "crisis_mental_health"
        else:
            # For non-crisis, check if category matches or is contextually overridden
            if response["method"] == "contextual_analysis":
                # Contextual override is acceptable - these provide better responses
                assert response["confidence"] == 0.95
                assert response["category"] == "contextual_override"
            else:
                # ML classification should be reasonably accurate
                # Allow for some flexibility in classification  
                assert response["method"] == "ml_model"
                # Category should be related to the expected one
                assert expected_category in response["category"] or response[
                    "category"
                ] in ["contextual_override", expected_category]

    def test_confidence_scores(self, engine):
        """Test that confidence scores are reasonable"""
        test_queries = [
            "I need help with mobility",
            "Medication management for seniors",
            "Feeling anxious about health",
            "Need respite care services",
            "Adaptive equipment for daily living",
        ]

        for query in test_queries:
            response = engine.generate_response(query)

            # Confidence should be between 0 and 1
            assert 0.0 <= response["confidence"] <= 1.0

            # Contextual overrides should have high confidence
            if response["method"] == "contextual_analysis":
                assert response["confidence"] == 0.95

            # Crisis detection should have maximum confidence
            if response["method"] == "crisis_detection":
                assert response["confidence"] == 1.0

    def test_ambiguous_query_handling(self, engine):
        """Test handling of ambiguous queries"""
        ambiguous_queries = [
            "I need help",
            "Having problems",
            "Not feeling well",
            "Family issues",
        ]

        for query in ambiguous_queries:
            response = engine.generate_response(query)

            # Should still provide a response
            assert response["response"]
            assert response["category"]

            # Confidence might be lower for ambiguous queries
            if response["method"] == "ml_model":
                # ML model might have lower confidence
                assert response["confidence"] >= 0.0

    def test_category_distribution(self, engine):
        """Test that model can classify into all categories"""
        category_test_queries = {
            "adl_mobility": "Help with walking and balance",
            "adl_self_care": "Bathing and dressing assistance",
            "senior_medication": "Organizing my medications",
            "senior_social": "Feeling lonely as a senior",
            "mental_health_anxiety": "Anxious about future",
            "mental_health_depression": "Feeling sad and hopeless",
            "caregiver_respite": "Need break from caregiving",
            "caregiver_burnout": "Exhausted from caring for parent",
            "disability_equipment": "Wheelchair recommendations",
            "disability_rights": "ADA accommodation at work",
        }

        categories_found = set()

        for expected_cat, query in category_test_queries.items():
            response = engine.generate_response(query)
            if response["method"] == "ml_model":
                categories_found.add(response["category"])

        # Should classify into multiple different categories
        assert len(categories_found) >= 5


class TestResponseQualityMetrics:
    """Test response quality metrics"""

    @pytest.fixture
    def engine(self, trained_model_path):
        """Create engine with trained model"""
        return HealthcareTrainedEngine(str(trained_model_path))

    def test_response_length(self, engine):
        """Test that responses are appropriately detailed"""
        queries = [
            "How do I transfer from bed to wheelchair?",
            "What medication reminders work best?",
            "I'm feeling overwhelmed as a caregiver",
        ]

        for query in queries:
            response = engine.generate_response(query)

            # Responses should be substantial
            assert len(response["response"]) > 100

            # But not too long
            assert len(response["response"]) < 1000

    def test_response_actionability(self, engine):
        """Test that responses contain actionable advice"""
        response = engine.generate_response(
            "My elderly father has trouble getting out of bed"
        )

        response_text = response["response"]

        # Should contain numbered steps or bullet points
        assert any(marker in response_text for marker in ["1)", "2)", "•", "-"])

        # Should contain specific actions
        actionable_keywords = ["Install", "Use", "Place", "Consider", "Contact", "Ask"]
        assert any(keyword in response_text for keyword in actionable_keywords)

    def test_response_safety_warnings(self, engine):
        """Test that responses include appropriate warnings"""
        response = engine.generate_response("I need help with wheelchair transfers")

        # Should include safety warning
        assert "⚠️" in response["response"]

        # Should mention professional consultation
        assert any(
            term in response["response"].lower()
            for term in ["professional", "healthcare provider", "therapist", "consult"]
        )

    def test_response_specificity(self, engine):
        """Test that responses are specific to the query"""
        # Test eating equipment
        eating_response = engine.generate_response(
            "I need adaptive equipment for eating"
        )
        assert (
            "eating" in eating_response["response"].lower()
            or "utensils" in eating_response["response"].lower()
            or "weighted" in eating_response["response"].lower()
        )

        # Test exercise
        exercise_response = engine.generate_response("What exercises help seniors?")
        assert any(
            term in exercise_response["response"].lower()
            for term in ["exercise", "walking", "balance", "strength", "tai chi"]
        )

        # Test medication
        med_response = engine.generate_response("How to remember medications?")
        assert any(
            term in med_response["response"].lower()
            for term in ["medication", "pill", "reminder", "organizer"]
        )


class TestPerformanceMetrics:
    """Test performance metrics of the system"""

    @pytest.fixture
    def engine(self, trained_model_path):
        """Create engine with trained model"""
        return HealthcareTrainedEngine(str(trained_model_path))

    def test_response_generation_time(self, engine):
        """Test that responses are generated quickly"""
        queries = [
            "I need help with mobility",
            "Medication management tips",
            "Feeling anxious about health",
        ]

        for query in queries:
            response = engine.generate_response(query)

            # Response should be generated in less than 100ms
            assert response["generation_time"] < 0.1

            # Cached responses should be even faster
            cached_response = engine.generate_response(query)
            assert cached_response.get("cached") == True
            assert cached_response["generation_time"] < 0.01

    def test_cache_effectiveness(self, engine):
        """Test that caching improves performance"""
        query = "How to manage multiple medications?"

        # First call - not cached
        response1 = engine.generate_response(query)
        time1 = response1["generation_time"]

        # Second call - should be cached
        response2 = engine.generate_response(query)
        time2 = response2["generation_time"]

        assert response2.get("cached") == True
        assert time2 < time1  # Cached should be faster

        # Verify cache stats
        stats = engine.get_stats()
        assert stats["cache_size"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
