import tkinter as tk
import random
import json
from tkinter import filedialog, messagebox
from functions.Apps_commons.gui import calculate_lixel_size, draw_grid_and_partitions, print_map_and_agents, draw_agents


class MapApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Task Generator")

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
        self.guest_map = []

        self.sidebar = tk.Frame(master, width=int(screen_width * 0.15), bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(fill='both', expand=True, side='left')

        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill='both', expand=True)

        # Button to import map
        self.import_button = tk.Button(self.sidebar, text="Import Map", command=self.import_game)
        self.import_button.pack(pady=5)


        # Input section for Home Agent #
        self.home_frame = tk.Frame(self.sidebar)
        self.home_frame.pack(pady=5)
        self.home_label = tk.Label(self.home_frame, text="Home Tasks #:")
        self.home_label.pack(side="left", padx=5)
        self.home_entry = tk.Entry(self.home_frame)
        self.home_entry.pack(side="left")

        # Input section for Guest Agent #
        self.guest_frame = tk.Frame(self.sidebar)
        self.guest_frame.pack(pady=5)
        self.guest_label = tk.Label(self.guest_frame, text="Guest Tasks #:")
        self.guest_label.pack(side="left", padx=5)
        self.guest_entry = tk.Entry(self.guest_frame)
        self.guest_entry.pack(side="left")

        # Button to generate home tasks
        self.home_task_button = tk.Button(self.sidebar, text="Randomly Add Home Tasks", command=self.generate_home_tasks)
        self.home_task_button.pack(pady=10)
        self.home_task_button.config(state="disabled")  # Initially disabled

        # Button to generate guest tasks
        self.guest_task_button = tk.Button(self.sidebar, text="Randomly Add Guest Tasks", command=self.generate_guest_tasks)
        self.guest_task_button.pack(pady=10)
        self.guest_task_button.config(state="disabled")  # Initially disabled

        # Button to export game state
        self.export_button = tk.Button(self.sidebar, text="Export Game State", command=self.export_game)
        self.export_button.pack(pady=10)

        self.home_agents = []
        self.guest_agents = []

        self.home_tasks = []
        self.guest_tasks = []



    def import_game(self):
        file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.map_array = data.get("map", [])
                self.dijkstras_map = data.get("dijkstras_map", [])

                try:
                    self.colored_map = data.get("colored_map", [])
                    self.partition_map = data.get("partition_map", [])
                    self.partition = data.get("partition", [])
                    self.guest_map = data.get("guest_map", [])
                    self.gates= data.get("gates",[])
                    self.parking=data.get("parking",[])
                    self.guest_dijkstras_map=data.get("guest_dijkstras_map",[])
                    self.border_map= data.get("border_map",[])
                except:
                    pass

                try:
                    # Load home agents
                    self.home_agents = [Agent(agent['location'][0], agent['location'][1]) for agent in data.get('home_agents', [])]
                except:
                    pass

                try:
                    # Load guest agents
                    self.guest_agents = [Agent(agent['location'][0], agent['location'][1]) for agent in data.get('guest_agents', [])]
                except:
                    pass

                 # Enable/Disable task buttons based on the presence of agents
                if self.home_agents:
                    self.home_task_button.config(state="normal")
                else:
                    self.home_task_button.config(state="disabled")

                if self.guest_agents:
                    self.guest_task_button.config(state="normal")
                else:
                    self.guest_task_button.config(state="disabled")


            self.total_cells = sum(sublist.count(1) for sublist in self.map_array)
            self.map_height = len(self.map_array)
            self.map_width = len(self.map_array[0]) if self.map_array else 0

            # Calculate the optimal lixel size based on the screen size and map dimensions
            self.lixel_size, self.gap_size = calculate_lixel_size(self.master.winfo_screenwidth(), self.master.winfo_screenheight(), self.map_width, self.map_height)

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.partition)
            draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)
            print_map_and_agents(self.map_array, self.home_agents, self.guest_agents)

    def export_game(self):
       
        
        print_map_and_agents(self.map_array, self.home_agents, self.guest_agents)
        game = {
            "map": self.map_array,
            "dijkstras_map": self.dijkstras_map,
            "colored_map": self.colored_map,
            "partition": self.partition,
            "partition_map": self.partition_map,
            "guest_map": self.guest_map,
            "gates": self.gates,
            "parking": self.parking,
            "guest_dijkstras_map": self.guest_dijkstras_map,
            "border_map": self.border_map
        }


        # Home agents section
        if self.home_agents:
            game['home_agents'] = [{'color': '#f20d0d', 'location': (agent.pos_x, agent.pos_y)} for agent in self.home_agents]
            game['home_tasks'] = self.home_tasks

        # Guest agents section
        if self.guest_agents:
            game['guest_agents'] = [{'color': '#f2f20d', 'location': (agent.pos_x, agent.pos_y)} for agent in self.guest_agents]
            game['guest_tasks'] = self.guest_tasks

        # Save game state to a JSON file
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(game, file, indent=4)
                print("Map data exported successfully.")












    def generate_home_tasks(self):
        try:
            task_count = int(self.home_entry.get())
            if task_count > 0:
                self.home_tasks = self.generate_tasks(task_count, self.map_array)
                print(f"Home Tasks Generated: {self.home_tasks}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the number of home tasks.")

    def generate_guest_tasks(self):
        try:
            task_count = int(self.guest_entry.get())
            if task_count > 0:
                self.guest_tasks = self.generate_tasks(task_count, self.guest_map)
                print(f"Guest Tasks Generated: {self.guest_tasks}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the number of guest tasks.")

    def generate_tasks(self, task_count, map_data):
        valid_positions = [(x, y) for y in range(len(map_data)) for x in range(len(map_data[0])) if map_data[y][x] == 1]
        tasks = []
        for _ in range(task_count):
            if len(valid_positions) >= 2:
                task = random.sample(valid_positions, 2)  # Pick two distinct x,y positions
                tasks.append(task)
        return tasks



class Agent:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y

def main():
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
