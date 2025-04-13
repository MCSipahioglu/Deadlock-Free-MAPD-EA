import heapq
from collections import deque

from functions.classes import Node
from functions.ZP_commons.occupied_spacetime import update_occupied_spacetime_G_path_w_duplicate_start, update_occupied_spacetime_Simple, update_occupied_spacetime_G1
import copy



def heuristic(node, goal, dijkstras_map):
    x1, y1, _ = node.position
    x2, y2, _ = goal.position
    return dijkstras_map[y1][x1][y2][x2]  # Use precomputed distance



def reconstruct_path(node):
    path = []
    while node is not None:
        path.append(node.position)
        node = node.parent
    return path[::-1]



def get_neighbors(node, t, dijkstras_map, occupied_spacetime=set(), occupied_spacetime_edges=set()):
    x, y, _ = node.position
    potential_neighbors = [
        (x    , y    , t + 1),  # Idling takes 1 time step. This MUST be the first potential neighbor, ensures a*_any tries idling paths first.
        (x + 1, y    , t + 1),
        (x - 1, y    , t + 1),
        (x    , y + 1, t + 1),
        (x    , y - 1, t + 1)
    ]

    #for pos in potential_neighbors:
    #    if pos in occupied_spacetime:
    #        print(f"Pos {pos} in ost")
    #    elif any((node.position, pos) == ((x2, y2, t1), (x1, y1, t2)) for (x1, y1, t1), (x2, y2, t2) in occupied_spacetime_edges):
    #        print(f"Pos {pos} in ostedges")

    # Filter out neighbors that are out of bounds, obstacles, or used in the first path
    """
    neighbors = [
        pos for pos in potential_neighbors
        if 0 <= pos[0] < len(dijkstras_map[0]) and 0 <= pos[1] < len(dijkstras_map)                                                  # No Escaping the Map
        and dijkstras_map[pos[1]][pos[0]] != 0                                                                                       # No Wall Collision
        and pos not in occupied_spacetime                                                                                            # No Vertex Collision
        and all((node.position, pos) != ((x2, y2, t1), (x1, y1, t2)) for (x1, y1, t1), (x2, y2, t2) in occupied_spacetime_edges)     # No Edge Collision
    ]
    """
    neighbors = [
        pos for pos in potential_neighbors
        if 0 <= pos[0] < len(dijkstras_map[0]) and 0 <= pos[1] < len(dijkstras_map)                                                  # No Escaping the Map
        and dijkstras_map[pos[1]][pos[0]] != 0                                                                                       # No Wall Collision
        and pos not in occupied_spacetime                                                                                            # No Vertex Collision
        and ((pos[0], pos[1], t), (node.position[0], node.position[1], t+1)) not in occupied_spacetime_edges     # No Edge Collision
    ]
    return neighbors








# A Star from start_spacetime until it can reach goal.  -> For All Purpose Pathfinding.
def a_star_algorithm(token, start_spacetime, goal, dijkstras_map):
    nodes={start_spacetime: Node(start_spacetime)}
    start=Node(start_spacetime)
    open_set = []
    closed_set = set()

    start.g = 0
    start.f = heuristic(start, goal, dijkstras_map)
    heapq.heappush(open_set, start)
    
    while open_set:
        current_node = heapq.heappop(open_set)

        if current_node.position[:2] == goal.position[:2]:  # Only check spatial position
            return reconstruct_path(current_node)

        closed_set.add(current_node.position)


        neighbor_poss=get_neighbors(current_node, current_node.position[2], dijkstras_map, token.occupied_spacetime, token.occupied_spacetime_edges)

        for neighbor_pos in neighbor_poss:
            if neighbor_pos in closed_set or neighbor_pos in token.occupied_spacetime:
                continue

            neighbor = nodes.get(neighbor_pos, Node(neighbor_pos))
            tentative_g = current_node.g + 1  # Assuming all edges have the same weight of 1

            if tentative_g < neighbor.g:
                neighbor.parent = current_node
                neighbor.g = tentative_g
                neighbor.h = heuristic(neighbor, goal, dijkstras_map)
                neighbor.f = neighbor.g + neighbor.h

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = neighbor

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)

    return None





# A Star from start_spacetime until it can reach goal with an extra last move for idling at the goal position. -> For Pickup and Delivery
def a_star_algorithm_pickup_or_delivery(token, start_spacetime, goal, dijkstras_map):
    #print(token.occupied_spacetime)

    nodes={start_spacetime: Node(start_spacetime)}
    start=Node(start_spacetime)
    open_set = []

    # Dictionary of queues for each time step
    closed_set = set()

    start.g = 0
    start.f = heuristic(start, goal, dijkstras_map)
    heapq.heappush(open_set, start)


    while open_set:
        current_node = heapq.heappop(open_set)
        #print(f"At Node {current_node.position}")

        #print(current_node.position)

        # Check if the current node is at the goal's spatial position
        if current_node.position[:2] == goal.position[:2]:

            # Check if a parent node of idling at pickup or delivery also exists
            if current_node.parent is not None and current_node.parent.position == (current_node.position[0], current_node.position[1], current_node.position[2] - 1):
                # Path ends with idling: return the reconstructed path
                return reconstruct_path(current_node)

        closed_set.add(current_node.position)

        neighbor_poss=get_neighbors(current_node, current_node.position[2], dijkstras_map, token.occupied_spacetime, token.occupied_spacetime_edges)

        for neighbor_pos in neighbor_poss:
            if neighbor_pos in closed_set or neighbor_pos in token.occupied_spacetime:
                continue

            neighbor = nodes.get(neighbor_pos, Node(neighbor_pos))

            tentative_g = current_node.g + 1 # Assuming all edges have the same weight of 1

            if tentative_g < neighbor.g:
                neighbor.parent = current_node
                neighbor.g = tentative_g
                neighbor.h = heuristic(neighbor, goal, dijkstras_map)
                neighbor.f = neighbor.g + neighbor.h

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = neighbor

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)





    return None






# A star any generator: Instead of calling a_star_any from scratch every time we call it we structure our generator as the a_star_any which resumes exploring different paths every time it is called hence returning a DIFFERENT VALID PATH every time it is called until there are no more valid paths left.
def a_star_any_generator(token, start_spacetime, map, path_horizon):
    nodes={}
    start=Node(start_spacetime)
    open_set = []
    closed_set = set()

    # Initialize the start node
    start.g = 0
    start.h = 0  # No heuristic cost in this case
    start.f = 0
    heapq.heappush(open_set, start)

    # Generator that continues the A* search
    while open_set:
        current_node = heapq.heappop(open_set)

        # Reconstruct the path
        path = reconstruct_path(current_node)

        # If we found a valid path, yield it to the caller
        if path[-1][2] == path_horizon:
            yield path
        
        closed_set.add(current_node.position)

        neighbor_poss = get_neighbors(current_node, current_node.position[2], map, token.occupied_spacetime_wo_counted, token.occupied_spacetime_edges)
        neighbor_poss = [pos for pos in neighbor_poss if pos[2] <= path_horizon]    # Without this line the code will try to find a path ending in _,_,horizon by trying to go forward in nodes (Which always goes forward in time so it won't be possible and be stuck in an infinite loop)

        for neighbor_pos in neighbor_poss:
            if neighbor_pos in closed_set or neighbor_pos in token.occupied_spacetime_wo_counted:
                continue

            neighbor = nodes.get(neighbor_pos, Node(neighbor_pos))
            tentative_g = current_node.g + 1  # Assuming all edges have the same weight of 1

            # Apply a heuristic penalty for movement
            if neighbor_pos[:2] == current_node.position[:2]:
                neighbor.h = 0      # No movement, idling
            else:   # Apply a small penalty for movement
                neighbor.h = 2  # Increase this value to make movement less favorable
            
            neighbor.f = tentative_g + neighbor.h  # Total cost f = g + h

            # If this neighbor offers a lower cost, update its g and parent
            if tentative_g < neighbor.g:
                neighbor.parent = current_node
                neighbor.g = tentative_g
                neighbor.f = neighbor.g + neighbor.h

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = neighbor

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)


    # When no more paths are available, the generator will stop
    return None







# Backstepping Algorithm: Calculates a valid combination of paths for agents in 1 partition, that accomodates a priority path. (Instead of using the priority path, the priority path is aready amended to the token.occupied_spacetime and all paths are calculated until the horizon of the priority path)
def recursive_path_planning(agent_index, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon, partition_map, gates, guest_map):
    if agent_index == len(other_agents_starts):
        # Base case: all agents have been processed
        return []

    start = other_agents_starts[agent_index]
    #print(f"Trying to Plan a Helper Path For Agent {other_agents_ids[agent_index]}, Starting From: {start}")
    #print(f"Occupied Spacetime {token.occupied_spacetime}")
    #print(f"Occupied Spacetime wo counted {token.occupied_spacetime_wo_counted}")
    
    # Backup the current state of the token. The token_backup is used to save the state of the token before trying a new path. This ensures that each trial starts with the token in the same state it was before the previous trial.
    token_backup = copy.deepcopy(token)

    
    for path in a_star_any_generator(token_backup, start, big_map_with_just_the_partition, horizon):

        if path is not None:    # This agent has no valid paths, the responsibility is on the previous agent to change its path.
            #print(f"Trying Path {path} for Agent {other_agents_ids[agent_index]}")
            token = update_occupied_spacetime_G_path_w_duplicate_start(token, path, partition_map, gates, guest_map) # Update the token's occupied spacetime with the current path

            # Recur for the next agent
            result_paths = recursive_path_planning(agent_index + 1, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon, partition_map, gates, guest_map)
            
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












# Backstepping Algorithm: Calculates a valid combination of paths for agents in 1 partition, that accomodates a priority path. (Instead of using the priority path, the priority path is aready amended to the token.occupied_spacetime and all paths are calculated until the horizon of the priority path)
def recursive_path_planning_G1(agent_index, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon, partition_map, gates, guest_map):
    if agent_index == len(other_agents_starts):
        # Base case: all agents have been processed
        return []

    start = other_agents_starts[agent_index]
    #print(f"Trying to Plan a Helper Path For Agent {other_agents_ids[agent_index]}, Starting From: {start}")
    #print(f"Occupied Spacetime {token.occupied_spacetime}")
    #print(f"Occupied Spacetime wo counted {token.occupied_spacetime_wo_counted}")
    
    # Backup the current state of the token. The token_backup is used to save the state of the token before trying a new path. This ensures that each trial starts with the token in the same state it was before the previous trial.
    token_backup = copy.deepcopy(token)

    
    for path in a_star_any_generator(token_backup, start, big_map_with_just_the_partition, horizon):

        if path is not None:    # This agent has no valid paths, the responsibility is on the previous agent to change its path.
            #print(f"Trying Path {path} for Agent {other_agents_ids[agent_index]}")
            token = update_occupied_spacetime_G1(token, path, partition_map, gates, guest_map) # Update the token's occupied spacetime with the current path

            # Recur for the next agent
            result_paths = recursive_path_planning_G1(agent_index + 1, token, other_agents_ids, other_agents_starts, big_map_with_just_the_partition, horizon, partition_map, gates, guest_map)
            
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

















# A star any generator: Instead of calling a_star_any from scratch every time we call it we structure our generator as the a_star_any which resumes exploring different paths every time it is called hence returning a DIFFERENT VALID PATH every time it is called until there are no more valid paths left.
def a_star_any(token, start_spacetime, map, path_horizon):
    nodes={}
    start=Node(start_spacetime)
    open_set = []
    closed_set = set()

    # Initialize the start node
    start.g = 0
    start.h = 0  # No heuristic cost in this case
    start.f = 0
    heapq.heappush(open_set, start)

    # Generator that continues the A* search
    while open_set:
        current_node = heapq.heappop(open_set)

        # Reconstruct the path
        path = reconstruct_path(current_node)

        # If we found a valid path, yield it to the caller
        if path[-1][2] == path_horizon:
            return path
        
        closed_set.add(current_node.position)

        neighbor_poss = get_neighbors(current_node, current_node.position[2], map, token.occupied_spacetime, token.occupied_spacetime_edges)
        neighbor_poss = [pos for pos in neighbor_poss if pos[2] <= path_horizon]    # Without this line the code will try to find a path ending in _,_,horizon by trying to go forward in nodes (Which always goes forward in time so it won't be possible and be stuck in an infinite loop)

        for neighbor_pos in neighbor_poss:
            if neighbor_pos in closed_set or neighbor_pos in token.occupied_spacetime:
                continue

            neighbor = nodes.get(neighbor_pos, Node(neighbor_pos))
            tentative_g = current_node.g + 1  # Assuming all edges have the same weight of 1

            # Apply a heuristic penalty for movement
            if neighbor_pos[:2] == current_node.position[:2]:
                neighbor.h = 0      # No movement, idling
            else:   # Apply a small penalty for movement
                neighbor.h = 2  # Increase this value to make movement less favorable
            
            neighbor.f = tentative_g + neighbor.h  # Total cost f = g + h

            # If this neighbor offers a lower cost, update its g and parent
            if tentative_g < neighbor.g:
                neighbor.parent = current_node
                neighbor.g = tentative_g
                neighbor.f = neighbor.g + neighbor.h

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = neighbor

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)


    # When no more paths are available, the generator will stop
    return None








# For SAS

# A star any generator: Instead of calling a_star_any from scratch every time we call it we structure our generator as the a_star_any which resumes exploring different paths every time it is called hence returning a DIFFERENT VALID PATH every time it is called until there are no more valid paths left.
def a_star_any_generator_NoPartitions(token, start_spacetime, map, path_horizon):
    nodes={}
    start=Node(start_spacetime)
    open_set = []
    closed_set = set()

    # Initialize the start node
    start.g = 0
    start.h = 0  # No heuristic cost in this case
    start.f = 0
    heapq.heappush(open_set, start)

    # Generator that continues the A* search
    while open_set:
        current_node = heapq.heappop(open_set)

        # Reconstruct the path
        path = reconstruct_path(current_node)

        # If we found a valid path, yield it to the caller
        if path[-1][2] == path_horizon:
            yield path
        
        closed_set.add(current_node.position)

        neighbor_poss = get_neighbors(current_node, current_node.position[2], map, token.occupied_spacetime, token.occupied_spacetime_edges)
        neighbor_poss = [pos for pos in neighbor_poss if pos[2] <= path_horizon]    # Without this line the code will try to find a path ending in _,_,horizon by trying to go forward in nodes (Which always goes forward in time so it won't be possible and be stuck in an infinite loop)

        for neighbor_pos in neighbor_poss:
            if neighbor_pos in closed_set or neighbor_pos in token.occupied_spacetime:
                continue

            neighbor = nodes.get(neighbor_pos, Node(neighbor_pos))
            tentative_g = current_node.g + 1  # Assuming all edges have the same weight of 1

            # Apply a heuristic penalty for movement
            if neighbor_pos[:2] == current_node.position[:2]:
                neighbor.h = 0      # No movement, idling
            else:   # Apply a small penalty for movement
                neighbor.h = 2  # Increase this value to make movement less favorable
            
            neighbor.f = tentative_g + neighbor.h  # Total cost f = g + h

            # If this neighbor offers a lower cost, update its g and parent
            if tentative_g < neighbor.g:
                neighbor.parent = current_node
                neighbor.g = tentative_g
                neighbor.f = neighbor.g + neighbor.h

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = neighbor

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)


    # When no more paths are available, the generator will stop
    return None



