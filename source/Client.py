import os
import socket
import rsa
import logging
from XORer import XORer
from diffiehellman import DiffieHellman


SEP = b"8===D<"
MESSAGE_END = b"###"


logging.basicConfig(filename='clientlog.log',
                    format='%(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)


def extract_parameters(data: bytes) -> dict[str, bytes]:
    request_parameters = {}
    for parameter in data.split(b"~~~"):
        if SEP in parameter:
            parameter = parameter.split(SEP)
            if len(parameter) > 2:
                return
            name, value = parameter
            request_parameters[name.decode()] = value
    return request_parameters


def create_message(sender: bytes, method: bytes, parameters: dict) -> bytes:
    message = sender + b" " + method + b"~~~"
    for key in parameters:
        message += key + SEP + parameters[key] + b"~~~"
    message += MESSAGE_END
    return message


class Client:
    def __init__(self, ip: str, port: int, type: bytes):
        self.type = type
        self._ip = ip
        self._port = port
        self._seed = None
        self._server_public_key = None
        self._do_handshake()

    def _do_handshake(self):
        self._do_diffie()
        self._do_xor()

    def _do_diffie(self):
        logger.info("Diffie Started")
        dh = DiffieHellman(group=2)
        public_key = dh.get_public_key()
        with socket.create_connection((self._ip, self._port)) as sock:
            msg = create_message(self.type,
                                  b"DIFFIE",
                                 {b"PUBLIC": public_key})
            sock.send(msg)
            data = sock.recv(1024)
            while not data[-len(MESSAGE_END):] == MESSAGE_END:
                data += sock.recv(1024)

            request_parameters = extract_parameters(data)

        shared = dh.generate_shared_key(request_parameters['PUBLIC'])
        logging.info(shared)
        self._seed = shared
        logger.info("Diffie finished")

    def _do_xor(self):
        logger.info("Xor started")
        pubkey, privkey = rsa.newkeys(2048)
        self._private_key = privkey
        rand_message = os.urandom(128)
        signature = rsa.sign(rand_message, privkey, 'SHA-256')
        msg = create_message(self.type, b"XOR", {
            b"NVALUE": pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big'),
            b"EVALUE": pubkey.e.to_bytes((pubkey.e.bit_length() + 7) // 8, 'big'),
            b"MESSAGE": rand_message,
            b"SIGNATURE": signature,
        })
        xorer = XORer(self._seed)
        encrypted_message = xorer.do_xor(msg) + MESSAGE_END
        with socket.create_connection((self._ip, self._port)) as sock:
            sock.send(encrypted_message)
            data = sock.recv(1024)
            while not data[-len(MESSAGE_END):] == MESSAGE_END:
                data += sock.recv(1024)
            data = data[:-len(MESSAGE_END)]
            decrypted = xorer.do_xor(data)
            request_parameters = extract_parameters(decrypted)

        n = int.from_bytes(request_parameters['NVALUE'], 'big')
        e = int.from_bytes(request_parameters['EVALUE'], 'big')
        server_public_key = rsa.PublicKey(n, e)
        self._server_public_key = server_public_key
        try:
            rsa.verify(request_parameters['MESSAGE'], request_parameters['SIGNATURE'], server_public_key)
        except rsa.pkcs1.VerificationError:
            logging.error("Something went wrong, reconnecting...")
            self._do_handshake()
        finally:
            logger.info("Xor Ended")

    def login(self, identifier: str, password: str):
        logger.info("LOGIN STARTED")
        msg = create_message(self.type, b"LOGIN", {
            b"IDENTIFIER": identifier.encode(),
            b"PASSWORD": password.encode()
        })
        with socket.create_connection((self._ip, self._port)) as sock:
            encrypted = rsa.encrypt(msg, self._server_public_key) + MESSAGE_END
            sock.send(encrypted)
            data = sock.recv(1024)
            try:
                decryted = rsa.decrypt(data, self._private_key)
            except rsa.pkcs1.DecryptionError:
                logging.error("How did we got here?")
        parameters = extract_parameters(decryted)
        if parameters['SUCCESS']:
            print('logged in')

    def signup(self,
               identifier: str,
               fname: str,
               lname: str,
               password: str,
               company_id: str,
               email: str):
        logger.info("LOGIN STARTED")
        msg = create_message(self.type, b"SIGNUP", {
            b"IDENTIFIER": identifier.encode(),
            b"FNAME": fname.encode(),
            b"PASSWORD": password.encode(),
            b"LNAME": lname.encode(),
            b"COMPANY_ID": company_id.encode(),
            b"EMAIL": email.encode()
        })
        logger.info(msg)
        with socket.create_connection((self._ip, self._port)) as sock:
            encrypted = rsa.encrypt(msg, self._server_public_key) + MESSAGE_END
            sock.send(encrypted)
            data = sock.recv(1024)
            try:
                decrypted = rsa.decrypt(data, self._private_key)
            except rsa.pkcs1.DecryptionError:
                logging.error("How did we got here?")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            print('signed up')


moshe = Client('127.0.0.1', 1337, b"USER")
moshe.signup('330816042',
             'Eyal',
             'Squeak',
             'eyal123',
             '900164',
             'hidataman2024@gmail.com')
