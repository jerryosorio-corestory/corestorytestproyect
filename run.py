"""
Application entry point.

Run this file directly to start the development server:
  python run.py

For production, use a WSGI server such as Gunicorn:
  gunicorn "run:app"
"""

import os
from app import create_app

# Read the desired environment from the ENV variable, fall back to 'development'
env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    # Debug mode is controlled by the config, not hardcoded here
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
