import tkinter as tk
import json
from tkinter import filedialog
import copy

from functions.Apps_commons.map_calculations import find_borders, find_gates, find_parking, create_border_map, create_partition_map, create_dijkstras_map
from functions.Apps_commons.gui import calculate_lixel_size, draw_colored_map


class MapApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Map Viewer with Partitions")

        # Set the initial window size to 0.75 of the screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        self.master.geometry(f"{window_width}x{window_height}")

        self.lixel_size = 20  # Lixel = Large Pixel
        self.gap_size = self.lixel_size // 10

        self.map_width = 0
        self.map_height = 0
        self.map_array = []
        self.colored_map = []  # Initialize colored_map
        self.selected_color = "#38947d"  # Default color is green

        self.sidebar = tk.Frame(master, width=int(screen_width * 0.15), bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(fill='both', expand=True, side='left')

        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill='both', expand=True)

        # Button to import map
        self.import_button = tk.Button(self.sidebar, text="Import Map", command=self.import_map)
        self.import_button.pack(pady=5)

        # Button to export map
        self.export_button = tk.Button(self.sidebar, text="Export Map", command=self.export_game_state)
        self.export_button.pack(pady=5)



        # Green shades buttons
        self.green_shades_frame = tk.Frame(self.sidebar)
        self.green_shades_frame.pack(pady=5)

        self.green_tones = ["#38947d", "#46b99c", "#6bc7b0","#90d5c4"]
        for shade in self.green_tones:
            btn = tk.Button(self.green_shades_frame, bg=shade, width=3, height=3, command=lambda s=shade: self.set_color(s))
            btn.pack(side='left', padx=2)

        # Red shades buttons
        self.red_shades_frame = tk.Frame(self.sidebar)
        self.red_shades_frame.pack(pady=5)

        self.red_tones = ["#c91d48", "#e23661", "#e96384", "#ef8fa7"]
        for shade in self.red_tones:
            btn = tk.Button(self.red_shades_frame, bg=shade, width=3, height=3, command=lambda s=shade: self.set_color(s))
            btn.pack(side='left', padx=2)

        # Blue shades buttons
        self.blue_shades_frame = tk.Frame(self.sidebar)
        self.blue_shades_frame.pack(pady=5)

        self.blue_tone = ["#386e94"]  # Single tone of blue
        for shade in self.blue_tone:
            btn = tk.Button(self.blue_shades_frame, bg=shade, width=3, height=3, command=lambda s=shade: self.set_color(s))
            btn.pack(side='left', padx=2)

        # Binding mouse click event to color lixels
        self.canvas.bind("<B1-Motion>", self.color_lixel)
        self.canvas.bind("<Button-1>", self.color_lixel)
        self.canvas.bind("<B3-Motion>", self.delete_color  )
        self.canvas.bind("<Button-3>", self.delete_color )




    def calculate_colored_map(self):
        # Define colors for different partitions
        wire_colors = ["#c91d48", "#e96384", "#e23661", "#ef8fa7"]  # Shades of red
        loop_colors = ["#38947d", "#6bc7b0", "#46b99c", "#90d5c4"]  # Shades of green
        parking_colors = ["#386e94"]  # Parking colors

        # Extract the partitions from the app's partition structure
        loops = self.partition['loops']
        wires = self.partition['wires']
        parking = self.partition.get('parking', [])

        # Create a copy of the map_array to color it
        colored_map = [row.copy() for row in self.map_array]

        # Color loop cells
        for i, loop in enumerate(loops):
            loop_color = loop_colors[i % len(loop_colors)]
            for cell in loop:
                x, y = cell  # Assuming the cell is given as (x, y)
                colored_map[y][x] = loop_color  # Access colored_map using (y, x)

        # Color wire cells
        for i, wire in enumerate(wires):
            wire_color = wire_colors[i % len(wire_colors)]
            for cell in wire:
                x, y = cell  # Assuming the cell is given as (x, y)
                colored_map[y][x] = wire_color  # Access colored_map using (y, x)

        # Color parking cells
        for i, parking_area in enumerate(parking):
            parking_color = parking_colors[i % len(parking_colors)]
            for cell in parking_area:
                x, y = cell  # Assuming the cell is given as (x, y)
                colored_map[y][x] = parking_color  # Access colored_map using (y, x)

        return colored_map




    def draw_gates_on_canvas(self):
        gate_color = "#800080"  # Purple color for gates
        gate_radius = self.lixel_size * 0.75 # Radius for the small circle

        for gate_pair in self.gates:
            for gate in gate_pair:
                x = gate[0]
                y = gate[1]

                offset = (self.lixel_size - gate_radius) / 2
                x1 = x * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + offset
                y1 = y * (self.lixel_size + self.gap_size) + self.gap_size * 1.5 + offset
                x2 = x1 + gate_radius
                y2 = y1 + gate_radius
                self.canvas.create_oval(x1, y1, x2, y2, outline="", fill=gate_color)


    def import_map(self):
        file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.map_array = data.get("map", [])
                self.dijkstras_map = data.get("dijkstras_map", [])
                for row in self.map_array:
                    print(row)
                self.partition = data.get("partition", [])
                self.colored_map = data.get("colored_map", [])
                if self.partition != [] and self.colored_map == []:
                    self.colored_map = self.calculate_colored_map(self.partition)
                if self.colored_map == []:
                    self.colored_map = copy.deepcopy(self.map_array)
                self.gates = data.get("gates", [])


            self.total_cells = sum(sublist.count(1) for sublist in self.map_array)
            self.map_height = len(self.map_array)
            self.map_width = len(self.map_array[0]) if self.map_array else 0

            # Calculate the optimal lixel size based on the screen size and map dimensions
            self.lixel_size, self.gap_size = calculate_lixel_size(self.master.winfo_screenwidth(), self.master.winfo_screenheight(), self.map_width, self.map_height)

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            draw_colored_map(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.colored_map)
            #self.draw_gates_on_canvas()



    def delete_color(self, event):
        last_color=self.selected_color
        self.selected_color="white"
        x = event.x
        y = event.y
        col = x // (self.lixel_size + self.gap_size)
        row = y // (self.lixel_size + self.gap_size)

        if 0 <= row < self.map_height and 0 <= col < self.map_width and self.map_array[row][col] == 1:
            self.colored_map[row][col] = 1  # Update colored_map instead of map_array
            x1 = col * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            y1 = row * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            x2 = x1 + self.lixel_size
            y2 = y1 + self.lixel_size
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=self.selected_color)

        self.selected_color=last_color

    def set_color(self, color):
        self.selected_color = color

    def print_colored_map(self):
        for row in self.colored_map:
            print(" ".join(str(cell) for cell in row))


    def color_lixel(self, event):
        x = event.x
        y = event.y
        col = x // (self.lixel_size + self.gap_size)
        row = y // (self.lixel_size + self.gap_size)

        if 0 <= row < self.map_height and 0 <= col < self.map_width and self.map_array[row][col] == 1:
            self.colored_map[row][col] = self.selected_color  # Update colored_map instead of map_array
            x1 = col * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            y1 = row * (self.lixel_size + self.gap_size) + self.gap_size * 1.5
            x2 = x1 + self.lixel_size
            y2 = y1 + self.lixel_size
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=self.selected_color)





            
    def switch_couples_in_array(self, optimal_partitions):
        # Helper function to switch the coordinates in a couple
        def switch_coordinates(couple):
            return (couple[1], couple[0])

        # Function to switch couples in a single optimal_partition
        def switch_couples(optimal_partition):
            # Switch couples in loops
            new_loops = [
                [switch_coordinates(couple) for couple in loop]
                for loop in optimal_partition['loops']
            ]
            
            # Switch couples in wires
            new_wires = [
                [switch_coordinates(couple) for couple in wire]
                for wire in optimal_partition['wires']
            ]
            
            # Return the modified optimal_partition
            return {
                'loops': new_loops,
                'wires': new_wires
            }

        # If the input is a single dictionary, convert it to a list
        if isinstance(optimal_partitions, dict):
            optimal_partitions = [optimal_partitions]

        # Apply switch_couples to each optimal_partition in the array
        switched_partitions = [switch_couples(partition) for partition in optimal_partitions]

        # If the input was a single dictionary, return a single dictionary
        if len(switched_partitions) == 1:
            return switched_partitions[0]
        
        return switched_partitions


    def find_partition(self, colored_map_original):

        colored_map = copy.deepcopy(colored_map_original)

        loops = []
        wires = []
        parking = []

        # Define directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Function to perform DFS to find connected components
        def dfs(row, col, color, component_type):
            component = []  # List to store the coordinates of the connected component
            stack = [(row, col)]  # Stack for DFS

            while stack:
                r, c = stack.pop()
                if 0 <= r < len(colored_map) and 0 <= c < len(colored_map[0]) and colored_map[r][c] == color:
                    component.append((c, r))  # Adjust coordinate format
                    colored_map[r][c] = None  # Mark visited
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < len(colored_map) and 0 <= nc < len(colored_map[0]) and colored_map[nr][nc] == color:
                            stack.append((nr, nc))

            if component_type == "loop":
                loops.append(component)
            elif component_type == "wire":
                wires.append(component)
            else:
                parking.append(component)

        # Iterate through the colored map to find loops and wires
        for row in range(len(colored_map)):
            for col in range(len(colored_map[0])):
                color = colored_map[row][col]
                if color in ["#38947d", "#46b99c", "#6bc7b0", "#90d5c4"]:
                    dfs(row, col, color, "loop")
                elif color in ["#c91d48", "#e23661", "#e96384", "#ef8fa7"]:
                    dfs(row, col, color, "wire")
                elif color in ["#386e94"]:
                    dfs(row, col, color, "parking")


        return {'loops': loops, 'wires': wires, 'parking': parking}


    def create_guest_map(self, map_array, optimal_partition):
        # Create a deep copy of map_array
        guest_map = copy.deepcopy(map_array)
        
        # Iterate over each wire in optimal_partition
        for wire in optimal_partition['wires']:
            for coordinate in wire:
                x, y = coordinate
                guest_map[y][x] = 0  # Set the position to 0
        
        for parking in optimal_partition['parking']:
            for coordinate in parking:
                x, y = coordinate
                guest_map[y][x] = 0  # Set the position to 0

        return guest_map


    def export_game_state(self):
        # Export map as distance lookup table.

        game = {
            "map": self.map_array,
            "dijkstras_map": self.dijkstras_map,
            "colored_map": self.colored_map
        }

        self.partition = self.find_partition(self.colored_map)



        # Partitions section
        if self.partition :
            game["partition"] = self.partition
            borders = find_borders(self.partition)
            game["border_map"] = create_border_map(self.map_array,borders)
            game["gates"] = find_gates(borders)
            game["parking"] = find_parking(self.partition)
            game["partition_map"]= create_partition_map(self.map_array,self.partition)
            game["guest_map"] = self.create_guest_map(self.map_array,self.partition)
            game["guest_dijkstras_map"] = create_dijkstras_map(game["guest_map"])



        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(game, file, indent=4)
                print("Map data exported successfully.")







def main():
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
