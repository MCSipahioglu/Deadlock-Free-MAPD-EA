




from collections import deque
import copy
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_G1, update_occupied_spacetime_H
from functions.ZP_commons.planning import is_path_valid





def find_path_invalid_from_timestep_revised(agent, path_invalid_from_timestep):
    # Find a closer time before starting gating or switching if this timestep of path was invalid.

    path_states = agent.path_states
    if path_states == []:
        return path_invalid_from_timestep

    active_gating_states_planner = ["Planner - At the Gate", "Planner - Gated to Other Partition", "Planner - Moving Out of the Gate"]
    active_gating_states_helper = ["Helper - At the Gate", "Helper - Making One Move Back", "Helper - Moving to Gate", "Helper - Gated to Other Partition"]
    active_switching_states_planner = ["Planner - At the Border", "Planner - Switched to Other Partition"]
    active_switching_states_helper = ["Helper - At the Border", "Helper - Switched to Other Partition"]

    # Start at the timestep where the invalidation was detected
    

    trimmed_path_states = []
    for path_state in path_states:
        if path_state.time <= path_invalid_from_timestep:
            trimmed_path_states.append(path_state)

    last_related_agent_ids = trimmed_path_states[-1].related_agent_ids
    last_state = None


    for path_state in reversed(trimmed_path_states):

        if path_state.related_agent_ids != last_related_agent_ids:
            last_related_agent_ids = path_state.related_agent_ids
            if last_related_agent_ids is None:      # This timestep has no relation, return it.
                return path_state.time
            else:                                   # Last timestep had a relation and this one has a different one. Last one was the last invalid.
                return path_state.time+1
            
        else:

            if (last_state in active_gating_states_planner and last_state != "Planner - At the Gate") or (last_state in active_gating_states_helper and last_state != "Helper - At the Gate") or (last_state in active_switching_states_planner and last_state != "Planner - At the Border") or (last_state in active_switching_states_helper and last_state != "Helper - At the Border"):
                continue
            elif last_state == "Planner - At the Gate" and path_state.path_state != "Planner - Going to Gate":
                return path_state.time + 1
            elif last_state == "Helper - At the Gate" and path_state.path_state != "Helper - Going to Gate":
                return path_state.time + 1
            elif last_state == "Planner - At the Border" and path_state.path_state != "Planner - Going to Border":
                return path_state.time + 1
            elif last_state == "Helper - At the Border" and path_state.path_state != "Helper - Going to Border":
                return path_state.time + 1
            elif last_state == "Planner - Going to Gate" and path_state.path_state != "Planner - Going to Gate":
                return path_state.time + 1
            elif last_state == "Helper - Going to Gate" and path_state.path_state != "Helper - Going to Gate":
                return path_state.time + 1
            elif last_state == "Planner - Going to Border" and path_state.path_state != "Planner - Going to Border":
                return path_state.time + 1
            elif last_state == "Helper - Going to Border" and path_state.path_state != "Helper - Going to Border":
                return path_state.time + 1


            last_related_agent_ids = path_state.related_agent_ids

            if path_state.path_state in active_gating_states_planner:
                last_state = path_state.path_state
            elif path_state.path_state in active_gating_states_helper:
                last_state = path_state.path_state
            elif path_state.path_state in active_switching_states_planner:
                last_state = path_state.path_state
            elif path_state.path_state in active_switching_states_helper:
                last_state = path_state.path_state
            elif path_state.path_state == "Planner - Going to Gate" or path_state.path_state == "Planner - Going to Border" or path_state.path_state == "Helper - Going to Gate" or path_state.path_state == "Helper - Going to Border" :
                last_state = path_state.path_state
            elif path_state.related_agent_ids:
                print(f"{agent.agent_type} Agent {agent.id} has Path State {path_state.path_state} with related agents {path_state.related_agent_ids} which is illegal.")
                exit()

        
    return path_state.time





def is_path_valid_with_timestep(agent, token):
    path_valid=True
    path = agent.path

    for path_spacetime in path:
        if path_spacetime in token.occupied_spacetime:
            #print(path_spacetime)
            return False, find_path_invalid_from_timestep_revised(agent, path_spacetime[2])

    for i in range(len(path) - 1):
        path_spacetime_edge=(path[i], path[i + 1])
        if path_spacetime_edge in token.occupied_spacetime_edges:
            #print(path_spacetime_edge)
            return False, find_path_invalid_from_timestep_revised(agent, path[i + 1][2])

    return path_valid, None



    
def invalidate_paths_onwards(agent_id, token, invalidate_from_time):
    # Invalidate onwards from and including "invalidate_from_time"

    # Check if the agent's path has already been invalidated after or at the given timestep
    if token.agents[agent_id - 1].path_set == 1 or (token.agents[agent_id - 1].earliest_timestep_invalidated is not None and token.agents[agent_id - 1].earliest_timestep_invalidated <= invalidate_from_time):
        return token  # Exit if the agent's path has already been invalidated after or at this timestep.


    # Never invalidate from mid-gating.
    if token.agents[agent_id-1].latest_gating_path_set:
        invalidate_from_time = max(invalidate_from_time , token.agents[agent_id-1].latest_gating_path_set[2]+1)

    


    
    #print(f"Invalidating Agent {agent_id}'s Paths From Time={invalidate_from_time} Onwards")

    token.agents[agent_id - 1].earliest_timestep_invalidated = invalidate_from_time

    # Find the index in the path corresponding to invalidate_from_time
    path = token.agents[agent_id - 1].path

    # Trim the path from invalidate_from_time onwards
    trimmed_path = [p for p in path if p[2] < invalidate_from_time]
    token.agents[agent_id - 1].path = trimmed_path


    if token.agents[agent_id - 1].path == [] and token.agents[agent_id - 1].state == 5:
        token.agents[agent_id - 1].state = 0

    

    path_states = token.agents[agent_id - 1].path_states

    # Prepare to invalidate path states
    path_states_to_flush = []
    trimmed_path_states = []

    for path_state in path_states:
        if path_state.time < invalidate_from_time:
            trimmed_path_states.append(path_state)
        else:
            path_states_to_flush.append(path_state)
            
    # Update the agent's path_states to keep only the valid ones
    token.agents[agent_id - 1].path_states = trimmed_path_states    


    # Recursively invalidate related agents from the point they were first involved
    for path_state in path_states_to_flush:
        if path_state.related_agent_ids:
            for related_agent_id in path_state.related_agent_ids:
                token = invalidate_paths_onwards(related_agent_id, token, find_path_invalid_from_timestep_revised(token.agents[related_agent_id - 1], path_state.time))

                


    
    return token



def slice_agent_path_from_until(agent, slicing_begin, slicing_horizon):
    #None her path yeni bir slice olmalı

    path = []
    path_states = []



    for j, agent_path_state in enumerate(agent.path_states):
        if slicing_begin < agent_path_state.time <= slicing_horizon:
            path.append(agent.path[j])
            path_states.append(agent_path_state)

    if path == []:
        return [], [], []

    active_gating_states_planner = ["Planner - Going to Gate", "Planner - At the Gate", "Planner - Gated to Other Partition", "Planner - Moving Out of the Gate"]
    active_gating_states_helper = ["Helper - Going to Gate", "Helper - At the Gate", "Helper - Making One Move Back", "Helper - Moving to Gate", "Helper - Gated to Other Partition"]
    active_switching_states_planner = ["Planner - Going to Border", "Planner - At the Border", "Planner - Switched to Other Partition"]
    active_switching_states_helper = ["Helper - Going to Border", "Helper - At the Border", "Helper - Switched to Other Partition"]


    last_related_agent_ids = path_states[0].related_agent_ids  # Start with the first related agent ID
    last_state = path_states[0].path_state  # Start with the first state
    last_slice_index = 0


    sliced_path = []
    sliced_path_states = []
    related_agents_per_slice = []

    for i, path_state in enumerate(path_states):
        if i > 0 and (path_state.related_agent_ids != last_related_agent_ids or \
                        last_state in ["Planner - Moving Out of the Gate", "Helper - Gated to Other Partition", "Planner - Switched to Other Partition", "Helper - Switched to Other Partition"]):
            # Append the current slice if there's a change
            sliced_path.append(path[last_slice_index:i])
            sliced_path_states.append(path_states[last_slice_index:i])
            related_agents_per_slice.append(last_related_agent_ids)
            last_slice_index = i

        last_related_agent_ids = path_state.related_agent_ids
        last_state = path_state.path_state

    # Append the final slice if there are any remaining path elements
    if last_slice_index < len(path):
        sliced_path.append(path[last_slice_index:])
        sliced_path_states.append(path_states[last_slice_index:])
        related_agents_per_slice.append(last_related_agent_ids)

    return sliced_path, sliced_path_states, related_agents_per_slice









# For aborting gating

def breadth_first_search_with_zero_cost(start, goal, dijkstras_map, zero_cost_coords):
    # Two queues: one for zero-cost paths (explored first), one for regular paths
    zero_cost_queue = deque([(start, [start], 0)])  # (current_position, path, zero_cost_count)
    regular_queue = deque()
    visited = set()  # To keep track of visited nodes

    while zero_cost_queue or regular_queue:
        # Prioritize zero-cost queue
        if zero_cost_queue:
            current, path, zero_cost_count = zero_cost_queue.popleft()
        else:
            current, path, zero_cost_count = regular_queue.popleft()

        x, y = current

        # Check if we have reached the goal
        if current == goal:
            return path, zero_cost_count  # Return the path and zero-cost cell count if goal is reached

        # Mark the current position as visited
        visited.add(current)

        # Explore neighboring cells (up, down, left, right)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x + dx, y + dy)

            # Check if neighbor is within bounds, traversable, and not visited
            if (0 <= neighbor[0] < len(dijkstras_map[0]) and
                0 <= neighbor[1] < len(dijkstras_map) and
                dijkstras_map[neighbor[1]][neighbor[0]] != 0 and  # Not a wall
                neighbor not in visited):  # Not already visited
                
                # If the neighbor is a zero-cost coordinate, add it to the zero-cost queue
                if neighbor in zero_cost_coords:
                    zero_cost_queue.append((neighbor, path + [neighbor], zero_cost_count + 1))  # Increment zero-cost count
                else:
                    # Add the neighbor and the path to the regular queue (with depth increment, but same zero-cost count)
                    regular_queue.append((neighbor, path + [neighbor], zero_cost_count))

    return None, 0  # Return None if no path is found and zero-cost count as 0




def calculate_minimum_effective_distance(gate, home_agents_and_nextmoves, guest_agents, partition, dijkstras_map):

    minimum_effective_distance=float('inf')
    path_of_danger = []
    guest_agents_in_partitions_locations = []
    for guest_agent in guest_agents:
        if guest_agent.location in partition:
            guest_agents_in_partitions_locations.append(guest_agent.location)
    

    for H_path in home_agents_and_nextmoves:
        home_agent_location = (H_path[0][0], H_path[0][1])
        home_agent_next_location = (H_path[1][0], H_path[1][1])
        
        path_from_home_to_gate, num_guest_agents_on_path = breadth_first_search_with_zero_cost(home_agent_location, gate, dijkstras_map, guest_agents_in_partitions_locations)

        # Length of path to the gate
        length_of_path = len(path_from_home_to_gate)

        # Determine if the home agent is idling or moving
        is_home_agent_idling = home_agent_location == home_agent_next_location

        effective_distance = length_of_path - num_guest_agents_on_path + (1 if is_home_agent_idling else 0)

        if effective_distance < minimum_effective_distance:
            minimum_effective_distance = effective_distance
            path_of_danger = path_from_home_to_gate  # Store the path as the most affected path


    return minimum_effective_distance, path_of_danger



























































def validate_and_set_paths_G1(primary_agent, first_agent_id, cascade_parent_id, token, partition_map, gates, guest_map, token_right_preservation, process_path_until):

    last_valid_time = max(token.time, primary_agent.latest_path_validated[2]) if primary_agent.latest_path_validated else token.time
    last_valid_location = (primary_agent.location[0], primary_agent.location[1], token.time) if last_valid_time == token.time else primary_agent.latest_path_validated

    primary_agent_path_slices, primary_agent_path_states_slices, primary_agent_related_agent_ids_per_slices = slice_agent_path_from_until(primary_agent, last_valid_time, process_path_until)

    #print(primary_agent_path_slices)
    #print(primary_agent_related_agent_ids_per_slices)

    path_valid = True  # Track if the current primary agent's slices are valid
    exit_cascade = False

    for (primary_agent_path_slice, primary_agent_related_agent_ids_per_slice) in zip(primary_agent_path_slices, primary_agent_related_agent_ids_per_slices):
        
        token_backup = copy.deepcopy(token)
        token_right_preservation_backup = copy.deepcopy(token_right_preservation)

        extended_primary_path_slice = [last_valid_location] + primary_agent_path_slice
        

        # For the first slice, check validity from the beginning
        if is_path_valid(extended_primary_path_slice, token_right_preservation):
            
            token = update_occupied_spacetime_G1(token, extended_primary_path_slice, partition_map, gates, guest_map)
            token_right_preservation = update_occupied_spacetime_G1(token_right_preservation, extended_primary_path_slice, partition_map, gates, guest_map)
            
            if primary_agent_related_agent_ids_per_slice:
                for related_agent_id in primary_agent_related_agent_ids_per_slice:
                    if related_agent_id != cascade_parent_id:
                        related_agent = token.agents[related_agent_id-1]
                        token, token_right_preservation, exit_cascade, exiting_agent_and_time = validate_and_set_paths_G1(related_agent, first_agent_id, primary_agent.id, token, partition_map, gates, guest_map, token_right_preservation, primary_agent_path_slice[-1][2])
                        if exit_cascade == True and primary_agent.id != first_agent_id:
                            return None, None, exit_cascade, exiting_agent_and_time
                        elif exit_cascade == True and primary_agent.id == first_agent_id:
                            break

                if exit_cascade == True and primary_agent.id == first_agent_id:
                    break    
                
            last_valid_time = primary_agent_path_slice[-1][2]
            last_valid_location = primary_agent_path_slice[-1]
            token.agents[primary_agent.id-1].latest_path_validated = last_valid_location
            print(f"{primary_agent.agent_type} Agent {primary_agent.id} path until {last_valid_location} is validated.")
        
        else:
            path_valid = False
            break

    
    
    # If path slice is invalid cascade all the way back to the initial agent. Invalidation should start from here.
    if path_valid == False:

        print(f"Agent {primary_agent.id} has invalid path slice {primary_agent_path_slice} with related {primary_agent_related_agent_ids_per_slice} cascading up for invalidation.")

        exit_cascade = True
        exiting_agent_and_time = (primary_agent.id, last_valid_time+1)
        if primary_agent.id != first_agent_id:
            return None, None, exit_cascade, exiting_agent_and_time
    


    # Only for the returning of the initial agent via a cascade exit.
    if exit_cascade == True and primary_agent.id == first_agent_id:     
        
        # Revert the tokens to the point however many slices were able to be validated.

        token_right_preservation = copy.deepcopy(token_right_preservation_backup)
        token = copy.deepcopy(token_backup)
        token = invalidate_paths_onwards(exiting_agent_and_time[0], token, exiting_agent_and_time[1])
        for agent in token.agents:
            if agent.path == []:
                token_right_preservation = update_occupied_spacetime_G1(token_right_preservation, [(token.agents[agent.id-1].location[0], token.agents[agent.id-1].location[1], token.time), (token.agents[agent.id-1].location[0], token.agents[agent.id-1].location[1], token.time+1)], partition_map, gates, guest_map)


        return token, token_right_preservation, None, None
    


    # If paths are valid and no exit was triggered, return the original token and preserved state
    return token, token_right_preservation, exit_cascade, None








def validate_and_set_paths_H(primary_agent, first_agent_id, cascade_parent_id, token, partition_map, gates, guest_map, token_right_preservation, process_path_until):

    last_valid_time = max(token.time, primary_agent.latest_path_validated[2]) if primary_agent.latest_path_validated else token.time
    last_valid_location = (primary_agent.location[0], primary_agent.location[1], token.time) if last_valid_time == token.time else primary_agent.latest_path_validated

    primary_agent_path_slices, primary_agent_path_states_slices, primary_agent_related_agent_ids_per_slices = slice_agent_path_from_until(primary_agent, last_valid_time, process_path_until)

    #print(primary_agent_path_slices)
    #print(primary_agent_related_agent_ids_per_slices)

    path_valid = True  # Track if the current primary agent's slices are valid
    exit_cascade = False

    for (primary_agent_path_slice, primary_agent_related_agent_ids_per_slice) in zip(primary_agent_path_slices, primary_agent_related_agent_ids_per_slices):
        
        token_backup = copy.deepcopy(token)
        token_right_preservation_backup = copy.deepcopy(token_right_preservation)

        extended_primary_path_slice = [last_valid_location] + primary_agent_path_slice
        

        # For the first slice, check validity from the beginning
        if is_path_valid(extended_primary_path_slice, token_right_preservation):
            
            token = update_occupied_spacetime_H(token, extended_primary_path_slice, partition_map, gates, guest_map)
            token_right_preservation = update_occupied_spacetime_H(token_right_preservation, extended_primary_path_slice, partition_map, gates, guest_map)
            
            if primary_agent_related_agent_ids_per_slice:
                for related_agent_id in primary_agent_related_agent_ids_per_slice:
                    if related_agent_id != cascade_parent_id:
                        related_agent = token.agents[related_agent_id-1]
                        token, token_right_preservation, exit_cascade, exiting_agent_and_time = validate_and_set_paths_H(related_agent, first_agent_id, primary_agent.id, token, partition_map, gates, guest_map, token_right_preservation, primary_agent_path_slice[-1][2])
                        if exit_cascade == True and primary_agent.id != first_agent_id:
                            return None, None, exit_cascade, exiting_agent_and_time
                        elif exit_cascade == True and primary_agent.id == first_agent_id:
                            break

                if exit_cascade == True and primary_agent.id == first_agent_id:
                    break    
                
            last_valid_time = primary_agent_path_slice[-1][2]
            last_valid_location = primary_agent_path_slice[-1]
            token.agents[primary_agent.id-1].latest_path_validated = last_valid_location
            print(f"{primary_agent.agent_type} Agent {primary_agent.id} path until {last_valid_location} is validated.")
        
        else:
            path_valid = False
            break

    
    
    # If path slice is invalid cascade all the way back to the initial agent. Invalidation should start from here.
    if path_valid == False:

        print(f"Agent {primary_agent.id} has invalid path slice {primary_agent_path_slice} with related {primary_agent_related_agent_ids_per_slice} cascading up for invalidation.")

        exit_cascade = True
        exiting_agent_and_time = (primary_agent.id, last_valid_time+1)
        if primary_agent.id != first_agent_id:
            return None, None, exit_cascade, exiting_agent_and_time
    


    # Only for the returning of the initial agent via a cascade exit.
    if exit_cascade == True and primary_agent.id == first_agent_id:     
        
        # Revert the tokens to the point however many slices were able to be validated.

        token_right_preservation = copy.deepcopy(token_right_preservation_backup)
        token = copy.deepcopy(token_backup)
        token = invalidate_paths_onwards(exiting_agent_and_time[0], token, exiting_agent_and_time[1])

        for agent in token.agents:
            if agent.path == []:
                token_right_preservation = update_occupied_spacetime_H(token_right_preservation, [(token.agents[agent.id-1].location[0], token.agents[agent.id-1].location[1], token.time), (token.agents[agent.id-1].location[0], token.agents[agent.id-1].location[1], token.time+1)], partition_map, gates, guest_map)

        return token, token_right_preservation, None, None
    


    # If paths are valid and no exit was triggered, return the original token and preserved state
    return token, token_right_preservation, exit_cascade, None


