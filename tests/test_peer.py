import pytest
import asyncio
from src.peer import Peer

@pytest.fixture
async def peer_connection():
    # Create a server and client connection pair for testing
    server = await asyncio.start_server(
        lambda r, w: None,
        '127.0.0.1',
        0
    )
    addr = server.sockets[0].getsockname()
    
    reader, writer = await asyncio.open_connection(*addr)
    peer = Peer(reader, writer)
    
    yield peer
    
    writer.close()
    await writer.wait_closed()
    server.close()
    await server.wait_closed()

@pytest.mark.asyncio
async def test_peer_send_receive(peer_connection):
    # Test message sending and receiving
    test_message = {"type": "test", "data": "hello"}
    await peer_connection.send(test_message)
    
    # In a real test, we would set up a proper echo server
    # and verify the received message matches what was sent
