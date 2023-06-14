import random
import mysql.connector
import string
import hashlib
import source.validator as validator


class PlateGateDB:
    def __init__(self):
        self._conn = None
        self._cur = None
        self._hostname = 'localhost'
        self._username = 'root'
        self._passwd = ''
        self._db_name = 'PlateGateDB'

    def _open(self):
        self._conn = mysql.connector.connect(
            host=self._hostname,
            user=self._username,
            password=self._passwd,
            database=self._db_name
        )
        self._cur = self._conn.cursor(dictionary=True)

    def _close(self):
        self._cur.close()
        self._conn.close()

    def select_all(self, table_name: str):
        self._open()
        self._cur.execute(f"SELECT * FROM {table_name};")
        val = self._cur.fetchall()
        self._close()
        return val

    def select_salt(self, id_number: str):
        self._open()
        self._cur.execute(f"SELECT salt FROM users WHERE id_number='{id_number}';")
        val = self._cur.fetchone()
        self._close()
        return val['salt']

    def get_hashed_password(self, table_name, id_number: str) -> str:
        self._open()
        self._cur.execute(f"SELECT password FROM {table_name} WHERE id_number='{id_number}';")
        val = self._cur.fetchone()
        self._close()
        return val['password']

    def get_user_by_id(self, id_number: str) -> dict[str, str]:
        self._open()
        self._cur.execute(f"SELECT * FROM users WHERE id_number='{id_number}'")
        val = self._cur.fetchone()
        self._close()
        return val

    def get_manager_by_company_id(self, company_id):
        self._open()
        self._cur.execute(f"SELECT manager_id FROM companies WHERE company_id='{company_id}'")
        val = self._cur.fetchone()
        self._close()
        return val['manager_id']

    def get_company_by_manager_id(self, manager_id) -> int:
        self._open()
        self._cur.execute(f"SELECT company_id FROM companies WHERE manager_id={manager_id}")
        val = self._cur.fetchone()
        self._close()
        return val['company_id']

    def get_manager_email_by_company_id(self, company_id):
        self._open()
        self._cur.execute(f"SELECT * FROM companies WHERE company_id='{company_id}'")
        val = self._cur.fetchone()
        self._close()
        return self.get_email(val['manager_id'])

    def get_company_by_user_id(self, id_number: str) -> tuple:
        self._open()
        self._cur.execute(f"SELECT company_id FROM users WHERE id_number='{id_number}'")
        val = self._cur.fetchone()
        company_id = val['company_id']
        self._cur.execute(f"SELECT company_name FROM companies WHERE company_id='{company_id}'")
        name = self._cur.fetchone()['company_name']
        self._close()
        return name, company_id

    def get_email(self,id_number: str) -> str:
        self._open()
        self._cur.execute(f"SELECT email FROM users WHERE id_number='{id_number}'")
        val = self._cur.fetchone()
        self._close()
        return val['email']

    @staticmethod
    def _generate_salt():
        return ''.join(random.choice(string.ascii_letters) for _ in range(20))

    @staticmethod
    def _hash_password(password: str, salt: str):
        return hashlib.sha256(str(password + salt).encode()).hexdigest()

    @staticmethod
    def _validate_params_user(kwargs):
        try:
            kwargs['id_number']
            kwargs['fname']
            kwargs['lname']
            kwargs['password']
        except KeyError:
            raise KeyError("You must insert id_number, first and last names, and the password")
        finally:
            return kwargs

    @staticmethod
    def _validate_values(kwargs):
        if not validator.validate_id(kwargs['id_number']):
            raise ValueError("Id is not valid")
        if not validator.validate_name(kwargs['fname']) or not validator.validate_name(kwargs['lname']):
            raise ValueError("User First or Last name are not valid")
        return kwargs

    @staticmethod
    def _figure_user_state(kwargs: dict):
        if kwargs.get('user_state', 0) > 1:
            return kwargs
        try:
            kwargs['company_id']
        except KeyError:
            kwargs['user_state'] = 0
        else:
            kwargs['user_state'] = 1
        return kwargs

    def _generate_company_id(self):
        company_id = random.randint(100_000, 1_000_000)
        is_exists = self.get_company_by_id(company_id)
        while is_exists:
            company_id = random.randint(100_000, 1_000_000)
            is_exists = self.get_company_by_id(company_id)
        return company_id

    def _configure_users_parameters(self, kwargs):
        kwargs = self._validate_params_user(kwargs)
        kwargs = self._validate_values(kwargs)
        kwargs = self._figure_user_state(kwargs)
        return kwargs

    def _insert_new_user(self, kwargs):
        kwargs = self._configure_users_parameters(kwargs)
        salt = self._generate_salt()
        hashed = self._hash_password(kwargs['password'], salt)
        kwargs['password'] = hashed
        kwargs['salt'] = salt
        return kwargs

    def _insert_new_car(self, **kwargs):
        try:
            kwargs['owner_id']
            kwargs['plate_number']
        except KeyError:
            raise KeyError("You must insert the owner's id number and the plate number")
        user = self.get_user_by_id(kwargs['owner_id'])
        if not user:
            raise ValueError("User id_number doesn't exist, Please add the user first")
        return kwargs

    def _insert_new_company(self, **kwargs):
        try:
            kwargs['manager_id']
            kwargs['company_name']
        except KeyError:
            raise KeyError("Please insert both manager_id and or company_name")
        else:
            company_id = self._generate_company_id()
            kwargs['company_id'] = company_id
            self.update('users', id_number=kwargs['manager_id'], user_state=2)
        finally:
            return kwargs

    def _insert_kwargs(self, table_name, kwargs):
        columns = ','.join(f"{col}" for col in kwargs)
        values = ','.join(f"%s" for _ in kwargs)
        query = f"INSERT INTO {table_name} (" \
                f"{columns}" \
                f") VALUES (" \
                f"{values}" \
                f");"
        self._open()
        inserted = False
        print(query)
        try:
            self._cur.execute(query, tuple(kwargs.values()))
            self._conn.commit()
        except Exception as err:
            print(str(err))
            raise err
        else:
            print("Insert was committed successfully")
            inserted = True
        finally:
            self._close()
            return inserted

    def insert_into(self, table_name: str, **kwargs) -> bool:
        """
        The insert function

        :param table_name: the name of the modified table

        :param kwargs: key, value pairs of column and value

        :return: True if the insert query passed False if not
        """
        print(kwargs)
        if table_name == 'users':
            kwargs = self._insert_new_user(kwargs)
        elif table_name == 'vehicles':
            kwargs = self._insert_new_car(**kwargs)
        elif table_name == 'companies':
            kwargs = self._insert_new_company(**kwargs)
        elif table_name == 'entries':
            kwargs = self._extract_entries_kwargs(**kwargs)
        else:
            return False

        return self._insert_kwargs(table_name, kwargs)

    def update(self, table_name: str, **kwargs):
        print(kwargs)
        key = next(iter(kwargs))
        value = kwargs.pop(key)
        query = f"UPDATE {table_name} SET "
        if 'password' in kwargs.keys():
            salt = self.select_salt(key)
            hashed = hashlib.sha256((kwargs['password'] + salt).encode()).hexdigest()
            kwargs['password'] = hashed
        for col in kwargs.keys():
            query += f"{col}=%s,"
        query = query[:-1] + " "
        query += f"WHERE {key}={value};"
        print(query % tuple(kwargs.values()))
        updated = False
        try:
            self._open()
            self._cur.execute(query, tuple(kwargs.values()))
            self._conn.commit()
        except Exception as err:
            print(str(err))
            raise err
        else:
            updated = True
        finally:
            self._close()
            return updated

    def remove_user(self, pk_key: str):
        return self.update('users', id_number=pk_key, user_state=-1)

    def remove_plate(self, plate_number):
        return self.update('vehicles', plate_number=plate_number, vehicle_state=-1)


    def _extract_entries_kwargs(self, **kwargs) -> dict:
        try:
            kwargs['car_id']
            kwargs['person_id']
            kwargs['company_id']
        except KeyError:
            raise KeyError("Please insert both person id and or car plate number")
        else:
            entry_id = self._generate_entry_id()
            kwargs['entry_id'] = entry_id
        finally:
            return kwargs

    def _generate_entry_id(self):
        entry_id = random.randint(1_000_000, 10_000_000)
        is_exists = self.get_entry_by_id(entry_id)
        while is_exists:
            entry_id = random.randint(1_000_000, 10_000_000)
            is_exists = self.get_entry_by_id(entry_id)
        return entry_id

    def get_vehicle_by_plate_number(self, plate_number):
        self._open()
        self._cur.execute(f"SELECT * FROM vehicles WHERE plate_number='{plate_number}'")
        val = self._cur.fetchone()
        self._close()
        return val

    def get_company_by_id(self, company_id):
        self._open()
        self._cur.execute(f"SELECT * FROM companies WHERE company_id='{company_id}'")
        val = self._cur.fetchone()
        self._close()
        return val

    def get_entry_by_id(self, entry_id):
        self._open()
        self._cur.execute(f"SELECT * FROM entries WHERE entry_id='{entry_id}'")
        val = self._cur.fetchone()
        self._close()
        return val

    def get_entries_by_company_id(self, company_id: str) -> list[dict[str, str]]:
        self._open()
        self._cur.execute(f"SELECT * FROM entries WHERE company_id='{company_id}'")
        val = self._cur.fetchall()
        self._close()
        return val

