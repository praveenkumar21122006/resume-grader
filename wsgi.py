import os
import sys
# Ensure backend is importable as package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app

# gunicorn entrypoint: wsgi:app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
