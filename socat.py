#!/usr/bin/python3
import socket
import sys
import select

# ip = "192.168.11.32"
# port = 3001
# 
# rip = "localhost"
# rport = 22

named_pipe = None
try:
    ip = sys.argv[1]
    port = int(sys.argv[2])
    rip = sys.argv[3]
    rport = int(sys.argv[4])
    named_pipe = sys.argv[5]
except:
    print(f"[Error] Usage: socat.py ipsrc portsrc ipdst portdst")

addr = (ip, port)
raddr = (rip, rport)

print(f"redirecting traffic from: {addr} -> {raddr}")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


buffsize = 4096
s.bind(addr)
s.listen(1)
while True:
    rs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn, addr = s.accept()
    bconnected = False
    print(f"connection accepted from: {addr}")

    rs.connect(raddr)
    print(f"connected to {raddr}")
    bconnected = True
    while True:
        rlist, wlist, xlist = select.select([rs, conn], [], [])

        data = None
        for sock in rlist:
            data = sock.recv(buffsize)
            if sock == conn:
                if not data:
                    print(f"client has closed connection")
                    break
                rs.send(data)
                print(f"transfered {len(data)} bytes: {addr} -> {raddr}")
                if named_pipe:
                    with open(named_pipe, 'wb') as f:
                        f.write(data)
            else:
                if not data:
                    print(f"server has closed connection")
                    rs.close()
                    break
                conn.send(data)
                print(f"transfered {len(data)} bytes: {raddr} -> {addr}")
        if not data:
            break

