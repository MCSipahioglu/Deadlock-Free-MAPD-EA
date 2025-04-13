from collections import deque           # Dijkstra

import copy





def create_dijkstras_map(map_array):
    """
    Precompute shortest distances between every pair of points on the map
    using a modified version of Dijkstra's algorithm.
    """
    INF = float('inf')
    map_height = len(map_array)
    map_width = len(map_array[0])
    distances = [[  0 if map_array[y][x] == 0 else [[INF for _ in range(map_width)] for _ in range(map_height)]  for x in range(map_width)] for y in range(map_height)]

    for y1 in range(map_height):
        for x1 in range(map_width):
            if map_array[y1][x1] != 0:
                visited = set()
                queue = deque([(y1, x1, 0)])
                visited.add((y1, x1))

                while queue:
                    cy, cx, dist = queue.popleft()
                    distances[y1][x1][cy][cx] = dist

                    for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < map_height and 0 <= nx < map_width and (ny, nx) not in visited:
                            if map_array[ny][nx] == 0:
                                distances[y1][x1][ny][nx] = INF  # Obstacle
                            else:
                                queue.append((ny, nx, dist + 1))
                                visited.add((ny, nx))

    return distances










def find_borders(partition):
    loops = partition['loops']
    wires = partition['wires']
    parking = partition['parking']
    
    # Combine loops and wires for easier processing
    elements = loops + wires + parking
    
    # Collect all points and categorize them
    points = {}
    for idx, element in enumerate(elements):
        for point in element:
            points[tuple(point)] = idx
    
    # Define a function to get all neighboring points
    def get_neighbors(point):
        x, y = point
        return [(x + dx, y + dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)] if (x + dx, y + dy) in points]
    
    borders = []
    processed = set()  # Keep track of processed border pairs
    
    # Check for borders
    for point in points:
        element_idx = points[point]
        neighbors = get_neighbors(point)
        for neighbor in neighbors:
            neighbor_idx = points[neighbor]
            if element_idx != neighbor_idx:
                border_pair = ((point, element_idx), (neighbor, neighbor_idx))
                reverse_border_pair = ((neighbor, neighbor_idx), (point, element_idx))
                if border_pair not in processed and reverse_border_pair not in processed:
                    borders.append(border_pair)
                    processed.add(border_pair)
    
    return borders



def find_gates(borders):
    border_count = {}
    gates = []
    
    # Count the number of borders between the same identifiers
    for (point1, idx1), (point2, idx2) in borders:
        if (idx1, idx2) in border_count:
            border_count[(idx1, idx2)] += 1
        elif (idx2, idx1) in border_count:
            border_count[(idx2, idx1)] += 1
        else:
            border_count[(idx1, idx2)] = 1
            gates.append(((point1, idx1), (point2, idx2)))
    
    # Remove pairs that are not gates
    for (idx1, idx2), count in border_count.items():
        if count > 1:
            gates = [gate for gate in gates if not ((gate[0][1], gate[1][1]) == (idx1, idx2) or (gate[0][1], gate[1][1]) == (idx2, idx1))]

    # Calculate gates_without_identifiers
    gates_without_identifiers = [(gate[0][0], gate[1][0]) for gate in gates]

    return gates_without_identifiers


def find_parking(partition):

    parking_locations=[]

    parking_groups = partition['parking']
    
    for parking_group in parking_groups:
        for parking_location in parking_group:
            parking_locations.append(parking_location)

    return parking_locations





def create_border_map_old(map_array, borders):
    # Create a deep copy of map_array
    border_map = [[0 for _ in row] for row in map_array]
    
    # Iterate over each border.
    for border in borders:
        border_cell_1=border[0][0]
        border_cell_2=border[1][0]

        border_map[border_cell_1[1]][border_cell_1[0]] = (border_cell_1,border_cell_2)
        border_map[border_cell_2[1]][border_cell_2[0]] = (border_cell_2,border_cell_1)


    return border_map



def create_border_map(map_array, borders):
    # Create a deep copy of map_array, initializing each cell with an empty list
    border_map = [[[] for _ in row] for row in map_array]
    
    # Iterate over each border.
    for border in borders:
        border_cell_1 = border[0][0]
        border_cell_2 = border[1][0]

        # Append the border pair to the list at each cell's location
        border_map[border_cell_1[1]][border_cell_1[0]].append((border_cell_1, border_cell_2))
        border_map[border_cell_2[1]][border_cell_2[0]].append((border_cell_2, border_cell_1))

    return border_map




def create_partition_map(map_array, partition):
    partition_map = [row[:] for row in map_array]  # Deep copy of map_array
    
    for loop in partition['loops']:
        for x, y in loop:
            partition_map[y][x] = loop
    
    for wire in partition['wires']:
        for x, y in wire:
            partition_map[y][x] = wire
    
    for parking in partition['parking']:
        for x, y in parking:
            partition_map[y][x] = parking
    
    return partition_map




