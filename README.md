# P2P Network Application

A peer-to-peer networking application implemented in Python that supports NAT hole punching for both TCP and UDP connections.

## Features

- NAT hole punching for TCP and UDP
- Peer discovery and connection management
- Asynchronous networking operations
- Command-line interface for easy interaction

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application as a server:
```bash
python -m src.main --mode server --port 8000
```

Run as a client:
```bash
python -m src.main --mode client --server-host localhost --server-port 8000
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## License

MIT License
