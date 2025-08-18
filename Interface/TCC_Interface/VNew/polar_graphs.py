import tkinter as tk
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import math

import shared_state as state
from ui_utils import limpar_area_principal, parar_animacoes, update_statistics_display, create_statistics_frame
from app_logic import atualizar_dados_para_graficos

def GraficosPolares():
    state.janela._current_graph_mode = 'polar'
    parar_animacoes()
    limpar_area_principal()
    bar_width_rad = 0.2

    if state.single_graph_mode.get():
        parent_frame_single_polar = ctk.CTkFrame(master=state.janela, fg_color="transparent")
        parent_frame_single_polar.pack(fill="both", expand=True, pady=10, padx=10)
        state.widgets_criados.append(parent_frame_single_polar)
        state.fig_single_polar = Figure(figsize=(8, 8), dpi=100)
        state.ax_single_polar = state.fig_single_polar.add_subplot(111, projection='polar')
        state.ax_single_polar.set_title("Polar Combined (Pitch, Raw, Yaw)")
        state.ax_single_polar.set_theta_direction(1)
        state.ax_single_polar.set_rlim(0, 1)
        state.ax_single_polar.set_rticks([])
        
        bars_to_plot_in_legend = []
        if state.check_var1.get():
            state.bar_pitch_single, = state.ax_single_polar.plot([0, 0], [0, 1], color='red', linewidth=2, label='Pitch', marker='o', markersize=8)
            bars_to_plot_in_legend.append(state.bar_pitch_single)
        if state.check_var2.get():
            state.bar_raw_single, = state.ax_single_polar.plot([0, 0], [0, 1], color='green', linewidth=2, label='Raw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(state.bar_raw_single)
        if state.check_var3.get():
            state.bar_yaw_single, = state.ax_single_polar.plot([0, 0], [0, 1], color='blue', linewidth=2, label='Yaw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(state.bar_yaw_single)

        if bars_to_plot_in_legend:
            state.ax_single_polar.legend(handles=bars_to_plot_in_legend, loc='upper right', bbox_to_anchor=(1.1, 1.1))

        canvas_single_polar = FigureCanvasTkAgg(state.fig_single_polar, master=parent_frame_single_polar)
        canvas_single_polar.get_tk_widget().pack(anchor=tk.CENTER, expand=True, fill='both')
        toolbar_single_polar = NavigationToolbar2Tk(canvas_single_polar, parent_frame_single_polar)
        toolbar_single_polar.update()
        stats_frame_single_polar = create_statistics_frame(parent_frame_single_polar, "Estatísticas Combinadas", state.single_polar_stats_labels)
        state.widgets_criados.append(stats_frame_single_polar)

        def atualizar_single_polar(i):
            atualizar_dados_para_graficos()
            updated_artists = []
            all_data_for_stats = []
            if len(state.y_data) > 0:
                if state.check_var1.get() and state.bar_pitch_single:
                    pitch_rad = math.radians(state.y_data[-1])
                    state.bar_pitch_single.set_data([0, pitch_rad], [0, 1])
                    updated_artists.append(state.bar_pitch_single)
                    all_data_for_stats.append(state.y_data[-1])
                if state.check_var2.get() and state.bar_raw_single:
                    raw_rad = math.radians(state.y_data2[-1])
                    state.bar_raw_single.set_data([0, raw_rad], [0, 1])
                    updated_artists.append(state.bar_raw_single)
                    all_data_for_stats.append(state.y_data2[-1])
                if state.check_var3.get() and state.bar_yaw_single:
                    yaw_rad = math.radians(state.y_data3[-1])
                    state.bar_yaw_single.set_data([0, yaw_rad], [0, 1])
                    updated_artists.append(state.bar_yaw_single)
                    all_data_for_stats.append(state.y_data3[-1])

            update_statistics_display(all_data_for_stats, state.single_polar_stats_labels)
            canvas_single_polar.draw_idle()
            return updated_artists
        state.ani_single_polar = FuncAnimation(state.fig_single_polar, atualizar_single_polar, interval=100, blit=False, cache_frame_data=False)

    else:
        num_active_polar_graphs = state.check_var1.get() + state.check_var2.get() + state.check_var3.get()
        if num_active_polar_graphs > 0:
            parent_frame_polar = ctk.CTkFrame(master=state.janela, fg_color="transparent")
            parent_frame_polar.pack(fill="both", expand=True, pady=10, padx=10)
            state.widgets_criados.append(parent_frame_polar)
            state.fig_polar = Figure(figsize=(4 * num_active_polar_graphs, 6), dpi=100)
            current_subplot = 1
            if state.check_var1.get():
                state.ax_polar1 = state.fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                state.ax_polar1.set_title("Polar Pitch"); state.ax_polar1.set_theta_direction(1)
                state.ax_polar1.set_rlim(0, 1)
                state.ax_polar1.set_rticks([])
                state.bar_polar1_patch = state.ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
                current_subplot += 1
            if state.check_var2.get():
                state.ax_polar2 = state.fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                state.ax_polar2.set_title("Polar Raw"); state.ax_polar2.set_theta_direction(1)
                state.ax_polar2.set_rlim(0, 1)
                state.ax_polar2.set_rticks([])
                state.bar_polar2_patch = state.ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
                current_subplot += 1
            if state.check_var3.get():
                state.ax_polar3 = state.fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                state.ax_polar3.set_title("Polar Yaw"); state.ax_polar3.set_theta_direction(1)
                state.ax_polar3.set_rlim(0, 1)
                state.ax_polar3.set_rticks([])
                state.bar_polar3_patch = state.ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]
                current_subplot += 1
            state.fig_polar.subplots_adjust(wspace=0.4, hspace=0.4)
            state.canvas_polar = FigureCanvasTkAgg(state.fig_polar, master=parent_frame_polar)
            state.canvas_polar.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

            toolbar_polar = NavigationToolbar2Tk(state.canvas_polar, parent_frame_polar)
            toolbar_polar.update()

            def atualizar_polar(i):
                atualizar_dados_para_graficos()
                updated_artists = []
                if state.check_var1.get() and len(state.y_data) > 0 and state.bar_polar1_patch:
                    pitch_rad = math.radians(state.y_data[-1])
                    state.bar_polar1_patch.set_x(pitch_rad - bar_width_rad/2)
                    updated_artists.append(state.bar_polar1_patch)
                if state.check_var2.get() and len(state.y_data2) > 0 and state.bar_polar2_patch:
                    raw_rad = math.radians(state.y_data2[-1])
                    state.bar_polar2_patch.set_x(raw_rad - bar_width_rad/2)
                    updated_artists.append(state.bar_polar2_patch)
                if state.check_var3.get() and len(state.y_data3) > 0 and state.bar_polar3_patch:
                    yaw_rad = math.radians(state.y_data3[-1])
                    state.bar_polar3_patch.set_x(yaw_rad - bar_width_rad/2)
                    updated_artists.append(state.bar_polar3_patch)
                state.canvas_polar.draw_idle()
                return updated_artists
            
            state.ani_polar = FuncAnimation(state.fig_polar, atualizar_polar, interval=100, blit=False, cache_frame_data=False)