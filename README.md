# networktools
network hack tools like relay and stuff using low level sockets

## Tools

### SSH Server (ssh_server.py)
A simple SSH server implementation using Python3 and Paramiko.

**Features:**
- Password and public key authentication
- Interactive shell access
- PTY support for proper terminal handling
- Multi-client support via threading
- Automatic host key generation

**Installation:**
```bash
pip3 install -r requirements.txt
```

**Usage:**
```bash
python3 ssh_server.py <bind_ip> <bind_port> [username] [password]
```

**Example:**
```bash
# Start SSH server on port 2222
python3 ssh_server.py 0.0.0.0 2222 admin secretpass

# Connect from client
ssh -p 2222 admin@localhost
```

**Default credentials:**
- Username: user
- Password: password

### Socket Relay (socat.py)
TCP socket relay that redirects traffic from one address to another.

**Usage:**
```bash
python3 socat.py <src_ip> <src_port> <dst_ip> <dst_port>
```

### SOCKS5 Proxy Client (talk2sock.py)
SOCKS5 proxy client using named pipes for communication.

**Usage:**
```bash
python3 talk2sock.py <listen_ip> <listen_port> <socks5_ip> <socks5_port> <dest_ip> <dest_port> <read_pipe> <write_pipe>
```
