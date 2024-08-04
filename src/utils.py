from geopy.distance import geodesic

def calculate_aerial_distance(coord1, coord2):
    return geodesic(coord1, coord2).meters

def calculate_total_distance(route):
    total_distance = 0
    for i in range(len(route) - 1):
        total_distance += calculate_aerial_distance(route[i], route[i+1])
    return total_distance
