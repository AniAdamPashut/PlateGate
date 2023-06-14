import Client

create_message = Client.create_message
extract_parameters = Client.extract_parameters


class User(Client.Client):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port, b"USER")

    def login(self, identifier: str, password: str) -> str:
        msg = create_message(self.type, b"LOGIN", {
            b"IDENTIFIER": identifier.encode(),
            b"PASSWORD": password.encode()
        })

        decrypted = self._send_and_recv_msg(msg, b"LOGIN")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            print('logged in')
            return parameters['AUTHORIZATION_CODE'].decode()
        return ''

    def signup(self,
               identifier: str,
               fname: str,
               lname: str,
               password: str,
               company_id: str,
               email: str) -> str:
        msg = create_message(self.type, b"SIGNUP", {
            b"IDENTIFIER": identifier.encode(),
            b"FNAME": fname.encode(),
            b"PASSWORD": password.encode(),
            b"LNAME": lname.encode(),
            b"COMPANY_ID": company_id.encode(),
            b"EMAIL": email.encode()
        })

        decrypted = self._send_and_recv_msg(msg, b'SIGNUP')

        parameters = extract_parameters(decrypted)
        try:
            if parameters['SUCCESS']:
                print('signed up')
                return parameters['AUTHORIZATION_CODE'].decode()
            print("didnt signed up")
            return ''
        except KeyError:
            return ''

    def get_user_info(self, auth_code: str, identifier: str):
        msg = create_message(b"USER", b"USERINFO", {
            b"AUTHORIZATION_CODE": auth_code.encode(),
            b"IDENTIFIER": identifier.encode()
        })

        decrypted = self._send_and_recv_msg(msg, b"USERINFO")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return parameters
        return parameters

    def mail_manager(self,
                     identifier: str,
                     token: str,
                     message: str) -> bool:
        msg = create_message(b"USER", b"MAILMANAGER", {
            b"AUTH_TOKEN": token.encode(),
            b"IDENTIFIER": identifier.encode(),
            b"MESSAGE": message.encode()
        })

        decrypted = self._send_and_recv_msg(msg, b"MAILMANAGER")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return True
        return False

    def delete_user(self, manager_id: str, token: str, identifier: str):
        msg = create_message(b"USER", b"DELETE", {
            b"AUTH_TOKEN": token.encode(),
            b"IDENTIFIER": identifier.encode(),
            b"MANAGER_ID": manager_id.encode()
        })
        decrypted = self._send_and_recv_msg(msg, b"DELETE")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return True
        return parameters['REASON'].decode()

    def update_user(self,
                    manager_id: str,
                    token: str,
                    identifier: str,
                    entries_dict: dict[str, str]):
        msg_dict = {
            b"AUTH_TOKEN": token.encode(),
            b"IDENTIFIER": identifier.encode(),
            b"MANAGER_ID": manager_id.encode()
        }
        for name, entry in entries_dict.items():
            if entry:
                msg_dict[name.upper().encode()] = entry.encode()

        msg = create_message(b"USER", b"UPDATE", msg_dict)
        decrypted = self._send_and_recv_msg(msg, b"UPDATE")
        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return True
        return False

    def add_plate(self,
                  manager_id,
                  plate_number,
                  user_id):
        msg = create_message(self.type, b"ADDPLATE", {
            b"MANAGER_ID": manager_id.encode(),
            b"PLATE_NUMBER": plate_number.encode(),
            b"USER_ID": user_id.encode()
        })
        decrypted = self._send_and_recv_msg(msg, b"ADDPLATE")
        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return True
        else:
            return parameters['REASON']

    def add_company(self,
                    company_name: str,
                    identifier: str,
                    fname: str,
                    lname: str,
                    password: str,
                    email: str) -> int | str:
        msg = create_message(self.type, b"ADDCOMPANY", {
            b"IDENTIFIER": identifier.encode(),
            b"FNAME": fname.encode(),
            b"LNAME": lname.encode(),
            b"PASSWORD": password.encode(),
            b"EMAIL": email.encode(),
            b"COMPANY_NAME": company_name.encode()
        })

        decrypted = self._send_and_recv_msg(msg, b"ADDCOMPANY")

        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return int.from_bytes(parameters['COMPANY_ID'], 'big')
        return parameters['REASON'].decode()

    def remove_plate(self, manager_id, plate_number, user_id):
        msg = create_message(self.type, b"REMOVEPLATE", {
            b"MANAGER_ID": manager_id.encode(),
            b"PLATE_NUMBER": plate_number.encode(),
            b"USER_ID": user_id.encode()
        })
        decrypted = self._send_and_recv_msg(msg, b"REMOVEPLATE")
        parameters = extract_parameters(decrypted)
        if parameters['SUCCESS']:
            return True
        else:
            return parameters['REASON']

    def get_entries(self, manager_id: str):
        msg = create_message(self.type, b"GETENTRIES", {
            b"MANAGER_ID": manager_id.encode()
        })
        decrypted = self._send_and_recv_msg(msg, b"GETENTRIES")
        parameters = extract_parameters(decrypted)
        if not parameters['SUCCESS']:
            return parameters['REASON']
