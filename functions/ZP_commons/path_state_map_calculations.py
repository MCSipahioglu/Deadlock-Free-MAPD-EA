

from functions.classes import PathState

# Simple Calculations regarding a map, path or states.

def slice_path_per_partition(path_for_planning_agent, partition_map):
    # Initialize variables
    sliced_paths = []
    current_path = []
    previous_partition = None

    for (x, y, t) in path_for_planning_agent:
        # Get the current partition
        current_partition = partition_map[y][x]
        
        # If we have moved to a new partition and there is an existing path, add it to the result
        if previous_partition is not None and current_partition != previous_partition:
            sliced_paths.append(current_path)
            current_path = []

        # Add the current point to the current path
        current_path.append((x, y, t))
        previous_partition = current_partition

    # Don't forget to add the last accumulated path
    if current_path:
        sliced_paths.append(current_path)

    return sliced_paths



def create_big_map_with_just_the_partition(dijkstras_map, partition):
    # Create a copy of dijkstra_map with all zeros
    map_w_just_the_partitions = [[0 for _ in range(len(row))] for row in dijkstras_map]
    
    # Update the copied map based on partition_of_slice
    for (x, y) in partition:
        if 0 <= y < len(dijkstras_map) and 0 <= x < len(dijkstras_map[y]):
            map_w_just_the_partitions[y][x] = 1
    
    return map_w_just_the_partitions




def create_dijkstras_map_with_own_partition_and_goal(dijkstras_map, partition, goal):
    # Create a copy of dijkstra_map with all zeros
    dijkstrasmap_w_own_partition_and_goal = [[0 for _ in range(len(row))] for row in dijkstras_map]
    
    # Update the copied map based on partition_of_slice
    for (x, y) in partition:
        if 0 <= y < len(dijkstras_map) and 0 <= x < len(dijkstras_map[y]):
            dijkstrasmap_w_own_partition_and_goal[y][x] = dijkstras_map[y][x]
        
    dijkstrasmap_w_own_partition_and_goal[goal[1]][goal[0]] = dijkstras_map[goal[1]][goal[0]]
    
    return dijkstrasmap_w_own_partition_and_goal


def create_dijkstras_map_with_guest_map_and_parking(dijkstras_map, guest_map, park):
    # Create a copy of dijkstra_map with all zeros
    dijkstras_map_with_guest_map_and_parking = [[0 for _ in range(len(row))] for row in dijkstras_map]
    
    for y in range(len(guest_map)):
        for x in range(len(guest_map[y])):
            if guest_map[y][x] == 1:
                dijkstras_map_with_guest_map_and_parking[y][x] = dijkstras_map[y][x]
        
    dijkstras_map_with_guest_map_and_parking[park[1]][park[0]] = dijkstras_map[park[1]][park[0]]
    
    return dijkstras_map_with_guest_map_and_parking





def prune_idle_steps(path):
    if not path:
        return path
    
    # Start pruning from the end of the path
    pruned_path = path[:]
    
    while len(pruned_path) > 1 and (pruned_path[-1][0], pruned_path[-1][1]) == (pruned_path[-2][0], pruned_path[-2][1]):
        pruned_path.pop()

    return pruned_path













def calculate_path_states(path_for_helper_agent, planner_agent_id, helper_agent_id, planner_cell_before_switching, planner_cell_after_switching, is_gating):


    # Create dictionary to store planner path states keyed by time
    planner_path_states_gating_or_switching = {}

    if is_gating:       # Gating

        path_states_planner = [PathState() for _ in range(len(path_for_helper_agent)-1)]    # Last time step for the planner is not part of the gating
        path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

        at_the_gate = path_for_helper_agent[-4]
        one_move_back = path_for_helper_agent[-3]
        move_to_gate = path_for_helper_agent[-2]
        switching_move = path_for_helper_agent[-1]

        planner_gate = planner_cell_before_switching
        helper_gate = planner_cell_after_switching

        for i, path in enumerate(path_for_helper_agent):

            if path != switching_move:
                path_states_planner[i].time = path[2]
                path_states_planner[i].agent_role = "Planner"
                path_states_planner[i].related_agent_ids = [helper_agent_id]
                path_states_planner[i].gate_or_border_before = planner_gate
                path_states_planner[i].gate_or_border_after = helper_gate



            path_states_helper[i].time = path[2]
            path_states_helper[i].agent_role = "Helper"
            path_states_helper[i].related_agent_ids = [planner_agent_id]
            path_states_helper[i].gate_or_border_before = helper_gate
            path_states_helper[i].gate_or_border_after = planner_gate



            # Define states for specific path points
            if path == at_the_gate:
                path_states_planner[i].path_state = "Planner - At the Gate"
                path_states_helper[i].path_state  = "Helper - At the Gate"
                planner_path_states_gating_or_switching[path_states_planner[i].time] = path_states_planner[i]
            elif path == one_move_back:
                path_states_planner[i].path_state = "Planner - Gated to Other Partition"
                path_states_helper[i].path_state  = "Helper - Making One Move Back"
                planner_path_states_gating_or_switching[path_states_planner[i].time] = path_states_planner[i]
            elif path == move_to_gate:
                path_states_planner[i].path_state = "Planner - Moving Out of the Gate"
                path_states_helper[i].path_state  = "Helper - Moving to Gate"
                planner_path_states_gating_or_switching[path_states_planner[i].time] = path_states_planner[i]
            elif path == switching_move:
                path_states_helper[i].path_state  = "Helper - Gated to Other Partition"   # At this timestep, the planner is no longer in the gating state.
            else:
                path_states_planner[i].path_state = "Planner - Going to Gate"
                path_states_helper[i].path_state  = "Helper - Going to Gate"
                planner_path_states_gating_or_switching[path_states_planner[i].time] = path_states_planner[i]
                
            
            

    else:               # Switching

        path_states_planner = [PathState() for _ in range(len(path_for_helper_agent))]
        path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

        at_the_border = path_for_helper_agent[-2]
        switching_move = path_for_helper_agent[-1]

        planner_border_before = planner_cell_before_switching
        planner_border_after = planner_cell_after_switching
        helper_border_before = (path_for_helper_agent[-2][0],path_for_helper_agent[-2][1])
        helper_border_after = (path_for_helper_agent[-1][0],path_for_helper_agent[-1][1])

        for i, path in enumerate(path_for_helper_agent):

            path_states_planner[i].time = path[2]
            path_states_helper[i].time = path[2]

            path_states_planner[i].agent_role = "Planner"
            path_states_helper[i].agent_role = "Helper"

            path_states_planner[i].related_agent_ids = [helper_agent_id]
            path_states_helper[i].related_agent_ids = [planner_agent_id]

            path_states_planner[i].gate_or_border_before = planner_border_before
            path_states_helper[i].gate_or_border_before = helper_border_before

            path_states_planner[i].gate_or_border_after = planner_border_after
            path_states_helper[i].gate_or_border_after = helper_border_after


            # Define states for specific path points
            if path == at_the_border:
                path_states_planner[i].path_state = "Planner - At the Border"
                path_states_helper[i].path_state  = "Helper - At the Border"
            elif path == switching_move:
                path_states_planner[i].path_state = "Planner - Switched to Other Partition"
                path_states_helper[i].path_state  = "Helper - Switched to Other Partition"
            else:
                path_states_planner[i].path_state = "Planner - Going to Border"
                path_states_helper[i].path_state  = "Helper - Going to Border" 

            planner_path_states_gating_or_switching[path_states_planner[i].time] = path_states_planner[i]

    return planner_path_states_gating_or_switching, path_states_helper



def calculate_path_states_for_switching_helper(path_for_helper_agent, planner_agent_id, helper_agent_id, planner_cell_before_switching, planner_cell_after_switching, is_gating):


    if is_gating:       # Gating

        path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

        at_the_gate = path_for_helper_agent[-4]
        one_move_back = path_for_helper_agent[-3]
        move_to_gate = path_for_helper_agent[-2]
        switching_move = path_for_helper_agent[-1]

        planner_gate = planner_cell_before_switching
        helper_gate = planner_cell_after_switching

        for i, path in enumerate(path_for_helper_agent):



            path_states_helper[i].time = path[2]
            path_states_helper[i].agent_role = "Helper"
            path_states_helper[i].related_agent_ids = [planner_agent_id]
            path_states_helper[i].gate_or_border_before = helper_gate
            path_states_helper[i].gate_or_border_after = planner_gate



            # Define states for specific path points
            if path == at_the_gate:
                path_states_helper[i].path_state  = "Helper - At the Gate"
            elif path == one_move_back:
                path_states_helper[i].path_state  = "Helper - Making One Move Back"
            elif path == move_to_gate:
                path_states_helper[i].path_state  = "Helper - Moving to Gate"
            elif path == switching_move:
                path_states_helper[i].path_state  = "Helper - Gated to Other Partition"   # At this timestep, the planner is no longer in the gating state.
            else:
                path_states_helper[i].path_state  = "Helper - Going to Gate"

            
            

    else:               # Switching

        path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

        at_the_border = path_for_helper_agent[-2]
        switching_move = path_for_helper_agent[-1]

        helper_border_before = (path_for_helper_agent[-2][0],path_for_helper_agent[-2][1])
        helper_border_after = (path_for_helper_agent[-1][0],path_for_helper_agent[-1][1])

        for i, path in enumerate(path_for_helper_agent):

            path_states_helper[i].time = path[2]

            path_states_helper[i].agent_role = "Helper"

            path_states_helper[i].related_agent_ids = [planner_agent_id]

            path_states_helper[i].gate_or_border_before = helper_border_before

            path_states_helper[i].gate_or_border_after = helper_border_after


            # Define states for specific path points
            if path == at_the_border:
                path_states_helper[i].path_state  = "Helper - At the Border"
            elif path == switching_move:
                path_states_helper[i].path_state  = "Helper - Switched to Other Partition"
            else:
                path_states_helper[i].path_state  = "Helper - Going to Border" 

    return path_states_helper





def calculate_path_states_for_intraloop_helper(path_for_helper_agent, planner_agent_id):

    path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

    for i, path in enumerate(path_for_helper_agent):

        path_states_helper[i].time = path[2]

        path_states_helper[i].agent_role = "Helper"

        path_states_helper[i].path_state  = "Helper - Helping With Intraloop Movement"

        path_states_helper[i].related_agent_ids = [planner_agent_id]

        path_states_helper[i].gate_or_border_before = None

        path_states_helper[i].gate_or_border_after = None


    return path_states_helper


def calculate_path_states_for_accommodation_helper(path_for_helper_agent):

    path_states_helper = [PathState() for _ in range(len(path_for_helper_agent))]

    for i, path in enumerate(path_for_helper_agent):

        path_states_helper[i].time = path[2]

        path_states_helper[i].agent_role = "Helper"

        path_states_helper[i].path_state  = "Helper - Helping With H Accommodation"

        path_states_helper[i].related_agent_ids = []

        path_states_helper[i].gate_or_border_before = None

        path_states_helper[i].gate_or_border_after = None


    return path_states_helper

def append_related_helper_to_planner_path_state(token, planner_agent_id, helper_agent_id, helper_agent_path):

    # Find the horizon (last timestep) from helper_agent_path
    helper_agent_horizon = helper_agent_path[-1][2]

    # Search for the matching path state in the planner agent's path states
    for path_state in token.agents[planner_agent_id-1].path_states:
        if path_state.time == helper_agent_horizon:
            # Add the helper_agent_id to the related agent ids if it matches
            if path_state.related_agent_ids is None:
                path_state.related_agent_ids = [helper_agent_id]  # Initialize as a list
            else:
                path_state.related_agent_ids.append(helper_agent_id)  # Append helper_agent_id

            print(f"Added helper_agent_id {helper_agent_id} to planner agent's path state at time {helper_agent_horizon}")
            break  # Exit loop once a match is found
    
    return token





















    #planner_path_states_gating_or_switching, path_states_helper = calculate_path_states(path_for_helper_agent, current_agent.id, token.agents[first_problematic_agent[0]-1].id, (move_before_failure[0], move_before_failure[1]), (move_at_failure[0], move_at_failure[1]), solved_by_gating)
    #all_helper_ids_paths_pathstates.append((first_problematic_agent[0], path_for_helper_agent, path_states_helper))
    #all_planner_path_states_gating_or_switching.append(planner_path_states_gating_or_switching)




def calculate_compound_path_states_for_planner(planner_path, all_helper_ids_paths_pathstates):


    planner_path_states = [PathState() for _ in range(len(planner_path))]
    


    for i, path in enumerate(planner_path):
        path_time = path[2]
        planner_path_states[i].time = path_time
        planner_path_states[i].agent_role = "Planner"


        for helper_agent_id, _, helper_agent_path_states in all_helper_ids_paths_pathstates:
            for helper_agent_path_state in helper_agent_path_states:
                if helper_agent_path_state.time == path_time:


                    if helper_agent_path_state.path_state == "Helper - At the Gate":
                        planner_path_states[i].path_state = "Planner - At the Gate"
                        planner_path_states[i].gate_or_border_before = (path[0], path[1])
                        planner_path_states[i].gate_or_border_after = (planner_path[i+1][0], planner_path[i+1][1])
                        planner_path_states[i].related_agent_ids = [helper_agent_id]

                        planner_path_states[i+1].path_state = "Planner - Gated to Other Partition"
                        planner_path_states[i+1].gate_or_border_before = (path[0], path[1])
                        planner_path_states[i+1].gate_or_border_after = (planner_path[i+1][0], planner_path[i+1][1])
                        planner_path_states[i+1].related_agent_ids = [helper_agent_id]


                        planner_path_states[i+2].path_state = "Planner - Moving Out of the Gate"
                        planner_path_states[i+2].gate_or_border_before = (path[0], path[1])
                        planner_path_states[i+2].gate_or_border_after = (planner_path[i+1][0], planner_path[i+1][1])
                        planner_path_states[i+2].related_agent_ids = [helper_agent_id]
                        


                    elif helper_agent_path_state.path_state == "Helper - At the Border":
                        planner_path_states[i].path_state = "Planner - At the Border"
                        planner_path_states[i].gate_or_border_before = (path[0], path[1])
                        planner_path_states[i].gate_or_border_after = (planner_path[i+1][0], planner_path[i+1][1])
                        planner_path_states[i].related_agent_ids = [helper_agent_id]

                        planner_path_states[i+1].path_state = "Planner - Switched to Other Partition"
                        planner_path_states[i+1].gate_or_border_before = (path[0], path[1])
                        planner_path_states[i+1].gate_or_border_after = (planner_path[i+1][0], planner_path[i+1][1])
                        planner_path_states[i+1].related_agent_ids = [helper_agent_id]


    assign_going_to_gate=0
    assign_going_to_border=0
    helper_agent = []



    for i in range(len(planner_path_states) - 1, -1, -1):
        if planner_path_states[i].path_state == "Planner - At the Gate":
            assign_going_to_gate=1
            assign_going_to_border=0
            helper_agent = planner_path_states[i].related_agent_ids
            gate_before = (planner_path[i][0], planner_path[i][1])
            gate_after = (planner_path[i+1][0], planner_path[i+1][1])

        elif planner_path_states[i].path_state == "Planner - At the Border":
            assign_going_to_gate=0
            assign_going_to_border=1
            helper_agent = planner_path_states[i].related_agent_ids
            border_before = (planner_path[i][0], planner_path[i][1])
            border_after = (planner_path[i+1][0], planner_path[i+1][1])

        elif planner_path_states[i].path_state == None:

            if assign_going_to_gate==0 and assign_going_to_border==0:
                planner_path_states[i].path_state = "Planner - Executing Task"
            
            elif assign_going_to_border==1:
                planner_path_states[i].path_state = "Planner - Going to Border"
                planner_path_states[i].gate_or_border_before = border_before
                planner_path_states[i].gate_or_border_after = border_after
                planner_path_states[i].related_agent_ids = helper_agent
            
            elif assign_going_to_gate==1:
                planner_path_states[i].path_state = "Planner - Going to Gate"
                planner_path_states[i].gate_or_border_before = gate_before
                planner_path_states[i].gate_or_border_after = gate_after
                planner_path_states[i].related_agent_ids = helper_agent

             





    return planner_path_states




