"""Application entry point"""
import argparse
from app import create_app

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Cora leaderboard API")
    arg_parser.add_argument("--host", default="127.0.0.1", help="Host to run the API on")
    arg_parser.add_argument("--port", default=5000, type=int, help="Port to run the API on")
    arg_parser.add_argument("--prod", action='store_true', help="Run the API in production mode")
    args = arg_parser.parse_args()

    app = create_app('production' if args.prod else 'development')
    app.run(host=args.host, port=args.port)