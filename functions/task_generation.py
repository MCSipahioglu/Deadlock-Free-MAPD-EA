import random
from collections import deque
from functions.classes import Task
import heapq
import random
from collections import deque
import itertools



# TASK GENERATION
def is_path_feasible(map_data, start, goal):
    """
    Use BFS to check if there is a path between start and goal coordinates.
    """
    if start == goal:
        return False

    map_height = len(map_data)
    map_width = len(map_data[0])
    queue = deque([start])
    visited = set()
    visited.add(start)

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        current = queue.popleft()
        if current == goal:
            return True

        for d in directions:
            neighbor = (current[0] + d[0], current[1] + d[1])
            if (0 <= neighbor[0] < map_height and
                0 <= neighbor[1] < map_width and
                neighbor not in visited and
                isinstance(map_data[neighbor[0]][neighbor[1]], list)):
                queue.append(neighbor)
                visited.add(neighbor)

    return False









def generate_tasks(map_data, n):

    generated_tasks = []

    map_height = len(map_data)
    map_width = len(map_data[0])

    while len(generated_tasks) < n:
        start_x = random.randint(0, map_width - 1)
        start_y = random.randint(0, map_height - 1)
        goal_x = random.randint(0, map_width - 1)
        goal_y = random.randint(0, map_height - 1)

        start = (start_x, start_y)
        goal = (goal_x, goal_y)

        if start != goal and map_data[start_y][start_x]!=0 and map_data[goal_y][goal_x]!=0:
            if is_path_feasible(map_data, start, goal):
                generated_tasks.append(Task(start, goal))  # Assign ID to task
                

    return generated_tasks




def is_valid_path(map_2d, start, goal, excluded_points):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    queue = deque([start])
    visited = set()
    visited.add(start)

    while queue:
        current = queue.popleft()
        if current == goal:
            return True
        for d in directions:
            neighbor = (current[0] + d[0], current[1] + d[1])
            if (0 <= neighbor[1] < len(map_2d) and 0 <= neighbor[0] < len(map_2d[0]) and
                map_2d[neighbor[1]][neighbor[0]] == 1 and
                neighbor not in visited and
               (neighbor not in excluded_points or neighbor == goal)):
                visited.add(neighbor)
                queue.append(neighbor)
    return False




def is_connected(map_2d, endpoints):
    # Convert the set of endpoints to a list
    endpoints_list = list(endpoints)
    
    # Check connectivity between all pairs of endpoints
    for i in range(len(endpoints_list)):
        for j in range(i + 1, len(endpoints_list)):
            # Check if there is a valid path between the pair of endpoints without passing through other endpoints
            if not is_valid_path(map_2d, endpoints_list[i], endpoints_list[j], set(endpoints_list) - {endpoints_list[i], endpoints_list[j]}):
                return False  # Return False if any pair of endpoints is not connected

    return True  # Return True if all endpoints are connected



def generate_nontask_endpoints(map_2d, agent_count):
    valid_positions = [(x, y) for y in range(len(map_2d)) for x in range(len(map_2d[0])) if map_2d[y][x] == 1]
    nontask_endpoints = set()

    while len(nontask_endpoints) < agent_count:
        if not valid_positions:
            # If valid_positions is empty, restart the process to generate endpoints. It might be possible that because the first endpoint we chose was bad the rest couldnt be generated.
            #print("Restarting endpoint generation...")
            return generate_nontask_endpoints(map_2d, agent_count)
        
        point = random.choice(valid_positions)
        valid_positions.remove(point)
        
        if point not in nontask_endpoints:
            # Temporarily add the new endpoint
            nontask_endpoints.add(point)
            # Check if adding the new endpoint maintains connectivity
            if is_connected(map_2d, nontask_endpoints):
                #print(f"Added nontask endpoint: {point}")
                pass
            else:
                # If adding the new endpoint breaks connectivity, remove it and try again
                nontask_endpoints.remove(point)
                #print(f"Rejected nontask endpoint: {point}")

    return list(nontask_endpoints)



def generate_well_formed_tasks(map_2d, task_count, agent_count):
    nontask_endpoints = generate_nontask_endpoints(map_2d, agent_count)
    valid_positions = [(x, y) for y in range(len(map_2d)) for x in range(len(map_2d[0])) if map_2d[y][x] == 1]
    non_nontask_vertices = [pos for pos in valid_positions if pos not in nontask_endpoints]

    if len(non_nontask_vertices) < task_count:
        raise ValueError("Not enough valid positions for the specified number of tasks")

    tasks = []
    task_endpoints = set()

    all_start_goal_combinations = list(itertools.combinations(non_nontask_vertices, 2))
    #print(all_start_goal_combinations)



    while len(tasks) < task_count:

        if not all_start_goal_combinations:
            # If valid_positions is empty, restart the process to generate endpoints. It might be possible that because the first endpoint we chose was bad the rest couldnt be generated.
            #print("Restarting task generation...")
            return generate_well_formed_tasks(map_2d, task_count, agent_count)
        
        start, goal = random.choice(all_start_goal_combinations)
        all_start_goal_combinations.remove((start, goal))
        
        
        # Check if start and goal are distinct and not in nontask endpoints
        if start != goal and start not in nontask_endpoints and goal not in nontask_endpoints:
            all_endpoints = set(nontask_endpoints) | task_endpoints
            
            # Check if there is a valid path between start and goal without passing through endpoints.
            if is_valid_path(map_2d, start, goal, all_endpoints):
                # Combine nontask and task endpoints
                hypothetic_endpoints = set(nontask_endpoints) | task_endpoints | {start, goal}
                
                # Check if adding start and goal does not disconnect any endpoints
                if is_connected(map_2d, hypothetic_endpoints):
                    tasks.append(Task(start, goal))
                    task_endpoints.add(start)
                    task_endpoints.add(goal)
                    #print(f"Added task: {start}, {goal}")
                else:
                    #print(f"Rejected task: {start}, {goal}")
                    pass
            else:
                #print(f"Rejected task: {start}, {goal}")
                pass
        else:
            #print(f"Rejected task: {start}, {goal}")
            pass


    return tasks, list(task_endpoints), nontask_endpoints





def tasks_to_spacetime_tasks(tasks, current_time):
    spacetime_tasks = []
    for task in tasks:
        start_x, start_y = task.start
        goal_x, goal_y = task.goal
        spacetime_tasks.append(((start_x, start_y, current_time), (goal_x, goal_y, float('inf'))))

    return spacetime_tasks











