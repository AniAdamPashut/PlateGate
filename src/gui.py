import hashlib
import tkinter
import User
import validator
from tkinter import messagebox


client = User.User('127.0.0.1', 1337)


def button_press_type(name):
    def inner(method):
        setattr(method, 'registered', True)
        setattr(method, 'name', name)
        return method

    return inner


def main():
    window = MainWindow('PlateGate')
    window.mainloop()


class MainWindow(tkinter.Tk):
    """
    The Main window of the gui application
    When logged in holds the identifier - id number - of the logged in user
    Also holds the token of the user
    """
    def __init__(self, window_title: str):
        super().__init__()
        self.title(window_title)
        self.geometry("1200x600")
        self._label = tkinter.Label(self, text='PlateGate', font=('Ariel', 30))
        self._label.pack(anchor='n')
        self._label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)
        self._logged = False
        self._identifier = None
        self._password = None
        self._add_plate_frame = None
        self._login_frame = LoginFrame(self)
        self._login_frame.pack(side='left', padx=70, pady=20)
        self._signup_frame = SignUpFrame(self)
        self._signup_frame.pack(side='right', padx=70, pady=20)
        self._logged_in_frame = None
        self._button = SubmitButton(self, 'open company')
        self._button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    def log_in_user(self, identifier, auth_code, password):
        """
        Logs in the user
        :param identifier: The id number of the user
        :param auth_code: Auth code retrieved from the user.login or user.signup methods
        :param password: The password of the user
        :return: True if the log in was success
        """
        self._password = password
        self._identifier = identifier
        self._logged = True
        details = client.get_user_info(auth_code, identifier)
        if not details['SUCCESS']:
            messagebox.askokcancel('User wan\'nt logged', details['REASON'].decode())
            return False
        details.pop('SUCCESS')
        state = details.pop('STATE')
        self._login_frame.destroy()
        self._signup_frame.destroy()
        self._label.destroy()
        if int.from_bytes(state, 'big') > 1:
            self._logged_in_frame = AdminLoggedFrame(self, details, identifier, self.token)
            self._logged_in_frame.pack(anchor='center', padx=70, pady=20)
        else:
            details.pop('COMPANY_ID')
            self._logged_in_frame = LoggedInFrame(self, details)
            self._logged_in_frame.pack(anchor='center', padx=70, pady=20)
        self._button.place_forget()
        return True

    def log_out_user(self):
        """
        Logs a user out of the system
        """
        self._logged_in_frame.destroy()
        self._add_plate_frame.destroy()
        self._login_frame = LoginFrame(self)
        self._signup_frame = SignUpFrame(self)
        self._login_frame.pack(side='left', padx=70, pady=20)
        self._signup_frame.pack(side='right', padx=70, pady=20)
        self._button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        self._label = tkinter.Label(self, text='PlateGate', font=('Ariel', 30))
        self._label.pack(anchor='n')

    @property
    def identifier(self):
        return self._identifier

    @property
    def token(self):
        raw = self.identifier + ':' + self._password
        return hashlib.sha256(raw.encode()).hexdigest()


"""
----------------------------------------------------------------------------------------
Top level windows
----------------------------------------------------------------------------------------
"""


class AddCompanyWindow(tkinter.Toplevel):
    """
    A window to add companies to the system
    """
    entries = ['fname', 'lname', 'identifier', 'email', 'password', 'company_name']

    def __init__(self):
        super().__init__()
        frame = tkinter.Frame(self)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        index = 1
        custom_entries = []
        for entry in self.entries:
            cstm_entry = CustomEntry(frame, entry, index)
            custom_entries.append(cstm_entry)
            index += 2
        self._frame = frame
        self._custom_entries = custom_entries
        self._submit = SubmitButton(self._frame, 'add company')
        self._submit.grid(row=index)
        self._frame.pack()


class ChangeDetailsWindow(tkinter.Toplevel):
    """
    A window to change users details (admin only)
    """
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
            self.detail_entries.append(entry)
            index += 2
        self.delete_button.grid(row=index, column=0)
        self.submit_button.grid(row=index+1, column=0)
        self._frame.pack()

    @property
    def identifier(self):
        return self._identifier


class ViewEntries(tkinter.Toplevel):
    key_to_column = {
        'ENTRY_ID': 0,
        'TIME': 1,
        'PERSON_ID': 2,
        'PERSON_NAME': 3,
        'PLATE_NUMBER': 4,
        'COMPANY_NAME': 5
    }

    def __init__(self, entry_values: list[dict[str, bytes]]):
        super().__init__()
        curr_row = 0
        for key, value in self.key_to_column.items():
            lbl = tkinter.Label(self, text=key)
            lbl.grid(row=curr_row, column=value)
        curr_row += 1
        for entry in entry_values:
            for key, value in entry.items():
                lbl = tkinter.Label(self, text=value.decode())
                try:
                    lbl.grid(row=curr_row, column=self.key_to_column[key])
                except KeyError:
                    pass
            curr_row += 1

"""
------------------------------------------------------------------------------
Frames start here
------------------------------------------------------------------------------
"""


class AdminLoggedFrame(tkinter.Frame):
    """
    The frame for logged admins
    """
    def __init__(self, master, user_details: dict[str, bytes], identifier, token):
        super().__init__(master)
        self._add_plate_frame = AddPlate(self, identifier, token)
        self._add_plate_frame.grid(row=1, column=2)
        self._label = tkinter.Label(self, text='Manager Interface', font=('Ariel', 30))
        self._label.grid(row=0, column=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.header = tkinter.Label(self)
        self.header.config(text='Details:')
        self.header.grid(sticky='n', row=1, column=1)
        self._labels = []
        index = 3
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
        self.update_label.grid(row=4, column=0)
        self.id_number = CustomEntry(self, 'identifier', 6)
        self._update_button = SubmitButton(self, 'update')
        self._update_button.grid(row=7, column=0)
        self._view_entries = SubmitButton(self, 'get entries')
        self._view_entries.grid(row=0, column=3)


class LoggedInFrame(tkinter.Frame):
    """
    The frame for logged users (not managers)
    """
    def __init__(self, master, user_details: dict[str, bytes]):
        super().__init__(master)
        self._label = tkinter.Label(self, text='User Interface', font=('Ariel', 30))
        self._label.grid(row=0, column=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.header = tkinter.Label(self)
        self.header.config(text='Details:')
        self.header.grid(sticky='n', row=3, column=1)
        self._labels = []
        index = 4
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
        self.update_label.grid(row=3, column=0)
        self.mail_entry = CustomEntry(self, 'message', 2)
        self.update_button = SubmitButton(self, 'mail_manager')
        self.update_button.grid(row=4, column=0)


class AddPlate(tkinter.Frame):
    """
    A frame to add/remove plates to the system (admin only)
    """
    def __init__(self, master, identifer, token):
        super().__init__(master, relief='solid', borderwidth=2)
        self.label = tkinter.Label(self, text='Add a license plate')
        self.label.grid(row=0)
        self.identifer = CustomEntry(self, 'worker_id', 2)
        self.plate_number = CustomEntry(self, 'plate_number', 4)
        self.button = SubmitButton(self, 'add plate')
        self.delete_button = SubmitButton(self, 'remove plate')
        self.button.grid(row=5)
        self.delete_button.grid(row=6)
        self.master_id = identifer
        self.token = token


class LoginFrame(tkinter.Frame):
    """
    A frame that enables users to log in to the system
    """
    def __init__(self, master):
        super().__init__(master, relief='solid', borderwidth=2)
        self._label = tkinter.Label(self, text='Login', font=('Ariel', 15))
        self._label.grid(row=0)
        self.button = SubmitButton(self, 'login')
        self.identifier = CustomEntry(self, 'identifier', 2)
        self.password = CustomEntry(self, 'password', 4)
        self.button.grid(row=5)


class SignUpFrame(tkinter.Frame):
    """
    A frame that enables the users to sign in to the system with a company id
    """
    def __init__(self, master):
        master_height = master.winfo_height() // 2
        master_width = master.winfo_width() // 2
        super().__init__(master, relief='solid', borderwidth=2, width=master_width, height=master_height)
        self._label = tkinter.Label(self, text='Signup', font=('Ariel', 15))
        self._label.grid(row=0)
        self.button = SubmitButton(self, 'signup')
        self.identifier = CustomEntry(self, 'identifier', 2)
        self.first_name = CustomEntry(self, 'fname', 4)
        self.last_name = CustomEntry(self, 'lname', 6)
        self.password = CustomEntry(self, 'password', 8)
        self.company_id = CustomEntry(self, 'company_id', 10)
        self.email = CustomEntry(self, 'email', 12)
        self.button.grid(row=13)


class CustomEntry(tkinter.Entry):
    """
    Custom tkinter.Entry class to make stuff easier
    """
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
    """
    An extension of the tkinter.Button class. To handle buttons and their commands
    """
    KNOWN_TYPES = ['signup',
                   'login',
                   'logout',
                   'mail_manager',
                   'update',
                   'commit',
                   'delete_user',
                   'add plate',
                   'remove plate',
                   'open company',
                   'add company',
                   'get entries']
    KNOWN_REQUESTS = {}

    def __init__(self, master, button_type: str):
        super().__init__(master, text=button_type, command=self._on_click)
        self.master = master
        if button_type not in self.KNOWN_TYPES:
            raise ValueError("Wrong type given in class constructor")
        self._type = button_type

        for method in dir(self):
            f = getattr(self, method)
            if callable(f) and getattr(f, 'registered', False):
                self.KNOWN_REQUESTS[getattr(f, 'name')] = f

    @button_press_type('login')
    def _login(self, entries_dict):
        """
        command to handle the press of the login button
        :param entries_dict: A dictionary with all the entries in the parent frame
        :return: None
        """
        try:
            if not validator.validate_id(entries_dict['identifier']):
                messagebox.askokcancel('error', 'id is incorrect')
                return
        except ValueError as error:
            messagebox.askokcancel('error', str(error))
            return
        try:
            logged = client.login(identifier=entries_dict['identifier'],
                                  password=entries_dict['password'], )
        except KeyError:
            return
        else:
            if not logged:
                messagebox.askokcancel('error logging in',
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
                messagebox.askokcancel('logged-in',
                                       'you logged in successfully. you may close this window.')

    @button_press_type('signup')
    def _signup(self, entries_dict):
        """
        A function that handles the press on the signup button
        :param entries_dict: The entries of the parent frame
        :return: None
        """
        try:
            if not validator.validate_id(entries_dict['identifier']):
                messagebox.askokcancel('error', 'id is incorrect')
                return
            if not (validator.validate_name(entries_dict['fname']) and validator.validate_name(entries_dict['lname'])):
                messagebox.askokcancel('error', 'first or last names are illegal')
                return
            if not validator.validate_email(entries_dict['email']):
                messagebox.askokcancel('error', 'email is illegal')
                return
            if not validator.validate_password(entries_dict['password']):
                messagebox.askokcancel('error', 'password is illegal')
                return
        except ValueError as error:
            messagebox.askokcancel('error', str(error))
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
                messagebox.askokcancel('error signing up',
                                     'something went wrong. '
                                     'try again later or validate your data with your manager.')
            else:
                window: MainWindow = self.winfo_toplevel()
                messagebox.askokcancel('signed-up',
                                    'you signed up successfully. you may close this window.')
                window.log_in_user(entries_dict['identifier'], signed, entries_dict['password'])

    @button_press_type('logout')
    def _logout(self, *_):
        """
        A function that handles the press of the logout button
        :param _: Discarding all parameters given
        :return: None
        """
        window = self.winfo_toplevel()
        if not isinstance(window, MainWindow):
            return
        window.log_out_user()

    @button_press_type('mail_manager')
    def _mail_manager(self, entries_dict):
        window = self.winfo_toplevel()
        if not isinstance(window, MainWindow):
            return
        try:
            result = client.mail_manager(window.identifier, window.token, entries_dict['message'])
        except KeyError:
            return
        else:
            if result:
                messagebox.askokcancel('Message Sent!', 'The message has been sent to your manager')
            else:
                messagebox.askokcancel('Message was not sent', '')

    @button_press_type('update')
    def _show_update(self, entries_dict):
        """
        A functions that handles the press of the update button. Open a new window to insert parameters
        :param entries_dict: The entries in the frame
        :return: None
        """
        window = self.winfo_toplevel()
        if not isinstance(window, MainWindow):
            return
        tpl = ChangeDetailsWindow(entries_dict['identifier'], window.identifier, window.token)
        tpl.mainloop()

    @button_press_type('delete_user')
    def _delete_user(self, *_):
        """
        A function to handle the press of the delete button.
        :param _: Discarding all parameters given
        :return: None
        """
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, ChangeDetailsWindow):
            return
        identifier = tpl.identifier
        token = tpl.token
        success = client.delete_user(tpl.manager_id, token, identifier)
        if success:
            messagebox.askokcancel('Deleted!',
                                   f'You deleted client {identifier}')
        else:
            messagebox.askokcancel('Client wasn\'t deleted', '')
        tpl.destroy()

    @button_press_type('commit')
    def _commit_to_db(self, entries_dict):
        """
        A function that handles the press of the commit button. Commits changes in db with the server
        :param entries_dict: The entries in the parent frame
        :return: None
        """
        print('committing')
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, ChangeDetailsWindow):
            return
        identifier = tpl.identifier
        token = tpl.token
        success = client.update_user(tpl.manager_id, token, identifier, entries_dict)
        if success:
            messagebox.askokcancel('Changes Committed!',
                                  f'You changed client {identifier}')
        else:
            messagebox.askokcancel('Changes were\'t committed', '')
        tpl.destroy()

    @button_press_type('add plate')
    def _add_plate(self, entries_dict):
        """
        A function that handles the press of the add plate button.
        :param entries_dict: The entries from parent frame
        :return: None
        """
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, MainWindow):
            return
        manager_id = tpl.identifier
        plate_number = entries_dict['plate_number']
        user_id = entries_dict['worker_id']
        resposne = client.add_plate(manager_id,
                                    plate_number,
                                    user_id)
        if resposne is True:
            messagebox.askokcancel('plate added', 'Plate number added successfully')
        else:
            messagebox.askokcancel('plate not added', resposne)

    @button_press_type('open company')
    def _open_company_window(self, *_):
        """
        A function that handles the press of the open company button. Opens a new window to insert comapny properties
        :param _: Discarding all parameters
        :return: None
        """
        tpl = AddCompanyWindow()
        tpl.mainloop()

    @button_press_type('add company')
    def _add_company(self, entries):
        """
        A function that handles the press of the add company button. Send requests to server with parameters from the window
        :param entries: The entries from the parent frame
        :return: None
        """
        try:
            if not validator.validate_id(entries['identifier']):
                messagebox.askokcancel('error', 'id is incorrect')
                return
            if not (validator.validate_name(entries['fname']) and validator.validate_name(entries['lname'])):
                messagebox.askokcancel('error', 'first or last names are illegal')
                return
            if not validator.validate_email(entries['email']):
                messagebox.askokcancel('error', 'email is illegal')
                return
            if not validator.validate_password(entries['password']):
                messagebox.askokcancel('error', 'password is illegal')
                return
        except ValueError as error:
            messagebox.askokcancel('error', str(error))
            return
        tpl = self.winfo_toplevel()
        reason = client.add_company(
            entries['company_name'],
            entries['identifier'],
            entries['fname'],
            entries['lname'],
            entries['password'],
            entries['email']
        )
        if isinstance(reason, str):
            messagebox.askokcancel('ERROR', reason)

        else:
            messagebox.askokcancel('Success',
                                   'Company was added successfully, log in to see your manager page'
                                   '\nThe Company id is ' + str(reason))

        tpl.destroy()

    @button_press_type('remove plate')
    def _remove_plate(self, entries):
        """
        A function that handles the remove plate button. Sends a request to the server with parameters to removing
        the plate
        :param entries: All the entries from the parent frame
        :return: None
        """
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, MainWindow):
            return
        manager_id = tpl.identifier
        plate_number = entries['plate_number']
        user_id = entries['worker_id']
        resposne = client.remove_plate(manager_id,
                                       plate_number,
                                       user_id)
        if resposne is True:
            messagebox.askokcancel('plate removed', 'Vehicle removed successfully')
        else:
            messagebox.askokcancel('plate not remove', resposne)

    @button_press_type('get entries')
    def _get_entries(self, *_):
        tpl = self.winfo_toplevel()
        if not isinstance(tpl, MainWindow):
            return
        manager_id = tpl.identifier
        entries = client.get_entries(str(manager_id))
        entries_view = ViewEntries(entries)
        entries_view.mainloop()

    def _on_click(self):
        """
        The command of all the buttons. Finds the entries from the parent frame and the function of the button and
        sends it to the correct function
        :return: None
        """
        entries = [entry for entry in self.master.winfo_children() if isinstance(entry, CustomEntry)]
        entries_dict = {entry.name: entry.get() for entry in entries}
        window = self.winfo_toplevel()
        print(self._type)
        print('starting function')
        if self._type == 'update':
            entries_dict['manager_id'] = window.identifier
            entries_dict['token'] = window.token

        self.KNOWN_REQUESTS[self._type](entries_dict)


if __name__ == '__main__':
    main()
