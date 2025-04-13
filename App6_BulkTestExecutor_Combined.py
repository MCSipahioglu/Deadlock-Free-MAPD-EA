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

from functions.classes import SingleTeamToken, Token, Agent, Task
from functions.move_execution import check_collisions, check_path_validity, check_all_agents_idle
from functions.SequentialAStar_1 import SAS_1


def execute_moves(token):

    for agent in token.agents:

        agent_type = agent.agent_type

        # Move the agent to the next position
        loc_x,loc_y,time_of_path = agent.path[0]

        agent.location=(loc_x,loc_y)
        agent.path.pop(0)           # Remove the current position from the path
        
        agent.current_path_state = agent.path_states[0]
        agent.path_states.pop(0)


        # Update the State for the move it made: Check if agent's location matches its assigned task's start or goal 
        if agent.state==0:                                                             # Free, No checks needed
            pass
        elif agent.state==5 and agent.path!=[]:                                        # Helping Ongoing, No checks needed
            pass
        elif agent.state==5 and agent.path==[]:                                        # Helping Completed
            agent.state=0
        elif tuple(agent.location) == agent.assigned_task.start and agent.state==1:    # Pick Up Reached
            agent.state = 2
        elif agent.state==2 and tuple(agent.location) != agent.assigned_task.start:    # Pick Up was Reached but it was left before Pickup was Completed
            agent.state = 1
        elif tuple(agent.location) == agent.assigned_task.start and agent.state==2:    # Pick Up Completed
            agent.state = 3
        elif tuple(agent.location) == agent.assigned_task.goal and agent.state==3:     # Delivery Reached
            agent.state = 4
        elif agent.state==4 and tuple(agent.location) != agent.assigned_task.goal:     # Delivery was Reached but it was left before Delivery was Completed
            agent.state = 3
        elif tuple(agent.location) == agent.assigned_task.goal and agent.state==4:     # Delivery Completed, Task Completed
            agent.state = 0
            agent.assigned_task = None

            if agent_type=="Home":
                token.home_tasking_time    += token.time-agent.task_assignment_time
                token.home_completed_tasks += 1
            else:
                token.guest_tasking_time    += token.time-agent.task_assignment_time
                token.guest_completed_tasks += 1


        # After the effect of its move is recorded above, Check if there are helper_paths queued up, switch to the helper state if there is.
        if agent.state==0 and agent.path_states:
            if agent.path_states[0].agent_role=="Helper":
                agent.state = 5



    return token




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
        self.combined_token = SingleTeamToken()
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



    if game.get('home_agents'):
        simulation_data.home_token.agents = [Agent(id=i+1, agent_type="Home", color=agent_data['color'], 
                                   location=tuple(agent_data['location']), state=0)
                             for i, agent_data in enumerate(game['home_agents'])]
    
    if game.get('home_tasks'):
        simulation_data.home_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['home_tasks']]
        simulation_data.imported_H_task_count=len(simulation_data.home_tasks)
        simulation_data.combined_token.unassigned_home_tasks = [simulation_data.home_tasks.pop(0) for _ in range(min(len(simulation_data.home_token.agents), len(simulation_data.home_tasks)))]  # Pop H many tasks to the unassigned tasks.

    if game.get('guest_agents'):
        simulation_data.guest_token.agents = [Agent(id=i+1+len(simulation_data.home_token.agents), agent_type="Guest", color=agent_data['color'], 
                                    location=tuple(agent_data['location']), state=0)
                              for i, agent_data in enumerate(game['guest_agents'])]
    
    if game.get('guest_tasks'):
        simulation_data.guest_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['guest_tasks']]
        simulation_data.imported_G_task_count=len(simulation_data.guest_tasks)
        simulation_data.combined_token.unassigned_guest_tasks = [simulation_data.guest_tasks.pop(0) for _ in range(min(len(simulation_data.guest_token.agents), len(simulation_data.guest_tasks)))] # Pop G many tasks to the unassigned tasks.


    simulation_data.combined_token.agents = simulation_data.home_token.agents + simulation_data.guest_token.agents

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
    combined_token = simulation_data.combined_token
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
            
        combined_token = SAS_1(combined_token, dijkstras_map)

        #print_agents(combined_token.agents, time)

        # Top up the tasks to the number of agents.
        while len(combined_token.unassigned_home_tasks) < len(home_token.agents) and home_tasks:
            combined_token.unassigned_home_tasks.append(home_tasks.pop(0))


        # Top up the tasks to the number of agents.
        while len(combined_token.unassigned_guest_tasks) < len(guest_token.agents) and guest_tasks:
            combined_token.unassigned_guest_tasks.append(guest_tasks.pop(0))


        check_path_validity(combined_token)

        if check_all_agents_idle(combined_token.agents):
            combined_token.all_agents_idle_counter += 1
        else:
            combined_token.all_agents_idle_counter = 0


        if combined_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Home Agents are Soft-Locked."
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, combined_token, 0, failure_message)  # Failure Code
            break




        


        # Move Execution and Collision Check (odd time steps)
        collision_identifier = check_collisions(combined_token.agents, [])

        if collision_identifier == 'No Collision':
            combined_token = execute_moves(combined_token)

            time += 1
            combined_token.time += 1
            #print(f"-------------------- TIME {time - 1} MOVES ARE EXECUTED -------------TIME IS NOW {time}")
            #print_agents(home_token.agents, time)
            #print_agents(guest_token.agents, time)

            print(f"{test_file_name} TIME IS NOW {time}, H Tasks: {combined_token.home_completed_tasks}/{imported_H_task_count}, G Tasks: {combined_token.guest_completed_tasks}/{imported_G_task_count}")

            if combined_token.unassigned_home_tasks==[]  and all(agent.state == 0 for agent in combined_token.agents if agent.agent_type == "Home"):
                if h_makespan_set==False:
                    combined_token.home_makespan=time
                    h_makespan_set=True
            
            if combined_token.unassigned_guest_tasks==[]  and  all(agent.state == 0 for agent in combined_token.agents if agent.agent_type == "Guest"):
                if g_makespan_set==False:
                    combined_token.guest_makespan=time
                    g_makespan_set=True
            
            if combined_token.home_completed_tasks>= imported_H_task_count - len(home_token.agents):
                if coexistance_coefficient_set==False:
                    coexistance_coefficient = combined_token.guest_completed_tasks/combined_token.home_completed_tasks if combined_token.home_completed_tasks!=0 else None
                    coexistance_coefficient_set=True


            # Check if all tasks are completed (No unassigned tasks and all home agents free)
            if combined_token.unassigned_home_tasks==[]  and  all(agent.state==0 for agent in combined_token.agents) and combined_token.unassigned_guest_tasks==[] :
                export_results(simulation_data, time, coexistance_coefficient, combined_token, 1)  # Success Code = 1
                break


        else:
            # Handle collision scenario
            print(f"TIME = {time} ------- SIMULATION STOPPED --------------------------")
            failure_message = (f"In the next timestep = {time+1}, Agent {collision_identifier['agents_in_collision'][0]['agent_type']} "
                                f"{collision_identifier['agents_in_collision'][0]['agent'].id} (from {collision_identifier['agents_in_collision'][0]['current_pos']}) and "
                                f"Agent {collision_identifier['agents_in_collision'][1]['agent_type']} {collision_identifier['agents_in_collision'][1]['agent'].id} "
                                f"(from {collision_identifier['agents_in_collision'][1]['current_pos']}) are going to {collision_identifier['type_of_collision']} Collide")
            print(failure_message)
            export_results(simulation_data, time, coexistance_coefficient, combined_token, 0, failure_message)  # Failure Code
            break



def export_results(simulation_data, time, coexistance_coefficient, combined_token, success_code, failure_message=None):

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
        
        "num_H_agents": len(combined_token.agents)/2,
        "num_G_agents": len(combined_token.agents)/2,
        "num_H_tasks": simulation_data.imported_H_task_count,
        "num_G_tasks": simulation_data.imported_G_task_count,
        
        "home_completedtasks": combined_token.home_completed_tasks if combined_token.home_completed_tasks > 0 else None,
        "home_makespan": combined_token.home_makespan if combined_token.home_completed_tasks > 0 else None,
        "home_sumofcosts": combined_token.home_tasking_time if combined_token.home_completed_tasks > 0 else None,
        "home_servicetime": (combined_token.home_tasking_time / combined_token.home_completed_tasks if combined_token.home_completed_tasks > 0 else None),
        
        "guest_completedtasks": combined_token.guest_completed_tasks if combined_token.guest_completed_tasks > 0 else None,
        "guest_makespan": combined_token.guest_makespan if combined_token.guest_completed_tasks > 0 else None,
        "guest_sumofcosts": combined_token.guest_tasking_time if combined_token.guest_completed_tasks > 0 else None,
        "guest_servicetime": combined_token.guest_tasking_time / combined_token.guest_completed_tasks  if combined_token.guest_completed_tasks > 0 else None,
        
        "coexistance_coefficient": coexistance_coefficient,
        "home_replan": combined_token.home_replan_counter,
        "guest_replan": combined_token.guest_replan_counter,
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
    #    run_simulation_for_file(test_folder, test_file)



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