import tkinter as tk                    # Map Drawer
import json                             # Export, Import
from tkinter import filedialog          # Import

from functions.Apps_commons.map_calculations import create_dijkstras_map
from functions.Apps_commons.gui import print_map

class DrawingApp:
    def __init__(self, master):
        self.master = master
        self.lixel_size = 20    # Lixel = Large Pixel
        self.map_width = 10
        self.map_height = 10
        self.gap_size = self.lixel_size // 10

        self.map_array = [[0] * self.map_width for _ in range(self.map_height)]

        self.sidebar = tk.Frame(master, width=200, bg='grey')
        self.sidebar.pack(expand=False, fill='both', side='right', anchor='nw')

        self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
        self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

        self.master.title("Map Drawer")

        self.scrollbar_x = tk.Scrollbar(master, orient=tk.HORIZONTAL)
        self.scrollbar_y = tk.Scrollbar(master, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="black",
                                xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)
        self.scrollbar_x.config(command=self.canvas.xview)
        self.scrollbar_y.config(command=self.canvas.yview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side="left")

        self.canvas.bind("<B1-Motion>", lambda event: self.paint(event, "white"))
        self.canvas.bind("<Button-1>", lambda event: self.paint(event, "white"))
        self.canvas.bind("<B3-Motion>", lambda event: self.paint(event, "black"))
        self.canvas.bind("<Button-3>", lambda event: self.paint(event, "black"))
        self.master.bind("<Return>", lambda event: self.update_all())

        self.draw_grid()

        # Input section for changing map width
        self.width_frame = tk.Frame(self.sidebar)
        self.width_frame.pack(pady=5)
        self.width_label = tk.Label(self.width_frame, text="Width (Cells):")
        self.width_label.pack(side="left", padx=5)
        self.width_entry = tk.Entry(self.width_frame)
        self.width_entry.insert(tk.END, f"{self.map_width}")
        self.width_entry.pack(side="left")

        # Input section for changing map height
        self.height_frame = tk.Frame(self.sidebar)
        self.height_frame.pack(pady=5)
        self.height_label = tk.Label(self.height_frame, text="Height (Cells):")
        self.height_label.pack(side="left", padx=5)
        self.height_entry = tk.Entry(self.height_frame)
        self.height_entry.insert(tk.END, f"{self.map_height}")
        self.height_entry.pack(side="left")

        # Input section for changing lixel size
        self.lixel_size_frame = tk.Frame(self.sidebar)
        self.lixel_size_frame.pack(pady=5)
        self.lixel_size_label = tk.Label(self.lixel_size_frame, text="Cell Size (Pixels):")
        self.lixel_size_label.pack(side="left", padx=5)
        self.lixel_size_entry = tk.Entry(self.lixel_size_frame)
        self.lixel_size_entry.insert(tk.END, f"{self.lixel_size}")
        self.lixel_size_entry.pack(side="left")

        # Button to update map
        self.update_button = tk.Button(self.sidebar, text="Update Map", command=self.update_all)
        self.update_button.pack(pady=10)

        # Button to clear map
        self.clear_button = tk.Button(self.sidebar, text="Clear", command=self.clear_map)
        self.clear_button.pack(pady=5)

        # Button to import map
        self.import_button = tk.Button(self.sidebar, text="Import Map", command=self.import_map)
        self.import_button.pack(pady=5)

        # Button to export map
        self.export_button = tk.Button(self.sidebar, text="Export Map", command=self.export_map)
        self.export_button.pack(pady=5)

        self.update_min_size()

    def draw_grid(self):
        self.canvas.delete("all")
        for row in range(self.map_height):
            for col in range(self.map_width):
                x1 = col * (self.lixel_size + self.gap_size) + self.gap_size * 2
                y1 = row * (self.lixel_size + self.gap_size) + self.gap_size * 2
                x2 = x1 + self.lixel_size
                y2 = y1 + self.lixel_size
                color = "white" if self.map_array[row][col] == 1 else "black"
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)





    def paint(self, event, color):
        x = min(max(event.x // (self.lixel_size + self.gap_size), 0), self.map_width - 1)
        y = min(max(event.y // (self.lixel_size + self.gap_size), 0), self.map_height - 1)
        x1 = max(x * (self.lixel_size + self.gap_size) + self.gap_size * 2, self.gap_size * 2)
        y1 = max(y * (self.lixel_size + self.gap_size) + self.gap_size * 2, self.gap_size * 2)
        x2 = x1 + self.lixel_size
        y2 = y1 + self.lixel_size
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill=color)

        lixel_row = y
        lixel_col = x
        self.map_array[lixel_row][lixel_col] = 1 if color == "white" else 0
        print_map(self.map_array)

    def clear_map(self):
        self.map_array = [[0] * self.map_width for _ in range(self.map_height)]
        self.draw_grid()



    def update_map_size(self):
        try:
            new_width = int(self.width_entry.get())
            new_height = int(self.height_entry.get())
            if new_width <= 0 or new_height <= 0:
                raise ValueError("Size must be positive")

            old_width = self.map_width
            old_height = self.map_height
            old_state = self.map_array

            self.map_width = new_width
            self.map_height = new_height
            self.map_array = [[0] * new_width for _ in range(new_height)]

            offset_x = (new_width - old_width) // 2
            offset_y = (new_height - old_height) // 2

            for i in range(old_height):
                for j in range(old_width):
                    if 0 <= i + offset_y < new_height and 0 <= j + offset_x < new_width:
                        self.map_array[i + offset_y][j + offset_x] = old_state[i][j]

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            self.draw_grid()
            self.update_min_size()
            self.update_window_size()
        except ValueError:
            print("Invalid input. Please enter positive integers for width and height.")

    def update_lixel_size(self):
        try:
            new_size = int(self.lixel_size_entry.get())
            if new_size <= 0:
                raise ValueError("Size must be positive")
            self.lixel_size = new_size
            self.gap_size = self.lixel_size // 10

            self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
            self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size

            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            self.draw_grid()
            self.update_min_size()
            self.update_window_size()
        except ValueError:
            print("Invalid input. Please enter a positive integer for lixel size.")

    def update_min_size(self):
        self.master.update_idletasks()
        min_width = self.master.winfo_reqwidth()
        min_height = self.master.winfo_reqheight()
        self.master.minsize(min_width, min_height)

    def update_all(self):
        self.update_map_size()
        self.update_lixel_size()

    def update_window_size(self):
        canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
        canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size
        sidebar_width = self.sidebar.winfo_width()
        total_width = canvas_width + sidebar_width
        total_height = max(canvas_height, self.master.winfo_height())
        self.master.geometry(f"{total_width}x{total_height}")





    def import_map(self):
        try:
            file_path = filedialog.askopenfilename(title="Open Map JSON File", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, "r") as file:
                    data = json.load(file)
                    self.map_array = data.get("map", [])


                    self.map_height = len(self.map_array)
                    self.map_width = len(self.map_array[0]) if self.map_array else 0
                    self.canvas_width = self.map_width * (self.lixel_size + self.gap_size) + self.gap_size
                    self.canvas_height = self.map_height * (self.lixel_size + self.gap_size) + self.gap_size
                    self.canvas.config(width=self.canvas_width, height=self.canvas_height)
                    self.width_entry.delete(0, tk.END)
                    self.width_entry.insert(tk.END, f"{self.map_width}")
                    self.height_entry.delete(0, tk.END)
                    self.height_entry.insert(tk.END, f"{self.map_height}")
                    self.draw_grid()
                    self.update_min_size()
                    self.update_window_size()
                    print("Map data imported successfully.")
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file '{file_path}'.")
        except Exception as e:
            print(f"Error importing map data: {e}")


    def export_map(self):
        try:
            # Find the bounding box of the map
            min_row, max_row = self.find_bounding_rows()
            min_col, max_col = self.find_bounding_cols()

            # Trim the map array
            trimmed_map = [row[min_col:max_col + 1] for row in self.map_array[min_row:max_row + 1]]

            # Create the game object
            game = {
                "map": trimmed_map,
                "dijkstras_map": create_dijkstras_map(trimmed_map)
            }

            # Ask the user to save the file
            file_path = filedialog.asksaveasfilename(
                title="Save Map JSON File",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )

            if file_path:
                with open(file_path, "w") as file:
                    json.dump(game, file, indent=4)
                print("Map data exported successfully.")
        except Exception as e:
            print(f"Error exporting map data: {e}")



    def find_bounding_rows(self):
        # Find the first and last rows with non-zero elements
        min_row = max_row = None
        for i, row in enumerate(self.map_array):
            if any(row):
                if min_row is None:
                    min_row = i
                max_row = i
        return min_row, max_row

    def find_bounding_cols(self):
        # Find the first and last columns with non-zero elements
        min_col = max_col = None
        for row in self.map_array:
            if any(row):
                start_col = row.index(1)
                end_col = len(row) - row[::-1].index(1) - 1
                if min_col is None or start_col < min_col:
                    min_col = start_col
                if max_col is None or end_col > max_col:
                    max_col = end_col
        return min_col, max_col



def main():
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
