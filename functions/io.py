
from tkinter import filedialog
import json



def import_game_state():
    file_path = filedialog.askopenfilename(title="Open Game State JSON File", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            game_state = json.load(file)
            return game_state


def print_tasks(tasks):
    for task in tasks:
        print(f"Start: {task.start}")
        print(f"Goal: {task.goal}")
        print()



def print_agents(agents, current_time):
    
       

    state_description = {
        0: "Free",
        1: "Going for Pick-Up",
        2: "Reached Pick-Up",
        3: "Going for Delivery",
        4: "Reached Delivery",
        5: "Helping...",
        6: "Going for Parking",
        7: "Parked"
    }
        
    for agent in agents:
        agents_type = agents[0].agent_type

        print(f"{agents_type} Agent ID: {agent.id}")  # Print the task ID
        print(f"Location: {agent.location}")                                    # Current location at the beginning of t
        print(f"State: {state_description.get(agent.state, 'Unknown')}")
        if agent.current_path_state:
            print(f"Path State: {agent.current_path_state.path_state} ")
        if agent.state in [1,2,3,4]:
            print(f"Task: {agent.assigned_task.start, agent.assigned_task.goal}")
        elif agent.claimed_parking_spot:
            print(f"Parking Spot: {agent.claimed_parking_spot}")
        if agent.path != []:
            print(f"Path: {agent.path}")
            print(f"Current Move: {agent.path[0]}")                             # Move it will make within time t.
        if agent.path_states != []:
            path_state=agent.path_states[0]
            time = path_state.time
            state = path_state.path_state


            if state == "Idle - No Valid Plan Possible" or state == "Idle - No Task Available" or state=="Idle - Initial Condition" or state== "Planner - Executing Task" or state == "Helper - Helping With H Accommodation":
                print(f"At time {time}, Agent {agent.id} will be {state}")
            elif state == "Helper - Helping With Intraloop Movement":
                print(f"At time {time}, Agent {agent.id} will be a {state}, Related to {path_state.related_agent_ids}")
            else:
                print(f"At time {time}, Agent {agent.id} will be {state} Between: {path_state.gate_or_border_before} -> {path_state.gate_or_border_after}), Related to {agents_type} Agent(s) {path_state.related_agent_ids}")
        print()

def print_map(map_array):
    print("Map Array:")
    print_map = [["·" if cell == 0 else "■" for cell in row] for row in map_array]
    for row in print_map:
        print(" ".join(row))

