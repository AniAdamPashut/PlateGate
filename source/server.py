import os
import socket
import threading
import hashlib
import rsa
import logging
from XORer import XORer
from diffiehellman import DiffieHellman


logging.basicConfig(filename='serverlogs.logs',
                    format='%(asctime)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)


def protocol(name):
    def inner(method):
        setattr(method, 'registered', True)
        setattr(method, 'name', name)
        return method
    return inner


RSA_PUBLIC_KEY = 'rsa_public_key'
RSA_PRIVATE_KEY = 'rsa_private_key'
SEED = 'seed'
SEP = b'8=D'


class Server:
    CLIENT_LIMIT = 100
    PORT = 1337
    KNOWN_CLIENTS = [b"USER", b"CMRA"]
    KNOWN_REQUESTS = {}

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # This code is brought to you by
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use
        self._sock = sock
        self._clients = {}

        for method in dir(self):
            f = getattr(self, method)
            if callable(f) and getattr(f, 'registered', False):
                self.KNOWN_REQUESTS[getattr(f, 'name')] = f

    @protocol(b"DIFFIE")
    def _do_diffie(self, client_id, client, data):
        print("Diffie-Hellman")
        dh = DiffieHellman(group=2)
        public_key = dh.get_public_key()

        milon = dict()
        for value in data.split(b"~~~"):
            if b"!!!" in value:
                value = value.split(b"!!!")
                milon[value[0].decode()] = value[1]

        msg = b"SRVR DIFFIE~~~"
        msg += b"PUBLIC" + SEP + public_key
        msg += b"~~~###"
        client.send(msg)
        seed = dh.generate_shared_key(milon['PUBLIC'])
        self._clients[client_id][SEED] = seed

    @protocol(b"XOR")
    def _do_xor(self, client_id, client, data):
        print("XOR")
        logger.debug(self._clients[client_id][SEED])
        pubkey, privkey = rsa.newkeys(2048)
        self._clients[client_id][RSA_PRIVATE_KEY] = privkey
        milon = dict()
        xorer = XORer(self._clients[client_id][SEED])
        data = client.recv(1024)
        while not data[-3:] == b"###":
            data += client.recv(1024)
        data = data[:-3]
        decrypted = xorer.do_xor(data)
        print(decrypted)
        for value in decrypted.split(b"~~~"):
            if SEP in value:
                value = value.split(SEP)
                milon[value[0].decode()] = value[1]

        print(milon)
        rand_message = os.urandom(128)
        msg = b"USER XOR~~~"
        msg += b"NVALUE" + SEP + pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big') + b"~~~"
        msg += b"EVALUE" + SEP + pubkey.e.to_bytes((pubkey.e.bit_length() + 7) // 8, 'big') + b"~~~"
        msg += b"MESSAGE" + SEP + rand_message + b"~~~"
        signature = rsa.sign(rand_message, privkey, 'SHA-256')
        msg += b"SIGNATURE" + SEP + signature + b"~~~"
        msg += b"LENGTH" + SEP + str(len(msg) + 20).encode() + b"~~~"
        msg += b"###"
        encrypted_message = xorer.do_xor(msg) + b"###"

    def _handle_client(self, client, addr):
        print(addr)
        client_id = hashlib.sha256(str(addr[0]).encode()).hexdigest()
        if client_id not in self._clients.keys():
            self._clients[client_id] = {}
        data = client.recv(1024)
        while not data[-3:] == b"###":
            data += client.recv(1024)

        if not data[:4] in self.KNOWN_CLIENTS:
            return

        splt = data.split(b"~~~")[0].split(b" ")
        if splt[1] not in self.KNOWN_REQUESTS.keys():
            return

        self.KNOWN_REQUESTS[splt[1]](client_id, client, data)
        client.close()
        self._clients -= 1

    def mainloop(self):
        self._sock.bind(('0.0.0.0', self.PORT))
        self._sock.listen()
        threads = []
        clients = 0
        while clients <= self.CLIENT_LIMIT:
            print('Waiting')
            client, addr = self._sock.accept()
            thread = threading.Thread(target=self._handle_client, args=(client, addr,))
            threads.append(thread)
            thread.start()
            clients += 1

        for thread in threads:
            thread.join()

        self._sock.close()


server = Server()
server.mainloop()


