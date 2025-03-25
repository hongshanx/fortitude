#!/usr/bin/env python3
"""
Main entry point for the AI API Server
"""
import sys
import os
import asyncio

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.index import app, init_litellm_models, port, config

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
