import random
import mysql.connector
import string
import hashlib


class PlateGateDB:
    def __init__(self):
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

    def select_salt(self, table_name: str, id_number: str):
        self._open()
        self._cur.execute(f"SELECT salt FROM {table_name} WHERE id_number='{id_number}';")
        val = self._cur.fetchone()
        self._close()
        return val['salt']

    def get_hashed_password(self, table_name, id_number: str) -> str:
        self._open()
        self._cur.execute(f"SELECT password FROM {table_name} WHERE id_number='{id_number}';")
        val = self._cur.fetchone()
        self._close()
        return val['password']

    def get_email(self, table_name: str, id_number: str) -> str:
        self._open()
        self._cur.execute(f"SELECT email FROM {table_name} WHERE id_number='{id_number}'")
        val = self._cur.fetchone()
        self._close()
        return val['email']

    def select_all_where(self, table_name: str, **kwargs):
        self._open()
        query = f"SELECT * FROM {table_name} WHERE "
        for col in kwargs.keys():
            query += f"{col}=%s,"
        query = query[:-1]
        query += ';'
        self._cur.execute(query, tuple(kwargs.values()))
        val = self._cur.fetchall()
        self._close()
        return val

    def show_tables(self):
        self._open()
        self._cur.execute("SHOW TABLES;")
        val = self._cur.fetchall()
        self._close()
        return val

    def show_databases(self):
        self._open()
        self._cur.execute("SHOW DATABASES;")
        val = self._cur.fetchall()
        self._close()
        return val

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
        if not Validator.validate_id(kwargs['id_number']):
            raise ValueError("Id is not valid")
        if not Validator.validate_name(kwargs['fname']) or not Validator.validate_name(kwargs['lname']):
            raise ValueError("User First or Last name are not valid")
        return kwargs

    @staticmethod
    def _figure_user_state(kwargs):
        try:
            kwargs['company_id']
        except KeyError:
            kwargs['user_state'] = 0
        else:
            kwargs['user_state'] = 1
        return kwargs

    def _generate_company_id(self):
        company_id = random.randint(100_000, 1_000_000)
        is_exists = self.select_all_where('companies', company_id=company_id)
        while is_exists:
            company_id = random.randint(100_000, 1_000_000)
            is_exists = self.select_all_where('companies', company_id=company_id)
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
        user = self.select_all_where('users', id_number=kwargs['owner_id'])
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
        query = f"INSERT INTO {table_name} ("
        for col in kwargs.keys():
            query += f"{col},"
        query = query[:-1]
        query += ") VALUES ("
        for _ in kwargs.values():
            query += "%s,"
        query = query[:-1]
        query += ");"
        self._open()
        inserted = False
        try:
            self._cur.execute(query, tuple(kwargs.values()))
            self._conn.commit()
        except Exception as err:
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
        else:
            return False

        return self._insert_kwargs(table_name, kwargs)

    def update(self, table_name: str, **kwargs):
        print(kwargs)
        key = next(iter(kwargs))
        value = kwargs.pop(key)
        query = f"UPDATE {table_name} SET "
        if 'password' in kwargs.keys():
            salt = self.select_salt(table_name, key)
            hashed = hashlib.sha256((kwargs['password'] + salt).encode()).hexdigest()
            kwargs['password'] = hashed
        for col in kwargs.keys():
            query += f"{col}=%s,"
        query = query[:-1] + " "
        query += f"WHERE {key}={value};"
        print(query)
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

    def delete_user(self, pk_key: str):
        return self.update('users', id_number=pk_key, user_state=-1)


class Validator:
    @staticmethod
    def validate_id(id_number: str):
        try:
            int(id_number)
        except ValueError:
            raise ValueError("Please insert a string made up from digits")
        if not id_number:
            return False
        if len(id_number) > 9:
            return False
        if len(id_number) < 9:
            id_number = "00000000" + id_number
            id_number = id_number[-9:]
            print(id_number)
        validator = "121212121"
        array = []
        for id_num, validating_num in zip(id_number, validator):
            num = int(id_num) * int(validating_num)
            if num > 10:
                num = num % 10 + num // 10
            array.append(num)
        id_sum = sum(array)
        return id_sum % 10 == 0

    @staticmethod
    def validate_name(name: str):
        return name.isalpha()
