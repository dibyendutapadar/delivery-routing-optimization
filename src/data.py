import random

def get_random_coordinates():
    # Generate random coordinates within Bangalore
    lat = 12.97 + random.uniform(-0.1, 0.1)
    lon = 77.59 + random.uniform(-0.1, 0.1)
    return [lat, lon]

def get_random_warehouse():
    return get_random_coordinates()

def get_random_locations(n):
    return [get_random_coordinates() for _ in range(n)]
