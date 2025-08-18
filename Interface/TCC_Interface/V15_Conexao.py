import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image, ImageTk
import numpy as np
import random
import math
import statistics
import serial.tools.list_ports
import socket

class SensorDashboard:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.initialize_variables()
        self.create_widgets()
        self.update_graph_display()

    def setup_window(self):
        self.root.title("Dashboard de Sensores")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        ctk.set_appearance_mode("System")

    def initialize_variables(self):
        self.data_streams = {
            'pitch': {'x': [], 'y': [], 'color': 'r', 'label': 'Pitch'},
            'raw': {'x': [], 'y': [], 'color': 'g', 'label': 'Raw'},
            'yaw': {'x': [], 'y': [], 'color': 'b', 'label': 'Yaw'}
        }
        self.check_vars = {name: tk.BooleanVar(value=True) for name in self.data_streams}
        self.single_graph_mode = tk.BooleanVar(value=False)
        self.random_data = tk.BooleanVar(value=False)
        self.angular_test_data = tk.BooleanVar(value=False)

        self.paused_acquisition = False
        self.angular_time_step = 0
        self.connection_mode = None
        self.serial_conn = None
        self.client_socket = None
        self.last_serial_line = None

        self.animations = []
        self.plot_widgets = []
        self.current_graph_mode = 'linear'

    def create_widgets(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = self.create_sidebar()
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def create_sidebar(self):
        frame = ctk.CTkFrame(self.root, width=250)
        frame.grid_propagate(False)

        ctk.CTkLabel(frame, text="Controles", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10, padx=10)

        # Graph type selection
        ctk.CTkLabel(frame, text="Tipo de Gráfico:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        graph_type_menu = ctk.CTkOptionMenu(frame, values=["Linear", "Polar", "3D"], command=self.switch_graph_mode)
        graph_type_menu.pack(pady=5, padx=20, fill="x")
        graph_type_menu.set("Linear")

        # Data stream selection
        for name, var in self.check_vars.items():
            ctk.CTkCheckBox(frame, text=self.data_streams[name]['label'], variable=var, command=self.update_graph_display).pack(pady=5, padx=20, anchor="w")

        ctk.CTkCheckBox(frame, text="Gráfico Único", variable=self.single_graph_mode, command=self.update_graph_display).pack(pady=10, padx=20, anchor="w")

        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10, padx=10)

        # Data source selection
        ctk.CTkCheckBox(frame, text="Dados Aleatórios", variable=self.random_data, command=lambda: self._update_data_gen_mode(self.random_data)).pack(pady=5, padx=20, anchor="w")
        ctk.CTkCheckBox(frame, text="Dados Angulares Teste", variable=self.angular_test_data, command=lambda: self._update_data_gen_mode(self.angular_test_data)).pack(pady=5, padx=20, anchor="w")
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10, padx=10)

        # Action buttons
        ctk.CTkButton(frame, text="Pausar Aquisição", command=self.toggle_pause).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(frame, text="Resetar Dados", command=self.reset_data).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(frame, text="Salvar Dados", command=self.save_data).pack(pady=5, padx=10, fill="x")

        return frame

    def switch_graph_mode(self, mode):
        self.current_graph_mode = mode.lower()
        self.update_graph_display()

    def update_graph_display(self):
        self.clear_main_area()
        mode_map = {
            'linear': self.display_linear_graphs,
            'polar': self.display_polar_graphs,
            '3d': self.display_3d_graph,
        }
        display_function = mode_map.get(self.current_graph_mode)
        if display_function:
            display_function()

    def display_linear_graphs(self):
        active_streams = [name for name, var in self.check_vars.items() if var.get()]
        if not active_streams: return

        if self.single_graph_mode.get():
            fig = Figure(figsize=(12, 6), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_title("Gráfico Combinado")
            ax.grid(True)
            for name in active_streams:
                stream = self.data_streams[name]
                stream['line'], = ax.plot([], [], color=stream['color'], label=stream['label'])
            ax.legend()
            self.create_canvas(fig, self.main_frame)
            self.animations.append(FuncAnimation(fig, self._update_linear, fargs=(ax, active_streams, True), interval=100, blit=False))
        else:
            for name in active_streams:
                stream = self.data_streams[name]
                frame = ctk.CTkFrame(self.main_frame)
                frame.pack(fill="both", expand=True, pady=5)
                self.plot_widgets.append(frame)
                fig = Figure(figsize=(12, 2), dpi=100)
                ax = fig.add_subplot(111)
                ax.set_title(stream['label'])
                ax.grid(True)
                stream['line'], = ax.plot([], [], color=stream['color'])
                self.create_canvas(fig, frame)
                self.animations.append(FuncAnimation(fig, self._update_linear, fargs=(ax, [name], False), interval=100, blit=False))
    
    def _update_linear(self, frame_num, ax, streams, is_single):
        self._acquire_and_update_data()
        if is_single:
            for name in streams:
                stream = self.data_streams[name]
                stream['line'].set_data(stream['x'], stream['y'])
        else: # multiple graphs
            stream = self.data_streams[streams[0]]
            stream['line'].set_data(stream['x'], stream['y'])
        
        ax.relim()
        ax.autoscale_view()
        return [stream['line'] for name in streams for stream in [self.data_streams[name]] if 'line' in stream]

    def display_polar_graphs(self):
        active_streams = [name for name, var in self.check_vars.items() if var.get()]
        if not active_streams: return

        if self.single_graph_mode.get():
            fig = Figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111, projection='polar')
            ax.set_title("Polar Combinado")
            ax.set_rlim(0, 1)
            ax.set_rticks([])
            for name in active_streams:
                stream = self.data_streams[name]
                stream['line'], = ax.plot([0,0], [0,1], color=stream['color'], label=stream['label'], linewidth=3)
            ax.legend()
            self.create_canvas(fig, self.main_frame)
            self.animations.append(FuncAnimation(fig, self._update_polar, fargs=(ax, active_streams, True), interval=100, blit=False))
        else:
            parent_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            parent_frame.pack(fill="both", expand=True)
            self.plot_widgets.append(parent_frame)
            num_plots = len(active_streams)
            fig = Figure(figsize=(4 * num_plots, 5), dpi=100)
            
            for i, name in enumerate(active_streams):
                stream = self.data_streams[name]
                ax = fig.add_subplot(1, num_plots, i + 1, projection='polar')
                ax.set_title(stream['label'])
                ax.set_rlim(0, 1)
                ax.set_rticks([])
                stream['line'], = ax.plot([0,0], [0,1], color=stream['color'], linewidth=3)
            
            self.create_canvas(fig, parent_frame)
            self.animations.append(FuncAnimation(fig, self._update_polar, fargs=(None, active_streams, False), interval=100, blit=False))

    def _update_polar(self, frame_num, ax_single, streams, is_single):
        self._acquire_and_update_data()
        updated_artists = []
        for name in streams:
            stream = self.data_streams[name]
            if stream['y']:
                angle_rad = math.radians(stream['y'][-1])
                if is_single:
                    stream['line'].set_data([0, angle_rad], [0, 1])
                else:
                    # For multiple plots, we need to get the corresponding ax from the figure
                    # This is a simplification; a more robust way would be to store axes with streams
                    stream['line'].set_data([0, angle_rad], [0, 1])
                updated_artists.append(stream['line'])
        return updated_artists

    def display_3d_graph(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.plot_widgets.append(frame)
        
        fig = Figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim([-1, 1]); ax.set_ylim([-1, 1]); ax.set_zlim([-1, 1])
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        
        self.vector_line, = ax.plot([0, 0], [0, 0], [0, 0], 'r-', linewidth=3)
        self.create_canvas(fig, frame)
        self.animations.append(FuncAnimation(fig, self._update_3d, fargs=(ax,), interval=100, blit=False))

    def _update_3d(self, frame_num, ax):
        self._acquire_and_update_data()
        pitch = math.radians(self.data_streams['pitch']['y'][-1] if self.data_streams['pitch']['y'] else 0)
        roll = math.radians(self.data_streams['raw']['y'][-1] if self.data_streams['raw']['y'] else 0) # Using raw as roll for 3D
        yaw = math.radians(self.data_streams['yaw']['y'][-1] if self.data_streams['yaw']['y'] else 0)

        x = np.cos(yaw) * np.cos(pitch)
        y = np.sin(yaw) * np.cos(pitch)
        z = np.sin(pitch)
        
        self.vector_line.set_data([0, x], [0, y])
        self.vector_line.set_3d_properties([0, z])
        return self.vector_line,
        
    def _acquire_and_update_data(self):
        if self.paused_acquisition:
            return

        values = []
        if self.random_data.get():
            values = [random.uniform(-90, 90), random.uniform(0, 360), random.uniform(0, 360)]
        elif self.angular_test_data.get():
            self.angular_time_step += 1
            pitch = 90 * math.sin(self.angular_time_step * 0.1)
            raw = (180 + 180 * math.cos(self.angular_time_step * 0.15)) % 360
            yaw = (self.angular_time_step * 5) % 360
            values = [pitch, raw, yaw]
        
        if len(values) == 3:
            self.data_streams['pitch']['y'].append(values[0])
            self.data_streams['raw']['y'].append(values[1])
            self.data_streams['yaw']['y'].append(values[2])
            
            # Common X-axis based on pitch data length
            time_step = len(self.data_streams['pitch']['y'])
            self.data_streams['pitch']['x'].append(time_step)
            self.data_streams['raw']['x'].append(time_step)
            self.data_streams['yaw']['x'].append(time_step)

    def _update_data_gen_mode(self, selected_var):
        if selected_var == self.random_data and self.random_data.get():
            self.angular_test_data.set(False)
        elif selected_var == self.angular_test_data and self.angular_test_data.get():
            self.random_data.set(False)
        self.update_graph_display()

    def create_canvas(self, fig, parent):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.plot_widgets.append(canvas.get_tk_widget())

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()
        self.plot_widgets.append(toolbar)

    def clear_main_area(self):
        for anim in self.animations:
            anim.event_source.stop()
        self.animations.clear()

        for widget in self.plot_widgets:
            widget.destroy()
        self.plot_widgets.clear()
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def reset_data(self):
        self.angular_time_step = 0
        for name in self.data_streams:
            self.data_streams[name]['x'].clear()
            self.data_streams[name]['y'].clear()
        self.update_graph_display()

    def toggle_pause(self):
        self.paused_acquisition = not self.paused_acquisition
        # Update button text if you have a reference to it
        print(f"Aquisição {'pausada' if self.paused_acquisition else 'retomada'}.")

    def save_data(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filename:
            return
        with open(filename, 'w') as f:
            headers = "\t".join([self.data_streams[name]['label'] for name in self.data_streams])
            f.write(f"Time\t{headers}\n")
            
            num_points = len(self.data_streams['pitch']['y'])
            for i in range(num_points):
                row = f"{i}\t"
                row += "\t".join([f"{self.data_streams[name]['y'][i]:.4f}" for name in self.data_streams])
                f.write(row + "\n")
        print(f"Dados salvos em {filename}")

    def close_app(self):
        self.clear_main_area()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = SensorDashboard(root)
    root.mainloop()