import Database.SugDelek as sd
import Database.SugRechev as sc
from Database.Database import PlateGateDB
from Database.Database import Validator
from fetch import GovApiFetcher


class Vehicle:
    def __init__(self, response):
        result = response['result']
        car_info = result['records'][0]
        self._car_info = car_info
        self._result = result
        self._RESOURCE_ID = result['resource_id']
        self._plate_number = car_info['mispar_rechev']
        self._sug_delek = sd.fuel_map[car_info['sug_delek_nm']]
        self._shnat_yetsur = car_info['shnat_yitzur']
        self._sug_rechev = None

    @property
    def totaled(self):
        return self._result['total_was_estimated']

    @property
    def plate_number(self):
        return self._plate_number

    @property
    def sug_delek(self):
        return self._sug_delek

    @property
    def shnat_yitsur(self):
        return int(self._shnat_yetsur)

    @property
    def active(self):
        return GovApiFetcher.is_car_active(self)

    @property
    def sug_rechev(self):
        return self._sug_rechev

    @property
    def valid(self):
        if self.totaled or not self.active:
            return False
        db = PlateGateDB()
        row = db.select_all_where('vehicles', plate_number=self.plate_number)
        if not row:
            return False
        row = row[0]
        return all([row['vehicle_state'] >= 1,
                    row['sug_rechev'] == self.sug_rechev.value[0],
                    row['sug_delek'] == self.sug_delek.value[0],
                    row['shnat_yitsur'] == self.shnat_yitsur])

    def add_to_database(self, owner_id):
        state = 1
        if self.totaled or not self.active:
            state = 0
        if not Validator.validate_id(owner_id):
            raise ValueError("The owner_id is not a valid id")
        db = PlateGateDB()
        return db.insert_into('vehicles',
                              plate_number=self.plate_number,
                              owner_id=owner_id,
                              sug_delek=self.sug_delek.value[0],
                              shnat_yitsur=int(self.shnat_yitsur),
                              sug_rechev=self.sug_rechev.value[0],
                              vehicle_state=state)


class Car(Vehicle):
    def __init__(self, response):
        super().__init__(response)
        self._sug_rechev = sc.rechev_map[self._car_info['sug_degem']]


class Motorcycle(Vehicle):
    def __init__(self, response):
        super().__init__(response)
        self._sug_rechev = sc.SugRechev.MOTORCYCLE


class OtherVehicle(Vehicle):
    def __init__(self, response):
        super().__init__(response)
        self._sug_rechev = sc.rechev_map[self._car_info['kvutzat_sug_rechev']]


class SelfImportedVehicle(Vehicle):
    def __init__(self, response):
        super().__init__(response)
        self._sug_rechev = sc.rechev_map[self._car_info['sug_rechev_cd'][0]]
