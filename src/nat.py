import socket
import asyncio
import logging
from typing import Tuple, Optional, Callable

class _TCPPunchProtocol(asyncio.Protocol):
    def __init__(self, on_connection: Callable):
        self.on_connection = on_connection
    def connection_made(self, transport):
        self.on_connection(transport)

async def tcp_hole_punch(local_host: str, local_port: int, target_host: str, target_port: int, timeout: float = 5.0) -> Optional[socket.socket]:
    """
    Attempt TCP hole punching by simultaneously listening and connecting.
    Returns the established socket if successful, else None.
    """
    loop = asyncio.get_event_loop()
    incoming_fut = loop.create_future()

    def on_incoming(transport):
        if not incoming_fut.done():
            incoming_fut.set_result(transport)

    server = await loop.create_server(lambda: _TCPPunchProtocol(on_incoming), local_host, local_port)
    try:
        # Start outgoing connection attempt
        outgoing_task = loop.create_task(loop.create_connection(asyncio.Protocol, target_host, target_port))
        # Wait for either incoming or outgoing connection
        done, pending = await asyncio.wait(
            [incoming_fut, outgoing_task],
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )
        sock = None
        if incoming_fut in done and incoming_fut.done():
            transport = incoming_fut.result()
            sock = transport.get_extra_info('socket')
        elif outgoing_task in done and outgoing_task.done():
            transport, _ = outgoing_task.result()
            sock = transport.get_extra_info('socket')
        for task in pending:
            task.cancel()
        if sock:
            logger.info(f"TCP hole punch successful: {sock.getsockname()} <-> {sock.getpeername()}")
            return sock
        logger.warning("TCP hole punch failed after all retries")
        return None
    finally:
        server.close()
        await server.wait_closed()
async def tcp_hole_punch(local_host: str, local_port: int, target_host: str, target_port: int, timeout: float = 5.0) -> Optional[socket.socket]:
    """
    Attempt TCP hole punching by simultaneously listening and connecting.
    Returns the established socket if successful, else None.
    """
    loop = asyncio.get_event_loop()
    server = await asyncio.start_server(lambda r, w: None, local_host, local_port)
    server_addr = server.sockets[0].getsockname()
    connect_task = loop.create_task(loop.create_connection(lambda: asyncio.Protocol(), target_host, target_port))
    accept_task = loop.create_task(server.accept())
    done, pending = await asyncio.wait([connect_task, accept_task], timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
    sock = None
    for task in done:
        try:
            result = task.result()
            if isinstance(result, tuple) and hasattr(result[1], 'get_extra_info'):
                # Accepted connection
                sock = result[1].get_extra_info('socket')
            elif isinstance(result, tuple) and hasattr(result[0], 'get_extra_info'):
                # Outgoing connection
                sock = result[0].get_extra_info('socket')
        except Exception as e:
            logger.error(f"TCP hole punch error: {e}")
    for task in pending:
        task.cancel()
    server.close()
    await server.wait_closed()
    if sock:
        logger.info(f"TCP hole punch successful: {sock.getsockname()} <-> {sock.getpeername()}")
        return sock
    logger.warning("TCP hole punch failed after all retries")
    return None
"""
This module contains utilities for NAT traversal and hole punching.
"""
import socket
import asyncio
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

async def create_punch_socket(host: str, port: int = 0) -> Tuple[socket.socket, int]:
    """
    Create a socket for NAT traversal and bind it to the specified host and port.
    If port is 0, a random available port will be used.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    _, port = sock.getsockname()
    sock.setblocking(False)
    return sock, port

async def punch_hole(sock: socket.socket, target_host: str, target_port: int,
                    retries: int = 5, timeout: float = 1.0) -> bool:
    """
    Attempt to punch a hole through NAT by sending UDP packets to the target.
    """
    loop = asyncio.get_event_loop()
    
    for i in range(retries):
        try:
            # Send punch packet
            await loop.sock_sendto(sock, b'punch', (target_host, target_port))
            
            # Wait for response
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 1024),
                    timeout=timeout
                )
                if data == b'punch_ack':
                    logger.info(f"NAT hole punch successful with {addr}")
                    return True
            except asyncio.TimeoutError:
                logger.debug(f"Punch attempt {i+1}/{retries} timed out")
                continue
                
        except Exception as e:
            logger.error(f"Error during hole punch: {e}")
            continue
    
    logger.warning("NAT hole punch failed after all retries")
    return False

async def establish_p2p_connection(local_host: str, target_host: str, target_port: int) -> Optional[socket.socket]:
    """
    Establish a peer-to-peer connection using NAT hole punching.
    """
    try:
        # Create and bind socket
        sock, local_port = await create_punch_socket(local_host)
        logger.info(f"Created local socket on port {local_port}")

        # Attempt hole punching
        success = await punch_hole(sock, target_host, target_port)
        if success:
            return sock
        else:
            sock.close()
            return None

    except Exception as e:
        logger.error(f"Failed to establish P2P connection: {e}")
        return None
