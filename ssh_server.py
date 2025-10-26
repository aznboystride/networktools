#!/usr/bin/env python3

"""
Simple SSH Server implementation using Paramiko
This server provides basic SSH functionality including authentication and shell access.
"""

import socket
import sys
import threading
import paramiko
import os
import subprocess
import pty
import select
import termios
import struct
import fcntl


class SSHServer(paramiko.ServerInterface):
    """SSH Server Interface handling authentication and channel requests"""

    def __init__(self, username="user", password="password"):
        self.event = threading.Event()
        self.username = username
        self.password = password

    def check_channel_request(self, kind, chanid):
        """Check if a channel request is allowed"""
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        """Authenticate using password"""
        if username == self.username and password == self.password:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """Authenticate using public key (allow any key for demo)"""
        if username == self.username:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        """Return allowed authentication methods"""
        return "password,publickey"

    def check_channel_shell_request(self, channel):
        """Allow shell requests"""
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height,
                                   pixelwidth, pixelheight, modes):
        """Allow PTY requests"""
        return True

    def check_channel_exec_request(self, channel, command):
        """Allow command execution"""
        self.event.set()
        return True


def handle_client(client_sock, addr, host_key, username, password):
    """Handle individual SSH client connection"""
    print(f"[+] Connection from {addr}")

    try:
        # Create SSH transport
        transport = paramiko.Transport(client_sock)
        transport.add_server_key(host_key)

        # Start SSH server
        server = SSHServer(username=username, password=password)
        transport.start_server(server=server)

        # Wait for authentication
        channel = transport.accept(20)
        if channel is None:
            print(f"[-] No channel for {addr}")
            return

        print(f"[+] Authenticated connection from {addr}")
        server.event.wait(10)

        if not server.event.is_set():
            print(f"[-] Client never asked for a shell for {addr}")
            return

        # Handle shell session
        try:
            # Create PTY for shell
            master, slave = pty.openpty()

            # Start shell process
            shell = subprocess.Popen(
                ["/bin/bash"],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                preexec_fn=os.setsid
            )

            print(f"[+] Shell started for {addr}")

            # Set non-blocking mode
            fcntl.fcntl(master, fcntl.F_SETFL, os.O_NONBLOCK)

            # Main I/O loop
            while True:
                # Check if channel is still active
                if channel.closed or not transport.is_active():
                    break

                # Use select for efficient I/O multiplexing
                r, w, e = select.select([channel, master], [], [], 0.1)

                # Handle data from SSH client
                if channel in r:
                    try:
                        data = channel.recv(1024)
                        if len(data) == 0:
                            break
                        os.write(master, data)
                    except Exception as e:
                        print(f"[!] Error reading from channel: {e}")
                        break

                # Handle data from shell
                if master in r:
                    try:
                        data = os.read(master, 1024)
                        if len(data) == 0:
                            break
                        channel.send(data)
                    except OSError:
                        # No data available
                        pass
                    except Exception as e:
                        print(f"[!] Error reading from master: {e}")
                        break

                # Check if shell process has exited
                if shell.poll() is not None:
                    break

            # Cleanup
            shell.terminate()
            shell.wait()
            os.close(master)
            os.close(slave)

        except Exception as e:
            print(f"[!] Error in shell handling: {e}")

        channel.close()

    except Exception as e:
        print(f"[!] Exception: {e}")
    finally:
        try:
            transport.close()
        except:
            pass
        client_sock.close()
        print(f"[-] Connection closed from {addr}")


def generate_or_load_host_key(key_path="ssh_host_rsa_key"):
    """Generate or load SSH host key"""
    if os.path.exists(key_path):
        print(f"[+] Loading host key from {key_path}")
        return paramiko.RSAKey(filename=key_path)
    else:
        print(f"[+] Generating new host key...")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(key_path)
        print(f"[+] Host key saved to {key_path}")
        return key


def main():
    """Main SSH server function"""
    # Parse command line arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <bind_ip> <bind_port> [username] [password]")
        print(f"Example: {sys.argv[0]} 0.0.0.0 2222 user password")
        sys.exit(1)

    bind_ip = sys.argv[1]
    bind_port = int(sys.argv[2])
    username = sys.argv[3] if len(sys.argv) > 3 else "user"
    password = sys.argv[4] if len(sys.argv) > 4 else "password"

    # Generate or load host key
    host_key = generate_or_load_host_key()

    # Create server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((bind_ip, bind_port))
    server_sock.listen(100)

    print(f"[+] SSH Server listening on {bind_ip}:{bind_port}")
    print(f"[+] Authentication: username='{username}', password='{password}'")
    print(f"[+] Waiting for connections...")

    try:
        while True:
            client_sock, addr = server_sock.accept()

            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_sock, addr, host_key, username, password)
            )
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
