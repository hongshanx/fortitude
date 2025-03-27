# pylint: disable=duplicate-code
"""Main application entry point and Flask server configuration.

This module initializes the Flask application, sets up middleware,
configures routes, and handles server startup tasks including
LiteLLM model initialization.
"""

import asyncio
import signal
import sys
from typing import Any, NoReturn, Tuple, Type

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.config.env import config
from src.middlewares.error_handler import handle_error, not_found
from src.routes.api_routes import api_bp
from src.services.litellm_service import LiteLLMService
from src.types.api import get_litellm_models, get_all_models, update_litellm_models

# Create Flask app
app = Flask(__name__)
port = config.server.port

# Middleware
CORS(app)

# Request logging in development
if config.server.is_dev:
    @app.before_request
    def log_request() -> None:
        """Log incoming requests in development mode."""
        print(f"{request.method} {request.url}")

# API routes
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def root() -> dict:
    """Root endpoint providing API information.

    Returns:
        dict: API metadata and available endpoints.
    """
    return jsonify({
        "name": "AI API Server",
        "version": "1.0.0",
        "description": "API server for OpenAI, DeepSeek, and LiteLLM models",
        "endpoints": {
            "models": "/api/models",
            "providers": "/api/providers",
            "completions": "/api/completions",
            "health": "/api/health",
            "predict_stock": "/api/predict/stock",
        },
    })


@app.errorhandler(404)
def handle_not_found(_: Exception) -> Tuple[dict, int]:
    """Handle 404 Not Found errors.

    Args:
        _: The exception that was raised (unused).

    Returns:
        Tuple[dict, int]: Error response and status code.
    """
    return not_found()


@app.errorhandler(Exception)
def handle_exception(e: Exception) -> Tuple[dict, int]:
    """Global exception handler.

    Args:
        e: The exception that was raised.

    Returns:
        Tuple[dict, int]: Error response and status code.
    """
    return handle_error(e)


async def init_litellm_models() -> None:
    """Initialize LiteLLM models at startup if configured."""
    openai_key_configured = (config.openai.api_key and
                           config.openai.api_key != "your_openai_api_key_here")
    deepseek_key_configured = (config.deepseek.api_key and
                             config.deepseek.api_key != "your_deepseek_api_key_here")
    litellm_key_configured = (config.litellm.api_key and
                            config.litellm.api_key != "your_litellm_api_key_here")

    print(f"🔑 OpenAI API key: {'Configured' if openai_key_configured else 'Not configured'}")
    print(f"🔑 DeepSeek API key: {'Configured' if deepseek_key_configured else 'Not configured'}")
    print(f"🔑 LiteLLM API key: {'Configured' if litellm_key_configured else 'Not configured'}")

    if not any([openai_key_configured, deepseek_key_configured, litellm_key_configured]):
        print("⚠️  Warning: No API keys configured. Please set up API keys in .env file.")

    if litellm_key_configured:
        try:
            print("🔄 Fetching LiteLLM models...")
            litellm_models = await LiteLLMService.get_models()
            print(f"Debug: LiteLLM models before update: {litellm_models}")
            update_litellm_models(litellm_models)
            print(f"Debug: LiteLLM models after update: {get_litellm_models()}")
            print(f"Debug: ALL_MODELS after update: {get_all_models()}")
            print(f"✅ Fetched {len(litellm_models)} LiteLLM models")
        except (ConnectionError, TimeoutError) as e:
            print(f"❌ Failed to fetch LiteLLM models due to connection error: {e}")
            update_litellm_models([])
            print("⚠️  No LiteLLM models will be available")
        except (ValueError, TypeError) as e:
            print(f"❌ Invalid response from LiteLLM API: {e}")
            update_litellm_models([])
            print("⚠️  No LiteLLM models will be available")
        except KeyError as e:
            print(f"❌ Missing required data in LiteLLM response: {e}")
            update_litellm_models([])
            print("⚠️  No LiteLLM models will be available")
        except (AttributeError, ImportError) as e:
            print(f"❌ Configuration or module error: {e}")
            update_litellm_models([])
            print("⚠️  No LiteLLM models will be available")


def handle_unhandled_exception(exc_type: Type[BaseException],
                             exc_value: BaseException,
                             exc_traceback: Any) -> None:
    """Handle unhandled exceptions globally.

    Args:
        exc_type: The type of the exception.
        exc_value: The exception instance.
        exc_traceback: The traceback object.
    """
    print("Unhandled Exception:", exc_value)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_unhandled_exception


def signal_handler(_: signal.Signals, __: Any) -> NoReturn:
    """Handle system signals for graceful shutdown.

    Args:
        sig: The signal number.
        frame: The current stack frame.
    """
    print("Shutting down...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Run initialization tasks
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_litellm_models())

    # Start server
    print(f"✅ Server running at http://localhost:{port}")
    print(f"📝 API documentation available at http://localhost:{port}/api")
    print(f"🔍 Health check at http://localhost:{port}/api/health")
    print(f"🌍 Environment: {config.server.flask_env}")

    app.run(host="0.0.0.0", port=port, debug=config.server.is_dev)
