import logging
import os
import socket
import sys
import threading
import hashlib
import time

import rsa
import Database
import Mailing
import dotenv
import datetime
from XORer import XORer
from diffiehellman import DiffieHellman

CONFIG = dotenv.dotenv_values('.env')

logging.basicConfig(filename='serverlogs.log',
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
SEP = b'8===D<'
MESSAGE_END = b"###"


def extract_parameters(data: bytes) -> dict[str, bytes]:
    request_parameters = {}
    for parameter in data.split(b"~~~"):
        if SEP in parameter:
            parameter = parameter.split(SEP)
            name, value = parameter
            request_parameters[name.decode()] = value
    return request_parameters


def create_message(sender: bytes, method: bytes, parameters: dict):
    message = sender + b" " + method + b"~~~"
    for key in parameters:
        message += key + SEP + parameters[key] + b"~~~"
    message += MESSAGE_END
    return message


class Server:
    CLIENT_LIMIT = 100
    PORT = 1337
    KNOWN_CLIENTS = [b"USER", b"CMRA"]
    KNOWN_REQUESTS = {}

    def __init__(self):
        self._client_count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sys.platform[:5] == 'linux':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            # This code is brought to you by
            # https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use
        self._sock = sock
        self._clients = {}
        mailer = Mailing.Mailer('smtp.gmail.com', False)
        mailer.enter_credentials(CONFIG['MAIL_ADDR'], CONFIG['MAIL_PASS'])
        self._mailer = mailer

        for method in dir(self):
            f = getattr(self, method)
            if callable(f) and getattr(f, 'registered', False):
                self.KNOWN_REQUESTS[getattr(f, 'name')] = f

    @protocol(b"DIFFIE")
    def _do_diffie(self, client_id, client, data):
        print("Diffie-Hellman")
        dh = DiffieHellman(group=2)
        public_key = dh.get_public_key()

        request_parameters = extract_parameters(data)

        msg = create_message(b"SRVR", b"DIFFIE", {
            b"PUBLIC": public_key
        })
        client.send(msg)
        seed = dh.generate_shared_key(request_parameters['PUBLIC'])
        self._clients[client_id][SEED] = seed

    @protocol(b"XOR")
    def _do_xor(self, client_id, client, data):
        print("XOR")
        logger.debug(self._clients[client_id][SEED])
        pubkey, privkey = rsa.newkeys(2048)
        self._clients[client_id][RSA_PRIVATE_KEY] = privkey
        xorer = XORer(self._clients[client_id][SEED])
        decrypted = xorer.do_xor(data)
        request_parameters = extract_parameters(decrypted)
        n = int.from_bytes(request_parameters['NVALUE'], 'big')
        e = int.from_bytes(request_parameters['EVALUE'], 'big')
        client_public_key = rsa.PublicKey(n, e)
        try:
            rsa.verify(request_parameters['MESSAGE'], request_parameters['SIGNATURE'], client_public_key)
        except rsa.pkcs1.VerificationError:
            logger.error("Very bad")
        rand_message = os.urandom(128)
        signature = rsa.sign(rand_message, privkey, 'SHA-256')
        msg = create_message(b"SRVR", b"XOR", {
            b"NVALUE": pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big'),
            b"EVALUE": pubkey.e.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big'),
            b"MESSAGE": rand_message,
            b"SIGNATURE": signature
        })
        encrypted_message = xorer.do_xor(msg) + MESSAGE_END
        client.send(encrypted_message)
        self._clients[client_id][RSA_PUBLIC_KEY] = client_public_key

    @protocol(b"LOGIN")
    def _login(self, client_id, client, data):
        try:
            clients_public_key = self._clients[client_id][RSA_PUBLIC_KEY]
        except KeyError as error:
            logger.error(str(error))
            raise

        parameters = extract_parameters(data)
        db = Database.PlateGateDB()
        identifier = parameters['IDENTIFIER'].decode()
        password = parameters['PASSWORD'].decode()
        salt = db.select_salt('users', identifier)
        hashed_passowrd = hashlib.sha256((password + salt).encode()).hexdigest()
        db_hashed_password = db.get_hashed_password('users', identifier)
        succeed = hashed_passowrd == db_hashed_password
        msg = create_message(b"SRVR", b"LOGIN", {
            b"SUCCESS": succeed.to_bytes(succeed.bit_length(), 'big')
        })
        encrypted = rsa.encrypt(msg, clients_public_key)
        client.send(encrypted)

    @protocol(b"SIGNUP")
    def _signup(self, client_id, client, data):
        print("SIGNUP")
        try:
            client_public_key = self._clients[client_id][RSA_PUBLIC_KEY]
        except KeyError as error:
            logger.error(str(error))
            return
        parameters = extract_parameters(data)
        identifier = parameters['IDENTIFIER'].decode()
        fname = parameters['FNAME'].decode()
        lname = parameters['LNAME'].decode()
        password = parameters['PASSWORD'].decode()
        company_id = parameters['COMPANY_ID'].decode()
        email = parameters['EMAIL'].decode()
        db = Database.PlateGateDB()
        if db.insert_into('users',
                          id_number=identifier,
                          fname=fname,
                          lname=lname,
                          password=password,
                          company_id=company_id,
                          email=email,
                          user_state=1):
            print('inserted')
            msg = create_message(b"SRVR", b"SIGNUP", {
                b"SUCCESS": True.to_bytes(True.bit_length(), 'big')
            })
            currtime = str(datetime.datetime.utcnow())
            self._mailer.mailto([email], "Don't reply", "You signed up successfully at " + currtime)
        else:
            print('not inserted')
            msg = create_message(b"SRVR", b"SIGNUP", {
                b"SUCCESS": False.to_bytes(False.bit_length(), 'big')
            })
        encrypted = rsa.encrypt(msg, client_public_key)
        client.send(encrypted)

    def _handle_client(self, client, addr):
        client_id = hashlib.sha256(str(addr[0]).encode()).hexdigest()
        if client_id not in self._clients.keys():
            self._clients[client_id] = {}
        data = client.recv(1024)
        while not data[-len(MESSAGE_END):] == MESSAGE_END:
            data += client.recv(1024)

        data = data[:-len(MESSAGE_END)]

        decrypted = None

        try:
            decrypted = rsa.decrypt(data, self._clients[client_id][RSA_PRIVATE_KEY])
            print(decrypted)
        except KeyError:
            if SEED not in self._clients[client_id]:
                self._do_diffie(client_id, client, data)
            else:
                self._do_xor(client_id, client, data)
            return
        except rsa.pkcs1.DecryptionError as error:
            decrypted = data
            raise

        if not decrypted[:4] in self.KNOWN_CLIENTS:
            client.close()
            self._client_count -= 1
            return

        function = decrypted.split(b"~~~")[0].split(b" ")[1]
        print(function)
        if function not in self.KNOWN_REQUESTS.keys():
            client.close()
            self._client_count -= 1
            return

        self.KNOWN_REQUESTS[function](client_id, client, decrypted)
        client.close()
        self._client_count -= 1

    def mainloop(self):
        self._sock.bind(('0.0.0.0', self.PORT))
        self._sock.listen()
        threads = []
        while self._client_count <= self.CLIENT_LIMIT:
            print('Waiting')
            client, addr = self._sock.accept()
            thread = threading.Thread(target=self._handle_client, args=(client, addr,))
            threads.append(thread)
            thread.start()
            self._client_count += 1

        for thread in threads:
            thread.join()

        self._sock.close()


server = Server()
server.mainloop()
