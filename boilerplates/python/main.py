#!/usr/bin/env python3
# pylint: disable=duplicate-code
"""
Main entry point for the AI API Server
"""
import asyncio
import sys
from pathlib import Path

# Add the project root directory to the Python path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Import after path setup to avoid import errors
from src.index import (  # pylint: disable=wrong-import-position
    app,
    init_litellm_models,
    port,
    config
)

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
