from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from utils import calculate_aerial_distance, calculate_total_distance
import time

def create_data_model(warehouse, locations, num_agents):
    data = {}
    data['locations'] = [warehouse] + locations
    data['num_locations'] = len(data['locations'])
    data['num_agents'] = num_agents
    data['depot'] = 0
    return data

def plan_delivery_routes(warehouse, locations, num_agents, progress_bar):
    data = create_data_model(warehouse, locations, num_agents)
    
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(data['num_locations'], data['num_agents'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(calculate_aerial_distance(data['locations'][from_node], data['locations'][to_node]))

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        50000,  # vehicle maximum travel distance in meters (50 km)
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    progress_step = 100 / (data['num_agents'] * data['num_locations'])
    current_progress = 0
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return [], []

    # Get routes and distances.
    routes = []
    distances = []
    for vehicle_id in range(data['num_agents']):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(data['locations'][node_index])
            index = solution.Value(routing.NextVar(index))
            current_progress = min(current_progress + progress_step, 100)
            progress_bar.progress(current_progress / 100)
        node_index = manager.IndexToNode(index)
        route.append(data['locations'][node_index])
        routes.append(route)
        route_distance = calculate_total_distance(route)
        distances.append(route_distance)
        current_progress = min(current_progress + progress_step, 100)
        progress_bar.progress(current_progress / 100)

    progress_bar.progress(1.0)
    return routes, distances
