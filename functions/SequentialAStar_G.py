

from collections import deque

import heapq
import copy
from functions.classes import Agent, Token, Node, Task, OccupancyCounter, PathUnfeasible, PathState

from functions.ZP_commons.tasks import closest_task
from functions.ZP_commons.a_star_algorithms import a_star_any_generator_NoPartitions, a_star_any
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_Simple
from functions.ZP_commons.planning import check_self_conflict_Simple
from functions.ZP_commons.H_accommodation import assign_home_helper_path
from functions.ZP_commons.path_state_map_calculations import prune_idle_steps, calculate_path_states_for_accommodation_helper
from functions.SequentialAStar_H import PathPlannerAStar
from functions.ZP_commons.existing_paths import invalidate_paths_onwards, is_path_valid_with_timestep
import threading
import time as realtime

# V2B: ZPG1 where Loop Limits = 1
# V2: with astar_any H accommodation
# V1: with manual H accommodation




# Global flag to track the timeout state
timed_out = [False]  # Using a list to pass by reference

# Function to interrupt after timeout


def group_2_away_agents(token,dijkstras_map):
    # Initialize group tracking
    agent_groups = {}  # Dictionary to hold the group ID for each agent
    current_group_id = 1  # Start group IDs from 1


    # Loop through each agent
    for i, agent_i in enumerate(token.agents):
        if i not in agent_groups:
            # If this agent has no group, assign a new group ID
            agent_groups[i] = current_group_id
            current_group_id += 1  # Prepare the next group ID
        
        # Check all other agents to see if they are within two moves
        for j, agent_j in enumerate(token.agents):
            if i != j:
                distance = dijkstras_map[agent_i.location[1]][agent_i.location[0]][agent_j.location[1]][agent_j.location[0]]
                if distance <= 2:
                    # If agent_j is within two moves of agent_i, assign them to the same group
                    if j in agent_groups:
                        # If agent_j already has a group, make agent_i's group match agent_j's
                        agent_groups[i] = agent_groups[j] = min(agent_groups[i], agent_groups[j])
                    else:
                        # If agent_j has no group, assign it the group of agent_i
                        agent_groups[j] = agent_groups[i]

    grouped_agents = {}
    for agent_index, group_id in agent_groups.items():
        agent = token.agents[agent_index]
        grouped_agents.setdefault(group_id, []).append((agent.id, (agent.location[0], agent.location[1], token.time)))

    # Display the groups
    groups = list(grouped_agents.values())  # Convert dictionary to a list of groups

     # Second pass: Merge groups that are within 2 moves of each other
    i = 0
    while i < len(groups):
        j = i + 1
        while j < len(groups):
            # Check if any agent in groups[i] is within 2 moves of any agent in groups[j]
            merge_needed = False
            for agent_i in groups[i]:
                for agent_j in groups[j]:
                    loc_i = agent_i[1][:2]  # (x, y) location of agent_i
                    loc_j = agent_j[1][:2]  # (x, y) location of agent_j
                    distance = dijkstras_map[loc_i[1]][loc_i[0]][loc_j[1]][loc_j[0]]
                    if distance <= 2:
                        merge_needed = True
                        break
                if merge_needed:
                    break
            
            if merge_needed:
                # Merge groups[j] into groups[i] and remove groups[j]
                groups[i].extend(groups[j])
                groups.pop(j)  # Remove the merged group
            else:
                j += 1  # Only move to the next group if no merge occurred

        i += 1  # Move to the next group

    return groups
    
    return groups


# Function to run with timeout, periodically checking for timeout flag
def run_with_timeout(target_function, timeout, *args):
    global timed_out  # Make sure we use the global timed_out variable

    # Reset the timeout flag before starting
    result = [None]
    timed_out[0] = False

    def target():
        result[0] = target_function(*args)

    def interrupt():
        print("Timeout reached, setting timed_out flag.")
        timed_out[0] = True
        target_thread.join()

    # Create a timer that will set the timed_out flag to True after 'timeout' seconds
    timer = threading.Timer(timeout, interrupt)
    timer.start()

    # Start the target function in a new thread
    target_thread = threading.Thread(target=target)
    target_thread.start()

    target_thread.join() 

    # If the function finished before timeout, cancel the timer
    if not timed_out[0]:
        timer.cancel()

    # Return the result and the timeout flag (False if it completed, True if timed out)
    return result[0]




# Backstepping Algorithm: Calculates a valid combination of paths for agents in 1 partition, that accomodates a priority path. (Instead of using the priority path, the priority path is aready amended to the token.occupied_spacetime and all paths are calculated until the horizon of the priority path)
def recursive_path_planning_NoPartitions(agent_index, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon):
    if timed_out[0]:  # If timeout occurred, exit early
        print(f"Function stopped due to timeout.")
        return None
        #raise PathUnfeasible("H Accommodation Took Too Long")
    
    if agent_index == len(other_agents_starts):
        # Base case: all agents have been processed
        return []

    start = other_agents_starts[agent_index]
    #print(f"Trying to Plan a Helper Path For Agent {other_agents_ids[agent_index]}, Starting From: {start}")
    #print(f"Occupied Spacetime {token.occupied_spacetime}")
    #print(f"Occupied Spacetime wo counted {token.occupied_spacetime_wo_counted}")


    
    # Backup the current state of the token. The token_backup is used to save the state of the token before trying a new path. This ensures that each trial starts with the token in the same state it was before the previous trial.
    token_backup = copy.deepcopy(token)

    
    for path in a_star_any_generator_NoPartitions(token_backup, start, big_map_with_just_the_partition, horizon):

        if path is not None:    # This agent has no valid paths, the responsibility is on the previous agent to change its path.
            #print(f"Trying Path {path} for Agent {other_agents_ids[agent_index]}")
            token = update_occupied_spacetime_Simple(token, path) # Update the token's occupied spacetime with the current path

            # Recur for the next agent
            result_paths = recursive_path_planning_NoPartitions(agent_index + 1, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon)
            
            if agent_index+1 != len(other_agents_starts):
                #print(f"The path returned by Agent {other_agents_ids[agent_index+1]} for trial is {result_paths}")
                pass



            if result_paths is not None:
                # If valid paths are found, return the current path along with the valid paths for subsequent agents
                return [path] + result_paths
            else:
                token = copy.deepcopy(token_backup) # Restore the token's state if the next agent couldn't find a path
        
        else:
            return None



def PathPlannerG_IntraLoop_NoPartitions(token, horizon, other_agents_and_starts, map):

    token_copy=copy.deepcopy(token) # token is passed by reference, don't change it when trying out paths.

    other_agents_ids=[]
    other_agents_starts=[]

    if other_agents_and_starts:
        for other_agent_and_start in other_agents_and_starts:
            other_agents_ids.append(other_agent_and_start[0])
            other_agents_starts.append(other_agent_and_start[1])


    # Start the recursive path planning for agents 1, 2, ..., n
    
    all_paths = recursive_path_planning_NoPartitions(0, token_copy, other_agents_ids, other_agents_starts, map, horizon)

    #all_paths = run_with_timeout( recursive_path_planning_NoPartitions, 30,       0, token_copy, other_agents_ids, other_agents_starts, map, horizon)
    
    #print(f"All paths is: {all_paths}")

    if all_paths:

        # Pruning increases efficiency in less congestion by not keeping helper agents occupied longer than needed.
        all_paths = [prune_idle_steps(path) for path in all_paths]
        # If you want to prune you need to remove the occupied spacetime, edge and counter too. Revert to a backup add in the occupied spacetime for the paths assigned.

        return all_paths


    else:
        #print(f"All helper paths couldn't be generated.")
        raise PathUnfeasible("H Moves Can't Be Accommodated")






# Plan accommodating moves for the G agents in the partition HMove is going to.
def AccommodateHMove_NoPartitions(horizon, dijkstras_map, token, G_group):

    all_helper_ids_paths_pathstates=[]

    planned_accommodation_paths=PathPlannerG_IntraLoop_NoPartitions(token, horizon, G_group, dijkstras_map)
    
    for i, (G_agent_id, _) in enumerate(G_group):

        path_for_helper_agent = planned_accommodation_paths[i]

        path_states_helper = calculate_path_states_for_accommodation_helper(path_for_helper_agent)

        all_helper_ids_paths_pathstates.append((G_agent_id, path_for_helper_agent, path_states_helper))

    #print(f"Agents ids {agents_we_will_get_muddy_with_ids}")
    #print(f"Planned Helper Paths {planned_helper_paths}")


    return all_helper_ids_paths_pathstates





def SAS_G(token, dijkstras_map):


    current_time=token.time
    home_agents_and_nextmoves=token.observations        # We observe the other team in the simulator.
    replan_count = 0
    complete_replan_required = False


    token.occupied_spacetime = set()
    token.occupied_spacetime_edges = set()
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
    #print(f"Accomodating H Moves Once")

    G_groups=group_2_away_agents(token,dijkstras_map)
    #for idx, group in enumerate(G_groups):
    #    print(f"Group {idx + 1}: {group}")

    for G_group in G_groups:

        try:
            all_intraloop_helper_ids_paths_pathstates_accommodation = AccommodateHMove_NoPartitions(current_time+1, dijkstras_map, token, G_group) #Calculate a set of paths once.
        except PathUnfeasible:
            return token, False
        
        #print(all_intraloop_helper_ids_paths_pathstates_accommodation)

        if all_intraloop_helper_ids_paths_pathstates_accommodation:
            for helper_agent_id, helper_agent_path, helper_agent_path_states in all_intraloop_helper_ids_paths_pathstates_accommodation:
                if len(helper_agent_path) > 1:
                    token = invalidate_paths_onwards(helper_agent_id, token, current_time)
                    token = assign_home_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states)
                    token = update_occupied_spacetime_Simple(token, helper_agent_path)
                    #print(f"ℍ Intraloop Accommodation Helper Agent {helper_agent_id} will Help with Path: {helper_agent_path}")
        #print(f"✓ H Accommodation Completed.")
        #print()





    # 4. Check if any path just became invalid due to the non-negotiable moves: H moves, non-negotiable G moves accomodating the H moves
    for i in range(len(token.agents)):
        agent = token.agents[i]
        if agent.path_set==0 and agent.gating_path_set==0:

            path_valid, path_invalid_from_timestep = is_path_valid_with_timestep(agent, token)
            
            if path_valid==False:
                #print(f"Path {agent.path} for agent {agent.id} is invalid")
                token = invalidate_paths_onwards(agent.id, token, path_invalid_from_timestep)


    #print(f"!!!Path: {token.agents[10-1].path}")

    
    # 6. Plan paths for agents that are free with 
    # ZPG priority is maintained by planning and replanning in id order. (If planning assign tasks as a bonus)

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
            token = update_occupied_spacetime_Simple(token, [(agent.location[0],agent.location[1],current_time)]+agent.path)
        
        


        for agent in token.agents:
            planner_agent_id = agent.id

            if token.agents[planner_agent_id-1].path ==[]:  # Agent requires path planning.

                if complete_replan_required == True:
                    replan_count += 1


                if ((token.agents[planner_agent_id-1].state == 0 and token.unassigned_tasks) or (token.agents[planner_agent_id-1].state != 0)):      # Free Agent : Needs a Task and a Path or Replan Agent: Just needs a new path.
                    
                    token_backup=copy.deepcopy(token)

                    try:

                        if (token.agents[planner_agent_id-1].state == 0):
                            #print()
                            #print(f"... Assigning Task to Agent {planner_agent_id}")
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
                        if token.agents[planner_agent_id-1].state ==1 or token.agents[planner_agent_id-1].state ==2: # State != 3
                            #print(f"... Planning Agent {planner_agent_id} Pickup")
                            path_start_to_pickup, path_states_start_to_pickup = PathPlannerAStar(dijkstras_map, agent, (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time), token.agents[planner_agent_id-1].assigned_task.start, token)

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
        







                        complete_path = path_start_to_pickup[1:] + path_pickupend_to_delivery[1:]  # Exclude the duplicate midpoint
                        #print(f"✓ Complete Path Planned for Agent {planner_agent_id}:", complete_path)





                    except PathUnfeasible:  # If a valid path doesn't exist, idle.
                        token = copy.deepcopy(token_backup)

                        token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1))
                        token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Valid Plan Possible", agent_role="Planner", time=current_time + 1, related_agent_ids=None))
                        token = update_occupied_spacetime_Simple(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1)])
                        
                        #print(f"Agent {token.agents[planner_agent_id-1].id} will idle with path {token.agents[planner_agent_id-1].path} instead.")
                    



                else:
                    token.agents[planner_agent_id-1].path.append((token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1))
                    token.agents[planner_agent_id-1].path_states.append(PathState(path_state="Idle - No Task Available", agent_role="Planner", time=current_time + 1, related_agent_ids=None))
                    token = update_occupied_spacetime_Simple(token, [(token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time), (token.agents[planner_agent_id-1].location[0], token.agents[planner_agent_id-1].location[1], current_time+1)])
                    #print(f"No Tasks, No Replanning Needed -> Agent {token.agents[planner_agent_id-1].id} idles with {token.agents[planner_agent_id-1].path}")



            else: # Not free with valid path.
                pass




        self_conflicting_agents = check_self_conflict_Simple(token.agents)

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

    return token, True

   




