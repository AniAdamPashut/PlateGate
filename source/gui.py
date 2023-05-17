import hashlib
import tkinter
import Client
import validator
from tkinter import messagebox


client = Client.User('127.0.0.1', 1337)


def protocol(name):
    def inner(method):
        setattr(method, 'registered', True)
        setattr(method, 'name', name)
        return method

    return inner


def main():
    window = MainWindow('PlateGate')
    window.mainloop()


class MainWindow(tkinter.Tk):
    def __init__(self, window_title: str):
        super().__init__()
        self.title(window_title)
        self.geometry("1200x600")
        self._logged = False
        self._identifier = None
        self._password = None
        self._login_frame = LoginFrame(self)
        self._login_frame.pack(side='left', padx=70, pady=20)
        self._signup_frame = SignUpFrame(self)
        self._signup_frame.pack(side='right', padx=70, pady=20)
        self._logged_in_frame = None

    def log_in_user(self, identifier, auth_code, password):
        self._password = password
        self._identifier = identifier
        self._logged = True
        details = client.get_user_info(auth_code, identifier)
        if not details['SUCCESS']:
            messagebox.showerror('User wan\'nt logged', details['REASON'].decode())
            return False
        details.pop('SUCCESS')
        self._login_frame.destroy()
        self._signup_frame.destroy()
        if int.from_bytes(details['STATE'], 'big') > 1:
            self._logged_in_frame = AdminLoggedFrame(self, details)
        else:
            self._logged_in_frame = LoggedInFrame(self, details)
        self._logged_in_frame.pack()
        return True

    def log_out_user(self):
        self._logged_in_frame.destroy()
        self._login_frame = LoginFrame(self)
        self._signup_frame = SignUpFrame(self)
        self._login_frame.pack(side='left', padx=70, pady=20)
        self._signup_frame.pack(side='right', padx=70, pady=20)

    @property
    def identifier(self):
        return self._identifier

    @property
    def password(self):
        return self._password

    @property
    def token(self):
        raw = self.identifier + ':' + self.password
        return hashlib.sha256(raw.encode()).hexdigest()


class LoggedInFrame(tkinter.Frame):
    def __init__(self, master, user_details: dict[str, bytes]):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.header = tkinter.Label(self)
        self.header.config(text='Details:')
        self.header.grid(sticky='n', row=0, column=1)
        self._labels = []
        index = 1
        for key in user_details:
            lbl = tkinter.Label(self)
            lbl['text'] = f'{key}: {user_details[key].decode()}'
            lbl.grid(sticky='n', row=index, column=1)
            self._labels.append(lbl)
            index += 1
        self.button = SubmitButton(self, 'logout')
        self.button.grid(row=index, column=1, sticky='n')
        self.update_label = tkinter.Label(self)
        self.update_label['text'] = 'Want to update your information?\nMail your manager'
        self.update_label.grid(row=0, column=0)
        self.mail_entry = CustomEntry(self, 'message', 2)
        self.update_button = SubmitButton(self, 'mail_manager')
        self.update_button.grid(row=4, column=0)


class AdminLoggedFrame(tkinter.Frame):
    def __init__(self, master, user_details: dict[str, bytes]):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.header = tkinter.Label(self)
        self.header.config(text='Details:')
        self.header.grid(sticky='n', row=0, column=1)
        self._labels = []
        index = 1
        for key in user_details:
            if key == 'STATE':
                continue
            lbl = tkinter.Label(self)
            lbl['text'] = f'{key}: {user_details[key].decode()}'
            lbl.grid(sticky='n', row=index, column=1)
            self._labels.append(lbl)
            index += 1
        self.button = SubmitButton(self, 'logout')
        self.button.grid(row=index, column=1, sticky='n')
        self.update_label = tkinter.Label(self)
        self.update_label['text'] = 'Want to update a worker details?\nEnter his id number:'
        self.update_label.grid(row=0, column=0)
        self.id_number = CustomEntry(self, 'identifier', 2)
        self._update_button = SubmitButton(self, 'update')
        self._update_button.grid(row=3, column=0)


class ChangeDetailsWindow(tkinter.Toplevel):
    details = ['fname', 'lname', 'email']

    def __init__(self, identifier, manager_id, token):
        super().__init__()
        self.token = token
        self._identifier = identifier
        self.manager_id = manager_id
        self._frame = tkinter.Frame(self)
        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_columnconfigure(2, weight=1)
        self._label = tkinter.Label(self._frame)
        self._label['text'] = f'Identifier: {identifier}'
        self._label.grid(row=0, sticky='n')
        self.delete_button = SubmitButton(self._frame, 'delete_user')
        self.submit_button = SubmitButton(self._frame, 'commit')
        self.detail_entries = []
        index = 2
        for detail in self.details:
            entry = CustomEntry(self._frame, detail, index)
            entry.grid(sticky='n', row=index, column=1)
            self.detail_entries.append(entry)
            index += 1
        self.delete_button.grid(row=index, column=0)
        self.submit_button.grid(row=index+1, column=0)
        self._frame.pack()

    @property
    def identifier(self):
        return self._identifier


class LoginFrame(tkinter.Frame):
    def __init__(self, master):
        super().__init__(master, relief='solid', borderwidth=2)
        self.button = SubmitButton(self, 'login')
        self.identifier = CustomEntry(self, 'identifier', 1)
        self.password = CustomEntry(self, 'password', 3)
        self.button.grid(row=4)


class SignUpFrame(tkinter.Frame):
    def __init__(self, master):
        master_height = master.winfo_height() // 2
        master_width = master.winfo_width() // 2
        super().__init__(master, relief='solid', borderwidth=2, width=master_width, height=master_height)
        self.button = SubmitButton(self, 'signup')
        self.identifier = CustomEntry(self, 'identifier', 1)
        self.first_name = CustomEntry(self, 'fname', 3)
        self.last_name = CustomEntry(self, 'lname', 5)
        self.password = CustomEntry(self, 'password', 7)
        self.company_id = CustomEntry(self, 'company_id', 9)
        self.email = CustomEntry(self, 'email', 11)
        self.button.grid(row=12)


class CustomEntry(tkinter.Entry):
    def __init__(self, master, name: str, grid_row: int):
        super().__init__(master)
        self.config(width=30)
        self.label = tkinter.Label(master)
        self.label.config(text=name)
        self.grid(row=grid_row)
        self.label.grid(row=grid_row-1)
        self.name = name
        if name == 'password':
            self.config(show='\u2022')


class SubmitButton(tkinter.Button):
    KNOWN_TYPES = ['signup', 'login', 'logout', 'mail_manager', 'update', 'commit', 'delete_user']
    KNOWN_REQUESTS = {}

    def __init__(self, master, type: str):
        super().__init__(master, text=type, command=self._on_click)
        self.master = master
        if type not in self.KNOWN_TYPES:
            raise ValueError("Wrong type given in class constructor")
        self._type = type

        for method in dir(self):
            f = getattr(self, method)
            if callable(f) and getattr(f, 'registered', False):
                self.KNOWN_REQUESTS[getattr(f, 'name')] = f

    @protocol('login')
    def _login(self, entries_dict):
        try:
            if not validator.validate_id(entries_dict['identifier']):
                messagebox.showerror('error', 'id is incorrect')
                return
        except ValueError as error:
            messagebox.showerror('error', str(error))
            return
        try:
            logged = client.login(identifier=entries_dict['identifier'],
                                  password=entries_dict['password'], )
        except KeyError:
            return
        else:
            if not logged:
                messagebox.showerror('error logging in',
                                     'something went wrong. '
                                     'if you id is correct '
                                     'try retyping the password')
            else:
                window = self.winfo_toplevel()
                if not isinstance(window, MainWindow):
                    return
                success = window.log_in_user(entries_dict['identifier'], logged, entries_dict['password'])
                if not success:
                    return
                messagebox.showinfo('logged-in',
                                    'you logged in successfully. you may close this window.')

    @protocol('signup')
    def _signup(self, entries_dict):
        try:
            if not validator.validate_id(entries_dict['identifier']):
                messagebox.showerror('error', 'id is incorrect')
                return
            if not (validator.validate_name(entries_dict['fname']) and validator.validate_name(entries_dict['lname'])):
                messagebox.showerror('error', 'first or last names are illegal')
                return
            if not validator.validate_email(entries_dict['email']):
                messagebox.showerror('error', 'email is illegal')
                return
        except ValueError as error:
            messagebox.showerror('error', str(error))
            return
        try:
            signed = client.signup(identifier=entries_dict['identifier'],
                                   fname=entries_dict['fname'],
                                   lname=entries_dict['lname'],
                                   password=entries_dict['password'],
                                   company_id=entries_dict['company_id'],
                                   email=entries_dict['email'])
        except KeyError:
            return
        else:
            if not signed:
                messagebox.showerror('error signing up',
                                     'something went wrong. '
                                     'try again later or validate your data with your manager.')
            else:
                window: MainWindow = self.winfo_toplevel()
                messagebox.showinfo('signed-up',
                                    'you signed up successfully. you may close this window.')
                window.log_in_user(entries_dict['identifier'], signed, entries_dict['password'])

    @protocol('logout')
    def _logout(self, *_):
        window = self.winfo_toplevel()
        window.log_out_user()

    @protocol('mail_manager')
    def _mail_manager(self, entries_dict):
        window = self.winfo_toplevel()
        if not isinstance(window, MainWindow):
            return
        try:
            result = client.mail_manager(window.identifier, window.password, entries_dict['message'])
        except KeyError:
            return
        else:
            if result:
                messagebox.showinfo('Message Sent!', 'The message has been sent to your manager')
            else:
                messagebox.showerror('Message was not sent', '')

    @protocol('update')
    def _show_update(self, entries_dict):
        window = self.winfo_toplevel()
        if not isinstance(window, MainWindow):
            return
        tpl = ChangeDetailsWindow(entries_dict['identifier'], window.identifier, window.token)
        tpl.mainloop()

    @protocol('delete_user')
    def _delete_user(self, *_):
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, ChangeDetailsWindow):
            return
        identifier = tpl.identifier
        token = tpl.token
        success = client.delete_user(token, identifier)
        if success:
            messagebox.showinfo('Deleted!',
                                f'You deleted client {identifier}')
        else:
            messagebox.showerror('Client wasn\'t deleted', '')
        tpl.destroy()

    @protocol('commit')
    def _commit_to_db(self, entries_dict):
        print('committing')
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, ChangeDetailsWindow):
            return
        identifier = tpl.identifier
        token = tpl.token
        success = client.update_user(tpl.manager_id, token, identifier, entries_dict)
        if success:
            messagebox.showinfo('Changes Committed!',
                                f'You changed client {identifier}')
        else:
            messagebox.showerror('Changes were\'t committed', '')
        tpl.destroy()

    def _on_click(self):
        entries = [entry for entry in self.master.winfo_children() if isinstance(entry, CustomEntry)]
        entries_dict = {entry.name: entry.get() for entry in entries}
        window = self.winfo_toplevel()
        print(self._type)
        if not (isinstance(window, MainWindow) or isinstance(window, ChangeDetailsWindow)):
            return
        print('starting function')
        if self._type == 'update':
            entries_dict['manager_id'] = window.identifier
            entries_dict['token'] = window.token

        self.KNOWN_REQUESTS[self._type](entries_dict)


if __name__ == '__main__':
    main()
