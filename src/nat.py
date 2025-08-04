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
