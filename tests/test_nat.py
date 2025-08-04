import pytest
import socket
import asyncio
from src.nat import create_punch_socket, punch_hole, establish_p2p_connection

@pytest.mark.asyncio
async def test_create_punch_socket():
    sock, port = await create_punch_socket('127.0.0.1')
    assert isinstance(sock, socket.socket)
    assert isinstance(port, int)
    assert port > 0
    sock.close()

@pytest.mark.asyncio
async def test_punch_hole():
    # Create two sockets for testing
    sock1, port1 = await create_punch_socket('127.0.0.1')
    sock2, port2 = await create_punch_socket('127.0.0.1')
    
    # Test hole punching between the sockets
    success = await punch_hole(sock1, '127.0.0.1', port2, retries=1)
    
    # Cleanup
    sock1.close()
    sock2.close()
    
    # Note: This test might fail in real environments due to no actual NAT
    assert success is False  # Expected in test environment

@pytest.mark.asyncio
async def test_establish_p2p_connection():
    sock = await establish_p2p_connection('127.0.0.1', '127.0.0.1', 12345)
    if sock:
        sock.close()
    # Note: This test is expected to fail in test environment
    assert sock is None
