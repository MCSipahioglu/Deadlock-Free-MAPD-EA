
from functions.classes import Agent, Token, Node, Task, PathUnfeasible, PathState, SimulationEnd


from functions.ZP_commons.tasks import closest_task
from functions.ZP_commons.a_star_algorithms import a_star_algorithm_pickup_or_delivery
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_Simple
from functions.ZP_commons.planning import check_self_conflict_Simple
from functions.ZP_commons.existing_paths import invalidate_paths_onwards

import copy







def PathPlannerAStar(dijkstras_map, current_agent, starting_spacetime, goal_position, token_actual):

    token = copy.deepcopy(token_actual) # Don't change the token_actual (It is always passed by reference to here)

    # Calculate a tentative path to the goal.
    planner_path = a_star_algorithm_pickup_or_delivery(token, starting_spacetime, Node(goal_position + (float('inf'),)), dijkstras_map)
    if planner_path == None:
        #print(f"Path planning for Agent {current_agent.id} is not feasible because there is no space to plan a path with the required helper paths.")
        raise PathUnfeasible("Problem C")


    planner_path_states = [PathState() for _ in range(len(planner_path))]
    for i, path in enumerate(planner_path):
        path_time = path[2]
        planner_path_states[i].time = path_time
        planner_path_states[i].agent_role = "Planner"
        planner_path_states[i].path_state = "Planner - Executing Task"
        planner_path_states[i].related_agent_ids = None
        planner_path_states[i].gate_or_border_before = None
        planner_path_states[i].gate_or_border_after = None


    return planner_path, planner_path_states








def SAS_H(token, dijkstras_map):

    current_time = token.time
    replan_count = 0
    complete_replan_required = False


    token.occupied_spacetime = set()
    token.occupied_spacetime_edges = set()

    for agent in token.agents:                          # Reset all flags
        agent.path_set=0                                # Flag for if this agent has been assigned a path or affirmed its existing path this loop.
        agent.gating_path_set=0 
        agent.earliest_timestep_invalidated=None 

    token_great_backup = copy.deepcopy(token)
    there_is_self_conflict = True

    while there_is_self_conflict:
        there_is_self_conflict=False

        token.occupied_spacetime = set()
        token.occupied_spacetime_edges = set()

        for agent in token.agents:
            token = update_occupied_spacetime_Simple(token, [(agent.location[0],agent.location[1],current_time)]+agent.path)



        for agent in token.agents:        # For all free agents (They request the token.)
            planner_agent_id = agent.id

            if token.agents[planner_agent_id-1].path ==[]:  # Agent requires path planning.

                if complete_replan_required == True:
                    replan_count += 1

                if ((token.agents[planner_agent_id-1].state == 0 and token.unassigned_tasks) or token.agents[planner_agent_id-1].state != 0):
                    
                    token_backup=copy.deepcopy(token)

                    try:

                        if (token.agents[planner_agent_id-1].state == 0):

                            #print()
                            #print(f"... Assigning Task to Agent {planner_agent_id}")
                            best_task = closest_task(dijkstras_map, token.agents[planner_agent_id-1].location, token.unassigned_tasks)  # Find the Best Task to Assign
                            token.agents[planner_agent_id-1].assigned_task = best_task              # Assign the best task to the agent
                            token.agents[planner_agent_id-1].task_assignment_time = token.time
                            token.unassigned_tasks.remove(best_task)                                # Remove the task from unassigned_tasks
                            
                            if tuple(token.agents[planner_agent_id-1].location) == tuple(best_task.start):
                                token.agents[planner_agent_id-1].state = 2  # Agent is already at the pickup of the task
                            else:
                                token.agents[planner_agent_id-1].state = 1  # Agent is assigned a task but not at the pickup
                            #print(f"✓ Assigned Task {best_task.start}->{best_task.goal} to Agent {planner_agent_id}")
                            #print()
                            
                    
                        else: # Replan
                            if complete_replan_required == False:
                                replan_count+=1


                        # ----------------- PICKUP INTER LOOP PLAN -----------------



                        if token.agents[planner_agent_id-1].state ==1 or token.agents[planner_agent_id-1].state ==2: # If needs to go to pickup or at the pickup needs path to pickup. (Even at the pickup needs 1 idling path.)
                            #print(f"... Planning Agent {planner_agent_id} Pickup")
                            path_start_to_pickup, path_states_start_to_pickup = PathPlannerAStar(dijkstras_map, agent, (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), token.agents[planner_agent_id-1].assigned_task.start, token)
                            
                            # Assign Path to Planner Agent
                            token = update_occupied_spacetime_Simple(token, path_start_to_pickup)
                            token.agents[planner_agent_id-1].path.extend(path_start_to_pickup[1:])
                            token.agents[planner_agent_id-1].path_states.extend(path_states_start_to_pickup[1:])
                            #print(f"✓ Pickup Path Planned for Agent {planner_agent_id}:", path_start_to_pickup)
                            #print()

                        else:
                            path_start_to_pickup=[(agent.location[0],agent.location[1],token.time)]

                        
                    

                        # ---------------- DELIVERY INTER LOOP PLAN ----------------

                        #print(f"... Planning Agent {planner_agent_id} Delivery")
                        path_pickupend_to_delivery, path_states_pickupend_to_delivery = PathPlannerAStar(dijkstras_map, agent, path_start_to_pickup[-1], token.agents[planner_agent_id-1].assigned_task.goal, token)
                        
                        # Assign Path to Planner Agent
                        token = update_occupied_spacetime_Simple(token, path_pickupend_to_delivery)
                        token.agents[planner_agent_id-1].path.extend(path_pickupend_to_delivery[1:])
                        token.agents[planner_agent_id-1].path_states.extend(path_states_pickupend_to_delivery[1:])
                        #print(f"✓ Delivery Path Planned for Agent {planner_agent_id}:", path_pickupend_to_delivery)
                        #print()

                        


                        complete_path = path_start_to_pickup[1:] + path_pickupend_to_delivery[1:]  # Exclude the duplicate starting points
                        #print(f"✓ Complete Path Planned for Agent {planner_agent_id}:", complete_path)






                    except PathUnfeasible:  # If a valid path doesn't exist, do anystar move.
                        token = copy.deepcopy(token_backup)

                        token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1))
                        token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=token.time + 1, related_agent_ids=None))
                        token = update_occupied_spacetime_Simple(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1)])
                        #print(f"Agent {token.agents[planner_agent_id-1].id} will idle with path {token.agents[planner_agent_id-1].path} instead.")
                    
                    
                else:   # If there are no more tasks to be assigned, idle.
                    token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1))
                    token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Task Available", agent_role="Planner", time=token.time + 1, related_agent_ids=None))
                    token = update_occupied_spacetime_Simple(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1)])
                    #print(f"No Tasks -> Agent {token.agents[planner_agent_id-1].id} idles with {token.agents[planner_agent_id-1].path}")



            else:       # If the agent doesn't need a path, it knows what to do, let him.
                pass






        self_conflicting_agents = check_self_conflict_Simple(token.agents)

        if self_conflicting_agents:
            there_is_self_conflict=True
            complete_replan_required = True
            #print("X There is Self Conflict")
            token = copy.deepcopy(token_great_backup)


            for self_conflicting_agent in self_conflicting_agents:

                self_conflicting_agent_id = self_conflicting_agent.id

                token = invalidate_paths_onwards(self_conflicting_agent_id, token, current_time)

                token.agents[self_conflicting_agent_id-1].path=[(token.agents[self_conflicting_agent_id-1].location[0], token.agents[self_conflicting_agent_id-1].location[1], current_time+1)]
                token.agents[self_conflicting_agent_id-1].path_states=[PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=current_time + 1, related_agent_ids=None)]
                token.agents[self_conflicting_agent_id-1].path_set=1
                #print(f"Agent {token.agents[self_conflicting_agent_id-1].id} will idle with path {token.agents[self_conflicting_agent_id-1].path} to resolve a self conflict.")

            token_great_backup = copy.deepcopy(token)

        else:
           #print("✓ There is No Self Conflict")
           pass



    token.replan_counter += replan_count

    return token







