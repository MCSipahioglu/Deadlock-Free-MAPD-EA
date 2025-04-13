





def closest_task(dijkstras_map, free_agent_location, tasks_to_assign):
    agent_x, agent_y = free_agent_location
    min_distance = float('inf')
    closest_task = None

    for task in tasks_to_assign:
        task_x, task_y = task.start
        distance = dijkstras_map[agent_y][agent_x][task_y][task_x]
        if distance < min_distance:
            min_distance = distance
            closest_task = task

    return closest_task

