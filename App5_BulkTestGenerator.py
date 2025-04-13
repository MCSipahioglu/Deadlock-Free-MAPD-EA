import json, random, os
from tkinter import filedialog
from functions.Apps_commons.random_placement import get_loop_positions_and_limits, get_wire_positions_and_limits, place_agents
class Agent:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y



# Global variables
map_array = []
dijkstras_map = []
partition_map = []
partition = []
guest_map = []
guest_dijkstras_map = []
colored_map = []
gates = []
parking = []
border_map = []
home_agents=[]
guest_agents=[]
imported_file_name=""
imported_settings = 0
#Task_Per_Agent_count = 0
Task_count = 0
H_Task_count = 0
G_Task_count = 0
H_Delivery_Points = []
G_Delivery_Points = []


def import_game_or_settings():
    file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            data = json.load(file)

            # Load basic map data
            global map_array, dijkstras_map, partition_map, partition, guest_map, gates, border_map, home_agents, guest_agents, colored_map, guest_dijkstras_map, parking, imported_file_name, imported_settings
            imported_file_name_with_extension = os.path.basename(file_path)  # Extract the file name from the path
            imported_file_name = os.path.splitext(imported_file_name_with_extension)[0]  # Remove the extension

            map_array = data.get("map", [])
            dijkstras_map = data.get("dijkstras_map", [])

            try:        # Load partition-specific data
                colored_map = data.get("colored_map", [])
                partition_map = data.get("partition_map", [])
                partition = data.get("partition", {})
                guest_map = data.get("guest_map", [])
                guest_dijkstras_map = data.get("guest_dijkstras_map", [])
                parking = data.get("parking", [])
                gates = data.get("gates", [])
                border_map = data.get("border_map", [])
            except Exception as e:
                print(f"Error loading additional map data: {e}")
            
            try:        # Load home agents
                home_agents = [Agent(agent['location'][0], agent['location'][1]) for agent in data.get('home_agents', [])]
            except Exception as e:
                print(f"Error loading home agents: {e}")

            try:        # Load guest agents
                guest_agents = [Agent(agent['location'][0], agent['location'][1]) for agent in data.get('guest_agents', [])]
            except Exception as e:
                print(f"Error loading guest agents: {e}")

            
            # Determine if it's a game or settings file
            if "settings" in imported_file_name.lower():
                global Task_count, H_Task_count, G_Task_count, H_Delivery_Points, G_Delivery_Points
                imported_settings = 1  # Mark as settings file
                imported_file_name = imported_file_name.replace("settings_", "")
                Task_count = data.get("Task_count", [])
                #Task_Per_Agent_count = data.get("Task_Per_Agent_count", [])
                H_Task_count = data.get("H_Task_count", [])
                G_Task_count = data.get("G_Task_count", [])
                H_Delivery_Points = data.get("H_Delivery_Points", [])
                G_Delivery_Points = data.get("G_Delivery_Points", [])

            else:
                imported_settings = 0  # Mark as game file




def export_game(home_tasks, guest_tasks):
    
    global map_array, dijkstras_map, colored_map, partition_map, partition, guest_map, gates, parking, guest_dijkstras_map, border_map, home_agents, guest_agents, imported_file_name

    # Prepare the game data
    game = {
        "map": map_array,
        "dijkstras_map": dijkstras_map,
        "colored_map": colored_map,
        "partition": partition,
        "partition_map": partition_map,
        "guest_map": guest_map,
        "guest_dijkstras_map": guest_dijkstras_map,
        "gates": gates,
        "parking": parking,
        "border_map": border_map,
        "home_agents": [{'color': '#f20d0d', 'location': (agent.pos_x, agent.pos_y)} for agent in home_agents],
        "home_tasks": home_tasks,
        "guest_agents": [{'color': '#f2f20d', 'location': (agent.pos_x, agent.pos_y)} for agent in guest_agents],
        "guest_tasks": guest_tasks
    }
    

    # Define the base directory
    base_dir = os.path.join("tests", imported_file_name, "tests")

    # Create the base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)

    # Determine the next available index for the test
    existing_indices = []
    
    for entry in os.listdir(base_dir):
        if entry.startswith(imported_file_name) and entry.endswith('.json'):
            try:
                # Extract the index from the filename (assuming format: imported_file_name_index.json)
                index = int(entry.split("_")[-1].split('.')[0])  # Get the number before the '.json'
                existing_indices.append(index)
            except ValueError:
                continue  # Ignore entries that don't match the expected format

    next_index = max(existing_indices, default=0) + 1  # Increment the highest index found, or start at 1

    # Define the file path for the game JSON using the calculated next_index
    file_path = os.path.join(base_dir, f"{imported_file_name}_{next_index}.json")

    # Save game state to a JSON file
    with open(file_path, 'w') as file:
        json.dump(game, file, indent=4)
        print(f"Game exported successfully to {file_path}.")



            
def export_settings(Task_count, H_Task_count, G_Task_count, H_Delivery_Points, G_Delivery_Points):

    global map_array, dijkstras_map, partition_map, partition, guest_map, gates, parking, colored_map, guest_dijkstras_map, border_map, home_agents, guest_agents, imported_file_name
        #"Task_Per_Agent_count": Task_Per_Agent_count,

    # Prepare settings data
    settings = {
        "Task_count": Task_count,
        "H_Task_count": H_Task_count,
        "G_Task_count": G_Task_count,
        "H_Delivery_Points": H_Delivery_Points,
        "G_Delivery_Points": G_Delivery_Points,
        "map": map_array,
        "dijkstras_map": dijkstras_map,
        "colored_map": colored_map,
        "partition": partition,
        "partition_map": partition_map,
        "guest_map": guest_map,
        "gates": gates,
        "parking": parking,
        "guest_dijkstras_map": guest_dijkstras_map,
        "border_map": border_map,
        "home_agents": [{'color': '#f20d0d', 'location': (agent.pos_x, agent.pos_y)} for agent in home_agents],
        "guest_agents": [{'color': '#f2f20d', 'location': (agent.pos_x, agent.pos_y)} for agent in guest_agents]
    }


    # Define the base directory
    base_dir = os.path.join("tests", imported_file_name)

    # Create the base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)

    # Define the settings file path
    settings_file_path = os.path.join(base_dir, f"settings_{imported_file_name}.json")

    # Save settings to a JSON file
    with open(settings_file_path, 'w') as file:
        json.dump(settings, file, indent=4)
        print(f"Settings exported successfully to {settings_file_path}.")







def get_valid_Test_count():
    while True:
        try:
            Test_count = int(input(f"Please Enter the number of Tests you would like to create. (Agent placement will be the same, task locations will be randomized within a set of the same delivery points) (At Least 1): "))
            if 1 <= Test_count:
                return Test_count
            else:
                print(f"Invalid input. Please enter a number above 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def get_valid_H_Delivery_Point_count(max_H_Delivery_Point_count):
    while True:
        try:
            H_Delivery_Point_count = int(input(f"Please Enter the number of Home Delivery Points you would like to create. (Home Task Delivery Points will be randomly selected from this set. Pickup points will be completely random) (Between 1 and {max_H_Delivery_Point_count}): "))
            if 1 <= H_Delivery_Point_count:
                return H_Delivery_Point_count
            else:
                print(f"Invalid input. Please enter a number above 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")



def get_valid_G_Delivery_Point_count(max_G_Delivery_Point_count):
    while True:
        try:
            G_Delivery_Point_count = int(input(f"Please Enter the number of Guest Delivery Points you would like to create. (Guest Task Delivery Points will be randomly selected from this set. Pickup points will be completely random) (Between 1 and {max_G_Delivery_Point_count}): "))
            if 1 <= G_Delivery_Point_count:
                return G_Delivery_Point_count
            else:
                print(f"Invalid input. Please enter a number above 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")





def get_valid_Task_Per_Agent_count():
    while True:
        try:
            Task_Per_Agent_count = int(input(f"Please Enter the number of Tasks per Agent you would like to place. (At Least 1): "))
            if 1 <= Task_Per_Agent_count:
                return Task_Per_Agent_count
            else:
                print(f"Invalid input. Please enter a number above 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")




def get_valid_Task_count():
    while True:
        try:
            Task_count = int(input(f"Please Enter the number of Tasks you would like to place. (At Least 1): "))
            if 1 <= Task_count:
                return Task_count
            else:
                print(f"Invalid input. Please enter a number above 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")



def get_valid_H_count(max_H_count):
    while True:
        try:
            H_count = int(input(f"Please Enter the number of Home Agents you would like to place. (Between 0 and {max_H_count}): "))
            if 0 <= H_count <= max_H_count:
                return H_count
            else:
                print(f"Invalid input. Please enter a number between 0 and {max_H_count}.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def get_valid_G_count(max_G_count):
    while True:
        try:
            G_count = int(input(f"Please Enter the number of Guest Agents you would like to place. (Between 0 and {max_G_count}): "))
            if 0 <= G_count <= max_G_count:
                return G_count
            else:
                print(f"Invalid input. Please enter a number between 0 and {max_G_count}.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")



def sample_map(map, H_Delivery_Point_count):
    sampled_points = []

    # Collect all valid (x, y) coordinates where dijkstras_map[y][x] != 0
    for y in range(len(map)):
        for x in range(len(map[y])):
            if map[y][x] != 0:
                sampled_points.append((x, y))

    # Randomly sample the specified number of delivery points
    selected_points = random.sample(sampled_points, H_Delivery_Point_count)

    return selected_points



def generate_tasks(map, H_Delivery_Points, H_Task_count):
    tasks = []

    # Collect all valid pickup points (x, y) where dijkstras_map[y][x] != 0
    valid_pickup_points = [
        (x, y) for y in range(len(map)) 
                  for x in range(len(map[y])) 
                  if map[y][x] != 0
    ]

    # Ensure we have enough valid pickup points to generate tasks
    if len(valid_pickup_points) == 0 or len(H_Delivery_Points) == 0:
        raise ValueError("No valid pickup points or delivery points available.")

    # Generate tasks
    for _ in range(H_Task_count):
        pickup_point = random.choice(valid_pickup_points)  # Random pickup point
        delivery_point = random.choice(H_Delivery_Points)  # Random delivery point
        tasks.append([pickup_point, delivery_point])  # Append the task as a list of points

    return tasks








# Import the Map
print("--------------------- GAME IMPORT ---------------------")
import_game_or_settings()
if imported_settings==0:
    print(f"✓ Game {imported_file_name} Imported Successfully.")

    valid_H_loop_positions_and_limits = get_loop_positions_and_limits(partition, "home")
    valid_H_wire_positions_and_limits = get_wire_positions_and_limits(partition)
    valid_H_positions_and_limits = valid_H_loop_positions_and_limits + valid_H_wire_positions_and_limits

    max_H_count = sum(limit for _, limit in valid_H_positions_and_limits)

    valid_G_positions_and_limits = get_loop_positions_and_limits(partition, "guest")
    max_G_count = sum(limit for _, limit in valid_G_positions_and_limits)





    # Take Agent Counts input from the user
    print("--------------------- AGENT PLACEMENT ---------------------")

    if len(home_agents)==0 and len(guest_agents)==0:
        print(f"Agent Locations weren't set in the Loaded Game. Please select the number of agents you would like placed.")

        print(f"This map can accommodate a maximum of {max_H_count} Home Agents and {max_G_count} Guest Agents.")
        H_count = get_valid_H_count(max_H_count)
        G_count = get_valid_G_count(max_G_count)

        # Place Agents
        home_agents = place_agents(H_count, "home", partition, home_agents, guest_agents)
        guest_agents = place_agents(G_count, "guest", partition, home_agents, guest_agents)
        print("✓ All Agents Randomly Placed.")
    elif len(home_agents)>0 and len(guest_agents)==0:
        print(f"{len(home_agents)} Home Agents were already set in the Loaded Game. Please select the number of Guest Agents you would like placed.")
        print(f"This map can accommodate a maximum of {max_G_count} Guest Agents.")
        H_count = len(home_agents)
        G_count = get_valid_G_count(max_G_count)
        guest_agents = place_agents(G_count, "guest", partition, home_agents, guest_agents)
        print("✓ All Guest Agents Randomly Placed.")
    elif len(home_agents)==0 and len(guest_agents)>1:
        print(f"{len(guest_agents)} Guest Agents were already set in the Loaded Game. Please select the number of Home Agents you would like placed.")
        print(f"This map can accommodate a maximum of {max_H_count} Home Agents.")
        H_count = get_valid_H_count(max_H_count)
        G_count = len(guest_agents)
        home_agents = place_agents(H_count, "home", partition, home_agents, guest_agents)
    else:
        print(f"The Game had {len(home_agents)} Preset Home Agents and {len(guest_agents)} Preset Guest Agents. Moving on to Task Generation.")
        H_count = len(home_agents)
        G_count = len(guest_agents)


    # Task Count Input
    print("--------------------- TASK SETTINGS ---------------------")
    Task_Per_Agent_count = get_valid_Task_Per_Agent_count()
    H_Task_count = Task_Per_Agent_count * H_count
    G_Task_count = Task_Per_Agent_count * G_count

    #Task_count = get_valid_Task_count()
    #H_Task_count = Task_count + H_count
    #G_Task_count = Task_count + G_count



    print(f"{H_Task_count} Home Agent Tasks will be created.")
    print(f"{G_Task_count} Guest Agent Tasks will be created.")

    #H_Delivery_Point_count = get_valid_H_Delivery_Point_count(sum(1 for row in dijkstras_map for element in row if element != 0))
    #G_Delivery_Point_count = get_valid_G_Delivery_Point_count(sum(1 for row in guest_map for element in row if element != 0))

    H_Delivery_Point_count = sum(1 for row in guest_map for element in row if element != 0)
    G_Delivery_Point_count = sum(1 for row in guest_map for element in row if element != 0)

    print(f"Home Delivery Points will be sampled from a set of {H_Delivery_Point_count} coordinates.")
    print(f"Guest Delivery Points will be sampled from a set of {G_Delivery_Point_count} coordinates.")

    H_Delivery_Points = sample_map(guest_map, H_Delivery_Point_count)   # Should sample dijkstras map if wires wanted to be used for tasks.
    G_Delivery_Points = sample_map(guest_map, G_Delivery_Point_count)

    #print(H_Delivery_Points)
    #print(G_Delivery_Points)

else:
    print(f"✓ Settings {imported_file_name} Imported Successfully.")
    print(f"There are {len(home_agents)} Home Agent(s) Already Placed.")
    print(f"There are {len(guest_agents)} Home Agent(s) Already Placed.")
    #print(f"{Task_Per_Agent_count} Task(s) per Agent will be created.")
    print(f"{H_Task_count} Home Agent Task(s) will be created.")
    print(f"{G_Task_count} Guest Agent Task(s) will be created.")
    print(f"Home Deliveries will be chosen from a set of {len(H_Delivery_Points)} Point(s).")
    print(f"Guest Deliveries will be chosen from a set of {len(G_Delivery_Points)} Point(s).")


# Test Count Input
print("--------------------- TEST SETTINGS ---------------------")
Test_count = get_valid_Test_count()

print(f"Creating {Test_count} tests within folder ./tests/{imported_file_name}/ ...")
if imported_settings==0:
    export_settings(Task_count, H_Task_count, G_Task_count, H_Delivery_Points, G_Delivery_Points)


# Generate tests
for test_index in range(Test_count):

    # Generate tasks for home and guest agents
    H_Tasks = generate_tasks(guest_map, H_Delivery_Points, H_Task_count)    # Should use dijkstras_map if wire tasking is wanted.
    G_Tasks = generate_tasks(guest_map, G_Delivery_Points, G_Task_count)

    # Call the export_game function with the generated tasks
    export_game(H_Tasks, G_Tasks)

