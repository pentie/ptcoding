#!/usr/bin/env python

import socket
import sys
import threading
import pdb as _pdb

def begin(addr = 'localhost', port = 8964):
    def __output(conn):
        while True:
            data = conn.recv(1024)
            if not data:break
            sys.stdout.write(data)
            sys.stdout.flush()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((addr, port))
    sock.listen(1)

    while True:
        conn, addr = sock.accept()
        print "connect from %s" % str(addr)

        threading.Thread(target = __output, args = (conn,)).start()
        
        try:
            while 1:
                i = sys.stdin.readline()
                conn.sendall(i)
        except socket.error:
            print "Connect close."
        finally:
            conn.close()

def pdb(addr = 'localhost', port = 8964):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((addr, port))

    return _pdb.Pdb(stdin = sock.makefile('r+', 0), stdout = sock.makefile('w+', 0))


