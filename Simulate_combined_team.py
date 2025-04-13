import tkinter as tk
from tkinter import messagebox
from functions.gui import MAPDApp
from functions.io import print_agents, import_game_state
import copy
import sys
import os

from functions.classes import Agent, Task
from functions.ZPH_exp_gating import ZPH
from functions.ZP_commons.H_accommodation import observe_others_moves
from functions.ZPG1_exp_gating import ZPG1
from functions.move_execution import check_collisions, check_path_validity, check_all_agents_idle
from functions.SequentialAStar_1 import SAS_1

real_time_step=500      # In ms


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



def step_forward(app):
    if app.step_counter % 2 == 0:
        print(f"TIME = {app.time} ------- MAPD PLANNING DONE ---------------------")

        app.combined_token=SAS_1(app.combined_token, app.dijkstras_map)

        print_agents(app.combined_token.agents, app.time)

        while len(app.combined_token.unassigned_home_tasks) < len(app.home_agents) and app.home_tasks:
            app.combined_token.unassigned_home_tasks.append(app.home_tasks.pop(0))

        while len(app.combined_token.unassigned_guest_tasks) < len(app.guest_agents) and app.guest_tasks:
            app.combined_token.unassigned_guest_tasks.append(app.guest_tasks.pop(0))
        
        check_path_validity(app.combined_token)

        app.display_tasks(app.combined_token.agents, 'red')
        app.display_moves(app.combined_token.agents)


        if check_all_agents_idle(app.combined_token.agents):
            app.combined_token.all_agents_idle_counter += 1
        else:
            app.combined_token.all_agents_idle_counter = 0

        if app.combined_token.all_agents_idle_counter>= 50:
            failure_message = "Simulation Ends Because Combined Agents went into a soft-lock."
            messagebox.showinfo("Softlock!", failure_message, icon='info')
            app.playing = False
            return


    else:
        # Step 2: Execute moves and update tasks if no collision. Changes location and state.

        collision_identifier = check_collisions(app.combined_token.agents, [])

        if  collision_identifier == 'No Collision':

            app.combined_token=execute_moves(app.combined_token)

            app.time +=1
            app.combined_token.time += 1
            print(f"-------------------- TIME {app.time-1} MOVES ARE EXECUTED -------------TIME IS NOW {app.time}")
            print_agents(app.combined_token.agents, app.time)
            #app.render_sidebar(time_label, htask_label_completed, htask_label_assigned, htask_label_intoken, htask_label_inqueue, gtask_label_completed, gtask_label_assigned, gtask_label_intoken, gtask_label_inqueue)

            app.display_map(app.map, app.combined_token.agents, [])
            app.display_tasks(app.combined_token.agents, 'red')




            if app.combined_token.unassigned_home_tasks==[]  and all(agent.state == 0 for agent in app.combined_token.agents if agent.agent_type == "Home"):
                if app.h_makespan_set==False:
                    app.combined_token.home_makespan=app.time
                    app.h_makespan_set=True
            
            if app.combined_token.unassigned_guest_tasks==[]  and  all(agent.state == 0 for agent in app.combined_token.agents if agent.agent_type == "Guest"):
                if app.g_makespan_set==False:
                    app.combined_token.guest_makespan=app.time
                    app.g_makespan_set=True
            
            if app.combined_token.home_completed_tasks>= app.imported_H_task_count - len(app.home_agents):
                if app.coexistance_coefficient_set==False:
                    app.coexistance_coefficient = app.combined_token.guest_completed_tasks/app.combined_token.home_completed_tasks if app.combined_token.home_completed_tasks!=0 else None
                    app.coexistance_coefficient_set=True


            # Check if all tasks are completed (No unassigned tasks and all home agents free)
            if app.combined_token.unassigned_home_tasks==[]  and  all(agent.state==0 for agent in app.combined_token.agents) and app.combined_token.unassigned_guest_tasks==[] :
                messagebox.showinfo("All Tasks Completed!",f"TIME IS {app.time}\nAll Tasks are completed!\nH-Makespan={app.combined_token.home_makespan}\nH-SumOfCosts={app.combined_token.home_tasking_time}\nH-ServiceTime={app.combined_token.home_tasking_time}/{app.combined_token.home_completed_tasks}\nG-Makespan={app.combined_token.guest_makespan}\nG-SumOfCosts={app.combined_token.guest_tasking_time}\nG-ServiceTime={app.combined_token.guest_tasking_time}/{app.combined_token.guest_completed_tasks}", icon='info')
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






    if game.get('home_agents'):
        pass
        app.home_agents = [Agent(id=i+1, agent_type="Home", color=agent_data['color'], location=tuple(agent_data['location']), state=0) for i, agent_data in enumerate(game['home_agents'])]
    
    if game.get('home_tasks'):
        app.home_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['home_tasks']]
        app.imported_H_task_count=len(app.home_tasks)
        app.combined_token.unassigned_home_tasks = [app.home_tasks.pop(0) for _ in range(min(len(app.home_agents), len(app.home_tasks)))]  # Pop H many tasks to the unassigned tasks.


    
    if game.get('guest_agents'):
        pass
        app.guest_agents = [Agent(id=i+1+len(app.home_agents), agent_type="Guest", color=agent_data['color'], location=tuple(agent_data['location']), state=0) for i, agent_data in enumerate(game['guest_agents'])]
    
    if game.get('guest_tasks'):
        app.guest_tasks = [Task(tuple(task[0]), tuple(task[1])) for task in game['guest_tasks']]
        app.imported_G_task_count=len(app.guest_tasks)
        app.combined_token.unassigned_guest_tasks = [app.guest_tasks.pop(0) for _ in range(min(len(app.guest_agents), len(app.guest_tasks)))]# Pop G many tasks to the unassigned tasks.


    app.combined_token.agents = app.home_agents + app.guest_agents
    



    # Display the game state
    app.display_map(app.map,app.combined_token.agents,[])
    print(f"TIME = {app.time} ------- STARTING CONDITION ----------------------")
    print_agents(app.combined_token.agents, app.time)






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






















