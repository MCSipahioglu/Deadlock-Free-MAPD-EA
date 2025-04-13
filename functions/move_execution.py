
from tkinter import messagebox


def check_all_agents_idle(agents):

    agents_idling_at_parking = 0

    for agent in agents:
        if (agent.location[0],agent.location[1]) != (agent.path[0][0],agent.path[0][1]) :
            return False
        
        elif agent.claimed_parking_spot:
            if (agent.location[0],agent.location[1]) == (agent.claimed_parking_spot[0], agent.claimed_parking_spot[1]):
                agents_idling_at_parking += 1

    if agents_idling_at_parking == len(agents):
        return False

    return True


    


def check_collisions(home_agents, guest_agents):
    next_positions = {}
    edge_collisions = {}
    collision_identifier = {
        'type_of_collision': None,
        'agents_in_collision': []
    }

    # Helper function to add agent information to the collision report
    def add_collision(agent, agent_type, current_pos, next_pos):
        collision_identifier['agents_in_collision'].append({
            'agent': agent,
            'agent_type': agent_type,
            'current_pos': current_pos,
            'next_pos': next_pos
        })


    all_agents = home_agents + guest_agents

    # Process both home and guest agents for collisions
    for agent in all_agents:
        agent_type=agent.agent_type
        current_pos = (agent.location[0], agent.location[1])
        next_pos = (agent.path[0][0], agent.path[0][1])

        # Check for vertex collisions (same next position)
        next_pos_key = tuple(next_pos)
        if next_pos_key in next_positions:
            # Vertex collision found
            collision_identifier['type_of_collision'] = 'Vertex'
            # Add the colliding agents
            add_collision(agent, agent_type, current_pos, next_pos)
            prev_agent = next_positions[next_pos_key]
            add_collision(prev_agent, prev_agent.agent_type, prev_agent.location, (prev_agent.path[0][0], prev_agent.path[0][1]))
            return collision_identifier
        
        # Store the next position and agent type
        next_positions[next_pos_key] = agent
        next_positions[next_pos_key].agent_type = agent_type

        # Check for edge collisions (two agents moving between the same two points)
        edge_key = (tuple(current_pos), tuple(next_pos))
        reverse_edge_key = (tuple(next_pos), tuple(current_pos))
        if reverse_edge_key in edge_collisions:
            # Edge collision found
            collision_identifier['type_of_collision'] = 'Edge'
            # Add the colliding agents
            add_collision(agent, agent_type, current_pos, next_pos)
            prev_agent = edge_collisions[reverse_edge_key]
            add_collision(prev_agent, prev_agent.agent_type, prev_agent.location, (prev_agent.path[0][0], prev_agent.path[0][1]))
            return collision_identifier

        # Store the edge and agent type
        edge_collisions[edge_key] = agent
        edge_collisions[edge_key].agent_type = agent_type

    return 'No Collision'



def check_path_validity(token):
    current_time=token.time

    for agent in token.agents:

        # Move the agent to the next position
        _,_,time_of_path = agent.path[0]
        time_of_path_state = agent.path_states[0].time

        # Check the validity of the the path.
        if time_of_path != current_time+1:
            messagebox.showinfo("Misassigned Path", f"Something went wrong. {agent.agent_type} Agent {agent.id} has path {agent.path[0]} but the next time is {current_time+1}", icon='info')
        elif time_of_path_state != current_time+1:
            messagebox.showinfo("Misassigned Path State", f"Something went wrong. {agent.agent_type} Agent {agent.id} has path state {agent.path_states[0]} but the next time is {current_time+1}", icon='info')



def execute_moves(token):

    for agent in token.agents:

        # Move the agent to the next position
        loc_x,loc_y,time_of_path = agent.path[0]

        agent.location=(loc_x,loc_y)
        agent.path.pop(0)           # Remove the current position from the path
        
        agent.current_path_state = agent.path_states[0]
        agent.path_states.pop(0)


        # Update the State for the move it made: Check if agent's location matches its assigned task's start or goal 
        if agent.state==0:                                                             # Free, No checks needed
            pass
        elif agent.state==5 and agent.path!=[]:                                        # Helping Ongoing, No checks needed
            pass
        elif agent.state==5 and agent.path==[]:                                        # Helping Completed
            agent.state=0
        elif tuple(agent.location) == agent.assigned_task.start and agent.state==1:    # Pick Up Reached
            agent.state = 2
        elif agent.state==2 and tuple(agent.location) != agent.assigned_task.start:    # Pick Up was Reached but it was left before Pickup was Completed
            agent.state = 1
        elif tuple(agent.location) == agent.assigned_task.start and agent.state==2:    # Pick Up Completed
            agent.state = 3
        elif tuple(agent.location) == agent.assigned_task.goal and agent.state==3:     # Delivery Reached
            agent.state = 4
        elif agent.state==4 and tuple(agent.location) != agent.assigned_task.goal:     # Delivery was Reached but it was left before Delivery was Completed
            agent.state = 3
        elif tuple(agent.location) == agent.assigned_task.goal and agent.state==4:     # Delivery Completed, Task Completed
            agent.state = 0
            agent.assigned_task = None
            token.tasking_time    += token.time-agent.task_assignment_time
            token.completed_tasks += 1



        # After the effect of its move is recorded above, Check if there are helper_paths queued up, switch to the helper state if there is.
        if agent.state==0 and agent.path_states:
            if agent.path_states[0].agent_role=="Helper":
                agent.state = 5



    return token

