from src.server import Server
from src.client import Client
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="P2P Network Application")
    parser.add_argument("--mode", choices=["server", "client"], required=True,
                       help="Run as server or client")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port to listen on (server) or connect to (client)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                       help="Host to bind to (server) or connect to (client)")
    parser.add_argument("--server-host", type=str, default="localhost",
                       help="Server host to connect to (client only)")
    parser.add_argument("--server-port", type=int, default=8000,
                       help="Server port to connect to (client only)")

    args = parser.parse_args()

    try:
        if args.mode == "server":
            server = Server(args.host, args.port)
            await server.start()
        else:
            client = Client(args.server_host, args.server_port)
            await client.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
