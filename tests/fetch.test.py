from source import fetch


print("START TEST")
print("-"*30)
vehicle = fetch.GovApiFetcher.get_vehicle_by_plate_number('57579202')
print(vehicle.plate_number)
print(vehicle.sug_delek)
print(vehicle.shnat_yitsur)
print(vehicle.sug_rechev)
print(f"is totaled {vehicle.totaled}")
print(f"is active {vehicle.active}")
print("-"*30)
print("END TEST")