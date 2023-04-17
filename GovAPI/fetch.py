import requests
import json
from Vehicles import *


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
