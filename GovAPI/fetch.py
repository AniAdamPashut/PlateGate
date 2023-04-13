import requests
import json
import Database.SugDelek as sd
import Database.SugRechev as sc


class GovApiFetcher:
    CARS_RESOURCE_ID = '053cea08-09bc-40ec-8f7a-156f0677aff3'
    MOTORCYCLE_RESOURCE_ID = 'bf9df4e2-d90d-4c0a-a400-19e15af8e95f'
    OTHER_VEHICLE_RESOURCE_ID = 'cd3acc5c-03c3-4c89-9c54-d40f93c0d790'
    NOT_ACTIVE_CARS_RESOURCE_ID = 'f6efe89a-fb3d-43a4-bb61-9bf12a9b9099'
    NOT_ACTIVE_VEHICLES_RESOURCE_ID = '6f6acd03-f351-4a8f-8ecf-df792f4f573a'
    FINAL_CANCELLATION_RESOURCE_ID = '851ecab1-0622-4dbe-a6c7-f950cf82abf9'
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
        if car_response['result']['records']:
            return Car(car_response)
        if motorcycle_response['result']['records']:
            return Motorcycle(motorcycle_response)
        if other_vehicle_response['result']['records']:
            return OtherVehicle(other_vehicle_response)
        return False

    @classmethod
    def is_car_active(cls, plate_number) # FIXME
        query = {'licensePlate': str(plate_number)}
        response = requests.post('https://www.gov.il/Api/Police/stolencar/api/sc/sc/', data=json.dumps(query))
        print(response)


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
        return self._shnat_yetsur

    @property
    def stolen(self):  # DON'T USE THIS
        pass
    @property
    def sug_rechev(self):
        return self._sug_rechev


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


car = GovApiFetcher.get_vehicle_by_plate_number(57579202)
print(car.sug_rechev)
