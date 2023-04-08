import requests
import json


class GovApiFetcher:
    RESOURCE_ID = '053cea08-09bc-40ec-8f7a-156f0677aff3'
    URL = 'https://data.gov.il/api/v3/datastore_search'

    @staticmethod
    def get_car_by_plate_number(self, plate_number):
        query = {"mispar_rechev": str(plate_number)}
        car_response = requests.get(self.URL, params={
            'resource_id': self.RESOURCE_ID,
            'q': json.dumps(query)
        })
        try:
            return Car(car_response.json()) if car_response.status_code == 200 else False
        except Exception as err:
            print(str(err))
            return False


class Car:
    def __init__(self, response):
        car_info = response['result']
