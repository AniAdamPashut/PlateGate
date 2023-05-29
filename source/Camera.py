import Client
import cv2
from typing import Any


class Camera(Client.Client):
    def __init__(self, ip: str, port: int, company_id: int):
        super().__init__(ip, port, b"CMRA")
        self._company_id = company_id

    def recognize(self, image: Any):
        filename = 'moshe.jpg'
        cv2.imwrite(filename, image)
        with open(filename, 'rb') as f:
            image_bytes = f.read()
        message = Client.create_message(self.type, b"RECOGNIZE", {
            b"IMAGE": image_bytes,
            b"COMPANY_ID": self._company_id.to_bytes(self._company_id.bit_length(), 'big')
        })
        response = self._send_and_recv_msg(message, b"RECOGNIZE")
        parameters = Client.extract_parameters(response)
        if parameters.get('SUCCESS', False):
            print("open thy gate")  # this will work someday
            return True
        print(parameters['REASON'])
        return False


if __name__ == '__main__':
    cmra = Camera('127.0.0.1', 1337, 900164)
    print(cmra.recognize(cv2.imread('pego.jpg')))

