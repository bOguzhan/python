import asyncio
import logging
import json
from typing import Optional, Dict
from .peer import Peer

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, server_host: str, server_port: int):
        self.server_host = server_host
        self.server_port = server_port
        self.peer_id: Optional[str] = None
        self.peers: Dict[str, Peer] = {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def start(self):
        """Start the client and connect to the server."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.server_host, self.server_port
            )
            logger.info(f"Connected to server at {self.server_host}:{self.server_port}")

            # Register with the server
            await self.register()

            # Start message handling loop
            await self.message_loop()

        except Exception as e:
            logger.error(f"Error starting client: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()

    async def register(self):
        """Register with the server."""
        register_msg = {
            'type': 'register'
        }
        await self._send_to_server(register_msg)

        response = await self._receive_from_server()
        if response and response.get('type') == 'register_ack':
            self.peer_id = response.get('peer_id')
            logger.info(f"Registered with server, assigned ID: {self.peer_id}")
        else:
            raise Exception("Failed to register with server")

    async def connect_to_peer(self, target_id: str):
        """Initiate connection to another peer."""
        connect_msg = {
            'type': 'connect',
            'target_id': target_id
        }
        await self._send_to_server(connect_msg)

    async def message_loop(self):
        """Main message handling loop."""
        try:
            # Start user input handling in the background
            asyncio.create_task(self.handle_user_input())
            
            while True:
                if not self.reader:
                    break

                message = await self._receive_from_server()
                if not message:
                    break

                await self.handle_message(message)
        except Exception as e:
            logger.error(f"Error in message loop: {e}")

    async def handle_user_input(self):
        """Handle user commands from stdin."""
        while True:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Enter command (connect <peer_id> or quit): "
                )
                
                if command.startswith("connect "):
                    peer_id = command.split(" ", 1)[1].strip()
                    logger.info(f"Initiating connection to peer: {peer_id}")
                    await self.connect_to_peer(peer_id)
                elif command == "quit":
                    logger.info("Shutting down...")
                    break
            except Exception as e:
                logger.error(f"Error handling command: {e}")

    async def handle_message(self, message: dict):
        """Handle incoming messages."""
        msg_type = message.get('type')
        if not msg_type:
            return

        if msg_type == 'connect_ready':
            await self.handle_connect_ready(message)
        elif msg_type == 'punch':
            await self.handle_punch(message)
        elif msg_type == 'error':
            logger.error(f"Received error: {message.get('message')}")

    async def handle_connect_ready(self, message: dict):
        """Handle connection ready message."""
        target_id = message.get('target_id')
        target_addr = message.get('target_addr')
        if not target_id or not target_addr:
            logger.error("Missing target_id or target_addr in connect_ready message")
            return

        peer_ip, peer_port = target_addr
        logger.info(f"Received peer public address: {peer_ip}:{peer_port}")
        # Start NAT punch process using public IP/port
        punch_msg = {
            'type': 'punch',
            'target_id': target_id,
            'port': peer_port,
            'target_addr': target_addr
        }
        await self._send_to_server(punch_msg)

    async def handle_punch(self, message: dict):
        """Handle punch message for NAT traversal (TCP)."""
        peer_id = message.get('peer_id')
        port = message.get('port', 25565)
        target_addr = message.get('target_addr')
        if not peer_id or not target_addr:
            logger.error("Missing peer_id or target_addr in punch message")
            return
        peer_ip, peer_port = target_addr
        logger.info(f"Received punch request from {peer_id} at {peer_ip}:{peer_port} (TCP)")
        from .nat import tcp_hole_punch
        sock = await tcp_hole_punch('0.0.0.0', port, peer_ip, peer_port)
        if sock:
            logger.info(f"TCP hole punch successful: {sock.getsockname()} <-> {sock.getpeername()}")
        else:
            logger.warning("TCP hole punch failed after all retries")

    async def _send_to_server(self, message: dict):
        """Send a message to the server."""
        if not self.writer:
            raise Exception("Not connected to server")
        
        try:
            data = json.dumps(message).encode()
            self.writer.write(data + b'\n')
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error sending message to server: {e}")
            raise

    async def _receive_from_server(self) -> Optional[dict]:
        """Receive a message from the server."""
        if not self.reader:
            return None

        try:
            data = await self.reader.readline()
            if not data:
                return None
            
            message = json.loads(data.decode())
            return message
        except Exception as e:
            logger.error(f"Error receiving message from server: {e}")
            return None
