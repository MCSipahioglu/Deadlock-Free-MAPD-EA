import tkinter as tk
from tkinter import messagebox
from functions.gui import MAPDApp
from functions.io import print_agents, import_game_state
import copy
import sys
import os

from functions.classes import Agent, Task
from functions.ZPH_V7_Switchok import ZPH
from functions.ZP_commons.H_accommodation import observe_others_moves
from functions.ZPG1_V3_w_self_collision_protection import ZPG1
from functions.move_execution import check_collisions, execute_moves, check_path_validity, check_all_agents_idle
from functions.SequentialAStar_H_w_parking import SAS_H
from functions.SequentialAStar_G_better import SAS_G

real_time_step=200      # In ms




def step_forward(app):
    if app.step_counter % 2 == 0:
        print(f"TIME = {app.time} ------- MAPD PLANNING DONE ---------------------")

        # Step 1: Assign tasks to agents and solve MAPD problem (Home MAPD -> G Observes H -> Guest MAPD)
        #app.home_token=ZPH(app.home_token, app.dijkstras_map, app.guest_dijkstras_map, app.partition_map, app.border_map, app.gates, app.guest_map)
        app.home_token=SAS_H(app.home_token, app.dijkstras_map)

        #print_agents(app.home_token.agents, app.time)
        app.display_tasks(app.home_token.agents, 'red')
        app.display_moves(app.home_token.agents)

        # Top up the tasks to the number of agents.
        while len(app.home_token.unassigned_tasks) < len(app.home_token.agents) and app.home_tasks:
            app.home_token.unassigned_tasks.append(app.home_tasks.pop(0))
        # Top up always to 2H so that no tasks is only entered when truly no tasks. No need, gun icinde biterse dinlensin sonra geri gelsin.
        


        app.guest_token.observations=observe_others_moves(app.guest_token, app.home_token, 3)   # Radius needs to be 2 to avoid moving into the same cell as a H. 3 in order to be able to abort gating before its too late.
        print(f"Observations {app.guest_token.observations}")



        #app.guest_token=ZPG1(app.guest_token, app.guest_dijkstras_map, app.partition_map, app.border_map, app.gates, app.guest_map)
        app.guest_token, token_exit_g = SAS_G(app.guest_token, app.guest_dijkstras_map)
        if token_exit_g == False:
            failure_message = "Simulation Ends Because Guest Agents went into a deadlock while trying to accommodate H moves."
            messagebox.showinfo("Deadlock!", failure_message, icon='info')
            app.playing = False
            return
        print()
        print_agents(app.guest_token.agents, app.time)
        app.display_tasks(app.guest_token.agents, 'yellow')
        app.display_moves(app.guest_token.agents)


        # Top up the tasks to the number of agents.
        while len(app.guest_token.unassigned_tasks) < len(app.guest_token.agents) and app.guest_tasks:
            app.guest_token.unassigned_tasks.append(app.guest_tasks.pop(0))
        

        if check_all_agents_idle(app.home_token.agents):
            app.home_token.all_agents_idle_counter += 1
        else:
            app.home_token.all_agents_idle_counter = 0

        if check_all_agents_idle(app.guest_token.agents):
            app.guest_token.all_agents_idle_counter += 1
        else:
            app.guest_token.all_agents_idle_counter = 0

        print(f"Home All Idle Counter: {app.home_token.all_agents_idle_counter}")
        print(f"Guest All Idle Counter: {app.guest_token.all_agents_idle_counter}")

        if app.home_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Home Agents went into a soft-lock."
            messagebox.showinfo("Softlock!", failure_message, icon='info')
            app.playing = False
            return
        elif app.guest_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Guest Agents went into a soft-lock."
            messagebox.showinfo("Softlock!", failure_message, icon='info')
            app.playing = False
            return


        check_path_validity(app.home_token)
        check_path_validity(app.guest_token)




        
    else:
        # Step 2: Execute moves and update tasks if no collision. Changes location and state.

        collision_identifier = check_collisions(app.home_token.agents, app.guest_token.agents)

        if  collision_identifier == 'No Collision':

            app.home_token=execute_moves(app.home_token)
            app.guest_token=execute_moves(app.guest_token)

            app.time +=1
            app.home_token.time += 1
            app.guest_token.time += 1
            print(f"-------------------- TIME {app.time-1} MOVES ARE EXECUTED -------------TIME IS NOW {app.time}")
            print_agents(app.home_token.agents, app.time)
            #print_agents(app.guest_token.agents, app.time)
            app.render_sidebar(time_label, htask_label_completed, htask_label_assigned, htask_label_intoken, htask_label_inqueue, gtask_label_completed, gtask_label_assigned, gtask_label_intoken, gtask_label_inqueue)


            
            app.display_map(app.map, app.home_token.agents, app.guest_token.agents)
            app.display_tasks(app.home_token.agents, 'red')
            app.display_tasks(app.guest_token.agents, 'yellow')


            if app.home_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in app.home_token.agents):
                if app.h_makespan_set==False:
                    app.home_token.makespan=app.time
                    app.h_makespan_set=True
            
            if app.guest_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in app.guest_token.agents):
                if app.g_makespan_set==False:
                    app.guest_token.makespan=app.time
                    app.g_makespan_set=True
            
            if app.home_token.completed_tasks>= app.imported_H_task_count - len(app.home_token.agents):
                if app.coexistance_coefficient_set==False:
                    app.coexistance_coefficient = app.guest_token.completed_tasks/app.home_token.completed_tasks if app.home_token.completed_tasks!=0 else None
                    app.coexistance_coefficient_set=True


            # Check if all tasks are completed (No unassigned tasks and all home agents free)
            if app.home_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in app.home_token.agents) and app.guest_token.unassigned_tasks==[]  and  all(agent.state==0 for agent in app.guest_token.agents):
                messagebox.showinfo("All Tasks Completed!",f"TIME IS {app.time}\nAll Tasks are completed!\nH-Makespan={app.home_token.makespan}\nH-SumOfCosts={app.home_token.tasking_time}\nH-ServiceTime={app.home_token.tasking_time}/{app.home_token.completed_tasks}\nG-Makespan={app.guest_token.makespan}\nG-SumOfCosts={app.guest_token.tasking_time}\nG-ServiceTime={app.guest_token.tasking_time}/{app.guest_token.completed_tasks}", icon='info')
                app.playing = False
                return
        
        else:
            print(f"TIME = {app.time} ------- SIMULATION STOPPED --------------------------")
            app.display_collision_moves([collision_identifier['agents_in_collision'][0], collision_identifier['agents_in_collision'][1]])
            messagebox.showinfo("Collision!", f"In the next timestep = {app.time+1}, Agent {collision_identifier['agents_in_collision'][0]['agent_type']} {collision_identifier['agents_in_collision'][0]['agent'].id} (from {collision_identifier['agents_in_collision'][0]['current_pos']}) and Agent {collision_identifier['agents_in_collision'][1]['agent_type']} {collision_identifier['agents_in_collision'][1]['agent'].id} (from {collision_identifier['agents_in_collision'][1]['current_pos']}) are going to {collision_identifier['type_of_collision']} Collide", icon='info')
            print(f"In the next timestep = {app.time+1}, Agent {collision_identifier['agents_in_collision'][0]['agent_type']} {collision_identifier['agents_in_collision'][0]['agent'].id} (from {collision_identifier['agents_in_collision'][0]['current_pos']}) and Agent {collision_identifier['agents_in_collision'][1]['agent_type']} {collision_identifier['agents_in_collision'][1]['agent'].id} (from {collision_identifier['agents_in_collision'][1]['current_pos']}) are going to {collision_identifier['type_of_collision']} Collide")
            app.playing = False



    app.step_counter = (app.step_counter+1)%2
    if app.playing:
        app.after_id = app.master.after(real_time_step, step_forward, app)  # Schedule the next call to step_forward()




def step_forward_button(app):

    # Pause if playing
    if app.playing:
        app.playing = not app.playing
        app.master.after_cancel(app.after_id)
        play_button.config(state=tk.NORMAL)
        pause_button.config(state=tk.DISABLED)
        
    step_forward(app)



def play_pause(app):
    app.playing = not app.playing
    if app.playing:
        after_id = app.master.after(real_time_step, step_forward, app)
        play_button.config(state=tk.DISABLED)
        pause_button.config(state=tk.NORMAL)
        if app.time == 216:
            app.playing = not app.playing
    else:
        app.master.after_cancel(app.after_id)
        play_button.config(state=tk.NORMAL)
        pause_button.config(state=tk.DISABLED)




if __name__ == "__main__":
    root = tk.Tk()
    app = MAPDApp(root)

    # Import Game
    game = import_game_state()

    # Decompose Game
    app.map = game['map']
    app.dijkstras_map = game['dijkstras_map']
    app.colored_map = game['colored_map']

    app.partition_map = [
    [
        [tuple(inner_list) for inner_list in cell] if cell != 0 else 0
        for cell in row
    ]
    for row in game['partition_map']]

    app.partition = game['partition']
    app.loops=app.partition['loops']
    app.wires=app.partition['wires']
    app.parking=app.partition['parking']
    app.border_map = game['border_map']
    app.gates = game['gates']
    app.guest_map = game['guest_map']
    app.guest_dijkstras_map = game['guest_dijkstras_map']

    print(sum(1 for row in app.dijkstras_map for element in row if element != 0))
    print(sum(1 for row in app.guest_map for element in row if element != 0))

    app.home_token.parking_constant = copy.deepcopy(game['parking'])
    app.home_token.parking_spots = copy.deepcopy(game['parking'])

    if game.get('home_agents'):
        pass
        app.home_token.agents = [Agent(id=i+1, agent_type="Home", color=agent_data['color'], location=tuple(agent_data['location']), state=0) for i, agent_data in enumerate(game['home_agents'])]
    
    if game.get('home_tasks'):
        app.home_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['home_tasks']]
        app.imported_H_task_count=len(app.home_tasks)
        app.home_token.unassigned_tasks = [app.home_tasks.pop(0) for _ in range(min(len(app.home_token.agents), len(app.home_tasks)))]  # Pop H many tasks to the unassigned tasks.


    
    if game.get('guest_agents'):
        pass
        app.guest_token.agents = [Agent(id=i+1, agent_type="Guest", color=agent_data['color'], location=tuple(agent_data['location']), state=0) for i, agent_data in enumerate(game['guest_agents'])]
    
    if game.get('guest_tasks'):
        app.guest_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['guest_tasks']]
        app.imported_G_task_count=len(app.guest_tasks)
        app.guest_token.unassigned_tasks = [app.guest_tasks.pop(0) for _ in range(min(len(app.guest_token.agents), len(app.guest_tasks)))] # Pop G many tasks to the unassigned tasks.




    # Display the game state
    app.display_map(app.map,app.home_token.agents,app.guest_token.agents)
    print(f"TIME = {app.time} ------- STARTING CONDITION ----------------------")
    print_agents(app.home_token.agents, app.time)
    print_agents(app.guest_token.agents, app.time)






    # Create Step Forward button
    step_button = tk.Button(app.sidebar, text="Step Forward", command=lambda: step_forward_button(app))
    step_button.pack()

    play_button = tk.Button(app.sidebar, text="Play", command=lambda: play_pause(app))
    play_button.pack()

    pause_button = tk.Button(app.sidebar, text="Pause", command=lambda: play_pause(app), state=tk.DISABLED)
    pause_button.pack()

    time_label = tk.Label(app.sidebar, text="Time = 0")
    time_label.pack()

    htask_label = tk.Label(app.sidebar, text="H Tasks")
    htask_label.pack()
    
    htask_label_completed = tk.Label(app.sidebar, text="Completed: 0 / 0")
    htask_label_completed.pack()

    htask_label_assigned = tk.Label(app.sidebar, text="Assigned: 0 / 0")
    htask_label_assigned.pack()

    htask_label_intoken = tk.Label(app.sidebar, text="In Token: 0 / 0")
    htask_label_intoken.pack()

    htask_label_inqueue = tk.Label(app.sidebar, text="In Queue: 0 / 0")
    htask_label_inqueue.pack()

    gtask_label = tk.Label(app.sidebar, text="G Tasks")
    gtask_label.pack()

    gtask_label_completed = tk.Label(app.sidebar, text="Completed: 0 / 0")
    gtask_label_completed.pack()

    gtask_label_assigned = tk.Label(app.sidebar, text="Assigned: 0 / 0")
    gtask_label_assigned.pack()

    gtask_label_intoken = tk.Label(app.sidebar, text="In Token: 0 / 0")
    gtask_label_intoken.pack()

    gtask_label_inqueue = tk.Label(app.sidebar, text="In Queue: 0 / 0")
    gtask_label_inqueue.pack()


    root.mainloop()






















