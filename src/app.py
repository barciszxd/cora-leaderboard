"""Cora leaderboard API"""
import argparse
from flask import Flask, jsonify

# Create Flask application instance
app = Flask(__name__)

# Define the GET endpoint
@app.route('/', methods=['GET'])
def hello_world():
    """Simple GET endpoint that returns a JSON response"""
    return jsonify({
        "response": "Hello world"
    })

# Additional endpoint for health check
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Flask API is running successfully"
    })

if __name__ == '__main__':
    # Run the Flask app in debug mode

    arg_parser = argparse.ArgumentParser(description="Cora leaderboard API")
    arg_parser.add_argument("--host", default="127.0.0.1", help="Host to run the API on")
    arg_parser.add_argument("--port", default=5000, type=int, help="Port to run the API on")
    arg_parser.add_argument("--debug", action='store_true', help="Run the API in debug mode")
    args = arg_parser.parse_args()

    app.run(debug=args.debug, host=args.host, port=args.port)
