import tkinter as tk
import random
import json
from tkinter import filedialog, messagebox
from functions.Apps_commons.gui import calculate_lixel_size, draw_grid_and_partitions, print_map_and_agents, draw_agent, draw_agents, draw_colored_map
from functions.Apps_commons.random_placement import place_agents


class MapApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Map Viewer with Agents")

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

        self.sidebar = tk.Frame(master, width=int(screen_width * 0.15), bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(fill='both', expand=True, side='left')

        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill='both', expand=True)

        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<Button-3>", self.right_click)

        # Button to import map
        self.import_button = tk.Button(self.sidebar, text="Import Map", command=self.import_game)
        self.import_button.pack(pady=5)


        # Input section for Home Agent #
        self.home_frame = tk.Frame(self.sidebar)
        self.home_frame.pack(pady=5)
        self.home_label = tk.Label(self.home_frame, text="Home Agent #:")
        self.home_label.pack(side="left", padx=5)
        self.home_entry = tk.Entry(self.home_frame)
        self.home_entry.pack(side="left")

        # Input section for Guest Agent #
        self.guest_frame = tk.Frame(self.sidebar)
        self.guest_frame.pack(pady=5)
        self.guest_label = tk.Label(self.guest_frame, text="Guest Agent #:")
        self.guest_label.pack(side="left", padx=5)
        self.guest_entry = tk.Entry(self.guest_frame)
        self.guest_entry.pack(side="left")

        # Button to update home agents
        self.update_home_button = tk.Button(self.sidebar, text="Randomize Home Agents", command=self.update_home_agents)
        self.update_home_button.pack(pady=10)

        # Button to update guest agents
        self.update_guest_button = tk.Button(self.sidebar, text="Randomize Guest Agents", command=self.update_guest_agents)
        self.update_guest_button.pack(pady=10)

        # Button to update all agents
        self.update_all_button = tk.Button(self.sidebar, text="Randomize All Agents", command=self.update_all_agents)
        self.update_all_button.pack(pady=10)

        # Button to export game state
        self.export_button = tk.Button(self.sidebar, text="Export Game State", command=self.export_game)
        self.export_button.pack(pady=10)

        self.home_agents = []
        self.guest_agents = []

        self.loops = []
        self.wires = []



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
                    self.guest_dijkstras_map = data.get("guest_dijkstras_map", [])
                    self.gates= data.get("gates",[])
                    self.parking= data.get("parking",[])
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

                    draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)
                    self.update_agent_counts()


            self.total_cells = sum(sublist.count(1) for sublist in self.map_array)
            self.map_height = len(self.map_array)
            self.map_width = len(self.map_array[0]) if self.map_array else 0

            # Calculate the optimal lixel size based on the screen size and map dimensions
            self.lixel_size, self.gap_size = calculate_lixel_size(self.master.winfo_screenwidth(), self.master.winfo_screenheight(), self.map_width, self.map_height)

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            #draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.partition)
            draw_colored_map(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.colored_map)
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
            "guest_dijkstras_map": self.guest_dijkstras_map,
            "parking": self.parking,
            "gates": self.gates,
            "border_map": self.border_map
        }


        # Home agents section
        if self.home_agents:
            game['home_agents'] = [{'color': '#f20d0d', 'location': (agent.pos_x, agent.pos_y)} for agent in self.home_agents]

        # Guest agents section
        if self.guest_agents:
            game['guest_agents'] = [{'color': '#f2f20d', 'location': (agent.pos_x, agent.pos_y)} for agent in self.guest_agents]

        # Save game state to a JSON file
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(game, file, indent=4)
                print("Map data exported successfully.")







         
    def left_click(self, event):
        # Get the coordinates of the clicked cell
        x = event.x // (self.lixel_size + self.gap_size)
        y = event.y // (self.lixel_size + self.gap_size)

        # If the cell has a home agent, remove it
        if (x, y) in [(agent.pos_x, agent.pos_y) for agent in self.home_agents]:
            self.home_agents = [agent for agent in self.home_agents if (agent.pos_x, agent.pos_y) != (x, y)]
            self.update_agent_counts()

        # If the cell is empty or has a guest agent, add a home agent
        elif self.map_array[y][x] == 1 or (x, y) in [(agent.pos_x, agent.pos_y) for agent in self.guest_agents]:
            # Remove any existing guest agent in the cell
            self.guest_agents = [agent for agent in self.guest_agents if (agent.pos_x, agent.pos_y) != (x, y)]

            # Add a home agent
            self.home_agents.append(Agent(x, y))
            self.update_agent_counts()
        
        # Redraw the map
        #draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.partition)
        draw_colored_map(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.colored_map)
        draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)

    def right_click(self, event):
        # Get the coordinates of the clicked cell
        x = event.x // (self.lixel_size + self.gap_size)
        y = event.y // (self.lixel_size + self.gap_size)

        # If the cell has a guest agent, remove it
        if (x, y) in [(agent.pos_x, agent.pos_y) for agent in self.guest_agents]:
            self.guest_agents = [agent for agent in self.guest_agents if (agent.pos_x, agent.pos_y) != (x, y)]
            self.update_agent_counts()

        # If the cell is empty or has a home agent, add a guest agent
        elif self.map_array[y][x] == 1 or (x, y) in [(agent.pos_x, agent.pos_y) for agent in self.home_agents]:
            # Remove any existing home agent in the cell
            self.home_agents = [agent for agent in self.home_agents if (agent.pos_x, agent.pos_y) != (x, y)]

            # Add a guest agent
            self.guest_agents.append(Agent(x, y))
            self.update_agent_counts()
        
        # Redraw the map
        #draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.partition)
        draw_colored_map(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.colored_map)
        draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)

    def update_agent_counts(self):
        self.home_entry.delete(0, tk.END)
        self.home_entry.insert(0, str(len(self.home_agents)))

        self.guest_entry.delete(0, tk.END)
        self.guest_entry.insert(0, str(len(self.guest_agents)))















    def update_home_agents(self):
        try:
            home_agent_count = int(self.home_entry.get())
            if self.validate_home_input(home_agent_count, len(self.guest_agents)):
                self.canvas.delete("home_agent")
                self.home_agents = place_agents(home_agent_count, "home", self.partition, self.home_agents, self.guest_agents)
                draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the number of home agents.")

    def update_guest_agents(self):
        #try:
            guest_agent_count = int(self.guest_entry.get())
            if self.validate_guest_input(len(self.home_agents), guest_agent_count):
                self.canvas.delete("guest_agent")
                self.guest_agents = place_agents(guest_agent_count, "guest", self.partition, self.home_agents, self.guest_agents)
                draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)
        #except ValueError:
           # messagebox.showerror("Invalid Input", "Please enter a valid integer for the number of guest agents.")

    def update_all_agents(self):
        try:
            home_agent_count = int(self.home_entry.get())
            guest_agent_count = int(self.guest_entry.get())
            if self.validate_all_input(home_agent_count, guest_agent_count):
                self.canvas.delete("home_agent")
                self.canvas.delete("guest_agent")
                self.home_agents = place_agents(home_agent_count, "home", self.partition, self.home_agents, self.guest_agents)
                self.guest_agents = place_agents(guest_agent_count, "guest", self.partition, self.home_agents, self.guest_agents)
                draw_agents(self.canvas, self.home_agents, self.guest_agents, self.lixel_size, self.gap_size)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for the number of agents.")




    def validate_home_input(self, home_agent_count, guest_agent_count):
        if home_agent_count < 0 or guest_agent_count < 0:
            messagebox.showerror("Invalid Input", "Number of agents cannot be negative.")
            return False

        if home_agent_count > self.total_cells - len(self.guest_agents):
            messagebox.showerror("Invalid Input", "Number of home agents exceeds available cells.")
            return False

        return True

    def validate_guest_input(self, home_agent_count, guest_agent_count):
        if home_agent_count < 0 or guest_agent_count < 0:
            messagebox.showerror("Invalid Input", "Number of agents cannot be negative.")
            return False

        if guest_agent_count > self.total_cells - len(self.home_agents):
            messagebox.showerror("Invalid Input", "Number of guest agents exceeds available cells.")
            return False

        return True

    def validate_all_input(self, home_agent_count, guest_agent_count):
        if home_agent_count < 0 or guest_agent_count < 0:
            messagebox.showerror("Invalid Input", "Number of agents cannot be negative.")
            return False

        if home_agent_count + guest_agent_count > self.total_cells:
            messagebox.showerror("Invalid Input", "Total number of agents exceeds available cells.")
            return False

        return True




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
