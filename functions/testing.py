def assign_predefined_paths(agents):
    paths = [
        [[7,6], [8,6], [8,5], [8,4], [8,3], [8,2], [8,1], [7,1], [6,1], [5,1], [5,2], [5,3], [4,3], [3,3], [2,3], [2,2], [2,1], [2,0], [1,0]],
        [[3,9], [4,9], [5,9], [5,8], [5,7], [5,6], [5,5], [5,4], [5,3], [4,3], [3,3], [2,3], [1,3]],
        [[1,2], [2,2], [2,3], [1,3], [0,3], [0,4], [0,5], [0,6], [0,7], [0,8], [0,9], [0,10], [1,10], [2,10], [3,10], [4,10], [5,10], [6,10], [7,10], [8,10], [9,10]],
        [[11,10], [10,10], [9,10], [8,10], [7,10], [6,10], [5,10], [5,9], [5,8], [5,7], [5,6], [4,6], [3,6], [2,6], [2,7], [2,8], [2,9], [1,9]],
        [[3,6], [4,6], [5,6], [5,5], [5,4], [5,3], [5,2], [5,1], [5,2], [5,3], [5,4], [5,5], [5,6], [5,7], [5,8], [5,9], [6,9], [7,9], [8,9], [9,9]]
    ]

    for i, agent in enumerate(agents):
        agent.path += paths[i]

    return agents




def closest_task(master_map, free_agent_location, tasks_to_assign):
    agent_x, agent_y = free_agent_location
    min_distance = float('inf')
    closest_task = None

    for task in tasks_to_assign:

        task_x, task_y = task.start
        distance = master_map[agent_y][agent_x][task_y][task_x]
        if distance < min_distance:
            min_distance = distance
            closest_task = task

    return closest_task






def demo_assign_tasks(token,master_map):

    agents=token.agents
    unassigned_tasks=token.unassigned_tasks

    for agent in agents:        # For all free agents (They request the token.)
        if agent.state == 0:

            # Already planned paths in space-time of non-free agents.
            planned_paths = [agent.path for agent in agents]    

            valid_tasks_to_assign = [task for task in unassigned_tasks if all(task.start != planned_path[-1] and task.goal != planned_path[-1] for planned_path in planned_paths)]

            # If valid tasks is not empty.
            if valid_tasks_to_assign:

                # Find the Best Task to Assign
                best_task = closest_task(master_map, agent.location, valid_tasks_to_assign)

                # Assign the best task to the agent
                agent.assigned_task = best_task
                if tuple(agent.location) == tuple(best_task.start):
                    agent.state = 2  # Agent is already at the pickup of the task
                else:
                    agent.state = 1  # Agent is assigned a task but not at the pickup
                
                # Remove the task from unassigned_tasks
                unassigned_tasks.remove(best_task)



            elif all(task.start != agent.location for task in unassigned_tasks):
                agent.path=[agent.location]
            else:
                pass

    
    token.agents=agents
    token.unassigned_tasks=unassigned_tasks

    return token
