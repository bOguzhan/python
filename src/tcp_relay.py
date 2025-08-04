import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TCPRelayServer:
    def __init__(self, listen_host: str, listen_port: int, target_host: str, target_port: int):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port

    async def handle_client(self, client_reader, client_writer):
        logger.info(f"Accepted connection from {client_writer.get_extra_info('peername')}")
        try:
            # Connect to the target server
            target_reader, target_writer = await asyncio.open_connection(self.target_host, self.target_port)
            logger.info(f"Connected to target {self.target_host}:{self.target_port}")

            async def relay(reader, writer):
                try:
                    while True:
                        data = await reader.read(4096)
                        if not data:
                            break
                        writer.write(data)
                        await writer.drain()
                except Exception as e:
                    logger.info(f"Relay error: {e}")
                finally:
                    writer.close()
                    await writer.wait_closed()

            await asyncio.gather(
                relay(client_reader, target_writer),
                relay(target_reader, client_writer)
            )
        except Exception as e:
            logger.error(f"Relay setup error: {e}")
        finally:
            client_writer.close()
            await client_writer.wait_closed()
            logger.info("Closed client connection")

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.listen_host, self.listen_port)
        logger.info(f"TCP relay listening on {self.listen_host}:{self.listen_port}, forwarding to {self.target_host}:{self.target_port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple TCP Relay Server")
    parser.add_argument('--listen-host', default='0.0.0.0', help='Relay listen host (default: 0.0.0.0)')
    parser.add_argument('--listen-port', type=int, required=True, help='Relay listen port')
    parser.add_argument('--target-host', required=True, help='Target host to forward to')
    parser.add_argument('--target-port', type=int, required=True, help='Target port to forward to')
    args = parser.parse_args()

    relay = TCPRelayServer(args.listen_host, args.listen_port, args.target_host, args.target_port)
    asyncio.run(relay.start())
