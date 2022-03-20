#!/usr/bin/python3

"""
This was created by Fair A.
on March 20, 2022 on MacBook.

Notes: select on fd does not work properly at least with named pipes.
named pipes are always ready even if data content is empty. So must
check size in addition

Commands that worked.
# creates socks5 proxy server
1) ssh -vvv -N -D 9000 fair@localhost
# creates socks5 proxy client for ssh
2) python3 talk2sock.py localhost 3001 localhost 9000 localhost 22 /tmp/pipe2 /tmp/pipe1
# use socks5 proxy client to talk to ssh server
3) ssh -vvv -p 3001 fair@localhost
"""
import socket
import sys
import select
import os
import subprocess

try:
    ip = sys.argv[1]
    port = int(sys.argv[2])
    socks5ip = sys.argv[3]
    socks5port = int(sys.argv[4])
    dest_ip = sys.argv[5]
    dest_port = int(sys.argv[6])
    read_pipe_fname = sys.argv[7]
    write_pipe_fname = sys.argv[8]
except:
    print(f"[Error] Usage: {sys.argv[0]} listen_ip listen_port socks5ip socks5port dest_ip dest_port read_pipe write_pipe")
    exit(1)

if not os.path.exists(read_pipe_fname):
    os.mkfifo(read_pipe_fname)
    os.system(f"chmod 777 {read_pipe_fname}")


if not os.path.exists(write_pipe_fname):
    os.mkfifo(write_pipe_fname)
    os.system(f"chmod 777 {write_pipe_fname}")


proxy_client_cmd = f"nc -X 5 -x {socks5ip}:{socks5port} {dest_ip} {dest_port} < {write_pipe_fname} > {read_pipe_fname} &"
#proxy_client_cmd = f"nc -X 5 -x {socks5ip}:{socks5port} {dest_ip} {dest_port}"

#sp = subprocess.Popen(proxy_client_cmd.split())
os.system(proxy_client_cmd)

addr = (ip, port)
print(f"redirecting traffic from: {addr} -> {read_pipe_fname}")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

buffsize = 4096
s.bind(addr)
s.listen(1)
read_pipe = os.open(read_pipe_fname, os.O_RDONLY | os.O_NONBLOCK)
#read_pipe = os.open(write_pipe_fname, os.O_RDONLY | os.O_NONBLOCK)
write_pipe = os.open(write_pipe_fname, os.O_WRONLY | os.O_NONBLOCK)
while True:
    conn, addr = s.accept()
    print(f"connection accepted from: {addr}")
    while True:
        rlist, wlist, xlist = select.select([read_pipe, conn], [], [])

        data = None
        for sock in rlist:
            if sock == conn:
                print(f"data is available on network!")
                data = sock.recv(buffsize)
                if not data:
                    print(f"client has closed connection")
                    break
                os.write(write_pipe, data)
                print(f"transfered {len(data)} bytes: {addr} -> {write_pipe_fname}")
            else:
                print(f"data is available on pipe!")
                try:
                    data = os.read(sock, buffsize)
                    if not data:
                        continue
                except BlockingIOError as e:
                    print(f"got blockingioerror, retrying...")
                    continue
                except Exception:
                    print(f"got exception")
                    continue
                if not data:
                    print(f"len(data): {len(data)}")
                    print(f"server has closed connection")
                conn.send(data)
                print(f"transfered {len(data)} bytes: {read_pipe_fname} -> {addr}")
        if not data:
            break

