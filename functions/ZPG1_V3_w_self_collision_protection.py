


import heapq
import copy
from functions.classes import Agent, Token, Node, Task, OccupancyCounter, PathUnfeasible, PathState

from functions.ZP_commons.tasks import closest_task
from functions.ZP_commons.a_star_algorithms import recursive_path_planning_G1, a_star_algorithm_pickup_or_delivery
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_G1
from functions.ZP_commons.planning import assign_helper_path, check_self_conflict, calculate_helper_gating_sequence, find_first_problematic_agent_ZPH, get_agents_we_are_planning_into_the_future_of, calculate_helper_switching_sequence_H
from functions.ZP_commons.H_accommodation import assign_home_helper_path, is_path_valid
from functions.ZP_commons.path_state_map_calculations import create_big_map_with_just_the_partition, prune_idle_steps, calculate_path_states_for_accommodation_helper, calculate_path_states_for_switching_helper, calculate_compound_path_states_for_planner
from functions.ZP_commons.existing_paths import is_path_valid_with_timestep, invalidate_paths_onwards, calculate_minimum_effective_distance


# V3: Reactive Self Conflict Resolver (Plan -> Check -> Replan)
# V2B: ZPG1 where Loop Limits = 1
# V2: with astar_any H accommodation
# V1: with manual H accommodation



def PathPlannerG1(dijkstras_map, partition_map, border_map, current_agent, starting_spacetime, goal_position, token_actual, gates, guest_map):

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
            if ([[move_before_failure[0],move_before_failure[1]],[move_at_failure[0],move_at_failure[1]]] in gates) or ([[move_at_failure[0],move_at_failure[1]],[move_before_failure[0],move_before_failure[1]]] in gates):
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
                token = update_occupied_spacetime_G1(token, path_for_helper_agent, partition_map, gates, guest_map)

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






def PathPlannerG_IntraLoop(token, priority_path, other_agents_and_starts, big_map_with_just_the_partition, partition_map, gates, guest_map):

    token_copy=copy.deepcopy(token) # token is passed by reference, don't change it when trying out paths.

    other_agents_ids=[]
    other_agents_starts=[]

    if other_agents_and_starts:
        for other_agent_and_start in other_agents_and_starts:
            other_agents_ids.append(other_agent_and_start[0])
            other_agents_starts.append(other_agent_and_start[1])


    horizon = priority_path[-1][2]  # All agents need to reach this horizon
    
    # Start the recursive path planning for agents 1, 2, ..., n
    
    all_paths = recursive_path_planning_G1(0, token_copy, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon, partition_map, gates, guest_map)

    ##print(f"All paths is: {all_paths}")

    if all_paths:

        # Pruning increases efficiency in less congestion by not keeping helper agents occupied longer than needed.
        all_paths = [prune_idle_steps(path) for path in all_paths]
        # If you want to prune you need to remove the occupied spacetime, edge and counter too. Revert to a backup add in the occupied spacetime for the paths assigned.

        return all_paths


    else:
        #print(f"All helper paths couldn't be generated.")
        raise PathUnfeasible("Problem B")






# Plan accommodating moves for the G agents in the partition HMove is going to.
def AccommodateHMove(H_path, dijkstras_map, partition_map, token, gates, guest_map):

    all_helper_ids_paths_pathstates=[]

    # Plan accomodation paths for all agents that will be in the same partition at the same time (Unnecessary paths will get pruned)
    partition_of_H_move=partition_map[H_path[-1][1]][H_path[-1][0]]
    big_map_with_just_the_partition=create_big_map_with_just_the_partition(dijkstras_map, partition_of_H_move)
    G_agents_in_H_move_partition=[]



    for agent in token.agents:
        if agent.path_set!=1 and agent.gating_path_set!=1 and partition_map[agent.location[1]][agent.location[0]]==partition_of_H_move:
            G_agents_in_H_move_partition.append((agent.id, (agent.location[0], agent.location[1], token.time)))


    if G_agents_in_H_move_partition:
        ##print(f"G Agents in H Accommodation Partition: {G_agents_in_H_move_partition}")

        planned_accommodation_paths=PathPlannerG_IntraLoop(token, H_path, G_agents_in_H_move_partition, big_map_with_just_the_partition, partition_map, gates, guest_map)
        
        for i, (G_agents_in_H_move_partition_id, _) in enumerate(G_agents_in_H_move_partition):

            path_for_helper_agent = planned_accommodation_paths[i]

            path_states_helper = calculate_path_states_for_accommodation_helper(path_for_helper_agent)

            all_helper_ids_paths_pathstates.append((G_agents_in_H_move_partition_id, path_for_helper_agent, path_states_helper))

        ##print(f"Agents ids {agents_we_will_get_muddy_with_ids}")
        ##print(f"Planned Helper Paths {planned_helper_paths}")


    return all_helper_ids_paths_pathstates






def ZPG1(token, dijkstras_map, partition_map, border_map, gates, guest_map):


    # 1. OK - Initialization: invalid=0 set=0
    # 2. Gating Check: Gating Agents (invalid=1 set=1), Agents Related to Gating Agents invalid=1, set=0
    # 3. Home Accomodation: Accomodating Agents (invalid=1 set=1), Agents Related to Accomodating Agents that Are Not Accomodating (invalid=1, set=0). Use recursive_path_planning, with idling heavily encouraged, for 1 timestep horizon into the future.
    #       At here all mandatory agents have invalid=1, set=1. No deadlock condition is guarenteed.
    # 4. Check Invalid Paths: After Accomodation, if set=0 and path_is_valid=0: invalid=1, related_invalid=1, set=0. (This check is separate from the next check because invalidation also invalidates related_agents' paths.)
    #       At here all agents with set=0 have their definitive invalid=1 or invalid=0 flag.
    # 5. After invalid path check: If invalid=0 and set=0 and not free -> Valid path. set=1.
    #       At here all mandatory agents have invalid=1, set=1. All agents with valid paths have invalid=0, set=1. Agents with invalid=1, set=0 needs replanning.
    # ZPG:  if invalid=0, set=1 and free -> Plan
    #       if invalid=1, set=0 -> Replan using other agents with set=0. -> Everybody in the end will have set=1.

    # Tips:
    # Any time path is set, update occupied spacetime.


    # Only do path set if you have invaldated a full path and put 1 step horizon path in place.
    # path_set is only used by invalidate paths to return everything preemptively.

    # Freezing condition: At any time step, G agents must be able to make 1 move to accomodate ANY H movement.
    # No deadlock condition can always easily be guarenteed if there are no G pairs that are currently gating. (Both gating agents in the same partition)
    # If no such pair exists all H moves can be accomodated by simply overwriting the next moves of some G agents.



    # 1. OK - Initialization: Reset all flags, Add H moves to occupied spacetime

    current_time=token.time
    home_agents_and_nextmoves=token.observations        # We observe the other team in the simulator.
    replan_count = 0
    complete_replan_required = False

    token.occupied_spacetime = set()
    token.occupied_spacetime_edges = set()
    token.occupied_partition_counter = OccupancyCounter()
    token.occupied_spacetime_wo_counted = set()

    for agent in token.agents:                          # Reset all flags
        agent.path_set=0                                # Flag for if this agent has been assigned a path or affirmed its existing path this loop.
        agent.gating_path_set=0 
        agent.earliest_timestep_invalidated=None 
        agent.latest_path_validated=None 

    for H_path in home_agents_and_nextmoves:           # Simple update to spacetime and edges. Counter is used for G agents only, gating removal is used for G agents only.
        token.occupied_spacetime.update(H_path)
        token.occupied_spacetime_wo_counted.update(H_path)
        token.occupied_spacetime_edges.add((H_path[0],H_path[1]))







    # 3. Accomodate Home and Non-negotiable Agents. (Accom H paths using non-gating G agents.)
    for H_path in home_agents_and_nextmoves:

        #print(f"Accomodating H Move: {H_path}")
        try:
            all_intraloop_helper_ids_paths_pathstates_accommodation = AccommodateHMove(H_path, dijkstras_map, partition_map, token, gates, guest_map)
        except PathUnfeasible:
            #print(f"X All Accommodation Paths COULDN'T be Calculated for the Home Agents")
            return None

        if all_intraloop_helper_ids_paths_pathstates_accommodation:
            for helper_agent_id, helper_agent_path, helper_agent_path_states in all_intraloop_helper_ids_paths_pathstates_accommodation:
                if len(helper_agent_path) > 1:
                    token = invalidate_paths_onwards(helper_agent_id, token, current_time)
                    token = assign_home_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                    token = update_occupied_spacetime_G1(token, helper_agent_path, partition_map, gates, guest_map)
                    #print(f"ℍ Intraloop Accommodation Helper Agent {helper_agent_id} will Help with Path: {token.agents[helper_agent_id-1].path}")
                    
        else:
            ##print(f"H Move: {H_path} doesn't need accommodation.")
            pass

        #print(f"✓ H Accommodation Completed.")
        #print()




    # 4. Check if any path just became invalid due to the non-negotiable moves: H moves, non-negotiable G moves accomodating the H moves
    for i in range(len(token.agents)):
        agent = token.agents[i]
        if agent.path_set==0 and agent.gating_path_set==0:

            path_valid, path_invalid_from_timestep = is_path_valid_with_timestep(agent, token)
            if path_valid==False:
                #print(f"Path {agent.path} for {agent.agent_type} Agent {agent.id} is invalid from timestep {path_invalid_from_timestep}")
                token = invalidate_paths_onwards(agent.id, token, path_invalid_from_timestep)






    # Occupancies are constructed from scratch every time.
    token_great_backup = copy.deepcopy(token)
    there_is_self_conflict = True

    while there_is_self_conflict:
        there_is_self_conflict=False

        token.occupied_spacetime = set()
        token.occupied_spacetime_edges = set()
        token.occupied_partition_counter = OccupancyCounter()
        token.occupied_spacetime_wo_counted = set()

        for H_path in home_agents_and_nextmoves:
            token.occupied_spacetime.update(H_path)
            token.occupied_spacetime_wo_counted.update(H_path)
            token.occupied_spacetime_edges.add((H_path[0],H_path[1]))

        for agent in token.agents:
            token = update_occupied_spacetime_G1(token, [(agent.location[0],agent.location[1],current_time)]+agent.path, partition_map, gates, guest_map)


        
        # 6. Plan paths for agents that are free with 
        # ZPG priority is maintained by planning and replanning in id order. (If planning assign tasks as a bonus)
        for agent in token.agents:
            planner_agent_id = agent.id

            if token.agents[planner_agent_id-1].path ==[]:  # Agent requires path planning. (Since it doesn't have a path, makes sense.)

                if complete_replan_required == True:
                    replan_count += 1

                if ((token.agents[planner_agent_id-1].state == 0 and token.unassigned_tasks) or token.agents[planner_agent_id-1].state != 0):      # Free Agent : Needs a Task and a Path or Replan Agent: Just needs a new path.
                    
                    token_backup=copy.deepcopy(token)

                    try:

                        if (token.agents[planner_agent_id-1].state == 0):   # Here for a task and a plan not replanning.
                            
                            #print()
                            #print(f"... Assigning Task to {agent.agent_type} Agent {planner_agent_id}")
                            best_task = closest_task(dijkstras_map, token.agents[planner_agent_id-1].location, token.unassigned_tasks)     # Find the Best Task to Assign
                            token.agents[planner_agent_id-1].assigned_task = best_task                                                     # Assign the best task to the agent
                            token.agents[planner_agent_id-1].task_assignment_time = current_time
                            token.unassigned_tasks.remove(best_task)                                            # Remove the task from unassigned_tasks
                            
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
                            path_start_to_pickup, path_states_start_to_pickup, all_helper_ids_paths_pathstates_pickup = PathPlannerG1(dijkstras_map, partition_map, border_map, agent, (token.agents[planner_agent_id-1].location[0],token.agents[planner_agent_id-1].location[1], current_time), token.agents[planner_agent_id-1].assigned_task.start, token, gates, guest_map)

                            # Assign Path to Planner Agent
                            token = update_occupied_spacetime_G1(token, path_start_to_pickup, partition_map, gates, guest_map)
                            token.agents[planner_agent_id-1].path.extend(path_start_to_pickup[1:])
                            token.agents[planner_agent_id-1].path_states.extend(path_states_start_to_pickup[1:])
                            #print(f"✓ Pickup Path Planned for Agent {planner_agent_id}:", path_start_to_pickup)
                            #print()

                            for helper_agent_id, helper_agent_path, helper_agent_path_states in all_helper_ids_paths_pathstates_pickup:
                                token = update_occupied_spacetime_G1(token, helper_agent_path, partition_map, gates, guest_map)
                                token = assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                                ##print(f"ℍ Interloop Pickup Helper Agent {helper_agent_id} will Gate/Switch with Path: {helper_agent_path}")
                            
                            #print()
                        else:
                            path_start_to_pickup=[(agent.location[0],agent.location[1],token.time)]

        

                    

                        # ---------------- DELIVERY INTER LOOP PLAN ----------------

                        #print(f"... Planning {agent.agent_type} Agent {planner_agent_id} Delivery")
                        path_pickupend_to_delivery, path_states_pickupend_to_delivery, all_helper_ids_paths_pathstates_delivery = PathPlannerG1(dijkstras_map, partition_map, border_map, agent, path_start_to_pickup[-1], token.agents[planner_agent_id-1].assigned_task.goal, token, gates, guest_map)

                        # Assign Path to Planner Agent
                        token = update_occupied_spacetime_G1(token, path_pickupend_to_delivery, partition_map, gates, guest_map)
                        token.agents[planner_agent_id-1].path.extend(path_pickupend_to_delivery[1:])
                        token.agents[planner_agent_id-1].path_states.extend(path_states_pickupend_to_delivery[1:])
                        #print(f"✓ Delivery Path Planned for Agent {planner_agent_id}:", path_pickupend_to_delivery)
                        #print()
        
                        for helper_agent_id, helper_agent_path, helper_agent_path_states in all_helper_ids_paths_pathstates_delivery:
                            token = update_occupied_spacetime_G1(token, helper_agent_path, partition_map, gates, guest_map)
                            token = assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                            ##print(f"ℍ Interloop Delivery Helper Agent {helper_agent_id} will Gate/Switch with Path: {helper_agent_path}")                              
                        #print()



                        complete_path = path_start_to_pickup[1:] + path_pickupend_to_delivery[1:]  # Exclude the duplicate midpoint
                        #print(f"✓ Complete Path Planned for {agent.agent_type} Agent {planner_agent_id}:", complete_path)





                    except PathUnfeasible:  # If a valid path doesn't exist, idle.
                        token = copy.deepcopy(token_backup)

                        token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1))
                        token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=current_time + 1, related_agent_ids=None))
                        token = update_occupied_spacetime_G1(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1)], partition_map, gates, guest_map)
                        #print(f"Agent {token.agents[planner_agent_id-1].id} will idle with path {token.agents[planner_agent_id-1].path} instead.")
                    



                else:
                    token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1))
                    token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Task Available", agent_role="Planner", time=current_time + 1, related_agent_ids=None))
                    token = update_occupied_spacetime_G1(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1)], partition_map, gates, guest_map)
                    #print(f"No Tasks, No Replanning Needed -> Agent {token.agents[planner_agent_id-1].id} idles with {token.agents[planner_agent_id-1].path}")



            else: # Not free with valid path.
                pass








        self_conflicting_agents = check_self_conflict(token, partition_map, guest_map)

        if self_conflicting_agents:
            there_is_self_conflict=True
            complete_replan_required = True
            #print("X There is Self Conflict")

            token = copy.deepcopy(token_great_backup)

            for self_conflicting_agent in self_conflicting_agents:
                if self_conflicting_agent.path_set == 0:

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

   




