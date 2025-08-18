import tkinter as tk
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

import shared_state as state
from ui_utils import limpar_area_principal, parar_animacoes
from app_logic import atualizar_dados_para_graficos


def Grafico3D():
    state.janela._current_graph_mode = '3d'
    parar_animacoes()
    limpar_area_principal()

    frame_3d = ctk.CTkFrame(master=state.janela)
    frame_3d.pack(fill="both", expand=True, pady=5, padx=10)
    state.widgets_criados.append(frame_3d)

    state.fig_3d = Figure(figsize=(8, 8), dpi=100)
    state.ax_3d = state.fig_3d.add_subplot(111, projection='3d')
    state.ax_3d.set_title("Visualização 3D dos Ângulos")
    state.ax_3d.set_xlim([-1, 1]); state.ax_3d.set_ylim([-1, 1]); state.ax_3d.set_zlim([-1, 1])
    state.ax_3d.set_xlabel('X'); state.ax_3d.set_ylabel('Y'); state.ax_3d.set_zlabel('Z')

    state.pitch_indicator_line, = state.ax_3d.plot([], [], [], color='r', label='Pitch')
    state.raw_indicator_line, = state.ax_3d.plot([], [], [], color='g', label='Roll') # Changed to Roll
    state.yaw_indicator_line, = state.ax_3d.plot([], [], [], color='b', label='Yaw')
    state.pitch_indicator_point, = state.ax_3d.plot([], [], [], 'ro')
    state.raw_indicator_point, = state.ax_3d.plot([], [], [], 'go')
    state.yaw_indicator_point, = state.ax_3d.plot([], [], [], 'bo')

    state.pitch_opposite_line, = state.ax_3d.plot([], [], [], color='r', linestyle='--')
    state.raw_opposite_line, = state.ax_3d.plot([], [], [], color='g', linestyle='--')
    state.yaw_opposite_line, = state.ax_3d.plot([], [], [], color='b', linestyle='--')
    state.pitch_opposite_point, = state.ax_3d.plot([], [], [], 'r', marker='x')
    state.raw_opposite_point, = state.ax_3d.plot([], [], [], 'g', marker='x')
    state.yaw_opposite_point, = state.ax_3d.plot([], [], [], 'b', marker='x')

    state.ax_3d.legend()

    canvas_3d = FigureCanvasTkAgg(state.fig_3d, master=frame_3d)
    canvas_3d.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

    toolbar_3d = NavigationToolbar2Tk(canvas_3d, frame_3d)
    toolbar_3d.update()

    controles_3d_frame = ctk.CTkFrame(frame_3d)
    controles_3d_frame.pack(fill="x", pady=5)

    def update_3d(frame):
        atualizar_dados_para_graficos()
        pitch = state.y_data[-1] if state.y_data and not state.override_pitch_var.get() else state.slider_pitch_val
        roll = state.y_data2[-1] if state.y_data2 and not state.override_roll_var.get() else state.slider_roll_val # Assuming y_data2 is roll
        yaw = state.y_data3[-1] if state.y_data3 and not state.override_yaw_var.get() else state.slider_yaw_val

        pitch_rad, roll_rad, yaw_rad = np.deg2rad([pitch, roll, yaw])

        # Pitch (Rotação em Y)
        x_p = np.cos(pitch_rad)
        z_p = -np.sin(pitch_rad)
        y_p = 0
        state.pitch_indicator_line.set_data([0, x_p], [0, y_p]); state.pitch_indicator_line.set_3d_properties([0, z_p])
        state.pitch_indicator_point.set_data([x_p], [y_p]); state.pitch_indicator_point.set_3d_properties([z_p])
        state.pitch_opposite_line.set_data([0, -x_p], [0, -y_p]); state.pitch_opposite_line.set_3d_properties([0, -z_p])
        state.pitch_opposite_point.set_data([-x_p], [-y_p]); state.pitch_opposite_point.set_3d_properties([-z_p])

        # Roll (Rotação em X)
        y_r = np.cos(roll_rad)
        z_r = np.sin(roll_rad)
        x_r = 0
        state.raw_indicator_line.set_data([0, x_r], [0, y_r]); state.raw_indicator_line.set_3d_properties([0, z_r])
        state.raw_indicator_point.set_data([x_r], [y_r]); state.raw_indicator_point.set_3d_properties([z_r])
        state.raw_opposite_line.set_data([0, -x_r], [0, -y_r]); state.raw_opposite_line.set_3d_properties([0, -z_r])
        state.raw_opposite_point.set_data([-x_r], [-y_r]); state.raw_opposite_point.set_3d_properties([-z_r])
        
        # Yaw (Rotação em Z)
        x_y = np.cos(yaw_rad)
        y_y = np.sin(yaw_rad)
        z_y = 0
        state.yaw_indicator_line.set_data([0, x_y], [0, y_y]); state.yaw_indicator_line.set_3d_properties([0, z_y])
        state.yaw_indicator_point.set_data([x_y], [y_y]); state.yaw_indicator_point.set_3d_properties([z_y])
        state.yaw_opposite_line.set_data([0, -x_y], [0, -y_y]); state.yaw_opposite_line.set_3d_properties([0, -z_y])
        state.yaw_opposite_point.set_data([-x_y], [-y_y]); state.yaw_opposite_point.set_3d_properties([-z_y])

        canvas_3d.draw_idle()
        return state.pitch_indicator_line, state.raw_indicator_line, state.yaw_indicator_line, state.pitch_indicator_point, state.raw_indicator_point, state.yaw_indicator_point, state.pitch_opposite_line, state.raw_opposite_line, state.yaw_opposite_line, state.pitch_opposite_point, state.raw_opposite_point, state.yaw_opposite_point

    state.ani_3d = FuncAnimation(state.fig_3d, update_3d, interval=100, blit=False)