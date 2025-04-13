

from collections import deque
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_G1
from functions.ZP_commons.planning import is_path_valid
from functions.ZP_commons.existing_paths import is_path_valid_with_timestep
import copy


# First observe the H team's moves.

def observe_others_moves(observer_token, observee_token, observation_radius):
    time=observee_token.time
    observed_agents_and_nextmoves = []

    # Define the possible moves based on the observation radius
    moves = []
    for dx in range(-observation_radius, observation_radius + 1):
        for dy in range(-observation_radius, observation_radius + 1):
            if abs(dx) + abs(dy) <= observation_radius and (dx != 0 or dy != 0):
                moves.append((dx, dy))

    #print(moves)

    for observer_agent in observer_token.agents:
        observer_location = observer_agent.location
        #print(f"Observer Location {observer_location}")

        for move in moves:
            observed_cell = (observer_location[0] + move[0], observer_location[1] + move[1])
            #print(f"Observed Cell {observed_cell}")
        
            for observee_agent in observee_token.agents:
                observee_location = observee_agent.location
                observee_next_move = observee_agent.path[0] if observee_agent.path else (observee_location[0],observee_location[1])

                #print(f"Observee Location {observee_location}")
            
                if observed_cell == observee_location:
                    observation = [(observee_agent.location[0], observee_agent.location[1], time), (observee_next_move[0],observee_next_move[1],time+1)]
                    if observation not in observed_agents_and_nextmoves:
                        observed_agents_and_nextmoves.append(observation)
                    break
                    

    return observed_agents_and_nextmoves














def invalidate_paths(agent_id, token):
    # Check if the agent has already been invalidated
    if token.agents[agent_id - 1].path_invalid == 1 or token.agents[agent_id - 1].path_set == 1:
        return token  # Exit if this agent's path is already invalidated or is set with a mandatory move.

    # Mark the current agent as invalidated
    token.agents[agent_id - 1].path_invalid = 1
    token.agents[agent_id - 1].path = []

    if token.agents[agent_id - 1].state == 5:
        token.agents[agent_id - 1].state = 0

    
    # Gather path states to flush them after getting related agent IDs
    path_states_to_flush = copy.deepcopy(token.agents[agent_id - 1].path_states)
    
    # Clear the current agent's path states
    token.agents[agent_id - 1].path_states = []

    # Invalidate related agents' paths
    for path_state in path_states_to_flush:
        if path_state.related_agent_ids:
            for related_agent_id in path_state.related_agent_ids:
                token = invalidate_paths(related_agent_id, token)
    
    return token








# Shouldn't lose original state.
def assign_home_helper_path(token, helper_agent_id, helper_agent_path, helper_agent_path_states):
    

    if token.agents[helper_agent_id-1].path == []:
        token.agents[helper_agent_id-1].path = helper_agent_path[1:]

    else:
        token.agents[helper_agent_id-1].path.extend(helper_agent_path[1:])

    token.agents[helper_agent_id-1].path_set=1
    token.agents[helper_agent_id-1].path_states.extend(helper_agent_path_states[1:])

    return token





def are_all_valid_with_timestep(agent_id, token, token_right_preservation_original, partition_map, gates, guest_map, current_time):
    
    token_right_preservation = copy.deepcopy(token_right_preservation_original)

    # Recursive function to collect related agents and check validity of their paths
    related_agent_ids = {agent_id}  # Start with the main agent
    all_valid = True             # Flag to track if all paths are valid

    # Collect all related agents recursively using path states
    def collect_related_agents(agent_id, visited_agents):
        if agent_id in visited_agents:
            return
        visited_agents.add(agent_id)
        related_agent_ids.add(agent_id)
        # Gather path states for the current agent
        path_states = token.agents[agent_id - 1].path_states
        for path_state in path_states:
            if path_state.related_agent_ids:
                for related_agent_id in path_state.related_agent_ids:
                    if related_agent_id not in visited_agents:
                        collect_related_agents(related_agent_id, visited_agents)

    # Start the recursion from the main agent
    collect_related_agents(agent_id, set())



    # Validate paths for all related agents by updating the token incrementally
    for related_id in related_agent_ids:
        related_agent = token.agents[related_id - 1]
        if related_agent.path_set == 0 and related_agent.state != 0 and related_agent.path:

            path_valid, path_invalid_from_timestep = is_path_valid_with_timestep(related_agent, token)

            if path_valid:
                print(f"Setting Agent {related_agent.id} path as valid in token_right_preservation.")
                token_right_preservation = update_occupied_spacetime_G1(token_right_preservation, [(related_agent.location[0], related_agent.location[1], current_time)] + related_agent.path, partition_map, gates, guest_map)
            else:
                print(f"Path {related_agent.path} for {related_agent.agent_type} Agent {related_agent.id} is invalid")
                
                return False, None, path_invalid_from_timestep    # Exit early if any path is invalid


    return True, related_agent_ids, None






def are_all_valid(agent_id, token, token_right_preservation_original, partition_map, gates, guest_map, current_time):
    
    token_right_preservation = copy.deepcopy(token_right_preservation_original)

    # Recursive function to collect related agents and check validity of their paths
    related_agent_ids = {agent_id}  # Start with the main agent
    all_valid = True             # Flag to track if all paths are valid

    # Collect all related agents recursively using path states
    def collect_related_agents(agent_id, visited_agents):
        if agent_id in visited_agents:
            return
        visited_agents.add(agent_id)
        related_agent_ids.add(agent_id)
        # Gather path states for the current agent
        path_states = token.agents[agent_id - 1].path_states
        for path_state in path_states:
            if path_state.related_agent_ids:
                for related_agent_id in path_state.related_agent_ids:
                    if related_agent_id not in visited_agents:
                        collect_related_agents(related_agent_id, visited_agents)

    # Start the recursion from the main agent
    collect_related_agents(agent_id, set())



    # Validate paths for all related agents by updating the token incrementally
    for related_id in related_agent_ids:
        related_agent = token.agents[related_id - 1]
        if related_agent.path_set == 0 and related_agent.state != 0 and related_agent.path:
            if is_path_valid(related_agent.path, token_right_preservation):
                print(f"Setting Agent {related_agent.id} path as valid in token_right_preservation.")
                token_right_preservation = update_occupied_spacetime_G1(token_right_preservation, [(related_agent.location[0], related_agent.location[1], current_time)] + related_agent.path, partition_map, gates, guest_map)
            else:
                print(f"Path {related_agent.path} for {related_agent.agent_type} Agent {related_agent.id} is invalid")
                all_valid = False
                break  # Exit early if any path is invalid


    return all_valid, related_agent_ids

    
   



# Then accomodate the H team's moves.


def BestSubLoop(map_coordinates, second_position, initial_position):    # Finds closest path between second -> initial_pos (the returned is a loop if second and initial are one apart)
    # Finds the shortest loop within the loop. The first element of this path starting from the G position is the BestMove.
    # initial_pos -> second_pos -> path -> initial_pos
    # The path is the shortest from second_pos to initial_pos with no duplicates and second_pos->initial_pos invalid.
    # [initial_pos, second_pos, path] defines the smallest loop in the loop partition. (path ends with initial_pos as well so use [second_pos, path] instead)
    
    
    # Create a set for quick lookup
    valid_positions = set(map_coordinates)
    
    # Initialize BFS structures
    queue = deque([(second_position, [second_position])])
    visited = set()
    visited.add(second_position)
    
    while queue:
        current_position, path = queue.popleft()
        
        # Explore possible moves (up, down, left, right)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_position = (current_position[0] + dx, current_position[1] + dy)
            
            if (next_position in valid_positions and
                next_position not in visited):
                # Check if the next_position is the initial_position
                if next_position == initial_position:
                    # Ensure that this is not the direct invalid path
                    if len(path) > 1:  # path length > 1 ensures at least one intermediate step
                        return path + [next_position]
                else:
                    visited.add(next_position)
                    queue.append((next_position, path + [next_position]))
    
    return []  # Return an empty list if no valid path is found


def BestSubWire(map_coordinates, initial_position, guest_agents):
    # Convert list of guest agent locations to a set for fast lookup
    occupied_cells = {agent.location for agent in guest_agents}
    
    # Convert list of map coordinates to a set for fast lookup
    map_coordinates_set = set(map_coordinates)
    
    # Define BFS
    def bfs(start):
        queue = deque([(start, [start])])  # Each element is a tuple (current_cell, path_to_current_cell)
        visited = set([start])  # Set of visited cells
        
        while queue:
            current_cell, path = queue.popleft()
            
            # Check if the current cell is an empty cell
            if current_cell in map_coordinates_set and current_cell not in occupied_cells:
                return path
            
            # Get neighboring cells (up, down, left, right)
            x, y = current_cell
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            
            for neighbor in neighbors:
                if neighbor in map_coordinates_set and neighbor not in visited and neighbor not in occupied_cells:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None  # If no empty cell is found
    
    # Perform BFS from the initial location
    return bfs(initial_position)






