import tkinter as tk
import json
from tkinter import filedialog
import copy
from functions.Apps_commons.map_calculations import find_gates, find_borders, create_border_map, create_partition_map, create_dijkstras_map
from functions.Apps_commons.gui import calculate_lixel_size, draw_grid, draw_grid_and_partitions



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
        self.partitions = []
        self.optimal_partitions = []
        self.current_partition_index = 0

        self.sidebar = tk.Frame(master, width=int(screen_width * 0.15), bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(fill='both', expand=True, side='left')

        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill='both', expand=True)





        # Button to import map
        self.import_button = tk.Button(self.sidebar, text="Import Map", command=self.import_map)
        self.import_button.pack(pady=10)

        # Button to calculate partitions
        self.partition_button = tk.Button(self.sidebar, text="Partition!", command=self.calculate_partitions)
        self.partition_button.pack(pady=5)

        # Button to show next alternative
        self.next_alternative_button = tk.Button(self.sidebar, text="Next Alternative", command=self.show_next_alternative, state=tk.DISABLED)
        self.next_alternative_button.pack(pady=5)

        # Coverage info label
        self.coverage_label = tk.Label(self.sidebar, text="Coverage: 0/0")
        self.coverage_label.pack(pady=5)

        # Partition info label
        self.partition_info_label = tk.Label(self.sidebar, text="Partition: 0/0")
        self.partition_info_label.pack(pady=5)


        # Button to export map
        self.export_button = tk.Button(self.sidebar, text="Export Map", command=self.export_game_state)
        self.export_button.pack(pady=10)


        # Button to import partitions
        self.import_button = tk.Button(self.sidebar, text="Import Partitions", command=self.import_optimal_partitions)
        self.import_button.pack(side='bottom', pady=5)

        # Button to export partitions
        self.export_button = tk.Button(self.sidebar, text="Export Partitions", command=self.export_optimal_partitions)
        self.export_button.pack(side='bottom', pady=5)






    def import_map(self):
        file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.map_array = data.get("map", [])
                self.dijkstras_map = data.get("dijkstras_map", [])

            self.total_cells = sum(sublist.count(1) for sublist in self.map_array)
            self.map_height = len(self.map_array)
            self.map_width = len(self.map_array[0]) if self.map_array else 0

            # Calculate the optimal lixel size based on the screen size and map dimensions
            self.lixel_size, self.gap_size = calculate_lixel_size(self.master.winfo_screenwidth(), self.master.winfo_screenheight(), self.map_width, self.map_height)

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            draw_grid(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array)
            


    def update_coverage_label(self):
        partition = self.optimal_partitions[self.current_partition_index]
        loop_cells = sum(len(loop) for loop in partition["loops"])
        wire_cells = sum(len(wire) for wire in partition["wires"])
        self.coverage_label.config(text=f"Coverage: {loop_cells}/{loop_cells+wire_cells}")

    def update_partition_info_label(self):
        optimal_partition_count = len(self.optimal_partitions)
        self.partition_info_label.config(text=f"Partition: {self.current_partition_index+1}/{optimal_partition_count}")

        if optimal_partition_count > 0:
            self.next_alternative_button.config(state=tk.NORMAL)
        else:
            self.next_alternative_button.config(state=tk.DISABLED)


    def calculate_partitions(self):
        all_loops = self.find_all_loops(self.map_array)
        #max_coverage_loop_sets = self.find_max_coverage_sets(self.map_array, all_loops)
        max_coverage_loop_sets = self.find_max_coverage_sets_stacked(self.map_array, all_loops)
        max_coverage_maximal_loop_sets = self.select_most_loops(max_coverage_loop_sets)
        map_partitions = self.get_map_partitions(self.map_array, max_coverage_maximal_loop_sets)
        self.optimal_partitions = self.filter_least_wire_partitions(map_partitions)

        self.current_partition_index = 0
        self.update_partition_info_label()
        self.update_coverage_label()
        if self.optimal_partitions:
            draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.optimal_partitions[self.current_partition_index])













    def show_next_alternative(self):
        self.current_partition_index = (self.current_partition_index + 1) % len(self.optimal_partitions)
        self.update_partition_info_label()
        self.update_coverage_label()
        if self.optimal_partitions:
            draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.optimal_partitions[self.current_partition_index])


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




    def create_guest_map(map_array, optimal_partition):
        # Create a deep copy of map_array
        guest_map = copy.deepcopy(map_array)
        
        # Iterate over each wire in optimal_partition
        for wire in optimal_partition['wires']:
            for coordinate in wire:
                y, x = coordinate
                guest_map[y][x] = 0  # Set the position to 0

        return guest_map








    def export_game_state(self):

        # Export map as distance lookup table.
        game = {
            "map": self.map_array,
            "dijkstras_map": self.dijkstras_map
        }

        # Partitions section
        if self.optimal_partitions:
            chosen_partition=self.optimal_partitions[self.current_partition_index]
            game["partition"] = self.switch_couples_in_array(chosen_partition)
            borders = find_borders(game["partition"])
            game["border_map"] = create_border_map(self.map_array,borders)
            game["gates"] = find_gates(borders)
            game["partition_map"] = create_partition_map(self.map_array,self.switch_couples_in_array(chosen_partition))
            game["guest_map"] = self.create_guest_map(self.map_array,chosen_partition)
            game["guest_dijkstras_map"] = create_dijkstras_map(game["guest_map"])

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(game, file, indent=4)
                print("Map data exported successfully.")

    def import_optimal_partitions(self):
        file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                self.optimal_partitions = json.load(file)

        for optimal_partition in self.optimal_partitions:
            print(optimal_partition)
        
        self.current_partition_index = 0
        self.update_partition_info_label()
        self.update_coverage_label()
        if self.optimal_partitions:
            draw_grid_and_partitions(self.canvas, self.canvas_frame, self.lixel_size, self.gap_size, self.map_array, self.optimal_partitions[self.current_partition_index])
        

    def export_optimal_partitions(self):
        
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.optimal_partitions, file, indent=4)

    def is_valid_move(self, map_2d, r, c):
        rows = len(map_2d)
        cols = len(map_2d[0])
        return 0 <= r < rows and 0 <= c < cols and map_2d[r][c] != 0

    def find_loops_from_cell(self, map_2d, start_r, start_c):
        rows = len(map_2d)
        cols = len(map_2d[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        loops = []

        def dfs(r, c, path, visited, depth):
            if (r, c) == (start_r, start_c) and depth >= 4:
                loops.append(path[:])
                return
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if self.is_valid_move(map_2d, nr, nc):
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        path.append((nr, nc))
                        dfs(nr, nc, path, visited, depth + 1)
                        path.pop()
                        visited.remove((nr, nc))
                    elif (nr, nc) == (start_r, start_c) and depth >= 4:
                        loops.append(path[:])
                        return

        visited = set()
        visited.add((start_r, start_c))
        dfs(start_r, start_c, [(start_r, start_c)], visited, 1)
        
        return loops

    def find_all_loops(self, map_2d):
        rows = len(map_2d)
        cols = len(map_2d[0])
        all_loops = []

        for r in range(rows):
            for c in range(cols):
                if map_2d[r][c] != 0:
                    loops = self.find_loops_from_cell(map_2d, r, c)
                    all_loops.extend(loops)
        
        # Remove duplicate loops (since loops are undirected, (A -> B -> C -> A) is the same as (B -> C -> A -> B))
        unique_loops = []
        seen = set()
        for loop in all_loops:
            loop_sorted = tuple(sorted(loop))
            if loop_sorted not in seen:
                seen.add(loop_sorted)
                unique_loops.append(loop)
        
        return unique_loops

    def find_max_coverage_sets(self, map_2d, loops):
        max_coverage = 0
        optimal_loop_sets = []

        def backtrack(index, covered_cells, current_set):
            nonlocal max_coverage, optimal_loop_sets

            # Base case: All loops are considered
            if index >= len(loops):
                if len(covered_cells) > max_coverage:
                    max_coverage = len(covered_cells)
                    optimal_loop_sets = [current_set]
                elif len(covered_cells) == max_coverage:
                    optimal_loop_sets.append(current_set)
                return

            # Option 1: Skip the current loop
            backtrack(index + 1, covered_cells, current_set)

            # Option 2: Include the current loop if it does not reuse any cells
            current_loop = loops[index]
            if not any(cell in covered_cells for cell in current_loop):
                new_covered_cells = covered_cells.union(current_loop)
                backtrack(index + 1, new_covered_cells, current_set + [current_loop])

        backtrack(0, set(), [])

        return optimal_loop_sets
    
    def find_max_coverage_sets_stacked(self, map_2d, loops):
        max_coverage = 0
        optimal_loop_sets = []
        stack = [(0, set(), [])]

        while stack:
            index, covered_cells, current_set = stack.pop()

            if index >= len(loops):
                if len(covered_cells) > max_coverage:
                    max_coverage = len(covered_cells)
                    optimal_loop_sets = [current_set]
                elif len(covered_cells) == max_coverage:
                    optimal_loop_sets.append(current_set)
                continue

            # Option 1: Skip the current loop
            stack.append((index + 1, covered_cells, current_set))

            # Option 2: Include the current loop if it does not reuse any cells
            current_loop = loops[index]
            if not any(cell in covered_cells for cell in current_loop):
                new_covered_cells = covered_cells.union(current_loop)
                stack.append((index + 1, new_covered_cells, current_set + [current_loop]))
        return optimal_loop_sets

    def select_most_loops(self, loop_sets):
        max_length = max(len(loop_set) for loop_set in loop_sets)
        max_loops_sets = [loop_set for loop_set in loop_sets if len(loop_set) == max_length]
        return max_loops_sets

    def get_map_partition(self, map_2d, maximal_loop_set):
        partition = {"loops": maximal_loop_set, "wires": []}

        # Create a set of cells covered by loops
        covered_cells = set()
        for loop in maximal_loop_set:
            covered_cells.update(loop)

        # Identify connected "wires" on the map
        def dfs(r, c, wire):
            if map_2d[r][c] == 0 or (r, c) in wire:
                return
            wire.append((r, c))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(map_2d) and 0 <= nc < len(map_2d[0]):
                    if map_2d[nr][nc] != 0 and (nr, nc) not in covered_cells:
                        dfs(nr, nc, wire)

        wires_set = set()
        for r in range(len(map_2d)):
            for c in range(len(map_2d[0])):
                if map_2d[r][c] != 0 and (r, c) not in covered_cells:
                    wire = []
                    dfs(r, c, wire)
                    if wire:
                        wire_set = frozenset(wire)
                        if wire_set not in wires_set:
                            partition["wires"].append(wire)
                            wires_set.add(wire_set)

        return partition

    def get_map_partitions(self, map_2d, maximal_loop_sets):
        map_partitions = []
        for maximal_loop_set in maximal_loop_sets:
            partition = self.get_map_partition(map_2d, maximal_loop_set)
            map_partitions.append(partition)
        return map_partitions

    def filter_least_wire_partitions(self, map_partitions):
        min_wire_sets = min(len(partition["wires"]) for partition in map_partitions)
        least_wire_partitions = [partition for partition in map_partitions if len(partition["wires"]) == min_wire_sets]
        return least_wire_partitions

def main():
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
