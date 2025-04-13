from functions.classes import Node
from functions.ZP_commons.a_star_algorithms import a_star_algorithm
from functions.ZP_commons.occupied_spacetime import update_partition_occupancy
import copy
from functions.ZP_commons.path_state_map_calculations import create_dijkstras_map_with_own_partition_and_goal

# Returns the agents with closer horizons than planner_path
def get_agents_we_are_planning_into_the_future_of(token, current_agent_id, planner_path):    
    current_time = token.time
    
    # Extract planner path horizon
    _, _, planner_path_horizon = planner_path[-1]

    # Initialize list to store agents we are planning into the future of
    agents_we_are_planning_into_the_future_of = []

    # Loop through all agents
    for agent in token.agents:
        if agent.id != current_agent_id:  # Skip the current agent
            # Determine the last node in the agent's helper path or normal path
            #print(f"Agent {agent.id} Path is {agent.path}")
            if agent.path:
                other_agent_path_end_spacetime = agent.path[-1]  # Normal path
            else:
                # If the agent has no path, use their current location and time
                other_agent_path_end_spacetime = (agent.location[0], agent.location[1], current_time)

            # Extract the horizon of the existing path
            _, _, other_agent_path_horizon = other_agent_path_end_spacetime

            # Check if the tentative path horizon exceeds the agent's path horizon
            if planner_path_horizon > other_agent_path_horizon:
                # Add agent ID and their current path end to the list
                agents_we_are_planning_into_the_future_of.append((agent.id, other_agent_path_end_spacetime))
    
    return agents_we_are_planning_into_the_future_of




# Returns the first agent we assume will be idling and we will be entering to the same partition with.
def find_first_problematic_agent_ZPH(planner_path, agents_we_are_planning_into_the_future_of, partition_map, guest_map):
    problem_found = False
    first_problematic_agent = None
    first_problematic_timestep = None
    first_problematic_planner_path_index = None
    minimum_horizon = float('inf')

    # Loop through the tentative path
    for i, planner_path_spacetime in enumerate(planner_path):
        planner_path_horizon = planner_path_spacetime[2]

        # Check each agent we are planning into the future of
        for agent_we_are_planning_into_the_future_of in agents_we_are_planning_into_the_future_of:
            _, _, agent_we_are_planning_into_the_future_of_horizon = agent_we_are_planning_into_the_future_of[1]

            # If the tentative path time exceeds the agent's horizon
            if planner_path_horizon > agent_we_are_planning_into_the_future_of_horizon:
                # Check if they are in the same loop partition (which indicates a problem)
                if guest_map[planner_path_spacetime[1]][planner_path_spacetime[0]]==1:      # In the loops (i.e. agent count limited)
                    if partition_map[planner_path_spacetime[1]][planner_path_spacetime[0]] == partition_map[agent_we_are_planning_into_the_future_of[1][1]][agent_we_are_planning_into_the_future_of[1][0]]:

                        # Tie-breaker for multiple other agents that have different horizons but will be detected at the same time since we loop through planner_path.
                        if agent_we_are_planning_into_the_future_of_horizon < minimum_horizon:
                            minimum_horizon = agent_we_are_planning_into_the_future_of_horizon
                            first_problematic_agent = agent_we_are_planning_into_the_future_of
                            first_problematic_timestep = planner_path_spacetime[-1]
                            first_problematic_planner_path_index = i
                            problem_found = True

        if problem_found:
           #print(f"We First See a Problem at Time {first_problematic_timestep} with Agent {first_problematic_agent} with Horizon {minimum_horizon}")
           return problem_found, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index                 

    
                        
    return problem_found, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index




def find_first_problematic_timestep_ZPG(planner_path, agents_we_are_planning_into_the_future_of, last_time_step_resolved, occupied_partition_counter, partition_map, gates, guest_map):
    problem_found = False
    first_problematic_timestep = None
    first_problematic_planner_path_index = None

    # Calculate the expected occupancy map. (Assuming everybody will stay in place after their plans end.) (Including the tentative path bcs working at the limit is ok, exceeding it is the problem.)
    _,_,planner_path_horizon=planner_path[-1]
    tentative_occupied_partition_counter = copy.deepcopy(occupied_partition_counter)    # Counter coming from planned paths.
    tentative_occupied_partition_counter=update_partition_occupancy(tentative_occupied_partition_counter, planner_path[1:], partition_map, guest_map)

    for agent_id, last_cell in agents_we_are_planning_into_the_future_of:
        x, y, t = last_cell  # Unpack the last known cell (x, y, t)
        other_agents_assumed_future_path = []

        # Construct the path until the time horizon
        for future_time in range(t + 1, t + planner_path_horizon + 1):
            other_agents_assumed_future_path.append((x, y, future_time))

        #print(f"Agent {agent_id}'s Assumed Future Path: {other_agents_assumed_future_path}")
        tentative_occupied_partition_counter=update_partition_occupancy(tentative_occupied_partition_counter, other_agents_assumed_future_path, partition_map, guest_map)
    #print(f"Assumed Future Partition Occupancy Counter: {tentative_occupied_partition_counter}")   #Doesn't include planner_path.




    # Find the first partition and time we are going to violate the agent limits of.
    for i, planner_path_spacetime in enumerate(planner_path):
        planner_path_x, planner_path_y, planner_path_time = planner_path_spacetime
        planner_path_partition_cells = partition_map[planner_path_y][planner_path_x]
        planner_path_occupied_partition_counter_index = (planner_path_partition_cells, planner_path_time)

        if planner_path_time>=last_time_step_resolved:  # Never mind the first hit. (If a interloop routing was solved by gating once for this path already, we want to avoid seeing an occupancy problem due to gating here.)
            if planner_path_occupied_partition_counter_index in tentative_occupied_partition_counter:

                # Check if any gates are present only once
                is_gated = any(((gate_x1, gate_y1) in planner_path_partition_cells) or ((gate_x2, gate_y2) in planner_path_partition_cells) 
                            for (gate_x1, gate_y1), (gate_x2, gate_y2) in gates)

                # Agent limit is N-1 if not gated, N-2 if gated
                planner_path_loop_agent_limit = len(planner_path_partition_cells) - 2 if is_gated else len(planner_path_partition_cells) - 1

                if tentative_occupied_partition_counter[planner_path_occupied_partition_counter_index] > planner_path_loop_agent_limit:
                    #print(f"We First See a Occupancy Counter Problem at Time {planner_path_time} in Partition {planner_path_occupied_partition_counter_index} Because {tentative_occupied_partition_counter[planner_path_occupied_partition_counter_index]} is bigger than Limit {planner_path_loop_agent_limit}")
                    first_problematic_timestep = planner_path_time
                    first_problematic_planner_path_index = i
                    problem_found=True
                    break

    return problem_found, first_problematic_timestep, first_problematic_planner_path_index



def find_first_problematic_timestep_ZPG_Limit1(planner_path, agents_we_are_planning_into_the_future_of, last_time_step_resolved, occupied_partition_counter, partition_map, gates, guest_map):
    problem_found = False
    first_problematic_timestep = None
    first_problematic_planner_path_index = None

    # Calculate the expected occupancy map. (Assuming everybody will stay in place after their plans end.) (Including the tentative path bcs working at the limit is ok, exceeding it is the problem.)
    _,_,planner_path_horizon=planner_path[-1]
    tentative_occupied_partition_counter = copy.deepcopy(occupied_partition_counter)    # Counter coming from planned paths.
    tentative_occupied_partition_counter=update_partition_occupancy(tentative_occupied_partition_counter, planner_path[1:], partition_map, guest_map)

    for agent_id, last_cell in agents_we_are_planning_into_the_future_of:
        x, y, t = last_cell  # Unpack the last known cell (x, y, t)
        other_agents_assumed_future_path = []

        # Construct the path until the time horizon
        for future_time in range(t + 1, t + planner_path_horizon + 1):
            other_agents_assumed_future_path.append((x, y, future_time))

        #print(f"Agent {agent_id}'s Assumed Future Path: {other_agents_assumed_future_path}")
        tentative_occupied_partition_counter=update_partition_occupancy(tentative_occupied_partition_counter, other_agents_assumed_future_path, partition_map, guest_map)
    #print(f"Assumed Future Partition Occupancy Counter: {tentative_occupied_partition_counter}")   #Doesn't include planner_path.




    # Find the first partition and time we are going to violate the agent limits of.
    for i, planner_path_spacetime in enumerate(planner_path):
        planner_path_x, planner_path_y, planner_path_time = planner_path_spacetime
        planner_path_partition_cells = partition_map[planner_path_y][planner_path_x]
        planner_path_occupied_partition_counter_index = (planner_path_partition_cells, planner_path_time)

        if planner_path_time>=last_time_step_resolved:  # Never mind the first hit. (If a interloop routing was solved by gating once for this path already, we want to avoid seeing an occupancy problem due to gating here.)
            if planner_path_occupied_partition_counter_index in tentative_occupied_partition_counter:

                # Check if any gates are present only once
                is_gated = any(((gate_x1, gate_y1) in planner_path_partition_cells) or ((gate_x2, gate_y2) in planner_path_partition_cells) 
                            for (gate_x1, gate_y1), (gate_x2, gate_y2) in gates)

                # Agent limit is N-1 if not gated, N-2 if gated
                #planner_path_loop_agent_limit = len(planner_path_partition_cells) - 2 if is_gated else len(planner_path_partition_cells) - 1
                planner_path_loop_agent_limit=1

                if tentative_occupied_partition_counter[planner_path_occupied_partition_counter_index] > planner_path_loop_agent_limit:
                    #print(f"We First See a Occupancy Counter Problem at Time {planner_path_time} in Partition {planner_path_occupied_partition_counter_index} Because {tentative_occupied_partition_counter[planner_path_occupied_partition_counter_index]} is bigger than Limit {planner_path_loop_agent_limit}")
                    first_problematic_timestep = planner_path_time
                    first_problematic_planner_path_index = i
                    problem_found=True
                    break

    return problem_found, first_problematic_timestep, first_problematic_planner_path_index





# Is a path using occupied spacetime or occupied edges?
def is_path_valid(path, token):
    path_valid=True

    for path_spacetime in path:
        if path_spacetime in token.occupied_spacetime:
            #print(path_spacetime)
            path_valid=False

    for i in range(len(path) - 1):
        path_spacetime_edge=(path[i], path[i + 1])
        if path_spacetime_edge in token.occupied_spacetime_edges:
            #print(path_spacetime_edge)
            path_valid=False

    return path_valid















def introduce_delays_before_switching(path, switching_timestep):
    # Takes a path. Idles at the second to last position until target_timestep. Moves to the last position at target_timestep.

    switching_move = path[-1]
    last_move_time = switching_move[2]
    
    path_with_delays=path[:-1]   # Go to the border.

    # Append idle steps at the same location until the target timestep is reached
    while path_with_delays[-1][2] < switching_timestep - 1:
        path_with_delays.append((path[-2][0], path[-2][1], last_move_time))
        last_move_time += 1

    # Append the final move at the exact time step
    path_with_delays.append((switching_move[0], switching_move[1], last_move_time))
    
    return path_with_delays


    

# Calculates a Gating Sequence for an Helper Agent at the right timesteps
def calculate_helper_gating_sequence(planner_path, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index, move_before_failure, move_at_failure, my_loop_after_the_failure, token, dijkstras_map):
    helper_path_found=False
    fixed_planner_path=[]

    # Find the other side of the gate the other agent must route to.
    gate_planner_side = (move_before_failure[0], move_before_failure[1])
    gate_helper_side = (move_at_failure[0], move_at_failure[1])
    distance_helper_to_helper_gate = dijkstras_map[first_problematic_agent[1][1]][first_problematic_agent[1][0]][gate_helper_side[1]][gate_helper_side[0]]
    earliest_timestep_helper_can_get_to_its_gate = first_problematic_agent[1][2] + distance_helper_to_helper_gate

    # For switching the helper must only use its own partition + the goal position.
    dijkstrasmap_w_own_partition_and_goal = create_dijkstras_map_with_own_partition_and_goal(dijkstras_map, my_loop_after_the_failure, gate_helper_side)

    #print(f"Earliest Timestep Helper Agent {first_problematic_agent[0]} can get to Helper Gate {gate_helper_side} is: {earliest_timestep_helper_can_get_to_its_gate}")


    # Plan for the helper agent to first come to the gate.
    path_to_gate_for_helper_agent = a_star_algorithm(token, first_problematic_agent[1], Node((gate_helper_side[0], gate_helper_side[1], float('inf'))), dijkstrasmap_w_own_partition_and_goal)
    if path_to_gate_for_helper_agent is None:
        return helper_path_found, None, None

    _, _, time_of_helper_at_gate = path_to_gate_for_helper_agent[-1]

    cells_around_helper_gate_planner_wont_go_to = []
    for cell in my_loop_after_the_failure:
        if (dijkstras_map[cell[1]][cell[0]][gate_helper_side[1]][gate_helper_side[0]] == 1):

            if (first_problematic_planner_path_index + 1) < len(planner_path):      # If planner not planning on staying at the gate
                if cell != (planner_path[first_problematic_planner_path_index + 1][0], planner_path[first_problematic_planner_path_index + 1][1]):
                    cells_around_helper_gate_planner_wont_go_to.append(cell)
            else:
                cells_around_helper_gate_planner_wont_go_to.append(cell)
            
    #print(f"Cells Around Helper Gate {gate_helper_side}, Helper Agent {first_problematic_agent[0]} can go to: {cells_around_helper_gate_planner_wont_go_to}")




    # Try each cell around the gate that I won't go to
    for cell_around_helper_gate_planner_wont_go_to in cells_around_helper_gate_planner_wont_go_to:


        # I will have to wait for the helper to come to its gate to switch first
        if earliest_timestep_helper_can_get_to_its_gate > first_problematic_timestep - 1:
            one_move_back = (cell_around_helper_gate_planner_wont_go_to[0], cell_around_helper_gate_planner_wont_go_to[1], time_of_helper_at_gate + 1)
            move_to_gate = (gate_helper_side[0], gate_helper_side[1], time_of_helper_at_gate + 2)
            switching_move = (gate_planner_side[0], gate_planner_side[1], time_of_helper_at_gate + 3)

            path_for_helper_agent = path_to_gate_for_helper_agent + [one_move_back, move_to_gate, switching_move]

            #print(f"Tentative Helper Path - Quick: {path_for_helper_agent}")

            if is_path_valid(path_for_helper_agent[1:], token):
                helper_path_found = True
                fixed_planner_path = introduce_delays_before_switching(planner_path[:first_problematic_planner_path_index+1], path_for_helper_agent[-3][2])
                if (planner_path[first_problematic_planner_path_index+1][0],planner_path[first_problematic_planner_path_index+1][1]) != (move_at_failure[0], move_at_failure[1]):
                    fixed_planner_path.append((planner_path[first_problematic_planner_path_index+1][0],planner_path[first_problematic_planner_path_index+1][1],path_for_helper_agent[-2][2]))
                return helper_path_found, path_for_helper_agent, fixed_planner_path
            else:
                continue  # Try another cell if not valid




        # I am farther from the gate, so plan for the helper to wait for me at its gate
        elif earliest_timestep_helper_can_get_to_its_gate <= first_problematic_timestep - 1:
            path_for_helper_agent = path_to_gate_for_helper_agent
            helper_agent_last_move_time = path_to_gate_for_helper_agent[-1][2] + 1

            # Insert delays
            while path_for_helper_agent[-1][2] < first_problematic_timestep - 1:
                path_for_helper_agent.append((path_to_gate_for_helper_agent[-1][0], path_to_gate_for_helper_agent[-1][1], helper_agent_last_move_time))
                helper_agent_last_move_time += 1

            # Now execute the gating
            path_for_helper_agent.append((cell_around_helper_gate_planner_wont_go_to[0], cell_around_helper_gate_planner_wont_go_to[1], helper_agent_last_move_time))
            path_for_helper_agent.append((gate_helper_side[0], gate_helper_side[1], helper_agent_last_move_time + 1))
            path_for_helper_agent.append((gate_planner_side[0], gate_planner_side[1], helper_agent_last_move_time + 2))

            #print(f"Tentative Helper Path - Delayed: {path_for_helper_agent}")

            if is_path_valid(path_for_helper_agent[1:], token):
                helper_path_found = True
                fixed_planner_path = introduce_delays_before_switching(planner_path[:first_problematic_planner_path_index+1], path_for_helper_agent[-3][2])
                if (planner_path[first_problematic_planner_path_index+1][0],planner_path[first_problematic_planner_path_index+1][1]) != (move_at_failure[0], move_at_failure[1]):
                    fixed_planner_path.append((planner_path[first_problematic_planner_path_index+1][0],planner_path[first_problematic_planner_path_index+1][1],path_for_helper_agent[-2][2]))   # The move after into the other partition
                return helper_path_found, path_for_helper_agent, fixed_planner_path
            else:
                continue  # Try another cell if not valid


    return helper_path_found, None, None




# Calculates a Switching Sequence for an Helper Agent to the closest cell in my loop that I won't use.
def calculate_helper_switching_sequence_H(planner_path, first_problematic_agent, first_problematic_timestep, first_problematic_planner_path_index, move_before_failure, planner_loop_before_the_failure, planner_loop_after_the_failure, token, dijkstras_map, border_map, partition_map):
    helper_path_found=False
    fixed_planner_path=[]

    min_helper_distance_to_a_cell_in_planner_loop=float('inf')
    for planner_loop_cell_before_the_failure in planner_loop_before_the_failure:
        if (planner_loop_cell_before_the_failure != (move_before_failure[0],move_before_failure[1])):        # Not the cell I will use to exit
            if border_map[planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]:      # And a bordering cell between our loops. (If this is not zero, this is a border cell in my loop.)
                border_pairs=border_map[planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]

                for border_pair in border_pairs:
                    
                
                    border_cell_in_planner_loop = border_pair[0]
                    border_cell_in_helper_loop = border_pair[1]
                    #print(f"Border Cell in My loop: {border_cell_in_planner_loop}, Border Cell in Helper Loop {border_cell_in_helper_loop}")


                    # Is this border, bordering the switching loop?
                    if partition_map[border_cell_in_helper_loop[1]][border_cell_in_helper_loop[0]] == partition_map[first_problematic_agent[1][1]][first_problematic_agent[1][0]]:

                        helper_distance_to_a_cell_in_planner_loop = dijkstras_map[first_problematic_agent[1][1]][first_problematic_agent[1][0]][planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]
                        if helper_distance_to_a_cell_in_planner_loop < min_helper_distance_to_a_cell_in_planner_loop:
                            min_helper_distance_to_a_cell_in_planner_loop = helper_distance_to_a_cell_in_planner_loop
                            closest_planner_loop_cell = planner_loop_cell_before_the_failure

    earliest_timestep_helper_can_get_to_planner_loop = first_problematic_agent[1][2] + min_helper_distance_to_a_cell_in_planner_loop
    #print(f"Earliest Timestep Helper Agent {first_problematic_agent[0]} can get to Closest Valid Cell {closest_planner_loop_cell} is: {earliest_timestep_helper_can_get_to_planner_loop}")


    # For switching the helper must only use its own partition + the goal position.
    dijkstrasmap_w_own_partition_and_goal = create_dijkstras_map_with_own_partition_and_goal(dijkstras_map, planner_loop_after_the_failure, closest_planner_loop_cell)



    if earliest_timestep_helper_can_get_to_planner_loop > first_problematic_timestep:       # Plan a path for agent 2 to come to my loop first if it is farther to the exchange then me.
        path_for_helper_agent = a_star_algorithm(token, first_problematic_agent[1], Node((closest_planner_loop_cell[0],closest_planner_loop_cell[1], float('inf'),)), dijkstrasmap_w_own_partition_and_goal)
        #print(f"Tentative Helper Path - Quick: {path_for_helper_agent}")

        if path_for_helper_agent is not None and is_path_valid(path_for_helper_agent[1:], token):
            helper_path_found=True
            fixed_planner_path = introduce_delays_before_switching(planner_path[:first_problematic_planner_path_index+1], path_for_helper_agent[-1][2])
            return helper_path_found, path_for_helper_agent, fixed_planner_path


    elif earliest_timestep_helper_can_get_to_planner_loop <= first_problematic_timestep:      # Otherwise helper plans with delays, then I plan. 

        path_for_helper_agent_early = a_star_algorithm(token, first_problematic_agent[1], Node((closest_planner_loop_cell[0],closest_planner_loop_cell[1], float('inf'),)), dijkstrasmap_w_own_partition_and_goal)
        if path_for_helper_agent_early is None:
            return helper_path_found, None, None
        
        #print(f"First Problematic Timestep is {first_problematic_timestep}")
        
        path_for_helper_agent = introduce_delays_before_switching(path_for_helper_agent_early, first_problematic_timestep)

        #print(f"Tentative Helper Path - Delayed: {path_for_helper_agent}")

        if is_path_valid(path_for_helper_agent[1:], token):
            helper_path_found=True
            fixed_planner_path = introduce_delays_before_switching(planner_path[:first_problematic_planner_path_index+1], path_for_helper_agent[-1][2])
            return helper_path_found, path_for_helper_agent, fixed_planner_path


    return helper_path_found, None, None







def calculate_helper_switching_sequence_G(agents_in_conflicted_loop,first_problematic_timestep,move_before_failure, planner_loop_before_the_failure, planner_loop_after_the_failure, token, dijkstras_map, border_map, partition_map):
    helper_path_found = False
    
    closest_agent = None
    min_helper_distance_to_a_cell_in_planner_loop=float('inf')
    for planner_loop_cell_before_the_failure in planner_loop_before_the_failure:
        if (planner_loop_cell_before_the_failure != (move_before_failure[0],move_before_failure[1])):  # But a bordering cell between our loops
            if border_map[planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]:  # If this is not zero, this is a border cell in my loop.
                border_pairs=border_map[planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]
                for border_pair in border_pairs:

                    border_cell_in_my_loop = border_pair[0]
                    border_cell_in_other_loop =  border_pair[1]
                    #print(f"Border Cell in My loop: {border_cell_in_my_loop}")

                    # Is this border, bordering the switching loop?
                    if partition_map[border_cell_in_other_loop[1]][border_cell_in_other_loop[0]] == planner_loop_after_the_failure:
                        
                        for agent_in_conflicted_loop in agents_in_conflicted_loop:
                            distance_to_a_cell_in_my_loop = dijkstras_map[agent_in_conflicted_loop[1][1]][agent_in_conflicted_loop[1][0]][planner_loop_cell_before_the_failure[1]][planner_loop_cell_before_the_failure[0]]
                            if distance_to_a_cell_in_my_loop < min_helper_distance_to_a_cell_in_planner_loop:
                                min_helper_distance_to_a_cell_in_planner_loop = distance_to_a_cell_in_my_loop
                                closest_planner_loop_cell = planner_loop_cell_before_the_failure
                                closest_agent = agent_in_conflicted_loop



    # Find the easiest agent we will force a switch with
    first_problematic_agent = closest_agent
    earliest_timestep_helper_can_get_to_planner_loop = first_problematic_agent[1][2] + min_helper_distance_to_a_cell_in_planner_loop
    #print(f"Closest Valid Cell Agent {first_problematic_agent[0]} Can Route To Is: {closest_planner_loop_cell}")
    #print(f"Earliest Timestep Helper Agent {first_problematic_agent[0]} can get to {closest_planner_loop_cell} is: {earliest_timestep_helper_can_get_to_planner_loop}")


    if earliest_timestep_helper_can_get_to_planner_loop > first_problematic_timestep:       # Plan a path for agent 2 to come to my loop first if it is farther to the exchange then me.
        path_for_helper_agent = a_star_algorithm(token, first_problematic_agent[1], Node((closest_planner_loop_cell[0],closest_planner_loop_cell[1], float('inf'),)), dijkstras_map)
        #print(f"Tentative Helper Path - Quick: {path_for_helper_agent}")
        if path_for_helper_agent is not None and is_path_valid(path_for_helper_agent[1:], token):
            helper_path_found=True
            return helper_path_found, path_for_helper_agent, first_problematic_agent





    elif earliest_timestep_helper_can_get_to_planner_loop <= first_problematic_timestep:      # Otherwise you plan with delays, then I plan. 

        path_for_helper_agent_early = a_star_algorithm(token, first_problematic_agent[1], Node((closest_planner_loop_cell[0],closest_planner_loop_cell[1], float('inf'),)), dijkstras_map)
        if path_for_helper_agent_early is None:
            return helper_path_found, None, first_problematic_agent

        helper_agent_last_move = path_for_helper_agent_early[-1]
        helper_agent_last_move_time = helper_agent_last_move[2]

        path_for_helper_agent_early.pop()
        path_for_helper_agent=path_for_helper_agent_early
        while path_for_helper_agent[-1][2]<first_problematic_timestep-1:    # Wait if you are early to the switch.
            path_for_helper_agent.append((path_for_helper_agent_early[-1][0],path_for_helper_agent_early[-1][1],helper_agent_last_move_time))
            helper_agent_last_move_time+=1
        path_for_helper_agent.append((helper_agent_last_move[0],helper_agent_last_move[1],helper_agent_last_move_time))   # Last move just in time
        
        #print(f"Tentative Helper Path - Delayed: {path_for_helper_agent}")
        if is_path_valid(path_for_helper_agent[1:], token):
            helper_path_found=True
            return helper_path_found, path_for_helper_agent, first_problematic_agent

    return helper_path_found, None, first_problematic_agent








def find_closest_agent_to_xy(agents, dijkstras_map, xy):
    x,y=xy
    closest_agent = None
    min_distance = float('inf')
    
    for agent in agents:
        distance_to_xy = dijkstras_map[agent[1][1]][agent[1][0]][y][x]
        if distance_to_xy < min_distance:
            min_distance = distance_to_xy
            closest_agent = agent
    
    return closest_agent


def find_closest_unclaimed_parking_spot_to_agent(dijkstras_map, planner_agent, agents, parking):

    # Returns the closest unclaimed parking spot.

    claimed_parking_spots = []
    for agent in agents:
        if agent.id != planner_agent.id:
            if agent.claimed_parking_spot != None:
                claimed_parking_spots.append(agent.claimed_parking_spot)

    x = planner_agent.location[0]
    y = planner_agent.location[1]

    closest_parking_spot = None
    min_distance = float('inf')
    
    for parking_spot in parking:
        if parking_spot not in claimed_parking_spots:
            distance_to_xy = dijkstras_map[y][x][parking_spot[1]][parking_spot[0]]
            if distance_to_xy < min_distance:
                min_distance = distance_to_xy
                closest_parking_spot = parking_spot
    
    return closest_parking_spot




def assign_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states):

    if token.agents[helper_agent_id-1].path == []:
        token.agents[helper_agent_id-1].path = helper_agent_path[1:]
    else:
        token.agents[helper_agent_id-1].path.extend(helper_agent_path[1:])

    if token.agents[helper_agent_id-1].state == 0:
        token.agents[helper_agent_id-1].state = 5

    #token.agents[helper_agent_id-1].path_set=1

    #if helper_agent_path_states[0].path_state == "Helper - At the Border" or helper_agent_path_states[0].path_state == "Helper - At the Gate":
    #    token.agents[helper_agent_id-1].path_states[-1] = helper_agent_path_states[0]
    token.agents[helper_agent_id-1].path_states.extend(helper_agent_path_states[1:])




    return token






def check_self_conflict(token, partition_map, guest_map):
    # Dictionary to hold agents by partition key

    problematic_agents = []

    partitioned_agents = {}

    # Iterate over each agent in the token's agent list
    for agent in token.agents:
        # Take the first path element (x, y, t)
        if agent.path:
            x, y, _ = agent.path[0]
            if guest_map[y][x] == 1:
                partition_key = str(partition_map[y][x])  # Convert array to string for use as a key

                # Group agents by partition key
                if partition_key not in partitioned_agents:
                    partitioned_agents[partition_key] = []
                partitioned_agents[partition_key].append(agent)
        else:
            #problematic_agents.append(agent)
            pass

    # Collect agents who share a partition with at least one other agent
    for agents in partitioned_agents.values():
        if len(agents) > 1:         # More than 1 agent in the same partition.
            for agent in agents:
                                    # And in the next timestep the agent shouldn't be in the mid 2 timesteps of gating. (i.e. current_path_state shouldn't be the first 2 path states of gating)
                if agent.path_states and agent.path_states[0].path_state not in ["Planner - Gated to Other Partition", "Planner - Moving Out of the Gate", "Helper - Making One Move Back", "Helper - Moving to Gate"] and agent.current_path_state.path_state not in ["Planner - Gated to Other Partition"]:
                    problematic_agents.append(agent)

    return problematic_agents








def check_self_conflict_Simple(agents):
    next_positions = {}
    edge_collisions = {}
    colliding_agents = []

    # Check each home agent for collisions
    for agent in agents:
        current_pos = (agent.location[0], agent.location[1])
        next_pos = (agent.path[0][0], agent.path[0][1])

        # Check for vertex collisions (same next position)
        next_pos_key = tuple(next_pos)
        if next_pos_key in next_positions:
            # Vertex collision found - add the current and the previous agent to the list
            colliding_agents.extend([agent, next_positions[next_pos_key]])
            continue  # Continue to the next agent

        # Store the next position
        next_positions[next_pos_key] = agent

        # Check for edge collisions (two agents moving between the same two points)
        edge_key = (tuple(current_pos), tuple(next_pos))
        reverse_edge_key = (tuple(next_pos), tuple(current_pos))
        if reverse_edge_key in edge_collisions:
            # Edge collision found - add the current and the previous agent to the list
            colliding_agents.extend([agent, edge_collisions[reverse_edge_key]])
            continue  # Continue to the next agent

        # Store the edge
        edge_collisions[edge_key] = agent

    # Return unique colliding agents only
    return list(set(colliding_agents)) if colliding_agents else []



