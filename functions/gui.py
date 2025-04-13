import tkinter as tk
from functions.classes import Token, SingleTeamToken
import copy

class MAPDApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Map Viewer with Agents")

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        self.master.geometry(f"{window_width}x{window_height}")
        
        self.step_counter = 0  # Counter to keep track of steps
        self.playing = 0       # Play-Pause Flag

        self.map_width = 0
        self.map_height = 0
        self.lixel_state_array = []

        self.sidebar = tk.Frame(master, width=int(screen_width * 0.15), bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill='both', expand=True)

        self.home_agents = []
        self.guest_agents = []

        

        self.map=[]
        self.dijkstras_map = []
        self.colored_map = []
        self.partition_map = []
        self.partition = []
        self.loops=[]
        self.wires=[]
        self.border_map = []
        self.gates = []
        self.parking = []
        self.guest_map = []
        self.guest_dijkstras_map = []


        self.home_token=Token()
        self.guest_token=Token()
        self.combined_token = SingleTeamToken()
        self.home_tasks = []
        self.guest_tasks = []
        self.imported_H_task_count=0
        self.imported_G_task_count=0
        self.time=0

        self.coexistance_coefficient=0

        self.h_makespan_set=False
        self.g_makespan_set=False
        self.coexistance_coefficient_set=False


    def render_sidebar(self, time_label, htask_label_completed, htask_label_assigned, htask_label_intoken, htask_label_inqueue, gtask_label_completed, gtask_label_assigned, gtask_label_intoken, gtask_label_inqueue):
    
        time_label.config(text=f"Time: {self.time}")
        
        htask_label_completed.config(text=f"Completed: {self.home_token.completed_tasks} / {self.imported_H_task_count}")
        htask_label_assigned.config(text=f"Assigned: {sum(1 for agent in self.home_token.agents if agent.assigned_task is not None)}")
        htask_label_intoken.config(text=f"In Token: {len(self.home_token.unassigned_tasks)}")
        htask_label_inqueue.config(text=f"In Queue: {len(self.home_tasks)}")

        gtask_label_completed.config(text=f"Completed: {self.guest_token.completed_tasks} / {self.imported_G_task_count}")
        gtask_label_assigned.config(text=f"Assigned: {sum(1 for agent in self.guest_token.agents if agent.assigned_task is not None)}")
        gtask_label_intoken.config(text=f"In Token: {len(self.guest_token.unassigned_tasks)}")
        gtask_label_inqueue.config(text=f"In Queue: {len(self.guest_tasks)}")




    def calculate_lixel_size(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        target_width = screen_width * 0.5
        target_height = screen_height * 0.5

        lixel_size_width = (target_width - (self.map_width + 1) * (target_width // (self.map_width + 1) // 10)) / self.map_width
        lixel_size_height = (target_height - (self.map_height + 1) * (target_height // (self.map_height + 1) // 10)) / self.map_height

        self.lixel_size = min(int(lixel_size_width), int(lixel_size_height))
        self.lixel_size = max(1, self.lixel_size)
        self.gap_size = self.lixel_size // 10

    def show_partition(self):
        wire_colors = ["#c91d48", "#e96384", "#e23661", "#ef8fa7"]  # Shades of red
        loop_colors = ["#38947d", "#6bc7b0", "#46b99c", "#90d5c4"]  # Shades of green
        parking_colors = ["#386e94"]

        for i, loop in enumerate(self.loops):
            loop_color = loop_colors[i % len(loop_colors)]
            for cell in loop:
                x1 = cell[0] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                y1 = cell[1] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                x2 = x1 + self.lixel_size
                y2 = y1 + self.lixel_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=loop_color)

        for i, wire in enumerate(self.wires):
            wire_color=wire_colors[i % len(wire_colors)]
            for cell in wire:
                x1 = cell[0] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                y1 = cell[1] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                x2 = x1 + self.lixel_size
                y2 = y1 + self.lixel_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=wire_color)
        
        for i, parking in enumerate(self.parking):
            parking_color = parking_colors[i % len(parking_colors)]
            for cell in parking:
                x1 = cell[0] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                y1 = cell[1] * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                x2 = x1 + self.lixel_size
                y2 = y1 + self.lixel_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=parking_color)

    def draw_grid(self):
        self.canvas.delete("all")
        for row in range(self.map_height):
            for col in range(self.map_width):
                x1 = col * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                y1 = row * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                x2 = x1 + self.lixel_size
                y2 = y1 + self.lixel_size
                color = "black" if self.lixel_state_array[row][col] == 0 else "white"
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)

        self.canvas.place(relx=0.4, rely=0.5, anchor="center")

    def draw_agent(self, x, y, color):
        agent_size = self.lixel_size * 0.75
        offset = (self.lixel_size - agent_size) / 2
        x1 = x * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + offset
        y1 = y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + offset
        x2 = x1 + agent_size
        y2 = y1 + agent_size
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color)

    def draw_agents(self):
        for agent in self.guest_agents:
            self.draw_agent(agent.location[0], agent.location[1], "#f2f20d")
    
        for agent in self.home_agents:
            self.draw_agent(agent.location[0], agent.location[1], "#f20d0d")



    def draw_colored_map(self):

        self.draw_grid()

        # Iterate through the colored_map to draw each colored lixel
        for row in range(len(self.colored_map)):
            for col in range(len(self.colored_map[row])):
                color = self.colored_map[row][col]
                if color != 1 and color != 0:  # Skip the walls or non-path cells
                    x1 = col * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                    y1 = row * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
                    x2 = x1 + self.lixel_size
                    y2 = y1 + self.lixel_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)


    def display_map(self, game_map, game_home_agents, game_guest_agents):
        self.lixel_state_array = game_map
        self.home_agents = game_home_agents
        self.guest_agents = game_guest_agents

        self.map_height = len(self.lixel_state_array)
        self.map_width = len(self.lixel_state_array[0]) if self.lixel_state_array else 0

        self.calculate_lixel_size()

        self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
        self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

        if self.colored_map:
            self.draw_colored_map()
        else:
            self.draw_grid()
            self.show_partition()
        self.draw_agents()


    def display_tasks(self, home_agents, color):
        """
        Display tasks on the canvas by drawing small squares at the edges of the cells for start positions
        and at the corners of the cells for goal positions for tasks with states smaller than 3.
        The color of these squares is specified by the 'color' parameter.
        """
        small_square_size = self.lixel_size * 0.1
        cell_center_offset = self.lixel_size / 2 - small_square_size / 2

        for home_agent in home_agents:
            if home_agent.assigned_task:        # If the home agent has an assigned task

                if home_agent.state > 0:        # Display goal positions if going for Pickup or going for Delivery.
                    goal_x, goal_y = home_agent.assigned_task.goal

                    # Calculate goal positions for small squares at corners
                    goal_positions = [
                        (goal_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5, goal_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5),  # Top-left
                        (goal_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size, goal_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5),  # Top-right
                        (goal_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5, goal_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size),  # Bottom-left
                        (goal_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size, goal_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size)  # Bottom-right
                    ]
                    for x, y in goal_positions:
                        self.canvas.create_rectangle(x, y, x + small_square_size, y + small_square_size, fill=color, outline=color)

                if  home_agent.state == 1 or home_agent.state == 2:   # Display start position only if going for Pick Up or Reached pick up. (Not after completed pick upp)
                    start_x, start_y = home_agent.assigned_task.start

                    # Calculate start positions for small squares at edges
                    start_positions = [
                        (start_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + cell_center_offset, start_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5),  # Top
                        (start_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + cell_center_offset, start_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size),  # Bottom
                        (start_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5, start_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + cell_center_offset),  # Left
                        (start_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + self.lixel_size - small_square_size, start_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.25 + cell_center_offset)  # Right
                    ]
                    for x, y in start_positions:
                        self.canvas.create_rectangle(x, y, x + small_square_size, y + small_square_size, fill=color, outline=color)





    def display_moves(self, agents):
        arrow_color = "black"
        circle_color = "black"
        circle_radius = self.lixel_size * 0.2  # Radius of the circle relative to the lixel size
        arrow_length=0.85

        for agent in agents:
            x, y = agent.location
            next_x, next_y,_ = agent.path[0]
            #next_x, next_y, _ = agent.path[0] if agent.path[0] != [] else (x, y)

            # Calculate the center of the current location
            x_center = x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2
            y_center = y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2

            if (x, y) == (next_x, next_y):
                # Draw a circle if the next move is the same as the current location
                self.canvas.create_oval(
                    x_center - circle_radius, y_center - circle_radius,
                    x_center + circle_radius, y_center + circle_radius,
                    outline=circle_color, width=self.lixel_size/10
                )
            else:
                # Calculate the center of the next move location
                next_x_center = next_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2
                next_y_center = next_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2

                # Draw an arrow from the current location to the next move location
                self.canvas.create_line(
                    x_center, y_center, x_center + (next_x_center-x_center)*arrow_length, y_center + (next_y_center-y_center)*arrow_length,
                    arrow=tk.LAST, fill=arrow_color, width=self.lixel_size/10
                )


    def display_collision_moves(self, colliding_agents):

        error_color = "blue"
        
        arrow_color = error_color
        circle_color = error_color
        circle_radius = self.lixel_size * 0.2  # Radius of the circle relative to the lixel size
        arrow_length=1
        small_square_size = self.lixel_size * 0.1

        for agent in colliding_agents:

            x, y = agent['current_pos']
            next_x, next_y = agent['next_pos']
            #next_x, next_y, _ = agent.path[0] if agent.path[0] != [] else (x, y)


            # Higlight the cell of collision in red
            x1 = next_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            y1 = next_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            x2 = x1 + self.lixel_size
            y2 = y1 + self.lixel_size
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=error_color, fill="", width=small_square_size)



            # Calculate the center of the current location
            x_center = x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2
            y_center = y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2

            if (x, y) == (next_x, next_y):
                # Draw a circle if the next move is the same as the current location
                self.canvas.create_oval(
                    x_center - circle_radius, y_center - circle_radius,
                    x_center + circle_radius, y_center + circle_radius,
                    outline=circle_color, width=self.lixel_size/10
                )
            else:
                # Calculate the center of the next move location
                next_x_center = next_x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2
                next_y_center = next_y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + self.lixel_size / 2

                # Draw an arrow from the current location to the next move location
                self.canvas.create_line(
                    x_center, y_center, x_center + (next_x_center-x_center)*arrow_length, y_center + (next_y_center-y_center)*arrow_length,
                    arrow=tk.LAST, fill=arrow_color, width=self.lixel_size/10
                )





