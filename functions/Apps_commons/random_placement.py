

import random

class Agent:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y





def get_loop_positions_and_limits(partition, agent_type):
    loop_positions_and_limits = []
    for loop in partition['loops']:
        valid_positions = loop  # All positions in loop are valid paths
        if agent_type == "home":
            max_agents_per_loop = 1  # At most one home agent per loop
        else:
            #max_agents = len(valid_positions) - 2  # At most N-2 guest agents per loop
            max_agents_per_loop = 1  # ZPG1 uses 1 G per loop
        loop_positions_and_limits.append((valid_positions, max_agents_per_loop))
    return loop_positions_and_limits



def get_wire_positions_and_limits(partition):
    wire_positions_and_limits = []
    for wire in partition['wires']:
        valid_positions = wire  # All positions in the wire are valid paths
        max_agents_per_wire = len(valid_positions)  # No constraint on wires for guest agents
        wire_positions_and_limits.append((valid_positions, max_agents_per_wire))
    return wire_positions_and_limits





def place_agents(agent_count, agent_type, partition, home_agents, guest_agents):
    # Clear existing agents of the specified type
    if agent_type == "home":
        home_agents.clear()
        occupied_positions = set((agent.pos_x, agent.pos_y) for agent in guest_agents)
        loop_positions = get_loop_positions_and_limits(partition, agent_type)
        wire_positions = get_wire_positions_and_limits(partition)
        #valid_positions = loop_positions + wire_positions
        valid_positions = loop_positions
    else:
        guest_agents.clear()
        occupied_positions = set((agent.pos_x, agent.pos_y) for agent in home_agents)
        valid_positions = get_loop_positions_and_limits(partition, agent_type)

    agents = []

    placement_dict = {",".join([f"({x},{y})" for x, y in positions]): 0 for positions, _ in valid_positions}

    for _ in range(agent_count):
        placed = False
        random.shuffle(valid_positions)

        for positions, max_agents in valid_positions:
            try_key = ",".join([f"({x},{y})" for x, y in positions])  # Convert positions to strings
            positions_copy = positions[:]  # Create a copy of positions

            if placement_dict[try_key] < max_agents:
                random.shuffle(positions_copy)
                
                # Directly integrated placement logic
                while positions_copy:
                    x, y = positions_copy.pop()
                    if (x, y) not in occupied_positions:
                        occupied_positions.add((x, y))
                        agent = Agent(x, y)
                        agents.append(agent)
                        placement_dict[try_key] += 1
                        placed = True
                        break

            if placed:
                break

        if not placed:
            raise ValueError(f"Not enough valid positions to place all {agent_type} agents")

    if agent_type == "home":
        home_agents.extend(agents)
    else:
        guest_agents.extend(agents)

    return agents
























































def calculate_valid_loop_positions(partition, agent_type):
    max_agents=0
    loop_positions = []
    for loop in partition['loops']:
        valid_positions = loop  # All positions in loop are valid paths
        if agent_type == "home":
            max_agents += 1  # At most one home agent per loop
        else:
            #max_agents += len(valid_positions) - 2  # At most N-2 guest agents per loop
            max_agents += 1  # ZPG1 uses 1 G per loop
        loop_positions.extend(valid_positions)
    return loop_positions, max_agents


def calculate_valid_wire_positions(partition):
    max_agents = 0
    wire_positions = []
    for wire in partition['wires']:
        valid_positions = wire  # All positions in loop are valid paths
        max_agents += len(valid_positions)  # At most N-2 guest agents per loop
        wire_positions.extend(valid_positions)
    return wire_positions, max_agents


def calculate_valid_H_positions(partition):
    valid_H_loop_positions, max_H_count_in_loops = calculate_valid_loop_positions(partition, "home")
    valid_H_wire_positions, max_H_count_in_wires = calculate_valid_wire_positions(partition)
    valid_H_positions = valid_H_loop_positions + valid_H_wire_positions
    max_H_count = max_H_count_in_loops + max_H_count_in_wires
    return valid_H_positions, max_H_count







