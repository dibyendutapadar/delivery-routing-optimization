import streamlit as st
import pandas as pd
import pydeck as pdk
from data import get_random_locations, get_random_warehouse
from routing import plan_delivery_routes
from utils import calculate_aerial_distance, calculate_total_distance

# Page configuration
st.set_page_config(
    page_title="Delivery Route Planner",
    layout="wide"
)

# Sidebar
st.sidebar.title("Delivery Route Planner")
st.sidebar.markdown("Enter the number of locations and delivery agents you want to simulate this for")

# User Inputs
num_locations = st.sidebar.number_input("Number of delivery locations (x)", min_value=1, max_value=100, value=5)
num_agents = st.sidebar.number_input("Number of delivery agents (y)", min_value=1, max_value=10, value=2)
start_button = st.sidebar.button("Plan Delivery")

# Main Panel
st.title("Delivery Route Planner")
with st.expander("About this application"):
    st.markdown("""
    This application simulates the planning of delivery routes for a specified number of locations and delivery agents within Bangalore.
    The algorithm used is the Vehicle Routing Problem (VRP) solver provided by [OR-Tools](https://developers.google.com/optimization), an optimization library developed by Google.

    ![OR-Tools](https://developers.google.com/static/optimization/images/ortools_banner.jpg)

    ### Algorithm
    The Vehicle Routing Problem (VRP) is a combinatorial optimization and integer programming problem that seeks to service a number of customers with a fleet of vehicles. It is a generalization of the Traveling Salesman Problem (TSP).

    - **Step 1:** Generate a warehouse location and random delivery locations within Bangalore.
    - **Step 2:** Use OR-Tools to solve the VRP with the specified number of delivery agents to minimize the total distance traveled.
    - **Step 3:** Display the routes for each delivery agent on the map and show the total distance traveled.

    The algorithm ensures that the delivery routes are optimized for minimal travel distance, taking into account the constraints of the VRP.
    
    For more information on OR-Tools, visit the [official documentation](https://developers.google.com/optimization).
    """)

st.subheader("Simulation")
st.markdown("The maps and results will be shown below after you enter the parameters and click on the 'Plan Delivery' button.")

if start_button:
    # Generate random locations
    warehouse = get_random_warehouse()
    locations = get_random_locations(num_locations)
    
    # Assign names to locations
    location_names = {tuple(loc): f"Location {i+1}" for i, loc in enumerate(locations)}
    location_names[tuple(warehouse)] = "Warehouse"
    
    st.write(f"Warehouse Location: {warehouse}")
    
    # Display map
    map_data = pd.DataFrame(locations, columns=['lat', 'lon'])
    map_data['name'] = map_data.apply(lambda row: location_names[(row['lat'], row['lon'])], axis=1)
    map_data.loc[-1] = [warehouse[0], warehouse[1], 'Warehouse']
    map_data.index = map_data.index + 1
    map_data = map_data.sort_index()
    
    # Initial map with only locations
    icon_data = pd.DataFrame(
        {
            "lat": [warehouse[0]] + [loc[0] for loc in locations],
            "lon": [warehouse[1]] + [loc[1] for loc in locations],
            "icon_data": [
                {"url": "https://img.icons8.com/color/48/000000/warehouse.png", "width": 48, "height": 48, "anchorY": 48}
            ] + [{"url": "https://img.icons8.com/ultraviolet/40/000000/marker.png", "width": 24, "height": 24, "anchorY": 24} for _ in locations],
            "label": ["Warehouse"] + [f"Location {i+1}" for i in range(len(locations))]
        }
    )

    icon_layer = pdk.Layer(
        type="IconLayer",
        data=icon_data,
        get_icon="icon_data",
        get_size=4,
        size_scale=10,
        get_position=["lon", "lat"],
        pickable=True,
        tooltip=True,
    )

    view_state = pdk.ViewState(
        latitude=warehouse[0],
        longitude=warehouse[1],
        zoom=11,
        pitch=0,
    )

    initial_deck = pdk.Deck(
        layers=[icon_layer],
        initial_view_state=view_state,
        tooltip={"text": "{label}"}
    )

    st.pydeck_chart(initial_deck)
    
    # Progress bar
    progress_bar = st.progress(0)
    
    # Plan delivery routes
    with st.spinner("Planning delivery routes..."):
        routes, distances = plan_delivery_routes(warehouse, locations, num_agents, progress_bar)
    
    if not routes:
        st.error("No solution found. Please try increasing the number of delivery agents or changing the number of delivery locations.")
    else:
        total_distance = sum(distances)
        
        st.subheader("Delivery Routes")
        st.markdown("### Routes and Distances")
        arrow_emoji = "➡️"
        for i, route in enumerate(routes):
            formatted_route = f"Delivery Agent {i+1}: " + f" {arrow_emoji} ".join([location_names[tuple(point)] for point in route])
            st.write(f"**{formatted_route}**")
            st.write(f"**Total Distance for Delivery Agent {i+1}:** {distances[i]:.2f} meters")
        
        st.write(f"**Total Distance Travelled by All Agents:** {total_distance:.2f} meters")
        
        # Plot routes on map
        route_layers = []
        colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], [0, 255, 255]]
        for i, route in enumerate(routes):
            route_path = [[point[1], point[0]] for point in route]  # Flip lat/lon for pydeck
            route_data = pd.DataFrame({
                "path": [route_path],
                "color": [colors[i % len(colors)]]
            })
            route_layer = pdk.Layer(
                "PathLayer",
                data=route_data,
                pickable=True,
                get_color="color",
                width_scale=20,
                width_min_pixels=2,
                get_path="path",
                get_width=5,
            )
            route_layers.append(route_layer)
        
        route_layers.append(icon_layer)
        
        route_deck = pdk.Deck(
            layers=route_layers,
            initial_view_state=view_state,
            tooltip={"text": "{label}"}
        )
        
        st.pydeck_chart(route_deck)
