import tkinter as tk
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation

import shared_state as state
from ui_utils import limpar_area_principal, parar_animacoes, update_statistics_display, create_statistics_frame
from app_logic import atualizar_dados_para_graficos

def Graficos():
    state.janela._current_graph_mode = 'linear'
    parar_animacoes()
    limpar_area_principal()

    if state.single_graph_mode.get():
        # Lógica para gráfico linear único...
        frame_single = ctk.CTkFrame(master=state.janela)
        frame_single.pack(fill="both", expand=True, pady=5, padx=10)
        state.widgets_criados.append(frame_single)
        
        state.fig_single_linear = Figure(figsize=(12, 6), dpi=100)
        state.ax_single_linear = state.fig_single_linear.add_subplot(111, title="Pitch, Raw, Yaw (Combined)", xlabel="Time", ylabel="Value")
        state.ax_single_linear.grid(True)

        lines = []
        if state.check_var1.get():
            state.line_pitch_single, = state.ax_single_linear.plot([], [], 'r-', label='Pitch')
            lines.append(state.line_pitch_single)
        if state.check_var2.get():
            state.line_raw_single, = state.ax_single_linear.plot([], [], 'g-', label='Raw')
            lines.append(state.line_raw_single)
        if state.check_var3.get():
            state.line_yaw_single, = state.ax_single_linear.plot([], [], 'b-', label='Yaw')
            lines.append(state.line_yaw_single)
        if lines:
            state.ax_single_linear.legend(handles=lines, loc='upper left')

        canvas = FigureCanvasTkAgg(state.fig_single_linear, master=frame_single)
        canvas.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
        NavigationToolbar2Tk(canvas, frame_single).update()
        
        stats_frame = create_statistics_frame(frame_single, "Estatísticas Combinadas", state.single_linear_stats_labels)
        state.widgets_criados.append(stats_frame)

        def atualizar(i):
            atualizar_dados_para_graficos()
            artists = []
            all_data = []
            if state.check_var1.get() and state.line_pitch_single:
                state.line_pitch_single.set_data(state.x_data, state.y_data)
                artists.append(state.line_pitch_single)
                all_data.extend(state.y_data)
            if state.check_var2.get() and state.line_raw_single:
                state.line_raw_single.set_data(state.x_data2, state.y_data2)
                artists.append(state.line_raw_single)
                all_data.extend(state.y_data2)
            if state.check_var3.get() and state.line_yaw_single:
                state.line_yaw_single.set_data(state.x_data3, state.y_data3)
                artists.append(state.line_yaw_single)
                all_data.extend(state.y_data3)

            update_statistics_display(all_data, state.single_linear_stats_labels)
            state.ax_single_linear.relim()
            state.ax_single_linear.autoscale_view()
            return artists

        state.ani_single_linear = FuncAnimation(state.fig_single_linear, atualizar, interval=100, blit=True, cache_frame_data=False)

    else:
        # Lógica para múltiplos gráficos lineares...
        def create_linear_graph_frame(title, line_color, data_x, data_y, stats_labels_dict):
            frame = ctk.CTkFrame(master=state.janela)
            frame.pack(fill="both", expand=True, pady=5, padx=10)
            state.widgets_criados.append(frame)
            
            fig = Figure(figsize=(12, 2), dpi=100)
            ax = fig.add_subplot(111, title=title)
            ax.grid(True)
            
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
            NavigationToolbar2Tk(canvas, frame).update()
            
            line, = ax.plot([], [], color=line_color)
            stats_frame = create_statistics_frame(frame, f"Estatísticas {title}", stats_labels_dict)
            state.widgets_criados.append(stats_frame)
            
            def atualizar(i):
                # A atualização dos dados é feita apenas uma vez
                if title == "Pitch":
                    atualizar_dados_para_graficos()
                
                line.set_data(data_x, data_y)
                ax.relim()
                ax.autoscale_view()
                update_statistics_display(data_y, stats_labels_dict)
                return line,

            return FuncAnimation(fig, atualizar, interval=100, blit=True, cache_frame_data=False)

        if state.check_var1.get():
            state.ani1 = create_linear_graph_frame("Pitch", "r", state.x_data, state.y_data, state.pitch_stats_labels)
        if state.check_var2.get():
            state.ani2 = create_linear_graph_frame("Raw", "g", state.x_data2, state.y_data2, state.raw_stats_labels)
        if state.check_var3.get():
            state.ani3 = create_linear_graph_frame("Yaw", "b", state.x_data3, state.y_data3, state.yaw_stats_labels)