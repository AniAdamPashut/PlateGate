import random


class XORer:
    def __init__(self, seed: bytes):
        self.random = random.Random(int.from_bytes(seed, 'big'))

    def do_xor(self, message):
        key = self.random.randbytes(len(message))
        return bytes(a ^ b for (a, b) in zip(key, message))
