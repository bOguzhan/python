import pytest
import asyncio
import json
from src.client import Client

@pytest.fixture
async def mock_server():
    # Create a mock server for testing
    server = await asyncio.start_server(
        handle_mock_connection,
        '127.0.0.1',
        0
    )
    addr = server.sockets[0].getsockname()
    
    yield addr
    
    server.close()
    await server.wait_closed()

async def handle_mock_connection(reader, writer):
    # Mock server handler that responds to registration
    while True:
        try:
            data = await reader.readline()
            if not data:
                break
                
            message = json.loads(data.decode())
            if message.get('type') == 'register':
                response = {
                    'type': 'register_ack',
                    'peer_id': 'test_peer_id'
                }
                writer.write(json.dumps(response).encode() + b'\n')
                await writer.drain()
        except:
            break
    
    writer.close()
    await writer.wait_closed()

@pytest.mark.asyncio
async def test_client_registration(mock_server):
    host, port = mock_server
    client = Client(host, port)
    
    # Test client registration
    client_task = asyncio.create_task(client.start())
    await asyncio.sleep(0.1)  # Give client time to register
    
    assert client.peer_id == 'test_peer_id'
    
    # Cleanup
    client_task.cancel()
    try:
        await client_task
    except asyncio.CancelledError:
        pass
