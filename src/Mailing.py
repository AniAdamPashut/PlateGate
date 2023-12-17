from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText


class Mailer:
    def __init__(self, host: str, debuglevel: int, port: int = 465):
        self._host = host
        self._debuglevel = debuglevel
        self._port = port
        self._user = None
        self._password = None
        self._conn = None

    def enter_credentials(self, usr: str, passw: str):
        self._user = usr
        self._password = passw

    def _login(self):
        self._conn.login(self._user, self._password)

    def _open_server(self):
        conn = SMTP(self._host, self._port)
        conn.set_debuglevel(self._debuglevel)
        self._conn = conn
        self._login()

    def _close_server(self):
        self._conn.quit()

    def mailto(self, dest: list[str], subject: str, body: str):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self._user

        self._open_server()
        try:
            self._conn.sendmail(self._user, dest, msg.as_string())
        except Exception as err:
            print(str(err))
        finally:
            self._close_server()
