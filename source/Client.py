import os
import socket
import time
import rsa
from XORer import XORer
from diffiehellman import DiffieHellman


SEP = b"8=D"


class Client:
    def __init__(self, ip: str, port: int):
        self._ip = ip
        self._port = port
        self._seed = None
        self._do_diffie()
        self._do_xor()

    def _do_diffie(self):
        dh = DiffieHellman(group=2)
        public_key = dh.get_public_key()
        milon = dict()
        with socket.create_connection((self._ip, self._port)) as sock:
            msg = b"USER DIFFIE~~~"
            msg += b"PUBLIC" + SEP + public_key
            msg += b"~~~###"
            sock.send(msg)
            data = sock.recv(1024)
            while not data[-3:] == b"###":
                data += sock.recv(1024)

            for value in data.split(b"~~~"):
                if SEP in value:
                    value = value.split(SEP)
                    milon[value[0].decode()] = value[1]

        shared = dh.generate_shared_key(milon['PUBLIC'])
        self._seed = shared

    def _do_xor(self):
        pubkey, privkey = rsa.newkeys(2048)
        self._private_key = privkey
        milon = dict()
        rand_message = os.urandom(128)
        first_msg = b"USER XOR~~~###"
        msg = b"USER XOR~~~"
        msg += b"NVALUE" + SEP + pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big') + b"~~~"
        msg += b"EVALUE" + SEP + pubkey.e.to_bytes((pubkey.e.bit_length() + 7) // 8, 'big') + b"~~~"
        msg += b"MESSAGE" + SEP + rand_message + b"~~~"
        signature = rsa.sign(rand_message, privkey, 'SHA-256')
        msg += b"SIGNATURE" + SEP + signature + b"~~~"
        msg += b"LENGTH" + SEP + str(len(msg) + 20).encode() + b"~~~"
        msg += b"###"
        xorer = XORer(self._seed)
        encrypted_message = xorer.do_xor(msg) + b"###"
        with socket.create_connection((self._ip, self._port)) as sock:
            sock.send(first_msg)
            time.sleep(0.5)
            sock.send(encrypted_message)

            data = sock.recv(1024)


moshe = Client('127.0.0.1', 1337)

