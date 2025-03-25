import asyncio
from flask import Flask, jsonify
from flask_cors import CORS
import sys
import signal
from src.config.env import config
from src.routes.api_routes import api_bp
from src.middlewares.error_handler import not_found, handle_error
from src.services.litellm_service import LiteLLMService
from src.types.api import update_litellm_models

# Create Flask app
app = Flask(__name__)
port = config.server.port

# Middleware
CORS(app)

# Request logging in development
if config.server.is_dev:
    @app.before_request
    def log_request():
        from flask import request
        print(f"{request.method} {request.url}")

# API routes
app.register_blueprint(api_bp, url_prefix='/api')

# Root route
@app.route('/')
def root():
    return jsonify({
        "name": "AI API Server",
        "version": "1.0.0",
        "description": "API server for OpenAI, DeepSeek, and LiteLLM models",
        "endpoints": {
            "models": "/api/models",
            "providers": "/api/providers",
            "completions": "/api/completions",
            "health": "/api/health",
        },
    })

# 404 handler
@app.errorhandler(404)
def handle_not_found(e):
    return not_found()

# Error handler
@app.errorhandler(Exception)
def handle_exception(e):
    return handle_error(e)

# Initialize LiteLLM models
async def init_litellm_models():
    """Fetch LiteLLM models at startup if configured"""
    openai_key_configured = config.openai.api_key and config.openai.api_key != "your_openai_api_key_here"
    deepseek_key_configured = config.deepseek.api_key and config.deepseek.api_key != "your_deepseek_api_key_here"
    litellm_key_configured = config.litellm.api_key and config.litellm.api_key != "your_litellm_api_key_here"
    
    print(f"🔑 OpenAI API key: {'Configured' if openai_key_configured else 'Not configured'}")
    print(f"🔑 DeepSeek API key: {'Configured' if deepseek_key_configured else 'Not configured'}")
    print(f"🔑 LiteLLM API key: {'Configured' if litellm_key_configured else 'Not configured'}")
    
    if not openai_key_configured and not deepseek_key_configured and not litellm_key_configured:
        print("⚠️  Warning: No API keys configured. Please set up API keys in .env file.")
    
    # Fetch LiteLLM models at startup if configured
    if litellm_key_configured:
        try:
            print("🔄 Fetching LiteLLM models...")
            litellm_models = await LiteLLMService.get_models()
            print(f"Debug: LiteLLM models before update: {litellm_models}")
            update_litellm_models(litellm_models)
            from src.types.api import LITELLM_MODELS, ALL_MODELS
            print(f"Debug: LITELLM_MODELS after update: {LITELLM_MODELS}")
            print(f"Debug: ALL_MODELS after update: {ALL_MODELS}")
            print(f"✅ Fetched {len(litellm_models)} LiteLLM models")
        except Exception as e:
            print(f"❌ Failed to fetch LiteLLM models: {e}")
            # Update with empty list in case of error
            update_litellm_models([])
            from src.types.api import LITELLM_MODELS, ALL_MODELS
            print(f"Debug: LITELLM_MODELS after error: {LITELLM_MODELS}")
            print(f"Debug: ALL_MODELS after error: {ALL_MODELS}")
            print("⚠️  No LiteLLM models will be available")

# Handle unhandled exceptions
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    print("Unhandled Exception:", exc_value)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_unhandled_exception

# Handle signals
def signal_handler(sig, frame):
    print("Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Run the app
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
