









def print_map(map_array):
    print("Map Array:")
    print_map = [["■" if cell == 1 else "·" for cell in row] for row in map_array]
    for row in print_map:
        print(" ".join(row))

def print_map_and_agents(map_array, home_agents, guest_agents):
    print("Map State")
    print_map = [["■" if cell == 1 else " " for cell in row] for row in map_array]

    for agent in home_agents:
        print_map[agent.pos_y][agent.pos_x] = "H"
    
    for agent in guest_agents:
        print_map[agent.pos_y][agent.pos_x] = "G"
    
    for row in print_map:
        print(" ".join(row))



def calculate_lixel_size(screen_width, screen_height, map_width, map_height):
    target_width = screen_width * 0.6  # 50% of the screen width
    target_height = screen_height * 0.6  # 50% of the screen height

    lixel_size_width = (target_width - (map_width + 1) * (target_width // (map_width + 1) // 10)) / map_width
    lixel_size_height = (target_height - (map_height + 1) * (target_height // (map_height + 1) // 10)) / map_height

    lixel_size = min(int(lixel_size_width), int(lixel_size_height))
    lixel_size = max(1, lixel_size)
    gap_size = lixel_size // 10

    return lixel_size, gap_size








def draw_grid(canvas, canvas_frame, lixel_size, gap_size, map_array):
    canvas.delete("all")
    map_height = len(map_array)
    map_width = len(map_array[0]) if map_array else 0
    
    for row in range(map_height):
        for col in range(map_width):
            x1 = col * (lixel_size + gap_size) + gap_size * 1.5
            y1 = row * (lixel_size + gap_size) + gap_size * 1.5
            x2 = x1 + lixel_size
            y2 = y1 + lixel_size
            color = "black" if map_array[row][col] == 0 else "white"
            canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)

    canvas_frame.place(relx=0.4, rely=0.5, anchor="center")


def draw_grid_and_partitions(canvas, canvas_frame, lixel_size, gap_size, map_array, partition):

    draw_grid(canvas, canvas_frame, lixel_size, gap_size, map_array)

    wire_colors = ["#c91d48", "#e96384", "#e23661", "#ef8fa7"]  # Shades of red
    loop_colors = ["#38947d", "#6bc7b0", "#46b99c", "#90d5c4"]  # Shades of green
    parking_colors = ["#386e94"]

    for i, loop in enumerate(partition["loops"]):
        loop_color = loop_colors[i % len(loop_colors)]
        for cell in loop:
            x1 = cell[0] * (lixel_size + gap_size) + gap_size * 1.5
            y1 = cell[1] * (lixel_size + gap_size) + gap_size * 1.5
            x2 = x1 + lixel_size
            y2 = y1 + lixel_size
            canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=loop_color)

    for i, wire in enumerate(partition["wires"]):
        wire_color = wire_colors[i % len(wire_colors)]
        for cell in wire:
            x1 = cell[0] * (lixel_size + gap_size) + gap_size * 1.5
            y1 = cell[1] * (lixel_size + gap_size) + gap_size * 1.5
            x2 = x1 + lixel_size
            y2 = y1 + lixel_size
            canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=wire_color)
    
    for i, parking in enumerate(partition["parking"]):
        parking_color = parking_colors[i % len(parking_colors)]
        for cell in parking:
            x1 = cell[0] * (lixel_size + gap_size) + gap_size * 1.5
            y1 = cell[1] * (lixel_size + gap_size) + gap_size * 1.5
            x2 = x1 + lixel_size
            y2 = y1 + lixel_size
            canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=parking_color)


def draw_colored_map(canvas, canvas_frame, lixel_size, gap_size, map_array, colored_map):

    draw_grid(canvas, canvas_frame, lixel_size, gap_size, map_array)

    # Iterate through the colored_map to draw each colored lixel
    for row in range(len(colored_map)):
        for col in range(len(colored_map[row])):
            color = colored_map[row][col]
            if color != 1 and color != 0:  # Skip the walls or non-path cells
                x1 = col * (lixel_size + gap_size) + gap_size * 1.5
                y1 = row * (lixel_size + gap_size) + gap_size * 1.5
                x2 = x1 + lixel_size
                y2 = y1 + lixel_size
                canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)



def draw_agent(canvas, x, y, color, agent_type, lixel_size, gap_size):
    agent_size = lixel_size * 0.75
    offset = (lixel_size - agent_size) / 2
    x1 = x * (lixel_size + gap_size) + gap_size * 1.5 + offset
    y1 = y * (lixel_size + gap_size) + gap_size * 1.5 + offset
    x2 = x1 + agent_size
    y2 = y1 + agent_size
    tag = "home_agent" if agent_type == "home" else "guest_agent"
    canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color, tags=tag)

def draw_agents(canvas, home_agents, guest_agents, lixel_size, gap_size):
    for agent in home_agents:
        draw_agent(canvas, agent.pos_x, agent.pos_y, "#f20d0d", "home", lixel_size, gap_size)
    for agent in guest_agents:
        draw_agent(canvas, agent.pos_x, agent.pos_y, "#f2f20d", "guest", lixel_size, gap_size)






