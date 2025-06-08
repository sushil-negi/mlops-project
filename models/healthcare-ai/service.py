#!/usr/bin/env python3
"""
Healthcare AI Docker Service Entry Point
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from healthcare_ai_engine import HealthcareAIEngine
    from healthcare_trained_engine import HealthcareTrainedEngine

    ENGINES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Healthcare engines: {e}")
    print("Will use basic healthcare model instead")
    ENGINES_AVAILABLE = False

# If engines not available, create a basic fallback
if not ENGINES_AVAILABLE:
    from healthcare_model import HealthcareResponseEngine

    class BasicHealthcareEngine:
        def __init__(self):
            self.response_engine = HealthcareResponseEngine()
            self.conversation_history = []

        def generate_response(self, message):
            response = self.response_engine.get_response(message)
            return {
                "response": response,
                "category": "general_healthcare",
                "confidence": 0.8,
                "method": "rule_based",
                "generation_time": 0.1,
            }

        def get_stats(self):
            return {
                "model_loaded": True,
                "categories": 4,
                "category_list": [
                    "adl",
                    "senior_care",
                    "mental_health",
                    "respite_care",
                ],
                "total_responses": 12,
                "cache_size": 0,
                "conversation_history": len(self.conversation_history),
                "model_type": "Rule-based Healthcare Engine",
            }


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HealthcareAIHandler(BaseHTTPRequestHandler):
    """HTTP handler for healthcare AI chatbot"""

    def __init__(self, *args, **kwargs):
        # Initialize AI engine (shared across requests)
        if not hasattr(self.__class__, "ai_engine"):
            logger.info("Initializing Healthcare AI Engine...")

            if ENGINES_AVAILABLE:
                # Try trained model first
                try:
                    logger.info("Attempting to load trained ML model...")
                    self.__class__.ai_engine = HealthcareTrainedEngine()
                    logger.info("✅ Trained ML model loaded successfully")
                except Exception as e:
                    logger.warning(f"Trained model failed: {e}")
                    try:
                        logger.info("Falling back to AI engine...")
                        self.__class__.ai_engine = HealthcareAIEngine(use_llm=False)
                        logger.info("✅ AI engine loaded successfully")
                    except Exception as e2:
                        logger.warning(f"AI engine failed: {e2}")
                        logger.info("Using basic healthcare engine")
                        self.__class__.ai_engine = BasicHealthcareEngine()
            else:
                logger.info("Using basic healthcare engine")
                self.__class__.ai_engine = BasicHealthcareEngine()

        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == "/health":
                self.send_health_response()
            elif self.path == "/stats":
                self.send_stats_response()
            elif self.path == "/" or self.path == "/chat":
                self.send_chat_interface()
            elif self.path == "/info":
                self.send_info_response()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"GET error: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == "/chat":
                self.handle_chat_request()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"POST error: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def send_health_response(self):
        """Send health check response"""
        try:
            if hasattr(self.ai_engine, "get_stats"):
                engine_stats = self.ai_engine.get_stats()
            else:
                engine_stats = self.ai_engine.get_conversation_stats()

            health_data = {
                "status": "healthy",
                "service": "Healthcare AI Assistant",
                "version": "3.0.0",
                "engine_stats": engine_stats,
                "timestamp": datetime.now().isoformat(),
            }

            self.send_json_response(health_data)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            error_data = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.send_json_response(error_data, status_code=500)

    def send_stats_response(self):
        """Send stats response"""
        try:
            if hasattr(self.ai_engine, "get_stats"):
                stats = self.ai_engine.get_stats()
            else:
                stats = self.ai_engine.get_conversation_stats()

            self.send_json_response(stats)
        except Exception as e:
            logger.error(f"Stats error: {e}")
            self.send_json_response({"error": str(e)}, status_code=500)

    def send_chat_interface(self):
        """Send chat interface HTML"""
        try:
            with open("healthcare_chat.html", "r", encoding="utf-8") as f:
                html_content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        except FileNotFoundError:
            self.send_error(404, "Chat interface not found")
        except Exception as e:
            logger.error(f"Chat interface error: {e}")
            self.send_error(500, f"Error serving chat interface: {str(e)}")

    def send_info_response(self):
        """Send service info response"""
        info_data = {
            "service": "Healthcare AI Assistant",
            "version": "3.0.0",
            "engine": "Trained ML Model" if USE_TRAINED_MODEL else "AI Engine",
            "endpoints": {
                "health": "/health",
                "chat": "/chat (POST)",
                "stats": "/stats",
            },
        }
        self.send_json_response(info_data)

    def handle_chat_request(self):
        """Handle chat requests"""
        try:
            # Read request data
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_json_response(
                    {"error": "No message provided"}, status_code=400
                )
                return

            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode("utf-8"))

            message = request_data.get("message", "").strip()
            if not message:
                self.send_json_response({"error": "Empty message"}, status_code=400)
                return

            # Generate response
            response_data = self.ai_engine.generate_response(message)

            self.send_json_response(response_data)

        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, status_code=400)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.send_json_response(
                {"error": f"Processing error: {str(e)}"}, status_code=500
            )

    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode("utf-8"))

    def log_message(self, format, *args):
        """Override to use logger instead of print"""
        logger.info(f"{self.address_string()} - {format % args}")


def start_healthcare_ai_service():
    """Start the healthcare AI service"""
    port = int(os.getenv("PORT", 8000))

    logger.info(f"🚀 Starting Healthcare AI Service on port {port}")
    logger.info(f"Engines available: {ENGINES_AVAILABLE}")

    try:
        server = HTTPServer(("0.0.0.0", port), HealthcareAIHandler)
        logger.info(f"✅ Healthcare AI Service ready at http://0.0.0.0:{port}")
        logger.info("Available endpoints:")
        logger.info("  - GET  /health  - Health check")
        logger.info("  - POST /chat    - Chat with AI")
        logger.info("  - GET  /stats   - Engine statistics")

        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("👋 Healthcare AI Service stopping...")
        server.shutdown()
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
        raise


if __name__ == "__main__":
    start_healthcare_ai_service()
