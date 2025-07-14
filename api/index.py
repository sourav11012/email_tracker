"""
Vercel looks for a variable called `app` (WSGI) or `handler` (ASGI).
We simply import the Flask instance from tracker.py.
"""
from api.tracker import app  # <- the Flask `app` defined above
