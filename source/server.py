import logging
import os
import random
import socket
import string
import sys
import threading
import hashlib
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
AUTHORIZATION_CODE = 'authorization_code'
SEED = 'seed'
SEP = b'8===D<'
MESSAGE_END = b"###"
AUTHORIZATION_TOKEN = 'auth_token'


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


def generate_random_string(length: int):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


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
        print(seed)
        self._clients[client_id][SEED] = seed

    @protocol(b"XOR")
    def _do_xor(self, client_id, client, data):
        print("XOR")
        logger.debug(self._clients[client_id][SEED])
        pubkey, privkey = rsa.newkeys(2048)
        self._clients[client_id][RSA_PRIVATE_KEY] = privkey
        xorer = XORer(self._clients[client_id][SEED])
        decrypted = xorer.do_xor(data)
        print(decrypted)
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
        if succeed:
            raw_token = identifier + ':' + password
            token = hashlib.sha256(raw_token.encode()).hexdigest()
            self._clients[client_id][AUTHORIZATION_TOKEN] = token
            code = generate_random_string(128)
            msg = create_message(b"SRVR", b"LOGIN", {
                b"SUCCESS": succeed.to_bytes(succeed.bit_length(), 'big'),
                b"AUTHORIZATION_CODE": code.encode()
            })
            self._clients[client_id][AUTHORIZATION_CODE] = code
        else:
            msg = create_message(b"SRVR", b"LOGIN", {
                b"SUCCESS": succeed.to_bytes(succeed.bit_length(), 'big')
            })
        encrypted = rsa.encrypt(msg, clients_public_key) + MESSAGE_END
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
            raw_token = identifier + ':' + password
            token = hashlib.sha256(raw_token.encode()).hexdigest()
            self._clients[client_id][AUTHORIZATION_TOKEN] = token
            code = generate_random_string(128)
            self._clients[client_id][AUTHORIZATION_CODE] = code
            msg = create_message(b"SRVR", b"SIGNUP", {
                b"SUCCESS": True.to_bytes(True.bit_length(), 'big'),
                b"AUTHORIZATION_CODE": code.encode()
            })
            currtime = str(datetime.datetime.utcnow())
            self._mailer.mailto([email], "Don't reply (PlateGate)", "You signed up successfully at " + currtime)
        else:
            msg = create_message(b"SRVR", b"SIGNUP", {
                b"SUCCESS": False.to_bytes(False.bit_length(), 'big')
            })
        encrypted = rsa.encrypt(msg, client_public_key) + MESSAGE_END
        print(encrypted)
        client.send(encrypted)
        print("SIGNUP END")

    @protocol(b"USERINFO")
    def _user_info(self, client_id, client, data):
        print("USERINFO")
        try:
            client_public_key = self._clients[client_id][RSA_PUBLIC_KEY]
        except KeyError as error:
            logger.error(str(error))
            return
        parameters = extract_parameters(data)
        auth_code = self._clients[client_id][AUTHORIZATION_CODE]
        if auth_code != parameters['AUTHORIZATION_CODE'].decode():
            msg = create_message(b"SRVR", b"USERINFO", {
                b"SUCCESS": False.to_bytes(False.bit_length(), 'big'),
                b"REASON": b"UNAUTHORIZED"
            })
            encrypted = rsa.encrypt(msg, client_public_key)
            client.send(encrypted)
            print("INCORRECT AUTH CODE")
            return
        db = Database.PlateGateDB()
        user = db.get_user_by_id(parameters['IDENTIFIER'].decode())
        company_name, _ = db.get_company_by_user_id(parameters['IDENTIFIER'].decode())
        msg = create_message(b"SRVR", b"USERINFO", {
            b"SUCCESS": True.to_bytes(True.bit_length(), 'big'),
            b"IDENTIFIER": str(user['id_number']).encode(),
            b"FNAME": user['fname'].encode(),
            b"LNAME": user['lname'].encode(),
            b"COMPANY_NAME": company_name.encode(),
            b"EMAIL": user['email'].encode()
        })
        encrypted = rsa.encrypt(msg, client_public_key) + MESSAGE_END
        client.send(encrypted)
        self._clients[client_id].pop(AUTHORIZATION_CODE)

    @protocol(b"MAILMANAGER")
    def _mail_manager(self, client_id, client, data):
        print('Mail MANAGER')
        try:
            client_public_key = self._clients[client_id][RSA_PUBLIC_KEY]
            client_token = self._clients[client_id][AUTHORIZATION_TOKEN]
        except KeyError as error:
            logger.error(str(error))
            return
        parameters = extract_parameters(data)
        token = parameters['AUTH_TOKEN'].decode()
        if token != client_token:
            msg = create_message(b"SRVR", b"MAILMANAGER", {
                b"SUCCESS": False.to_bytes(False.bit_length(), 'big'),
                b"REASON": b"CLIENT TOKEN IS FAULTY"
            })
            encrypted = rsa.encrypt(msg, client_public_key) + MESSAGE_END
            client.send(encrypted)
            print('Faulty Token')
            return
        message = parameters['MESSAGE'].decode()
        client_id_number = parameters['IDENTIFIER']
        db = Database.PlateGateDB()
        _, client_company_id = db.get_company_by_user_id(client_id_number.decode())
        print(client_company_id)
        client_manager = db.get_manager_by_company_id(client_company_id)
        manager_email = db.get_email('users', client_manager)
        self._mailer.mailto([manager_email], f'Message from {client_id_number.decode()} (PlateGate)', message)
        msg = create_message(b"SRVR", b"MAILMANAGER", {
            b"SUCCESS": True.to_bytes(True.bit_length(), 'big')
        })
        encrypted = rsa.encrypt(msg, client_public_key) + MESSAGE_END
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
            print('closing client')
            client.close()
            self._client_count -= 1
            return

        self.KNOWN_REQUESTS[function](client_id, client, decrypted)
        client.close()
        try:
            auth_code = self._clients[client_id][AUTHORIZATION_CODE]
        except KeyError:
            self._clients[client_id] = {
                AUTHORIZATION_TOKEN: self._clients[client_id][AUTHORIZATION_TOKEN]
            }
        else:
            self._clients[client_id] = {
                AUTHORIZATION_TOKEN: self._clients[client_id][AUTHORIZATION_TOKEN],
                AUTHORIZATION_CODE: auth_code
            }
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
