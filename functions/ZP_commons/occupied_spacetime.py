

def occupied_spacetime_edges(path):
    # Extract Edges from the path
    spacetime_edges = set()
    for i in range(len(path) - 1):
        spacetime_edges.add((path[i], path[i + 1]))
    return spacetime_edges


def update_occupied_spacetime_Simple(token, path_w_duplicate_start):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(path_w_duplicate_start[1:])
    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token




def calculate_spacetime_path_and_its_partitions(path, partition_map, gates, guest_map):
    
    spacetime_path_and_its_partitions=[]

    # Block the partition wholely in the same spacetime.
    for spacetime in path:
        x, y, t = spacetime
        if guest_map[y][x]==1:       # If x,y is in a loop, block that loop for that time step.
            partition_cells = partition_map[y][x]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))

    
    
    # Loop through the path again to check for gating
    for i in range(len(path) - 1):
        x1, y1, t1 = path[i]                #Taking a sequence of paths
        x2, y2, t2 = path[i + 1]
        
        # Check if the current sequential coordinates match any gate
        for gate in gates:
            (gate_x1, gate_y1), (gate_x2, gate_y2) = gate
            if ((x1, y1) == (gate_x1, gate_y1) and (x2, y2) == (gate_x2, gate_y2)) or ((x1, y1) == (gate_x2, gate_y2) and (x2, y2) == (gate_x1, gate_y1)):
                initial_loop = partition_map[y1][x1]
                final_loop = partition_map[y2][x2]  



                # Leave the places open, that allows gating after I enter the partition.
                # Remove (x2, y2, t2+1) from spacetime_path_and_its_partitions if present
                if (x2, y2, t2+1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x2, y2, t2+1))

                # Remove (x2', y2', t2) if it's 1 move away from (x2, y2) but not (x1, y1)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    try:
                        if path[i+2]:
                            
                            x3, y3, t3 = path[i + 1]
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2))
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2-1))
                            
                            for cell in final_loop:
                                if((cell == (x2 + dx + 1, y2 + dy)     and cell != (x2,y2)) or
                                (cell == (x2 + dx - 1, y2 + dy)     and cell != (x2,y2)) or
                                (cell == (x2 + dx    , y2 + dy + 1) and cell != (x2,y2)) or
                                (cell == (x2 + dx    , y2 + dy - 1) and cell != (x2,y2))):
                                    spacetime_path_and_its_partitions.append((cell[0], cell[1], t2-1))

                        else:   # Dont use this to plan into my future.
                            pass
                    except IndexError:
                        # Handle the case where 'path[i+2]' doesn't exist
                        pass



                # Leave the places open that allows gating before I enter the partition.
                if (x1, y1, t1-1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x1, y1, t1-1))

                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    if path[i-1]:
                        x0, y0, t0 = path[i - 1]
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1))
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1+1))

                        for cell in initial_loop:       # Block the region around the region around the gate so that a robot HAS TO be in time for gating.
                            if((cell == (x1 + dx + 1, y1 + dy)     and cell != (x1,y1)) or
                               (cell == (x1 + dx - 1, y1 + dy)     and cell != (x1,y1)) or
                               (cell == (x1 + dx    , y1 + dy + 1) and cell != (x1,y1)) or
                               (cell == (x1 + dx    , y1 + dy - 1) and cell != (x1,y1))):
                                spacetime_path_and_its_partitions.append((cell[0], cell[1], t1+1))
                        

                    else:   # Not possible to gate before me.
                        pass
                    
        # Bir önceki gateten geçmişse buna açıklık bıraktı.
        # Bu da gateten geçince tamemen işin bitmiş olması lazım ama bu da açıklık bırakıyor. (Hayır işi birmiş olmak zorunda değil başka biri tersten yine yetiebilir, chain gating)
        # Ama devamındaki tlerdeki partitionu bloklıcak. 
        # Dolayısıyla eğer bu sırada valid bir şekilde biri gatee yetişebilirse ve o sırada 2. partition boşalmışsa o da gateleyebilir. Nice. 
    spacetime_path_and_its_partitions.extend(path)

    return spacetime_path_and_its_partitions





def update_occupied_spacetime_H(token, path_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_G1(path_w_duplicate_start[1:], partition_map, gates, guest_map))

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token





def update_occupied_spacetime_H_w_gating_protection(token, path_w_duplicate_start, path_states_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_G1_w_gating_protection(path_w_duplicate_start[1:], path_states_w_duplicate_start[1:], partition_map, gates, guest_map))
    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token






def update_partition_occupancy(occupied_partition_counter, path, partition_map, guest_map):

    for spacetime in path:
        x, y, t = spacetime
        
        # Block the partition wholly in the same spacetime if the agent limit is reached.
        if guest_map[y][x] == 1:  # If x, y is in a loop, increment the occupancy of that loop for that time step once.
            partition_cells = partition_map[y][x]
            occupied_partition_counter_index = (partition_cells, t)
            
            if occupied_partition_counter_index in occupied_partition_counter:
                occupied_partition_counter[occupied_partition_counter_index] += 1

                    
            else:
                occupied_partition_counter[occupied_partition_counter_index] = 1
    
    return occupied_partition_counter









def update_ost_with_carved_out_gating(token, path, partition_map, gates, guest_map ):

    token.occupied_spacetime.update(path)

    # Loop through the path again to check for gating
    for i in range(len(path) - 1):
        x1, y1, t1 = path[i]                #Taking a sequence of paths
        x2, y2, t2 = path[i + 1]
        
        # Check if the current sequential coordinates match any gate
        for gate in gates:
            (gate_x1, gate_y1), (gate_x2, gate_y2) = gate
            if ((x1, y1) == (gate_x1, gate_y1) and (x2, y2) == (gate_x2, gate_y2)) or ((x1, y1) == (gate_x2, gate_y2) and (x2, y2) == (gate_x1, gate_y1)):

                # Leave the places open, that allows gating after I enter the partition.
                # Remove (x2, y2, t2+1) from occupied_spacetime if present
                if (x2, y2, t2+1) in token.occupied_spacetime:
                    if(not any((x2, y2, t2+1) in agent.path for agent in token.agents)):
                        token.occupied_spacetime.discard((x2, y2, t2+1))

                # Remove (x2', y2', t2) if it's 1 move away from (x2, y2) but not (x1, y1)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    try:
                        if path[i+2]:
                            
                            x3, y3, t3 = path[i + 1]
                            if (x2 + dx, y2 + dy, t2) in token.occupied_spacetime and (x2 + dx, y2 + dy) != (x3, y3):
                                if(not any((x2 + dx, y2 + dy, t2) in agent.path for agent in token.agents)):
                                    token.occupied_spacetime.discard((x2 + dx, y2 + dy, t2))
                            if (x2 + dx, y2 + dy, t2) in token.occupied_spacetime and (x2 + dx, y2 + dy) != (x3, y3):
                                if(not any((x2 + dx, y2 + dy, t2-1) in agent.path for agent in token.agents)):
                                    token.occupied_spacetime.discard((x2 + dx, y2 + dy, t2-1))


                        else:   # Dont use this to plan into my future.
                            pass
                    except IndexError:
                        # Handle the case where 'path[i+2]' doesn't exist
                        pass

                # Leave the places open that allows gating before I enter the partition.
                if (x1, y1, t1-1) in token.occupied_spacetime:
                    if(not any((x1, y1, t1-1) in agent.path for agent in token.agents)):
                        token.occupied_spacetime.discard((x1, y1, t1-1))

                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    if path[i-1]:
                        x0, y0, t0 = path[i - 1]
                        if (x1 + dx, y1 + dy, t1) in token.occupied_spacetime and (x1 + dx, y1 + dy) != (x0, y0):
                            if(not any((x1 + dx, y1 + dy, t1) in agent.path for agent in token.agents)):
                                token.occupied_spacetime.discard((x1 + dx, y1 + dy, t1))
                        
                        if (x1 + dx, y1 + dy, t1) in token.occupied_spacetime and (x1 + dx, y1 + dy) != (x0, y0):
                            if(not any((x1 + dx, y1 + dy, t1+1) in agent.path for agent in token.agents)):
                                token.occupied_spacetime.discard((x1 + dx, y1 + dy, t1+1))

                    else:   # Not possible to gate before me.
                        pass
                    
        # Bir önceki gateten geçmişse buna açıklık bıraktı.
        # Bu da gateten geçince tamemen işin bitmiş olması lazım ama bu da açıklık bırakıyor. (Hayır işi birmiş olmak zorunda değil başka biri tersten yine yetiebilir, chain gating)
        # Ama devamındaki tlerdeki partitionu bloklıcak. 
        # Dolayısıyla eğer bu sırada valid bir şekilde biri gatee yetişebilirse ve o sırada 2. partition boşalmışsa o da gateleyebilir. Nice. 

    return token


def update_partition_occupancy_and_vertices(occupied_partition_counter, path, partition_map, gates, guest_map):
    occupied_spacetime = []

    for spacetime in path:
        x, y, t = spacetime
        
        # Block the partition wholly in the same spacetime if the agent limit is reached.
        if guest_map[y][x] == 1:  # If x, y is in a loop, increment the occupancy of that loop for that time step once.
            partition_cells = partition_map[y][x]
            occupied_partition_counter_index = (partition_cells, t)
            
            if occupied_partition_counter_index in occupied_partition_counter:
                occupied_partition_counter[occupied_partition_counter_index] += 1                   
            else:
                occupied_partition_counter[occupied_partition_counter_index] = 1

            
            # Check if any gates are present only once
            is_gated = any(((gate_x1, gate_y1) in partition_cells) or ((gate_x2, gate_y2) in partition_cells) 
                            for (gate_x1, gate_y1), (gate_x2, gate_y2) in gates)

            # Agent limit is N-1 if not gated, N-2 if gated
            loop_agent_limit = len(partition_cells) - 2 if is_gated else len(partition_cells) - 1
            
            if occupied_partition_counter[occupied_partition_counter_index] == loop_agent_limit:
                occupied_spacetime.extend((cell[0], cell[1], t) for cell in partition_cells)
    
    return occupied_partition_counter, occupied_spacetime







def update_occupied_spacetime_G_path_w_duplicate_start(token, path_w_duplicate_start, partition_map, gates, guest_map):
    
    token.occupied_partition_counter, delivery_occupied_spacetime_due_to_loop_limits = update_partition_occupancy_and_vertices(token.occupied_partition_counter, path_w_duplicate_start[1:], partition_map, gates, guest_map)
    token.occupied_spacetime.update(delivery_occupied_spacetime_due_to_loop_limits)

    token = update_ost_with_carved_out_gating(token, path_w_duplicate_start[1:], partition_map, gates, guest_map)

    # OK
    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))

    return token

























# Helper path needs to be set in ost before Planner for it to be valid.
def calculate_spacetime_path_and_its_partitions_G1_w_gating_protection(path, path_states, partition_map, gates, guest_map):
    
    spacetime_path_and_its_partitions=[]

    # Block the partition wholely in the same spacetime.
    for i, spacetime in enumerate(path):
        path_state = path_states[i]
        x, y, t = spacetime
        if guest_map[y][x]==1:       # If x,y is in a loop, block that loop for that time step.
            partition_cells = partition_map[y][x]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))
        
        if path_state.path_state in ["Planner - Gated to Other Partition", "Planner - Moving Out of the Gate"] :       # If Planner midgating, protect the previous loop which is supposed to stay empty for the helper's return.
            partition_cells = partition_map[path_state.gate_or_border_before[1]][path_state.gate_or_border_before[0]]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))

    
    
    # Loop through the path again to check for gating
    for i in range(len(path) - 1):
        x1, y1, t1 = path[i]                #Taking a sequence of paths
        x2, y2, t2 = path[i + 1]
        
        # Check if the current sequential coordinates match any gate
        for gate in gates:
            (gate_x1, gate_y1), (gate_x2, gate_y2) = gate
            if ((x1, y1) == (gate_x1, gate_y1) and (x2, y2) == (gate_x2, gate_y2)) or ((x1, y1) == (gate_x2, gate_y2) and (x2, y2) == (gate_x1, gate_y1)):
                initial_loop = partition_map[y1][x1]
                final_loop = partition_map[y2][x2]  



                # Leave the places open, that allows gating after I enter the partition.
                # Remove (x2, y2, t2+1) from spacetime_path_and_its_partitions if present
                if (x2, y2, t2+1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x2, y2, t2+1))

                # Remove (x2', y2', t2) if it's 1 move away from (x2, y2) but not (x1, y1)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    try:
                        if path[i+2]:
                            
                            x3, y3, t3 = path[i + 1]
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2))
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2-1))
                            

                        else:   # Dont use this to plan into my future.
                            pass
                    except IndexError:
                        # Handle the case where 'path[i+2]' doesn't exist
                        pass



                # Leave the places open that allows gating before I enter the partition.
                if (x1, y1, t1-1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x1, y1, t1-1))

                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    if path[i-1]:
                        x0, y0, t0 = path[i - 1]
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1))
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1+1))
                        

                    else:   # Not possible to gate before me.
                        pass
                    
        # Bir önceki gateten geçmişse buna açıklık bıraktı.
        # Bu da gateten geçince tamemen işin bitmiş olması lazım ama bu da açıklık bırakıyor. (Hayır işi birmiş olmak zorunda değil başka biri tersten yine yetiebilir, chain gating)
        # Ama devamındaki tlerdeki partitionu bloklıcak. 
        # Dolayısıyla eğer bu sırada valid bir şekilde biri gatee yetişebilirse ve o sırada 2. partition boşalmışsa o da gateleyebilir. Nice. 

    # Make sure the path proper is in the list. (If an agent wants to idle at a gate after gating that idling move will be removed otherwise.)
    spacetime_path_and_its_partitions.extend(path)


    return spacetime_path_and_its_partitions


def update_occupied_spacetime_G1_w_gating_protection(token, path_w_duplicate_start, path_states_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_G1_w_gating_protection(path_w_duplicate_start[1:], path_states_w_duplicate_start[1:], partition_map, gates, guest_map))

    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token




def calculate_spacetime_path_and_its_partitions_G1(path, partition_map, gates, guest_map):
    
    spacetime_path_and_its_partitions=[]

    # Block the partition wholely in the same spacetime.
    for spacetime in path:
        x, y, t = spacetime
        if guest_map[y][x]==1:       # If x,y is in a loop, block that loop for that time step.
            partition_cells = partition_map[y][x]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))

    
    '''  
    # Loop through the path again to check for gating
    for i in range(len(path) - 1):
        x1, y1, t1 = path[i]                #Taking a sequence of paths
        x2, y2, t2 = path[i + 1]
        
        # Check if the current sequential coordinates match any gate
        for gate in gates:
            (gate_x1, gate_y1), (gate_x2, gate_y2) = gate
            if ((x1, y1) == (gate_x1, gate_y1) and (x2, y2) == (gate_x2, gate_y2)) or ((x1, y1) == (gate_x2, gate_y2) and (x2, y2) == (gate_x1, gate_y1)):
                initial_loop = partition_map[y1][x1]
                final_loop = partition_map[y2][x2]  



                # Leave the places open, that allows gating after I enter the partition.
                # Remove (x2, y2, t2+1) from spacetime_path_and_its_partitions if present
                if (x2, y2, t2+1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x2, y2, t2+1))

                # Remove (x2', y2', t2) if it's 1 move away from (x2, y2) but not (x1, y1)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    try:
                        if path[i+2]:
                            
                            x3, y3, t3 = path[i + 1]
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2))
                            if (x2 + dx, y2 + dy, t2) in spacetime_path_and_its_partitions and (x2 + dx, y2 + dy) != (x3, y3):
                                spacetime_path_and_its_partitions.remove((x2 + dx, y2 + dy, t2-1))
                            

                        else:   # Dont use this to plan into my future.
                            pass
                    except IndexError:
                        # Handle the case where 'path[i+2]' doesn't exist
                        pass



                # Leave the places open that allows gating before I enter the partition.
                if (x1, y1, t1-1) in spacetime_path_and_its_partitions:
                    spacetime_path_and_its_partitions.remove((x1, y1, t1-1))

                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    if path[i-1]:
                        x0, y0, t0 = path[i - 1]
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1))
                        if (x1 + dx, y1 + dy, t1) in spacetime_path_and_its_partitions and (x1 + dx, y1 + dy) != (x0, y0):
                            spacetime_path_and_its_partitions.remove((x1 + dx, y1 + dy, t1+1))
                        

                    else:   # Not possible to gate before me.
                        pass
         '''         
        # Bir önceki gateten geçmişse buna açıklık bıraktı.
        # Bu da gateten geçince tamemen işin bitmiş olması lazım ama bu da açıklık bırakıyor. (Hayır işi birmiş olmak zorunda değil başka biri tersten yine yetiebilir, chain gating)
        # Ama devamındaki tlerdeki partitionu bloklıcak. 
        # Dolayısıyla eğer bu sırada valid bir şekilde biri gatee yetişebilirse ve o sırada 2. partition boşalmışsa o da gateleyebilir. Nice. 

    # Make sure the path proper is in the list. (If an agent wants to idle at a gate after gating that idling move will be removed otherwise.)
    spacetime_path_and_its_partitions.extend(path)


    return spacetime_path_and_its_partitions







def update_occupied_spacetime_G1(token, path_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_G1(path_w_duplicate_start[1:], partition_map, gates, guest_map))

    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token



def update_occupied_spacetime_w_gating_removal(token, path_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_G1(path_w_duplicate_start[1:], partition_map, gates, guest_map))

    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token












# Helper path needs to be set in ost before Planner for it to be valid.
def calculate_spacetime_path_and_its_partitions_no_remove(path, path_states, partition_map, gates, guest_map):
    
    spacetime_path_and_its_partitions=[]

    # Block the partition wholely in the same spacetime.
    for i, spacetime in enumerate(path):
        path_state = path_states[i]
        x, y, t = spacetime
        if guest_map[y][x]==1:       # If x,y is in a loop, block that loop for that time step.
            partition_cells = partition_map[y][x]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))
        
        if path_state.path_state in ["Planner - Gated to Other Partition", "Planner - Moving Out of the Gate"] :       # If Planner midgating, protect the previous loop which is supposed to stay empty for the helper's return.
            partition_cells = partition_map[path_state.gate_or_border_before[1]][path_state.gate_or_border_before[0]]  
            for cell in partition_cells:
                spacetime_path_and_its_partitions.append((cell[0], cell[1], t))

    
    spacetime_path_and_its_partitions.extend(path)


    return spacetime_path_and_its_partitions


def update_occupied_spacetime_w_gating_protection(token, path_w_duplicate_start, path_states_w_duplicate_start, partition_map, gates, guest_map):
    
    # Block the path. Block the partitions for the t a path goes through them. (With some modifications for allowing gating)
    token.occupied_spacetime.update(calculate_spacetime_path_and_its_partitions_no_remove(path_w_duplicate_start[1:], path_states_w_duplicate_start[1:], partition_map, gates, guest_map))

    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))


    return token



























































# Archive

def update_partition_occupancy_and_vertices_LoopLimit1(occupied_partition_counter, path, partition_map, guest_map):
    occupied_spacetime = []

    for spacetime in path:
        x, y, t = spacetime
        
        # Block the partition wholly in the same spacetime if the agent limit is reached.
        if guest_map[y][x] == 1:  # If x, y is in a loop, increment the occupancy of that loop for that time step once.
            partition_cells = partition_map[y][x]
            occupied_partition_counter_index = (partition_cells, t)
            
            if occupied_partition_counter_index in occupied_partition_counter:
                occupied_partition_counter[occupied_partition_counter_index] += 1                   
            else:
                occupied_partition_counter[occupied_partition_counter_index] = 1
            

            loop_agent_limit = 1
            if occupied_partition_counter[occupied_partition_counter_index] == loop_agent_limit:
                occupied_spacetime.extend((cell[0], cell[1], t) for cell in partition_cells)
    
    return occupied_partition_counter, occupied_spacetime







def update_occupied_spacetime_G_path_w_duplicate_start_LoopLimit1(token, path_w_duplicate_start, partition_map, gates, guest_map):
    
    token.occupied_partition_counter, delivery_occupied_spacetime_due_to_loop_limits = update_partition_occupancy_and_vertices_LoopLimit1(token.occupied_partition_counter, path_w_duplicate_start[1:], partition_map, guest_map)
    token.occupied_spacetime.update(delivery_occupied_spacetime_due_to_loop_limits)

    token = update_ost_with_carved_out_gating(token, path_w_duplicate_start[1:], partition_map, gates, guest_map)

    # OK
    token.occupied_spacetime_wo_counted.update(path_w_duplicate_start[1:])

    token.occupied_spacetime_edges = token.occupied_spacetime_edges.union(occupied_spacetime_edges(path_w_duplicate_start))

    return token