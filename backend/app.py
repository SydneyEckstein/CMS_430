"""
Wikipedia Chain Finder - Flask Application

This module provides the REST API for the Wikipedia Chain Finder:
- GET /api/health - Health check endpoint
- POST /api/find-path - Find shortest path between two Wikipedia articles

The frontend is served as static files from the frontend directory.
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)


@app.route('/')
def index():
    """Serve the frontend application."""
    return app.send_static_file('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the server is running."""
    return jsonify({'status': 'ok'})


@app.route('/api/find-path', methods=['POST'])
def find_path():
    """
    Find the shortest path between two Wikipedia articles.

    Request body (JSON):
        {
            "start": "Article_Title",
            "end": "Article_Title"
        }

    Response (JSON):
        Success (200):
            {
                "success": true,
                "path": ["Article1", "Article2", ...],
                "depth": 3,
                "pages_explored": 150
            }
        Error (400/404/500):
            {
                "success": false,
                "error": "Descriptive error message"
            }
    """
    # Implementation will be added in Phase 4
    return jsonify({
        'success': False,
        'error': 'Not implemented yet'
    }), 501


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
