import pytest
import asyncio
from src.server import Server

@pytest.fixture
async def server():
    server = Server('127.0.0.1', 0)
    yield server

@pytest.mark.asyncio
async def test_server_start(server):
    # Start server in background task
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Give server time to start
    
    # Test basic server functionality
    assert len(server.peers) == 0
    assert len(server.pending_connections) == 0
    
    # Cleanup
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
