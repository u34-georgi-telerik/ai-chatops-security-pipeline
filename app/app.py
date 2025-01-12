"""
app.py
This module initializes and runs the Flask application.
"""

import os
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """
    Return a simple greeting message.
    """
    return "Hello, World!"


if __name__ == "__main__":

    # Entry point for the Flask application.
    # The app runs on the port specified in the environment variable 'PORT'
    # or defaults to 5000 and listens on all interfaces.

    app.run(port=os.environ.get("PORT", 5000), host="0.0.0.0")
