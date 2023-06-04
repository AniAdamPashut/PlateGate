import requests
import json
import source.SugDelek as sd
import source.SugRechev as sc
from source.Database import PlateGateDB
import validator


"""
איתור סוג הרכב בעייתי. לכן נוצרו 4 מחלקות כלל אחת מטפלת בסוג הרכב בדרך שלה 
"""

class GovApiFetcher:
    CARS_RESOURCE_ID = '053cea08-09bc-40ec-8f7a-156f0677aff3'
    MOTORCYCLE_RESOURCE_ID = 'bf9df4e2-d90d-4c0a-a400-19e15af8e95f'
    OTHER_VEHICLE_RESOURCE_ID = 'cd3acc5c-03c3-4c89-9c54-d40f93c0d790'
    NOT_ACTIVE_CARS_RESOURCE_ID = 'f6efe89a-fb3d-43a4-bb61-9bf12a9b9099'
    NOT_ACTIVE_VEHICLES_RESOURCE_ID = '6f6acd03-f351-4a8f-8ecf-df792f4f573a'
    FINAL_CANCELLATION_RESOURCE_ID = '851ecab1-0622-4dbe-a6c7-f950cf82abf9'
    SELF_IMPORT_RESOURCE_ID = '03adc637-b6fe-402b-9937-7c3d3afc9140'
    URL = 'https://data.gov.il/api/3/action/datastore_search'

    @classmethod
    def get_vehicle_by_plate_number(cls, plate_number):
        query = {"mispar_rechev": str(plate_number)}
        car_response = requests.get(cls.URL, params={
            'resource_id': cls.CARS_RESOURCE_ID,
            'q': json.dumps(query)
        }).json()
        motorcycle_response = requests.get(cls.URL, params={
            'resource_id': cls.MOTORCYCLE_RESOURCE_ID,
            'q': json.dumps(query)
        }).json()
        other_vehicle_response = requests.get(cls.URL, params={
            'resource_id': cls.OTHER_VEHICLE_RESOURCE_ID,
            'q': json.dumps(query)
        }).json()
        self_imported_response = requests.get(cls.URL, params={
            'resource_id': cls.SELF_IMPORT_RESOURCE_ID,
            'q': json.dumps(query)
        }).json()
        if car_response['result']['records']:
            return Car(car_response)
        if motorcycle_response['result']['records']:
            return Motorcycle(motorcycle_response)
        if other_vehicle_response['result']['records']:
            return OtherVehicle(other_vehicle_response)
        if self_imported_response['result']['records']:
            return SelfImportedVehicle(self_imported_response)
        return False

    @classmethod
    def is_car_active(cls, vehicle):
        query = {"mispar_rechev": str(vehicle.plate_number)}
        res_id = cls.NOT_ACTIVE_VEHICLES_RESOURCE_ID
        if isinstance(vehicle, Car):
            res_id = cls.NOT_ACTIVE_CARS_RESOURCE_ID
        response = requests.get(cls.URL, params={
            'resource_id': res_id,
            'q': json.dumps(query)
        }).json()
        is_active = response['result']['records']
        response = requests.get(cls.URL, params={
            'resource_id': cls.FINAL_CANCELLATION_RESOURCE_ID,
            'q': json.dumps(query)
        }).json()
        is_canceled = response['result']['records']
        return not (is_active or is_canceled)


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
        row = db.get_vehicle_by_plate_number(self.plate_number)
        if not row:
            return False
        return all([row['vehicle_state'] >= 1,
                    row['sug_rechev'] == self.sug_rechev.value[0],
                    row['sug_delek'] == self.sug_delek.value[0],
                    row['shnat_yitsur'] == self.shnat_yitsur])

    def add_to_database(self, owner_id):
        state = 1
        if self.totaled or not self.active:
            state = 0
        if not validator.validate_id(owner_id):
            raise ValueError("The owner_id is not a valid id")
        db = PlateGateDB()
        return db.insert_into('vehicles',
                              plate_number=self.plate_number,
                              owner_id=owner_id,
                              sug_delek=self.sug_delek.value,
                              shnat_yitsur=int(self.shnat_yitsur),
                              sug_rechev=self.sug_rechev.value,
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

