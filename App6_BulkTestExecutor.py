import tkinter as tk
from tkinter import filedialog
import json
import os
from functions.io import print_agents
import copy
import time as real_time
from multiprocessing import Pool
from functools import partial
import re

from functions.classes import Token, Agent, Task
from functions.ZPH_V7_Switchok import ZPH
from functions.ZP_commons.H_accommodation import observe_others_moves
from functions.ZPG1_V3_w_self_collision_protection import ZPG1
from functions.move_execution import check_collisions, execute_moves, check_path_validity, check_all_agents_idle
from functions.SequentialAStar_H_w_parking import SAS_H              
from functions.SequentialAStar_G_better import SAS_G




class SimulationData:
    def __init__(self):

        self.test_folder=None
        self.test_file=None

        self.map = []
        self.dijkstras_map = []
        self.colored_map = []
        self.partition_map = []
        self.partition = []
        self.loops = []
        self.wires = []
        self.border_map = []
        self.gates = []
        self.parking = []
        self.guest_dijkstras_map = []
        self.guest_map = []

        self.imported_H_task_count = 0
        self.imported_G_task_count = 0

        self.home_token = Token()
        self.guest_token = Token()
        self.home_tasks = []
        self.guest_tasks = []

        self.time = 0

        self.coexistance_coefficient = None

        self.h_makespan_set = False
        self.g_makespan_set = False
        self.coexistance_coefficient_set = False






def select_test_folder():
    """Pop-up window to select the test folder."""
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    folder_selected = filedialog.askdirectory(title="Select Test Folder")
    return folder_selected





def initialize_simulation(test_folder, test_file):
    """Initialize the game state from a test file."""
    simulation_data = SimulationData()


    with open(test_file) as file:
        game = json.load(file)

    
    simulation_data.test_folder = test_folder
    simulation_data.test_file = test_file

    simulation_data.map = game['map']
    simulation_data.dijkstras_map = game['dijkstras_map']
    simulation_data.colored_map = game["colored_map"]

    simulation_data.partition_map = [
        [
            [tuple(inner_list) for inner_list in cell] if cell != 0 else 0
            for cell in row
        ]
        for row in game['partition_map']]
    
    simulation_data.partition = game['partition']
    simulation_data.loops = simulation_data.partition['loops']
    simulation_data.wires = simulation_data.partition['wires']
    simulation_data.parking = simulation_data.partition['parking']
    simulation_data.border_map = game['border_map']
    simulation_data.gates = game['gates']
    simulation_data.guest_map = game['guest_map']
    simulation_data.guest_dijkstras_map = game['guest_dijkstras_map']

    simulation_data.home_token.parking_constant = copy.deepcopy(game['parking'])
    simulation_data.home_token.parking_spots = copy.deepcopy(game['parking'])



    if game.get('home_agents'):
        simulation_data.home_token.agents = [Agent(id=i+1, agent_type="Home", color=agent_data['color'], 
                                   location=tuple(agent_data['location']), state=0)
                             for i, agent_data in enumerate(game['home_agents'])]
    
    if game.get('home_tasks'):
        simulation_data.home_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['home_tasks']]
        simulation_data.imported_H_task_count=len(simulation_data.home_tasks)
        simulation_data.home_token.unassigned_tasks = [simulation_data.home_tasks.pop(0) for _ in range(min(len(simulation_data.home_token.agents), len(simulation_data.home_tasks)))]  # Pop H many tasks to the unassigned tasks.

    if game.get('guest_agents'):
        simulation_data.guest_token.agents = [Agent(id=i+1, agent_type="Guest", color=agent_data['color'], 
                                    location=tuple(agent_data['location']), state=0)
                              for i, agent_data in enumerate(game['guest_agents'])]
    
    if game.get('guest_tasks'):
        simulation_data.guest_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['guest_tasks']]
        simulation_data.imported_G_task_count=len(simulation_data.guest_tasks)
        simulation_data.guest_token.unassigned_tasks = [simulation_data.guest_tasks.pop(0) for _ in range(min(len(simulation_data.guest_token.agents), len(simulation_data.guest_tasks)))] # Pop G many tasks to the unassigned tasks.

    #print(f"TIME = {time} ------- STARTING CONDITION ----------------------")
    #print_agents(home_token.agents, time)
    #print_agents(guest_token.agents, time)
    return simulation_data



def run_simulation(simulation_data):


    test_file_name =  re.search(r'\\(\w+_\d+)\.json$', simulation_data.test_file).group(1)

    """Run the MAPD simulation."""
    map=simulation_data.map
    dijkstras_map = simulation_data.dijkstras_map
    colored_map = simulation_data.colored_map
    partition_map = simulation_data.partition_map
    partition = simulation_data.partition
    loops=simulation_data.loops
    wires=simulation_data.wires
    border_map = simulation_data.border_map
    gates = simulation_data.gates
    parking = simulation_data.parking
    guest_dijkstras_map = simulation_data.guest_dijkstras_map
    guest_map = simulation_data.guest_map

    imported_H_task_count=simulation_data.imported_H_task_count
    imported_G_task_count=simulation_data.imported_G_task_count

    home_token=simulation_data.home_token
    guest_token=simulation_data.guest_token
    home_tasks = simulation_data.home_tasks
    guest_tasks = simulation_data.guest_tasks

    time=simulation_data.time

    coexistance_coefficient=simulation_data.coexistance_coefficient

    h_makespan_set=simulation_data.h_makespan_set
    g_makespan_set=simulation_data.g_makespan_set
    coexistance_coefficient_set=simulation_data.coexistance_coefficient_set



    while True:
        # MAPD Planning Step (even time steps)
        #print(f"TIME = {time} ------- MAPD PLANNING DONE ---------------------")
            
        #home_token = ZPH(home_token, dijkstras_map, guest_dijkstras_map, partition_map, border_map, gates, guest_map)
        home_token = SAS_H(home_token, dijkstras_map)

        #print_agents(home_token.agents, time)

        # Top up the tasks to the number of agents.
        while len(home_token.unassigned_tasks) < len(home_token.agents) and home_tasks:
            home_token.unassigned_tasks.append(home_tasks.pop(0))



        guest_token.observations = observe_others_moves(guest_token, home_token, 3)
        #print(f"Observations {guest_token.observations}")


        #guest_token = ZPG1(guest_token, guest_dijkstras_map, partition_map, border_map, gates, guest_map)
        #guest_token, token_exit_g = SAS_G(guest_token, dijkstras_map)           # Pure SAS
        guest_token, token_exit_g = SAS_G(guest_token, guest_dijkstras_map)    # SAS H Parks
        if token_exit_g == False:
            failure_message = "Simulation Ends Because Guest Agents went into a deadlock."
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, 0, failure_message)  # Failure Code
            break
        #print()
        #print_agents(guest_token.agents, time)

        # Top up the tasks to the number of agents.
        while len(guest_token.unassigned_tasks) < len(guest_token.agents) and guest_tasks:
            guest_token.unassigned_tasks.append(guest_tasks.pop(0))




        if check_all_agents_idle(home_token.agents):
            home_token.all_agents_idle_counter += 1
        else:
            home_token.all_agents_idle_counter = 0

        if check_all_agents_idle(guest_token.agents):
            guest_token.all_agents_idle_counter += 1
        else:
            guest_token.all_agents_idle_counter = 0

        if home_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Home Agents are Soft-Locked."
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, 0, failure_message)  # Failure Code
            break
        elif guest_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Guest Agents are Soft-Locked."
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, 0, failure_message)  # Failure Code
            break


        check_path_validity(home_token)
        check_path_validity(guest_token)
        


        # Move Execution and Collision Check (odd time steps)
        collision_identifier = check_collisions(home_token.agents, guest_token.agents)

        if collision_identifier == 'No Collision':
            home_token = execute_moves(home_token)
            guest_token = execute_moves(guest_token)

            time += 1
            home_token.time += 1
            guest_token.time += 1
            #print(f"-------------------- TIME {time - 1} MOVES ARE EXECUTED -------------TIME IS NOW {time}")
            #print_agents(home_token.agents, time)
            #print_agents(guest_token.agents, time)

            print(f"{test_file_name} TIME IS NOW {time}, H Tasks: {home_token.completed_tasks}/{imported_H_task_count}, G Tasks: {guest_token.completed_tasks}/{imported_G_task_count}")

            if home_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in home_token.agents):
                if h_makespan_set==False:
                    home_token.makespan=time
                    h_makespan_set=True
                
            
            if guest_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in guest_token.agents):
                if g_makespan_set==False:
                    guest_token.makespan=time
                    g_makespan_set=True
            
            if home_token.completed_tasks>= imported_H_task_count - len(home_token.agents):
                if coexistance_coefficient_set==False:
                    coexistance_coefficient = guest_token.completed_tasks/home_token.completed_tasks
                    coexistance_coefficient_set=True


            if home_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in  home_token.agents) and guest_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in guest_token.agents):
                export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, 1)  # Success Code = 1
                break

        else:
            # Handle collision scenario
            print(f"TIME = {time} ------- SIMULATION STOPPED --------------------------")
            failure_message = (f"In the next timestep = {time+1}, Agent {collision_identifier['agents_in_collision'][0]['agent_type']} "
                                f"{collision_identifier['agents_in_collision'][0]['agent'].id} (from {collision_identifier['agents_in_collision'][0]['current_pos']}) and "
                                f"Agent {collision_identifier['agents_in_collision'][1]['agent_type']} {collision_identifier['agents_in_collision'][1]['agent'].id} "
                                f"(from {collision_identifier['agents_in_collision'][1]['current_pos']}) are going to {collision_identifier['type_of_collision']} Collide")
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, 0, failure_message)  # Failure Code
            break



def export_results(simulation_data, time, coexistance_coefficient, home_token, guest_token, success_code, failure_message=None):

    test_folder = simulation_data.test_folder
    test_file = simulation_data.test_file

    coverage = sum(1 for row in simulation_data.guest_map for cell in row if cell != 0)
    total_cells = sum(1 for row in simulation_data.dijkstras_map for cell in row if cell != 0)

    """Export the results of the simulation."""
    results = {
        "time": time,
        "success_code": success_code,
        "failure_message": failure_message,
        
        "coverage": coverage if simulation_data.guest_map else None,
        "total_cells": total_cells,
        
        "num_H_agents": len(home_token.agents),
        "num_G_agents": len(guest_token.agents),
        "num_H_tasks": simulation_data.imported_H_task_count,
        "num_G_tasks": simulation_data.imported_G_task_count,
        
        "home_completedtasks": home_token.completed_tasks if home_token.completed_tasks > 0 else None,
        "home_makespan": home_token.makespan if home_token.completed_tasks > 0 else None,
        "home_sumofcosts": home_token.tasking_time if home_token.completed_tasks > 0 else None,
        "home_servicetime": (home_token.tasking_time / home_token.completed_tasks if home_token.completed_tasks > 0 else None),
        
        "guest_completedtasks": guest_token.completed_tasks if guest_token.completed_tasks > 0 else None,
        "guest_makespan": guest_token.makespan if guest_token.completed_tasks > 0 else None,
        "guest_sumofcosts": guest_token.tasking_time if guest_token.completed_tasks > 0 else None,
        "guest_servicetime": guest_token.tasking_time / guest_token.completed_tasks  if guest_token.completed_tasks > 0 else None,
        
        "coexistance_coefficient": coexistance_coefficient,
        "home_replan": home_token.replan_counter,
        "guest_replan": guest_token.replan_counter,
    }


    # Ensure the results directory exists
    result_dir = os.path.join(test_folder, '../results')
    os.makedirs(result_dir, exist_ok=True)  # Create the directory if it doesn't exist

    # Construct the result file path
    result_file = os.path.join(result_dir, f"result_{os.path.basename(test_file)}")
    
    # Save the results to the file
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
    
    print(f"Results saved to {result_file}")





def run_simulation_for_file(test_folder, test_file):
    print(f"Running simulation for {test_file}")
    simulation_data = initialize_simulation(test_folder, test_file)
    run_simulation(simulation_data)




def main():
    # Select the test folder

    test_folder = select_test_folder()

    test_files = [os.path.join(test_folder, f) for f in os.listdir(test_folder) if f.endswith('.json')]

    pool_size = 5  # Use 5 cores concurrently. Should resolve in 5 cycles.

    # Start timing
    start_time = real_time.time()

   


    # Run simulation for each test file
    run_simulation_with_folder = partial(run_simulation_for_file, test_folder)
    with Pool(pool_size) as pool:
        pool.map(run_simulation_with_folder, test_files)



    #for test_file in test_files:
    #    run_simulation_for_file(test_file)



    end_time = real_time.time()
    elapsed_time = end_time - start_time
    avg_elapsed_time = elapsed_time / len(test_files)

    # Convert to hours, minutes, seconds
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)

    print(f"It took {int(hours)} Hours {int(minutes)} Minutes {seconds} Seconds to Process {len(test_files)} Test Files.")

    # Convert to hours, minutes, seconds
    hours, rem = divmod(avg_elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)

    print(f"It took {int(hours)} Hours {int(minutes)} Minutes {seconds} Seconds in Average to Process 1 Test File.")





if __name__ == "__main__":
    main()