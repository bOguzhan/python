import asyncio
import logging
import json
from typing import Dict, Set
from .peer import Peer

logger = logging.getLogger(__name__)

class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.peers: Dict[str, Peer] = {}
        self.pending_connections: Set[str] = set()

    async def start(self):
        """Start the server and listen for incoming connections."""
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming peer connections."""
        peer_addr = writer.get_extra_info('peername')
        logger.info(f'New connection from {peer_addr}')

        peer = Peer(reader, writer)
        peer_id = f"{peer_addr[0]}:{peer_addr[1]}"
        peer.public_addr = peer_addr  # Store public address on the peer object
        self.peers[peer_id] = peer

        try:
            while True:
                try:
                    message = await peer.receive()
                    if not message:
                        break

                    await self.handle_message(peer_id, message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid message format from {peer_id}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message from {peer_id}: {e}")
                    break
        except Exception as e:
            logger.error(f"Error handling connection from {peer_id}: {e}")
        finally:
            await self.remove_peer(peer_id)

    async def handle_message(self, peer_id: str, message: dict):
        """Handle incoming messages from peers."""
        msg_type = message.get('type')
        if not msg_type:
            return

        if msg_type == 'register':
            await self.handle_register(peer_id, message)
        elif msg_type == 'connect':
            await self.handle_connect_request(peer_id, message)
        elif msg_type == 'punch':
            await self.handle_punch_request(peer_id, message)

    async def handle_register(self, peer_id: str, message: dict):
        """Handle peer registration."""
        logger.info(f"Registered peer {peer_id}")
        # Store public address for this peer
        peer = self.peers[peer_id]
        peer.public_addr = peer.writer.get_extra_info('peername')
        response = {
            'type': 'register_ack',
            'peer_id': peer_id,
            'public_addr': peer.public_addr
        }
        await peer.send(response)

    async def handle_connect_request(self, peer_id: str, message: dict):
        """Handle connection requests between peers."""
        target_id = message.get('target_id')
        if not target_id or target_id not in self.peers:
            await self.peers[peer_id].send({
                'type': 'error',
                'message': 'Target peer not found'
            })
            return

        # Notify both peers about the connection request, including public IP/port
        await self.peers[peer_id].send({
            'type': 'connect_ready',
            'target_id': target_id,
            'target_addr': self.peers[target_id].public_addr
        })
        await self.peers[target_id].send({
            'type': 'connect_ready',
            'target_id': peer_id,
            'target_addr': self.peers[peer_id].public_addr
        })

    async def handle_punch_request(self, peer_id: str, message: dict):
        """Handle NAT punch requests."""
        target_id = message.get('target_id')
        if not target_id or target_id not in self.peers:
            return

        # Forward punch request to target peer, including peer_id and target_addr
        punch_msg = {
            'type': 'punch',
            'peer_id': peer_id,
            'port': message.get('port', 0),
            'target_addr': self.peers[peer_id].public_addr
        }
        await self.peers[target_id].send(punch_msg)

    async def remove_peer(self, peer_id: str):
        """Remove a peer from the server."""
        if peer_id in self.peers:
            await self.peers[peer_id].close()
            del self.peers[peer_id]
            logger.info(f"Peer {peer_id} disconnected")
