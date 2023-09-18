import os
import socket
import rsa
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


SEP = b"8===D<"
MESSAGE_END = b"###"
MESSAGE_HALF = b"!==!"


def extract_parameters(data: bytes) -> dict[str, bytes]:
    request_parameters = {}
    for parameter in data.split(b"~~~"):
        if SEP in parameter:
            parameter = parameter.split(SEP)
            name, value = parameter
            request_parameters[base64.b64decode(name).decode()] = base64.b64decode(value)
    return request_parameters


def create_message(sender: bytes, method: bytes, parameters: dict[bytes, bytes]):
    message = sender + b" " + method + b"~~~"
    for key, value in parameters.items():
        message += base64.b64encode(key) + SEP + base64.b64encode(value) + b"~~~"
    message += MESSAGE_END
    return message


class Client:
    def __init__(self, ip: str, port: int, client_type: bytes):
        self.type = client_type
        self._ip = ip
        self._port = port
        self._server_public_key = None
        self._private_key = None
        self._do_handshake()

    def _do_handshake(self):
        logger.info("Xor started")
        pubkey, privkey = rsa.newkeys(1024)
        self._private_key = privkey
        rand_message = os.urandom(16)
        signature = rsa.sign(rand_message, privkey, 'SHA-256')
        msg = create_message(self.type, b"XOR", {
            b"NVALUE": pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, 'big'),
            b"EVALUE": pubkey.e.to_bytes((pubkey.e.bit_length() + 7) // 8, 'big'),
            b"MESSAGE": rand_message,
            b"SIGNATURE": signature,
        })
        with socket.create_connection((self._ip, self._port)) as sock:
            print(msg)
            sock.send(msg)
            data = sock.recv(1024)
            while not data[-len(MESSAGE_END):] == MESSAGE_END:
                data += sock.recv(1024)
            data = data[:-len(MESSAGE_END)]
            request_parameters = extract_parameters(data)
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

    def _send_and_recv_msg(self, msg, method):
        print(msg)
        aes_key = os.urandom(16)
        iv = os.urandom(16)
        aes_object = Cipher(algorithms.AES(aes_key), mode=modes.CBC(iv))
        aes_info = create_message(self.type, method, {
            b"AES_KEY": aes_key,
            b"IVECTOR": iv
        })
        encrypted_info = rsa.encrypt(aes_info, self._server_public_key)
        encryptor = aes_object.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_msg = padder.update(msg) + padder.finalize()
        encrypted_data = encryptor.update(padded_msg) + encryptor.finalize()
        encrypted = encrypted_info + MESSAGE_HALF + encrypted_data + MESSAGE_END
        with socket.create_connection((self._ip, self._port)) as sock:
            sock.send(encrypted)
            data = self.get_all_data(sock)

            if not (MESSAGE_HALF in data):
                return data

        return self.decrypt_message(data)

    @staticmethod
    def get_all_data(sock):
        data = sock.recv(1024)
        while not data.endswith(MESSAGE_END):
            data += sock.recv(1024)
        data = data[:-len(MESSAGE_END)]
        return data

    def decrypt_message(self, data: bytes):
        info, content = data.split(MESSAGE_HALF)
        decrypted_info = rsa.decrypt(info, self._private_key)
        parameters = extract_parameters(decrypted_info)

        aes_key = parameters['AES_KEY']
        iv = parameters['IVECTOR']
        unpadder = padding.PKCS7(128).unpadder()
        aes = Cipher(algorithms.AES(aes_key), mode=modes.CBC(iv))
        decryptor = aes.decryptor()
        decrypted = decryptor.update(content) + decryptor.finalize()
        decrypted = unpadder.update(decrypted) + unpadder.finalize()

        return decrypted
