from src.server import Server
from src.client import Client
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="P2P Network Application")
    parser.add_argument("--mode", choices=["server", "client", "client-app"], required=True,
                       help="Run as server, client, or client-app")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port to listen on (server) or connect to (client)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                       help="Host to bind to (server) or connect to (client)")
    parser.add_argument("--server-host", type=str, default="localhost",
                       help="Server host to connect to (client only)")
    parser.add_argument("--server-port", type=int, default=8000,
                       help="Server port to connect to (client only)")
    parser.add_argument("--relay-port", type=int, default=None,
                       help="Relay listen port (for relay request)")
    parser.add_argument("--relay-target-host", type=str, default=None,
                       help="Relay target host (for relay request)")
    parser.add_argument("--relay-target-port", type=int, default=None,
                       help="Relay target port (for relay request)")

    args = parser.parse_args()

    try:
        if args.mode == "server":
            # Optionally start relay if relay args are provided
            if args.relay_port and args.relay_target_host and args.relay_target_port:
                from src.tcp_relay import TCPRelayServer
                relay = TCPRelayServer(args.host, args.relay_port, args.relay_target_host, args.relay_target_port)
                asyncio.create_task(relay.start())
                logger.info(f"Started TCP relay on {args.host}:{args.relay_port} -> {args.relay_target_host}:{args.relay_target_port}")
            server = Server(args.host, args.port)
            await server.start()
        else:
            from src.client import Client
            # If client-app mode, pass relay args
            if args.mode == "client-app":
                client = Client(args.server_host, args.server_port)
                client.relay_port = args.relay_port
                client.relay_target_host = args.relay_target_host
                client.relay_target_port = args.relay_target_port
                await client.start()
            else:
                client = Client(args.server_host, args.server_port)
                await client.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
