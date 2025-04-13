
from functions.classes import Agent, Token, Node, Task, PathUnfeasible, PathState


from functions.ZP_commons.tasks import closest_task
from functions.ZP_commons.a_star_algorithms import a_star_algorithm_pickup_or_delivery, a_star_algorithm
from functions.ZP_commons.planning import get_agents_we_are_planning_into_the_future_of, find_first_problematic_agent_ZPH, is_path_valid, calculate_helper_gating_sequence, calculate_helper_switching_sequence_H, assign_helper_path, find_closest_unclaimed_parking_spot_to_agent, check_self_conflict
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_w_gating_removal, update_occupied_spacetime_w_gating_protection
from functions.ZP_commons.path_state_map_calculations import calculate_path_states_for_switching_helper, calculate_compound_path_states_for_planner, create_dijkstras_map_with_guest_map_and_parking
from functions.ZP_commons.existing_paths import invalidate_paths_onwards

import copy

# V8: Gating Protection
# V7: Reactive Self Conflict Resolver (Plan -> Check -> Replan)
# V6: Parking
# V5: with astar planner for p/d idling.
# V4: Better Modularity
# V3: with Forcing Gatings
# V2: with Forcing Switches
# V1: With Passive Gating Only







def PathPlannerH(dijkstras_map, partition_map, border_map, current_agent, starting_spacetime, goal_position, token_actual, gates, guest_map):

    token = copy.deepcopy(token_actual) # Don't change the token_actual (It is always passed by reference to here)

    all_helper_ids_paths_pathstates=[]
    fixed_tentative_path = []

    # Calculate a tentative path to the goal.
    tentative_path = a_star_algorithm_pickup_or_delivery(token, starting_spacetime, Node(goal_position + (float('inf'),)), dijkstras_map)
    if tentative_path == None:
        #print(f"Path planning for Agent {current_agent.id} is not feasible because there is no space to plan a path with the required helper paths.")
        raise PathUnfeasible("Problem C")


    problem_found=True
    while problem_found==True:
        problem_found=False
        solved_by_gating = False


        #print(f"Tentative Path: {tentative_path}")
        ##print(f"Occupied Spacetime: {token.occupied_spacetime}")
        ##print(f"Occupied Spacetime Edges: {token.occupied_spacetime_edges}")


        # Check if we are planning into the future of any agents.
        agents_we_are_planning_into_the_future_of = get_agents_we_are_planning_into_the_future_of(token, current_agent.id, tentative_path)
        #print(f"Agents We Are Planning into the Future of Are: {agents_we_are_planning_into_the_future_of}")    
        
        # Find the first agent we assume will be idling and we will be entering to the same partition with.
        problem_found, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index = find_first_problematic_agent_ZPH(tentative_path, agents_we_are_planning_into_the_future_of, partition_map, guest_map)
        
        

        # Find the closest position in my loop where this first problematic agent should be rerouted to, that is not on my path.
        if problem_found==True:

            move_before_failure=tentative_path[first_problematic_planner_path_index-1]
            move_at_failure=tentative_path[first_problematic_planner_path_index]
            #print(f"Move Before First Failure is {move_before_failure} Because We Assume Agent {first_problematic_agent[0]} will idle at {first_problematic_agent[1]}")

            planner_loop_before_the_failure = partition_map[move_before_failure[1]][move_before_failure[0]]
            planner_loop_after_the_failure = partition_map[move_at_failure[1]][move_at_failure[0]]

            

            

            
            # Failure needs to be resolved by gating.
            if ([move_at_failure[0],move_at_failure[1]] not in token_actual.parking_constant) and (([[move_before_failure[0],move_before_failure[1]],[move_at_failure[0],move_at_failure[1]]] in gates) or ([[move_at_failure[0],move_at_failure[1]],[move_before_failure[0],move_before_failure[1]]] in gates)):
                #print(f"Failure Needs to be Resolved by a Gating Sequence")
                helper_path_found, path_for_helper_agent, fixed_tentative_path = calculate_helper_gating_sequence(tentative_path, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index, move_before_failure, move_at_failure, planner_loop_after_the_failure, token, dijkstras_map)
                solved_by_gating = True


            # Failure can be resolved by enabling switch with the closest cell in my loop that I won't use.
            else: 
                #print(f"Failure Can be Resolved by Simultaneous Switching")
                helper_path_found, path_for_helper_agent, fixed_tentative_path = calculate_helper_switching_sequence_H(tentative_path, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index, move_before_failure, planner_loop_before_the_failure, planner_loop_after_the_failure, token, dijkstras_map, border_map, partition_map)





            # After all we try to find a helper path if it is not feasible, then path planning is not feasible for this agent.
            if helper_path_found == True:

 
                #print(f"Tentative Helper Path for Agent {first_problematic_agent[0]} is: {path_for_helper_agent}")
                token.agents[first_problematic_agent[0]-1].path.extend(path_for_helper_agent[1:])
                token = update_occupied_spacetime_w_gating_removal(token, path_for_helper_agent, partition_map, gates, guest_map)
            
                #print(f"Fix Tentative Planner Path: {fixed_tentative_path}")

                if is_path_valid(fixed_tentative_path[1:], token) == False: # This catches an impossible to resolve problem in sequential planning where
                    #print(f"Path planning for Agent {current_agent.id} is not feasible because if the helper paths are planned then the planner path won't be feasible because there's a third agent causing this impossibility.")
                    raise PathUnfeasible("Problem E")



                # Calculate a new tentative path to the goal. (Starting from the ned of fixed_planner_path)
                additional_tentative_path = a_star_algorithm_pickup_or_delivery(token, fixed_tentative_path[-1], Node(goal_position + (float('inf'),)), dijkstras_map)
                if additional_tentative_path == None:
                    #print(f"Path planning for Agent {current_agent.id} is not feasible because there is no space to plan a path with the required helper paths.")
                    raise PathUnfeasible("Problem D")
                
                #print(f"Additional Tentative Planner Path: {additional_tentative_path}")

                tentative_path = fixed_tentative_path + additional_tentative_path[1:]

               

                path_states_helper = calculate_path_states_for_switching_helper(path_for_helper_agent, current_agent.id, token.agents[first_problematic_agent[0]-1].id, (move_before_failure[0], move_before_failure[1]), (move_at_failure[0], move_at_failure[1]), solved_by_gating)
                all_helper_ids_paths_pathstates.append((first_problematic_agent[0], path_for_helper_agent, path_states_helper))



            else:
                #print(f"All helper paths couldn't be generated. Path planning for Agent {current_agent.id} is not feasible because Agent {first_problematic_agent[0]} is stuck")
                raise PathUnfeasible("Problem A")
                

        else:
           #print(f"Planner Tentative Path is OK")
           pass

    
    # if tentative_path has no problems:
    planner_path=tentative_path

    planner_path_states = calculate_compound_path_states_for_planner(planner_path, all_helper_ids_paths_pathstates)


    return planner_path, planner_path_states, all_helper_ids_paths_pathstates











def ZPH(token, dijkstras_map, guest_dijkstras_map, partition_map, border_map, gates, guest_map):

    current_time = token.time
    replan_count = 0
    complete_replan_required = False

    token.occupied_spacetime = set()
    token.occupied_spacetime_edges = set()

    for agent in token.agents:                          # Reset all flags
        agent.path_set=0                                # Flag for if this agent has been assigned a path or affirmed its existing path this loop.
        agent.gating_path_set=0 
        agent.earliest_timestep_invalidated=None 




    for agent in token.agents:
        if agent.latest_gating_path_set:
            if agent.latest_gating_path_set[2]>current_time:

                gating_path_to_set = []
                gating_path_states_to_set = []
                for i, path_step in enumerate(agent.path):
                    path_state_step = agent.path_states[i]
                    if path_step[2] <= agent.latest_gating_path_set[2]:
                        gating_path_to_set.append(path_step)
                        gating_path_states_to_set.append(path_state_step)

                if gating_path_to_set != []:
                    token.agents[agent.id-1].gating_path_set = 1
                    update_occupied_spacetime_w_gating_protection(token, [(token.agents[agent.id-1].location[0],token.agents[agent.id-1].location[1], current_time)] + gating_path_to_set, [token.agents[agent.id-1].current_path_state] + gating_path_states_to_set, partition_map, gates, guest_map)
                else:
                    #print(f"{agent.agent_type} Agent {agent.id} has the start of a gating path but not the rest ")
                    exit()





    for i in range(len(token.agents)):
        agent = token.agents[i]
        is_planner = False

        if agent.path_states and agent.path_states[0]:
            next_path_state = agent.path_states[0]
            next_state = next_path_state.path_state

            # Check if agent is "At the Gate" and gating_path_set is 0
            if (next_state == "Planner - Gated to Other Partition" or next_state == "Helper - Making One Move Back") and agent.gating_path_set == 0:
                is_planner = (next_state == "Planner - Gated to Other Partition")

                gating_pairs_id = next_path_state.related_agent_ids[0]


                token.agents[agent.id-1].gating_path_set = 1
                token.agents[gating_pairs_id-1].gating_path_set = 1

                if is_planner:
                    token.agents[agent.id-1].latest_gating_path_set = agent.path[1]
                    token.agents[gating_pairs_id-1].latest_gating_path_set = agent.path[2]

                    update_occupied_spacetime_w_gating_protection(token, [(token.agents[agent.id-1].location[0],token.agents[agent.id-1].location[1], current_time)] + token.agents[agent.id-1].path[:2], [token.agents[agent.id-1].current_path_state] + token.agents[agent.id-1].path_states[:2]   ,partition_map, gates, guest_map)
                    update_occupied_spacetime_w_gating_protection(token, [(token.agents[gating_pairs_id-1].location[0],token.agents[gating_pairs_id-1].location[1], current_time)] + token.agents[gating_pairs_id-1].path[:3] ,  [token.agents[gating_pairs_id-1].current_path_state] + token.agents[gating_pairs_id-1].path_states[:3], partition_map, gates, guest_map)
                else:
                    token.agents[agent.id-1].latest_gating_path_set = agent.path[2]
                    token.agents[gating_pairs_id-1].latest_gating_path_set = agent.path[1]

                    update_occupied_spacetime_w_gating_protection(token, [(token.agents[agent.id-1].location[0],token.agents[agent.id-1].location[1], current_time)] + token.agents[agent.id-1].path[:3], [token.agents[agent.id-1].current_path_state] + token.agents[agent.id-1].path_states[:3], partition_map, gates, guest_map)
                    update_occupied_spacetime_w_gating_protection(token, [(token.agents[gating_pairs_id-1].location[0],token.agents[gating_pairs_id-1].location[1], current_time)] + token.agents[gating_pairs_id-1].path[:2] ,  [token.agents[gating_pairs_id-1].current_path_state] + token.agents[gating_pairs_id-1].path_states[:2] , partition_map, gates, guest_map)









    token_great_backup = copy.deepcopy(token)
    there_is_self_conflict = True

    while there_is_self_conflict:
        there_is_self_conflict=False

        token.occupied_spacetime = set()
        token.occupied_spacetime_edges = set()

        for agent in token.agents:
            token = update_occupied_spacetime_w_gating_protection(token, [(agent.location[0],agent.location[1],current_time)]+agent.path, [agent.current_path_state]+agent.path_states, partition_map, gates, guest_map)




        for agent in token.agents:        # For all free agents (They request the token.)
            planner_agent_id = agent.id

            if token.agents[planner_agent_id-1].path ==[]:  # Agent requires path planning.

                if complete_replan_required == True:
                    replan_count += 1


                if ((token.agents[planner_agent_id-1].state == 0 and token.unassigned_tasks) or token.agents[planner_agent_id-1].state != 0):      # Free Agent : Needs a Task and a Path or Replan Agent: Just needs a new path.
                    
                    token_backup=copy.deepcopy(token)

                    try:

                        if (token.agents[planner_agent_id-1].state == 0):   # Here for a task and a plan not replanning.
                            
                            #print()
                            #print(f"... Assigning Task to {agent.agent_type} Agent {planner_agent_id}")
                            best_task = closest_task(guest_dijkstras_map, token.agents[planner_agent_id-1].location, token.unassigned_tasks)  # Find the Best Task to Assign
                            token.agents[planner_agent_id-1].assigned_task = best_task              # Assign the best task to the agent
                            token.agents[planner_agent_id-1].task_assignment_time = token.time
                            token.unassigned_tasks.remove(best_task)                                # Remove the task from unassigned_tasks

                            if token.agents[planner_agent_id-1].claimed_parking_spot != None:
                                token.parking_spots.append(token.agents[planner_agent_id-1].claimed_parking_spot)
                                token.agents[planner_agent_id-1].claimed_parking_spot = None

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
                            #print(f"... Planning {agent.agent_type} Agent {planner_agent_id} Pickup")
                            path_start_to_pickup, path_states_start_to_pickup, all_helper_ids_paths_pathstates_pickup = PathPlannerH(guest_dijkstras_map, partition_map, border_map, agent, (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), token.agents[planner_agent_id-1].assigned_task.start, token, gates, guest_map)
                            
                            # Assign Path to Planner Agent
                            token = update_occupied_spacetime_w_gating_protection(token, path_start_to_pickup, path_states_start_to_pickup, partition_map, gates, guest_map)
                            token.agents[planner_agent_id-1].path.extend(path_start_to_pickup[1:])
                            token.agents[planner_agent_id-1].path_states.extend(path_states_start_to_pickup[1:])
                            #print(f"✓ Pickup Path Planned for Agent {planner_agent_id}:", path_start_to_pickup)
                            #print()

                            for helper_agent_id, helper_agent_path, helper_agent_path_states in all_helper_ids_paths_pathstates_pickup:
                                token = update_occupied_spacetime_w_gating_protection(token, helper_agent_path, helper_agent_path_states, partition_map, gates, guest_map)
                                token = assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                                #print(f"ℍ Interloop Pickup Helper Agent {helper_agent_id} will Gate/Switch with Path: {helper_agent_path}")

                            #print()
                        else:
                            path_start_to_pickup=[(agent.location[0],agent.location[1],token.time)]
                        
                        
                        


                        # ---------------- DELIVERY INTER LOOP PLAN ----------------

                        #print(f"... Planning {agent.agent_type} Agent {planner_agent_id} Delivery")
                        path_pickupend_to_delivery, path_states_pickupend_to_delivery, all_helper_ids_paths_pathstates_delivery = PathPlannerH(guest_dijkstras_map, partition_map, border_map, agent, path_start_to_pickup[-1], token.agents[planner_agent_id-1].assigned_task.goal, token, gates, guest_map)
                        
                        # Assign Path to Planner Agent
                        token = update_occupied_spacetime_w_gating_protection(token, path_pickupend_to_delivery, path_states_pickupend_to_delivery, partition_map, gates, guest_map)
                        token.agents[planner_agent_id-1].path.extend(path_pickupend_to_delivery[1:])
                        token.agents[planner_agent_id-1].path_states.extend(path_states_pickupend_to_delivery[1:])
                        #print(f"✓ Delivery Path Planned for Agent {planner_agent_id}:", path_pickupend_to_delivery)
                        #print()

                        for helper_agent_id, helper_agent_path, helper_agent_path_states in all_helper_ids_paths_pathstates_delivery:
                            token = update_occupied_spacetime_w_gating_protection(token, helper_agent_path, helper_agent_path_states, partition_map, gates, guest_map)
                            token = assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                            #print(f"ℍ Interloop Delivery Helper Agent {helper_agent_id} will Gate/Switch with Path: {helper_agent_path}")
                        #print()



                        complete_path = path_start_to_pickup[1:] + path_pickupend_to_delivery[1:]  # Exclude the duplicate starting points
                        #print(f"✓ Complete Path Planned for {agent.agent_type} Agent {planner_agent_id}:", complete_path)





                    except PathUnfeasible:  # If a valid path doesn't exist, idle.
                        token = copy.deepcopy(token_backup)

                        token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1))
                        token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=token.time + 1, related_agent_ids=None))
                        token = update_occupied_spacetime_w_gating_protection(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1)], [token.agents[planner_agent_id-1].current_path_state] + token.agents[planner_agent_id-1].path_states, partition_map, gates, guest_map)
                        #print(f"Agent {token.agents[planner_agent_id-1].id} will idle with path {token.agents[planner_agent_id-1].path} instead.")
                    
                




                else:   # If there are no more tasks to be assigned, park.

                    token_backup=copy.deepcopy(token)

                    try:

                        if token.agents[planner_agent_id-1].claimed_parking_spot == None:
                            #print()
                            #print(f"... Assigning Parking Spot to {agent.agent_type} Agent {planner_agent_id}")
                            closest_unclaimed_parking_spot = find_closest_unclaimed_parking_spot_to_agent(dijkstras_map, token.agents[planner_agent_id-1], token.agents, token.parking_spots)                    
                            token.agents[planner_agent_id-1].claimed_parking_spot = closest_unclaimed_parking_spot
                            token.parking_spots.remove(closest_unclaimed_parking_spot)
                            #print(f"✓ Assigned Parking Spot {closest_unclaimed_parking_spot} to Agent {planner_agent_id}")
                            #print()
                        
                        
                        # ----------------- PARKING INTER LOOP PLAN -----------------

                        #print(f"... Planning {agent.agent_type} Agent {planner_agent_id} Parking")
                        path_to_park, path_states_to_park, all_helper_ids_paths_pathstates_pickup = PathPlannerH(create_dijkstras_map_with_guest_map_and_parking(dijkstras_map, guest_map, token.agents[planner_agent_id-1].claimed_parking_spot ), partition_map, border_map, agent, (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), (token.agents[planner_agent_id-1].claimed_parking_spot[0], token.agents[planner_agent_id-1].claimed_parking_spot[1]), token, gates, guest_map)
                        
                        if len(path_to_park) == 2 and (path_to_park[-1][0], path_to_park[-1][1]) == (path_to_park[-2][0], path_to_park[-2][1]):
                            pass                                # Don't cut anything off if the generated path is pure idling.
                        else:
                            path_to_park = path_to_park[:-1]   # Cut off the excess path. Since this is planned using the pickup delivery planner.
                            path_states_to_park = path_states_to_park[:-1]

                        # Assign Path to Planner Agent
                        token = update_occupied_spacetime_w_gating_protection(token, path_to_park, path_states_to_park, partition_map, gates, guest_map)
                        token.agents[planner_agent_id-1].path.extend(path_to_park[1:])
                        token.agents[planner_agent_id-1].path_states.extend(path_states_to_park[1:])
                        #print(f"✓ Parking Path Planned for Agent {planner_agent_id}:", path_to_park)
                        #print()

                        for helper_agent_id, helper_agent_path, helper_agent_path_states in all_helper_ids_paths_pathstates_pickup:
                            token = update_occupied_spacetime_w_gating_protection(token, helper_agent_path, helper_agent_path_states, partition_map, gates, guest_map)
                            token = assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                            #print(f"ℍ Interloop Pickup Helper Agent {helper_agent_id} will Gate/Switch with Path: {helper_agent_path}")

                            
                        #print()


                    except:
                        token = copy.deepcopy(token_backup)

                        token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1))
                        token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=token.time + 1, related_agent_ids=None))
                        token = update_occupied_spacetime_w_gating_protection(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], token.time+1)], [token.agents[planner_agent_id-1].current_path_state] + token.agents[planner_agent_id-1].path_states, partition_map, gates, guest_map)
                        #print(f"Agent {token.agents[planner_agent_id-1].id} will idle with path {token.agents[planner_agent_id-1].path} instead.")



                    

            else:       # If the agent doesn't need a path, it knows what to do, let him.
                pass
















        for i in range(len(token.agents)):
            agent = token.agents[i]
            is_planner = False

            if agent.path_states and agent.path_states[0]:
                next_path_state = agent.path_states[0]
                next_state = next_path_state.path_state

                # Check if agent is "At the Gate" and gating_path_set is 0
                if (next_state == "Planner - Gated to Other Partition" or next_state == "Helper - Making One Move Back") and agent.gating_path_set == 0:
                    is_planner = (next_state == "Planner - Gated to Other Partition")

                    gating_pairs_id = next_path_state.related_agent_ids[0]

                    #print(f"✓ Setting the Valid Newly Planned Gating Sequence for {agent.agent_type} Agents {agent.id} and {gating_pairs_id}")
                    token.agents[agent.id - 1].gating_path_set = 1
                    token.agents[gating_pairs_id - 1].gating_path_set = 1

                    if is_planner:
                        # Update paths for planner
                        token.agents[agent.id - 1].latest_gating_path_set = agent.path[1]
                        token.agents[gating_pairs_id - 1].latest_gating_path_set = agent.path[2]

                    else:
                        # Update paths for helper
                        token.agents[agent.id - 1].latest_gating_path_set = agent.path[2]
                        token.agents[gating_pairs_id - 1].latest_gating_path_set = agent.path[1]
                    
                    token_great_backup.agents[agent.id - 1] = token.agents[agent.id - 1]
                    token_great_backup.agents[gating_pairs_id - 1] = token.agents[gating_pairs_id - 1]





        self_conflicting_agents = check_self_conflict(token, partition_map, guest_map)

        if self_conflicting_agents:

            token = copy.deepcopy(token_great_backup)


            for self_conflicting_agent in self_conflicting_agents:
                if self_conflicting_agent.gating_path_set == 0 and self_conflicting_agent.path_set == 0:
                    there_is_self_conflict=True
                    complete_replan_required = True
                    #print("X There is Self Conflict")


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







