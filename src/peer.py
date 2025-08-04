import asyncio
import json
from typing import Optional

class Peer:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.addr = writer.get_extra_info('peername')

    async def send(self, message: dict):
        """Send a message to the peer."""
        try:
            data = json.dumps(message).encode() + b'\n'
            self.writer.write(data)
            await self.writer.drain()
        except Exception as e:
            raise Exception(f"Failed to send message: {e}")

    async def receive(self) -> Optional[dict]:
        """Receive a message from the peer."""
        try:
            data = await self.reader.readline()
            if not data:
                return None
            return json.loads(data.decode())
        except Exception as e:
            raise Exception(f"Failed to receive message: {e}")

    async def close(self):
        """Close the peer connection."""
        if not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()
