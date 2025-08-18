import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
import serial.tools.list_ports
import socket
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence # Importa ImageSequence para GIFs
import math # Importar para funções senoidais
import numpy as np # Importar para operações numéricas, como linspace
from mpl_toolkits.mplot3d import Axes3D # Importa o Axes3D
import statistics # Import for statistical calculations

###### SERVIDOR
# Removendo as variáveis globais de IP e Porta fixas
# ESP_IP = "192.168.0.112"
# ESP_PORT = 12345

# Variáveis de dados
global dados
x_data, y_data = [], [] # Pitch (time, value)
x_data2, y_data2 = [], [] # Raw (time, value)
x_data3, y_data3 = [], [] # Yaw (time, value)

# Variáveis de widgets e gráficos
ultima_linha = None
canvas = None
client = None
ax, ax2, ax3 = None, None, None # For linear 2D plots
# Removidos line_3d, pois será substituído por indicadores de ângulo
ani1, ani2, ani3,= None, None, None
serial_conn = None
widgets_criados = [] # Widgets na área principal
label_dados = None

# Variáveis para gráficos polares
ax_polar1, ax_polar2, ax_polar3 = None, None, None
canvas_polar = None
ani_polar = None
fig_polar = None
bar_polar1_patch, bar_polar2_patch, bar_polar3_patch = None, None, None

# Variáveis para figuras
fig_pitch, fig_raw, fig_yaw = None, None, None
fig_single_linear = None # For single linear graph
fig_single_polar = None  # For single polar graph
fig_3d = None # Para o gráfico 3D

# Initialize single graph animations to None globally
ani_single_linear = None
ani_single_polar = None
ani_3d = None # Para o gráfico 3D


# Variáveis para indicadores do gráfico 3D
global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
global pitch_indicator_point, raw_indicator_point, yaw_indicator_point

# Variables for opposite angle indicators
global pitch_opposite_line, raw_opposite_line, yaw_opposite_line
global pitch_opposite_point, raw_opposite_point, yaw_opposite_point

# Variables for single linear graph lines
global line_pitch_single, line_raw_single, line_yaw_single

# Variables for single polar graph bars
global bar_pitch_single, bar_raw_single, bar_yaw_single


# Variáveis de estado
global modo_conexao
modo_conexao = None # Pode ser 'serial', 'wifi', ou None
global paused_acquisition # Novo: Variável para controlar a pausa da aquisição
paused_acquisition = False

# Variáveis para nova geração de dados angulares
global angular_time_step
angular_time_step = 0

# Frame para os controles laterais dos gráficos
controles_graficos_frame = None

# Variável global para o frame do título da aba principal (a barra de destaque)
main_title_frame = None

# Variável global para a janela principal
janela = None

# Variáveis globais para a animação do GIF
global gif_frames, gif_index, gif_label, gif_after_id, gif_path # Adicionado gif_path aqui
gif_frames = []
gif_index = 0
gif_label = None
gif_after_id = None
gif_path = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Alien.gif' # Definindo o caminho do GIF globalmente

# Global variables for statistics labels
global pitch_stats_labels, raw_stats_labels, yaw_stats_labels
global single_linear_stats_labels, single_polar_stats_labels, single_3d_stats_labels
pitch_stats_labels = {}
raw_stats_labels = {}
yaw_stats_labels = {}
single_linear_stats_labels = {}
single_polar_stats_labels = {}
single_3d_stats_labels = {}

# NOVAS VARIÁVEIS GLOBAIS PARA OS VALORES DOS SLIDERS DO GRÁFICO 3D E SEUS LABELS
global slider_pitch_val, slider_roll_val, slider_yaw_val
global label_pitch_val, label_roll_val, label_yaw_val
slider_pitch_val = 0.0
slider_roll_val = 0.0
slider_yaw_val = 0.0
label_pitch_val = None
label_roll_val = None
label_yaw_val = None

# Variáveis globais para os checkboxes de sobreposição e seleção de dados, etc.
# ESTAS VARIÁVEIS SÃO AGORA INICIALIZADAS DENTRO DE setup_main_window()
global override_pitch_var, override_roll_var, override_yaw_var
global random_data, angular_test_data, single_graph_mode
global check_var1, check_var2, check_var3

# Nova variável global para o botão ativo da barra lateral
global active_sidebar_button
active_sidebar_button = None


def fechar_programa():
    global janela
    parar_animacoes() # Certifica-se de parar as animações ao fechar
    if janela:
        janela.destroy()

def sair_tela_cheia(event):
    if janela:
        janela.attributes('-fullscreen', False)

def pausar_aquisicao():
    """Pausa a aquisição de dados."""
    global paused_acquisition
    paused_acquisition = True
    print("Aquisição de dados pausada.")

def continuar_aquisicao():
    """Resume a aquisição de dados."""
    global paused_acquisition
    paused_acquisition = False
    print("Aquisição de dados retomada.")

def _update_data_generation_mode(selected_var):
    """
    Controla que apenas uma opção de geração de dados (aleatório ou angular) esteja ativa.
    """
    global random_data, angular_test_data
    if selected_var == random_data:
        if random_data.get():
            angular_test_data.set(False)
    elif selected_var == angular_test_data:
        if angular_test_data.get():
            random_data.set(False)
    update_graph_display()


def criar_controles_laterais(parent):
    """Cria o frame com os controles dos gráficos na barra lateral."""
    global check_var1, check_var2, check_var3, random_data, angular_test_data, single_graph_mode

    # Frame para os controles
    frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))

    # Título
    label_titulo = ctk.CTkLabel(frame, text="Opções do Gráfico", font=ctk.CTkFont(size=14, weight="bold"))
    label_titulo.pack(pady=(10, 5), padx=10, fill="x")

    # Checkboxes de seleção de gráfico (para múltiplos gráficos)
    # Estes só devem aparecer se 'single_graph_mode' não estiver selecionado
    # Vamos gerenciar a visibilidade na função update_graph_display indiretamente ou no comando do single_graph_mode
    check_button1 = ctk.CTkCheckBox(frame, text="Pitch", variable=check_var1, command=update_graph_display)
    check_button1.pack(pady=5, padx=20, anchor="w")

    check_button2 = ctk.CTkCheckBox(frame, text="Raw", variable=check_var2, command=update_graph_display)
    check_button2.pack(pady=5, padx=20, anchor="w")

    check_button3 = ctk.CTkCheckBox(frame, text="Yaw", variable=check_var3, command=update_graph_display)
    check_button3.pack(pady=5, padx=20, anchor="w")

    # Checkbox para modo de gráfico único
    single_graph_checkbox = ctk.CTkCheckBox(frame, text="Gráfico Único", variable=single_graph_mode, command=update_graph_display)
    single_graph_checkbox.pack(pady=10, padx=20, anchor="w")


    # Separador
    separator = ttk.Separator(frame, orient='horizontal')
    separator.pack(fill='x', pady=10, padx=10)

    # Checkbox de dados aleatórios
    BtRandomData = ctk.CTkCheckBox(frame, text="Dados Aleatórios", variable=random_data, command=lambda: _update_data_generation_mode(random_data))
    BtRandomData.pack(pady=5, padx=20, anchor="w")

    # NOVO: Checkbox de dados angulares
    BtAngularData = ctk.CTkCheckBox(frame, text="Dados Angulares (0-360°)", variable=angular_test_data, command=lambda: _update_data_generation_mode(angular_test_data))
    BtAngularData.pack(pady=5, padx=20, anchor="w")


    # Botões de ação
    botao_salvar = ctk.CTkButton(frame, text="Salvar Dados", command=lambda: salvar_dados(y_data, y_data2, y_data3))
    botao_salvar.pack(pady=10, fill="x", padx=10)

    botao_resetar = ctk.CTkButton(frame, text="Resetar Dados", command=resetar_dados)
    botao_resetar.pack(pady=5, fill="x", padx=10)

    # Novo: Botões de Pausar e Continuar Aquisição
    botao_pausar = ctk.CTkButton(frame, text="Pausar Aquisição", command=pausar_aquisicao)
    botao_pausar.pack(pady=5, fill="x", padx=10)

    botao_continuar = ctk.CTkButton(frame, text="Continuar Aquisição", command=continuar_aquisicao)
    botao_continuar.pack(pady=5, fill="x", padx=10)

    return frame

# MODIFIED: Function to create a frame for statistics display to lay out labels horizontally
def create_statistics_frame(parent_frame, title_text, label_dict):
    stats_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    stats_frame.pack(pady=(5, 0), padx=10, fill="x")
    
    ctk.CTkLabel(stats_frame, text=title_text, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0,2))
    
    # Create an inner frame to hold the statistics labels horizontally
    inner_stats_labels_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
    inner_stats_labels_frame.pack(fill="x")

    label_dict['min'] = ctk.CTkLabel(inner_stats_labels_frame, text="Min: N/A")
    label_dict['min'].pack(side="left", padx=(0, 10)) # Added right padding

    label_dict['max'] = ctk.CTkLabel(inner_stats_labels_frame, text="Max: N/A")
    label_dict['max'].pack(side="left", padx=(0, 10)) # Added right padding
    
    label_dict['mean'] = ctk.CTkLabel(inner_stats_labels_frame, text="Média: N/A")
    label_dict['mean'].pack(side="left", padx=(0, 10)) # Added right padding
    
    label_dict['std'] = ctk.CTkLabel(inner_stats_labels_frame, text="Desvio Padrão: N/A")
    label_dict['std'].pack(side="left", padx=(0, 0)) # No right padding for the last one
    
    return stats_frame

# Function to update statistics labels
def update_statistics_display(data_list, label_dict):
    if not data_list:
        label_dict['min'].configure(text="Min: N/A")
        label_dict['max'].configure(text="Max: N/A")
        label_dict['mean'].configure(text="Média: N/A")
        label_dict['std'].configure(text="Desvio Padrão: N/A")
        return

    min_val = min(data_list)
    max_val = max(data_list)
    mean_val = statistics.mean(data_list)
    std_dev_val = statistics.stdev(data_list) if len(data_list) > 1 else 0.0

    label_dict['min'].configure(text=f"Min: {min_val:.2f}")
    label_dict['max'].configure(text=f"Max: {max_val:.2f}")
    label_dict['mean'].configure(text=f"Média: {mean_val:.2f}")
    label_dict['std'].configure(text=f"Desvio Padrão: {std_dev_val:.2f}")


def resetar_dados():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3, angular_time_step
    global line_pitch_single, line_raw_single, line_yaw_single # single linear lines
    global bar_pitch_single, bar_raw_single, bar_yaw_single # single polar bars
    global pitch_stats_labels, raw_stats_labels, yaw_stats_labels, single_linear_stats_labels, single_polar_stats_labels, single_3d_stats_labels # Statistics labels
    global slider_pitch_val, slider_roll_val, slider_yaw_val # Reset slider values
    global label_pitch_val, label_roll_val, label_yaw_val # Reset slider labels
    global override_pitch_var, override_roll_var, override_yaw_var # Reset override checkboxes

    x_data.clear(); y_data.clear()
    x_data2.clear(); y_data2.clear()
    x_data3.clear(); y_data3.clear()
    angular_time_step = 0 # Resetar o contador de tempo para dados angulares

    # Reset slider values to default (e.g., 0)
    slider_pitch_val = 0.0
    slider_roll_val = 0.0
    slider_yaw_val = 0.0
    # Also reset the slider widgets if they exist
    if 'slider_pitch' in globals() and slider_pitch: slider_pitch.set(0)
    if 'slider_roll' in globals() and slider_roll: slider_roll.set(0)
    if 'slider_yaw' in globals() and slider_yaw: slider_yaw.set(0)

    # Reset override checkboxes
    override_pitch_var.set(False)
    override_roll_var.set(False)
    override_yaw_var.set(False)


    # Resetar eixos e patches dos gráficos 2D lineares (múltiplos)
    if ax:
        ax.clear()
        ax.set_title("Pitch")
        ax.grid(True)
        global line1
        line1, = ax.plot([], [], 'r-')
    if ax2:
        ax2.clear()
        ax2.set_title("Raw")
        ax2.grid(True)
        global line2
        line2, = ax2.plot([], [], 'g-')
    if ax3:
        ax3.clear()
        ax3.set_title("Yaw")
        ax3.grid(True)
        global line3
        line3, = ax3.plot([], [], 'b-')

    # Reset for single linear graph
    global ax_single_linear
    if 'ax_single_linear' in globals() and ax_single_linear:
        ax_single_linear.clear()
        ax_single_linear.set_title("Pitch, Raw, Yaw (Combined)")
        ax_single_linear.grid(True)
        # Re-initialize the lines for the single graph based on selection
        # Initialize them to None first to avoid NameError if not selected
        line_pitch_single = None
        line_raw_single = None
        line_yaw_single = None

        lines_to_plot = []
        if check_var1.get():
            line_pitch_single, = ax_single_linear.plot([], [], 'r-', label='Pitch')
            lines_to_plot.append(line_pitch_single)
        if check_var2.get():
            line_raw_single, = ax_single_linear.plot([], [], 'g-', label='Raw')
            lines_to_plot.append(line_raw_single)
        if check_var3.get():
            line_yaw_single, = ax_single_linear.plot([], [], 'b-', label='Yaw')
            lines_to_plot.append(line_yaw_single)

        # Update legend based on actually plotted lines
        if lines_to_plot:
            ax_single_linear.legend()
        else:
            # If no lines are plotted, clear the legend
            if ax_single_linear.legend_:
                ax_single_linear.legend_.remove()


    # Resetar eixos e patches dos gráficos polares (múltiplos)
    if bar_polar1_patch: bar_polar1_patch.set_x(0 - bar_polar1_patch.get_width()/2)
    if bar_polar2_patch: bar_polar2_patch.set_x(0 - bar_polar2_patch.get_width()/2)
    if bar_polar3_patch: bar_polar3_patch.set_x(0 - bar_polar3_patch.get_width()/2)

    # Reset for single polar graph
    global ax_single_polar
    if 'ax_single_polar' in globals() and ax_single_polar:
        ax_single_polar.clear()
        ax_single_polar.set_title("Polar Combined (Pitch, Raw, Yaw)")
        ax_single_polar.set_theta_direction(1)
        ax_single_polar.set_rlim(0, 1)
        ax_single_polar.set_rticks([])
        # Re-initialize lines for the single polar graph based on selection
        bar_pitch_single = None
        bar_raw_single = None
        bar_yaw_single = None

        bars_to_plot = []
        if check_var1.get():
            bar_pitch_single, = ax_single_polar.plot([0, 0], [0, 1], color='red', linewidth=2, label='Pitch', marker='o', markersize=8)
            bars_to_plot.append(bar_pitch_single)
        if check_var2.get():
            bar_raw_single, = ax_single_polar.plot([0, 0], [0, 1], color='green', linewidth=2, label='Raw', marker='o', markersize=8)
            bars_to_plot.append(bar_raw_single)
        if check_var3.get():
            bar_yaw_single, = ax_single_polar.plot([0, 0], [0, 1], color='blue', linewidth=2, label='Yaw', marker='o', markersize=8)
            bars_to_plot.append(bar_yaw_single)

        # Update legend based on actually plotted bars
        if bars_to_plot:
            ax_single_polar.legend(loc='upper right')
        else:
            if ax_single_polar.legend_:
                ax_single_polar.legend_.remove()

    # Reset statistics display
    update_statistics_display([], pitch_stats_labels)
    update_statistics_display([], raw_stats_labels)
    update_statistics_display([], yaw_stats_labels)
    update_statistics_display([], single_linear_stats_labels)
    update_statistics_display([], single_polar_stats_labels)
    update_statistics_display([], single_3d_stats_labels)

    # Redesenhar os canvases
    if 'canvas_pitch' in globals() and canvas_pitch: canvas_pitch.draw_idle()
    if 'canvas_raw' in globals() and canvas_raw: canvas_raw.draw_idle()
    if 'canvas_yaw' in globals() and canvas_yaw: canvas_yaw.draw_idle()
    if 'canvas_single_linear' in globals() and canvas_single_linear: canvas_single_linear.draw_idle()
    if canvas_polar: canvas_polar.draw_idle()
    if 'canvas_single_polar' in globals() and canvas_single_polar: canvas_single_polar.draw_idle()
    if 'canvas_3d' in globals() and canvas_3d: canvas_3d.draw_idle()

    # If the 3D graph is active, force an update from sliders as well
    if hasattr(janela, '_current_graph_mode') and janela._current_graph_mode == '3d':
        # Ensure the labels are updated as well
        if label_pitch_val: label_pitch_val.configure(text=f"Pitch: {slider_pitch_val:.1f}°")
        if label_roll_val: label_roll_val.configure(text=f"Roll: {slider_roll_val:.1f}°")
        if label_yaw_val: label_yaw_val.configure(text=f"Yaw: {slider_yaw_val:.1f}°")
        # Força o redesenho do 3D usando os novos valores (geralmente 0)
        if 'fig_3d' in globals() and fig_3d:
            update_3d(None) # Pass None as frame argument, as it's not from FuncAnimation


def salvar_dados(y_data_to_save, y_data2_to_save, y_data3_to_save):
    nome_arquivo = filedialog.asksaveasfilename(
        title="Salvar Dados do Gráfico",
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if nome_arquivo:
        with open(nome_arquivo, 'w') as f:
            f.write("Tempo\tPitch\tRaw\tYaw\n")
            # Assumindo que todos os y_data têm o mesmo comprimento
            min_len = min(len(y_data_to_save), len(y_data2_to_save), len(y_data3_to_save))
            for i in range(min_len):
                f.write(f"{i}\t{y_data_to_save[i]}\t{y_data2_to_save[i]}\t{y_data3_to_save[i]}\n")
        print(f"Arquivo salvo em: {nome_arquivo}")
    else:
        print("Operação de salvamento cancelada.")

def adquirir_dados_continuamente():
    global serial_conn, ultima_linha, client, modo_conexao, paused_acquisition, angular_time_step
    valores = []
    if paused_acquisition: # Se a aquisição estiver pausada, retorne imediatamente
        return []

    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
    elif angular_test_data.get():
        angular_time_step += 1
        # Pitch: -90 a 90, oscilação senoidal
        pitch = 90 * math.sin(angular_time_step * 0.1)
        # Raw: 0 a 360, movimento em círculo completo
        raw = (180 + 180 * math.cos(angular_time_step * 0.15)) % 360
        # Yaw: 0 a 360, avança linearmente
        yaw = (angular_time_step * 5) % 360
        valores = [pitch, raw, yaw]
    elif modo_conexao == 'serial' and serial_conn and serial_conn.is_open:
        try:
            while serial_conn.in_waiting:
                ultima_linha = serial_conn.readline().decode('utf-8').strip()
            if ultima_linha:
                valores = [float(val) for val in ultima_linha.split()]
        except Exception as e:
            print(f"Erro ao ler dados do Serial: {e}")
            ultima_linha = None
    elif modo_conexao == 'wifi' and client:
        try:
            data = client.recv(32).decode('utf-8').strip()
            if data:
                numeros = [float(val) for val in data.split()]
                if len(numeros) == 3: valores = numeros
        except Exception as e:
            print(f"Erro ao ler dados do Wi-Fi: {e}")
            client = None
    return valores

def atualizar_dados_para_graficos():
    """Adquire novos dados e os adiciona às listas de dados globais."""
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    valores = adquirir_dados_continuamente()
    if len(valores) == 3:
        x_data.append(len(x_data))
        y_data.append(valores[0]) # Pitch
        x_data2.append(len(x_data2))
        y_data2.append(valores[1]) # Raw
        x_data3.append(len(x_data3))
        y_data3.append(valores[2]) # Yaw

def update_graph_display():
    if hasattr(janela, '_current_graph_mode'):
        if janela._current_graph_mode == 'linear':
            Graficos()
        elif janela._current_graph_mode == 'polar':
            GraficosPolares()
        elif janela._current_graph_mode == '3d':
            Grafico3D()


def limpar_area_principal():
    """Destrói todos os widgets na área principal, incluindo o frame do título."""
    global main_title_frame
    for widget in widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    widgets_criados.clear()
    if main_title_frame and main_title_frame.winfo_exists():
        main_title_frame.destroy()
        main_title_frame = None

def parar_animacoes():
    """Para todas as animações e fecha figuras Matplotlib."""
    global ani1, ani2, ani3, ani_polar, ani_3d, ani_single_linear, ani_single_polar
    global fig_polar, fig_pitch, fig_raw, fig_yaw, fig_3d, fig_single_linear, fig_single_polar

    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if ani_single_linear: ani_single_linear.event_source.stop(); ani_single_linear = None
    if ani_single_polar: ani_single_polar.event_source.stop(); ani_single_polar = None
    if ani_3d: ani_3d.event_source.stop(); ani_3d = None

    if fig_pitch:
        if ax: ax.clear()
        plt.close(fig_pitch)
        fig_pitch = None
    if fig_raw:
        if ax2: ax2.clear()
        plt.close(fig_raw)
        fig_raw = None
    if fig_yaw:
        if ax3: ax3.clear()
        plt.close(fig_yaw)
        fig_yaw = None
    if fig_polar:
        if ax_polar1: ax_polar1.clear()
        if ax_polar2: ax_polar2.clear()
        if ax_polar3: ax_polar3.clear()
        plt.close(fig_polar)
        fig_polar = None
    if fig_single_linear:
        global ax_single_linear
        if 'ax_single_linear' in globals() and ax_single_linear: ax_single_linear.clear()
        plt.close(fig_single_linear)
        fig_single_linear = None
    if fig_single_polar:
        global ax_single_polar
        if 'ax_single_polar' in globals() and ax_single_polar: ax_single_polar.clear()
        plt.close(fig_single_polar)
        fig_single_polar = None
    if fig_3d:
        global ax_3d
        if 'ax_3d' in globals() and ax_3d: ax_3d.clear()
        plt.close(fig_3d)
        fig_3d = None


def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw, fig_pitch, fig_raw, fig_yaw
    global single_graph_mode
    global fig_single_linear, canvas_single_linear, ax_single_linear, ani_single_linear
    global line_pitch_single, line_raw_single, line_yaw_single
    global pitch_stats_labels, raw_stats_labels, yaw_stats_labels, single_linear_stats_labels

    janela._current_graph_mode = 'linear'
    #x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear() # REMOVED: Data clearing
    parar_animacoes()
    limpar_area_principal()

    if single_graph_mode.get(): # Single graph mode
        frame_single_linear = ctk.CTkFrame(master=janela); frame_single_linear.pack(fill="both", expand=True, pady=5, padx=10)
        fig_single_linear = Figure(figsize=(12, 6), dpi=100)
        ax_single_linear = fig_single_linear.add_subplot(111)
        ax_single_linear.set_title("Pitch, Raw, Yaw (Combined)")
        ax_single_linear.grid(True)
        ax_single_linear.set_xlabel("Time")
        ax_single_linear.set_ylabel("Value")

        line_pitch_single = None
        line_raw_single = None
        line_yaw_single = None

        lines_to_plot_in_legend = []

        if check_var1.get():
            line_pitch_single, = ax_single_linear.plot([], [], 'r-', label='Pitch')
            lines_to_plot_in_legend.append(line_pitch_single)
        if check_var2.get():
            line_raw_single, = ax_single_linear.plot([], [], 'g-', label='Raw')
            lines_to_plot_in_legend.append(line_raw_single)
        if check_var3.get():
            line_yaw_single, = ax_single_linear.plot([], [], 'b-', label='Yaw')
            lines_to_plot_in_legend.append(line_yaw_single)

        if lines_to_plot_in_legend:
            ax_single_linear.legend(handles=lines_to_plot_in_legend, loc='upper left')
        else:
            if ax_single_linear.legend_:
                ax_single_linear.legend_.remove()


        canvas_single_linear = FigureCanvasTkAgg(fig_single_linear, master=frame_single_linear)
        canvas_single_linear.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

        toolbar_single_linear = NavigationToolbar2Tk(canvas_single_linear, frame_single_linear)
        toolbar_single_linear.update()
        widgets_criados.append(frame_single_linear)

        # Add statistics frame for single linear graph
        stats_frame_single_linear = create_statistics_frame(frame_single_linear, "Estatísticas Combinadas", single_linear_stats_labels)
        widgets_criados.append(stats_frame_single_linear)


        def atualizar_single_linear(i):
            atualizar_dados_para_graficos()
            updated_artists = []
            
            # Collect all data that is currently being plotted for statistics
            all_data_for_stats = []
            if check_var1.get() and line_pitch_single:
                line_pitch_single.set_data(x_data, y_data)
                updated_artists.append(line_pitch_single)
                all_data_for_stats.extend(y_data)
            if check_var2.get() and line_raw_single:
                line_raw_single.set_data(x_data2, y_data2)
                updated_artists.append(line_raw_single)
                all_data_for_stats.extend(y_data2)
            if check_var3.get() and line_yaw_single:
                line_yaw_single.set_data(x_data3, y_data3)
                updated_artists.append(line_yaw_single)
                all_data_for_stats.extend(y_data3)

            # Update statistics for the single combined graph
            update_statistics_display(all_data_for_stats, single_linear_stats_labels)

            if ax_single_linear:
                ax_single_linear.relim()
                ax_single_linear.autoscale_view()
                canvas_single_linear.draw_idle()
            return updated_artists

        ani_single_linear = FuncAnimation(fig_single_linear, atualizar_single_linear, interval=100, blit=False, cache_frame_data=False)


    else: # Original multiple graph mode
        if check_var1.get():
            frame_pitch = ctk.CTkFrame(master=janela); frame_pitch.pack(fill="both", expand=True, pady=5, padx=10)
            fig_pitch = Figure(figsize=(12, 2), dpi=100)
            ax = fig_pitch.add_subplot(111); ax.set_title("Pitch"); ax.grid(True)
            canvas_pitch = FigureCanvasTkAgg(fig_pitch, master=frame_pitch)
            canvas_pitch.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

            toolbar_pitch = NavigationToolbar2Tk(canvas_pitch, frame_pitch)
            toolbar_pitch.update()
            line1, = ax.plot([], [], 'r-'); widgets_criados.append(frame_pitch)
            # Add statistics frame for Pitch
            stats_frame_pitch = create_statistics_frame(frame_pitch, "Estatísticas Pitch", pitch_stats_labels)
            widgets_criados.append(stats_frame_pitch)


        if check_var2.get():
            frame_raw = ctk.CTkFrame(master=janela); frame_raw.pack(fill="both", expand=True, pady=5, padx=10)
            fig_raw = Figure(figsize=(12, 2), dpi=100)
            ax2 = fig_raw.add_subplot(111); ax2.set_title("Raw"); ax2.grid(True)
            canvas_raw = FigureCanvasTkAgg(fig_raw, master=frame_raw)
            canvas_raw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

            toolbar_raw = NavigationToolbar2Tk(canvas_raw, frame_raw)
            toolbar_raw.update()
            line2, = ax2.plot([], [], 'g-'); widgets_criados.append(frame_raw)
            # Add statistics frame for Raw
            stats_frame_raw = create_statistics_frame(frame_raw, "Estatísticas Raw", raw_stats_labels)
            widgets_criados.append(stats_frame_raw)

        if check_var3.get():
            frame_yaw = ctk.CTkFrame(master=janela); frame_yaw.pack(fill="both", expand=True, pady=5, padx=10)
            fig_yaw = Figure(figsize=(12, 2), dpi=100)
            ax3 = fig_yaw.add_subplot(111); ax3.set_title("Yaw"); ax3.grid(True)
            canvas_yaw = FigureCanvasTkAgg(fig_yaw, master=frame_yaw)
            canvas_yaw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

            toolbar_yaw = NavigationToolbar2Tk(canvas_yaw, frame_yaw)
            toolbar_yaw.update()
            line3, = ax3.plot([], [], 'b-'); widgets_criados.append(frame_yaw)
            # Add statistics frame for Yaw
            stats_frame_yaw = create_statistics_frame(frame_yaw, "Estatísticas Yaw", yaw_stats_labels)
            widgets_criados.append(stats_frame_yaw)

        def atualizar_cartesianos(i):
            atualizar_dados_para_graficos()
            updated_artists = []
            if check_var1.get() and ax and line1:
                line1.set_data(x_data, y_data)
                ax.relim(); ax.autoscale_view()
                updated_artists.append(line1)
                if canvas_pitch: canvas_pitch.draw_idle()
                # Update statistics for Pitch
                update_statistics_display(y_data, pitch_stats_labels)

            if check_var2.get() and ax2 and line2:
                line2.set_data(x_data2, y_data2)
                ax2.relim(); ax2.autoscale_view()
                updated_artists.append(line2)
                if canvas_raw: canvas_raw.draw_idle()
                # Update statistics for Raw
                update_statistics_display(y_data2, raw_stats_labels)

            if check_var3.get() and ax3 and line3:
                line3.set_data(x_data3, y_data3)
                ax3.relim(); ax3.autoscale_view()
                updated_artists.append(line3)
                if canvas_yaw: canvas_yaw.draw_idle()
                # Update statistics for Yaw
                update_statistics_display(y_data3, yaw_stats_labels)
            return updated_artists

        if check_var1.get() and fig_pitch:
            ani1 = FuncAnimation(fig_pitch, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
        if check_var2.get() and fig_raw:
            ani2 = FuncAnimation(fig_raw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
        if check_var3.get() and fig_yaw:
            ani3 = FuncAnimation(fig_yaw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)

def GraficosPolares():
    global canvas_polar, widgets_criados, ani_polar, fig_polar, ax_polar1, ax_polar2, ax_polar3
    global bar_polar1_patch, bar_polar2_patch, bar_polar3_patch
    global single_graph_mode
    global fig_single_polar, canvas_single_polar, ax_single_polar, ani_single_polar
    global bar_pitch_single, bar_raw_single, bar_yaw_single
    global pitch_stats_labels, raw_stats_labels, yaw_stats_labels, single_polar_stats_labels

    janela._current_graph_mode = 'polar'
    #x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear() # REMOVED: Data clearing
    parar_animacoes()
    limpar_area_principal()

    bar_width_rad = 0.2

    if single_graph_mode.get(): # Single graph mode
        parent_frame_single_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
        parent_frame_single_polar.pack(fill="both", expand=True, pady=10, padx=10)
        widgets_criados.append(parent_frame_single_polar)

        fig_single_polar = Figure(figsize=(8, 8), dpi=100)
        ax_single_polar = fig_single_polar.add_subplot(111, projection='polar')
        ax_single_polar.set_title("Polar Combined (Pitch, Raw, Yaw)")
        ax_single_polar.set_theta_direction(1) # Clockwise
        ax_single_polar.set_rlim(0, 1) # Normalised radius
        ax_single_polar.set_rticks([]) # No radial ticks for a cleaner look

        bar_pitch_single = None
        bar_raw_single = None
        bar_yaw_single = None
        
        bars_to_plot_in_legend = []

        if check_var1.get():
            # Initial plot for Pitch
            bar_pitch_single, = ax_single_polar.plot([0, 0], [0, 1], color='red', linewidth=2, label='Pitch', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_pitch_single)
        if check_var2.get():
            # Initial plot for Raw
            bar_raw_single, = ax_single_polar.plot([0, 0], [0, 1], color='green', linewidth=2, label='Raw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_raw_single)
        if check_var3.get():
            # Initial plot for Yaw
            bar_yaw_single, = ax_single_polar.plot([0, 0], [0, 1], color='blue', linewidth=2, label='Yaw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_yaw_single)

        if bars_to_plot_in_legend:
            ax_single_polar.legend(handles=bars_to_plot_in_legend, loc='upper right', bbox_to_anchor=(1.1, 1.1))
        else:
            if ax_single_polar.legend_:
                ax_single_polar.legend_.remove()

        canvas_single_polar = FigureCanvasTkAgg(fig_single_polar, master=parent_frame_single_polar)
        canvas_single_polar.get_tk_widget().pack(anchor=tk.CENTER, expand=True, fill='both')

        toolbar_single_polar = NavigationToolbar2Tk(canvas_single_polar, parent_frame_single_polar)
        toolbar_single_polar.update()

        # Add statistics frame for single polar graph
        stats_frame_single_polar = create_statistics_frame(parent_frame_single_polar, "Estatísticas Combinadas", single_polar_stats_labels)
        widgets_criados.append(stats_frame_single_polar)

        def atualizar_single_polar(i):
            atualizar_dados_para_graficos()
            updated_artists = []
            all_data_for_stats = []

            if len(y_data) > 0:
                if check_var1.get() and bar_pitch_single:
                    pitch_rad = math.radians(y_data[-1])
                    bar_pitch_single.set_data([0, pitch_rad], [0, 1])
                    updated_artists.append(bar_pitch_single)
                    all_data_for_stats.append(y_data[-1])
                if check_var2.get() and bar_raw_single:
                    raw_rad = math.radians(y_data2[-1])
                    bar_raw_single.set_data([0, raw_rad], [0, 1])
                    updated_artists.append(bar_raw_single)
                    all_data_for_stats.append(y_data2[-1])
                if check_var3.get() and bar_yaw_single:
                    yaw_rad = math.radians(y_data3[-1])
                    bar_yaw_single.set_data([0, yaw_rad], [0, 1])
                    updated_artists.append(bar_yaw_single)
                    all_data_for_stats.append(y_data3[-1])
            
            # Update statistics for the single combined polar graph
            update_statistics_display(all_data_for_stats, single_polar_stats_labels)

            canvas_single_polar.draw_idle() # Redraw the canvas
            return updated_artists

        ani_single_polar = FuncAnimation(fig_single_polar, atualizar_single_polar, interval=50, blit=False, cache_frame_data=False)


    else: # Original multiple polar graph mode
        num_active_polar_graphs = check_var1.get() + check_var2.get() + check_var3.get()
        if num_active_polar_graphs > 0:
            parent_frame_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
            parent_frame_polar.pack(fill="both", expand=True, pady=10, padx=10)
            widgets_criados.append(parent_frame_polar)

            fig_polar = Figure(figsize=(4 * num_active_polar_graphs, 6), dpi=100)
            current_subplot = 1

            if check_var1.get():
                ax_polar1 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                ax_polar1.set_title("Polar Pitch")
                ax_polar1.set_theta_direction(1)
                ax_polar1.set_rlim(0, 1)
                ax_polar1.set_rticks([])
                bar_polar1_patch = ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
                current_subplot += 1
            if check_var2.get():
                ax_polar2 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                ax_polar2.set_title("Polar Raw")
                ax_polar2.set_theta_direction(1)
                ax_polar2.set_rlim(0, 1)
                ax_polar2.set_rticks([])
                bar_polar2_patch = ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
                current_subplot += 1
            if check_var3.get():
                ax_polar3 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
                ax_polar3.set_title("Polar Yaw")
                ax_polar3.set_theta_direction(1)
                ax_polar3.set_rlim(0, 1)
                ax_polar3.set_rticks([])
                bar_polar3_patch = ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]
                current_subplot += 1

            fig_polar.subplots_adjust(wspace=0.5) # Adjust horizontal spacing
            canvas_polar = FigureCanvasTkAgg(fig_polar, master=parent_frame_polar)
            canvas_polar.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

            toolbar_polar = NavigationToolbar2Tk(canvas_polar, parent_frame_polar)
            toolbar_polar.update()

            # Add statistics frames for multiple polar graphs
            if check_var1.get():
                stats_frame_pitch = create_statistics_frame(parent_frame_polar, "Estatísticas Pitch", pitch_stats_labels)
                widgets_criados.append(stats_frame_pitch)
            if check_var2.get():
                stats_frame_raw = create_statistics_frame(parent_frame_polar, "Estatísticas Raw", raw_stats_labels)
                widgets_criados.append(stats_frame_raw)
            if check_var3.get():
                stats_frame_yaw = create_statistics_frame(parent_frame_polar, "Estatísticas Yaw", yaw_stats_labels)
                widgets_criados.append(stats_frame_yaw)

            def atualizar_polares(i):
                atualizar_dados_para_graficos()
                updated_artists = []
                if len(y_data) > 0:
                    if check_var1.get() and bar_polar1_patch:
                        pitch_rad = math.radians(y_data[-1])
                        bar_polar1_patch.set_x(pitch_rad - bar_width_rad/2)
                        bar_polar1_patch.set_height(1) # Keep height at 1 for fixed length indicator
                        updated_artists.append(bar_polar1_patch)
                        update_statistics_display(y_data, pitch_stats_labels)
                    if check_var2.get() and bar_polar2_patch:
                        raw_rad = math.radians(y_data2[-1])
                        bar_polar2_patch.set_x(raw_rad - bar_width_rad/2)
                        bar_polar2_patch.set_height(1)
                        updated_artists.append(bar_polar2_patch)
                        update_statistics_display(y_data2, raw_stats_labels)
                    if check_var3.get() and bar_polar3_patch:
                        yaw_rad = math.radians(y_data3[-1])
                        bar_polar3_patch.set_x(yaw_rad - bar_width_rad/2)
                        bar_polar3_patch.set_height(1)
                        updated_artists.append(bar_polar3_patch)
                        update_statistics_display(y_data3, yaw_stats_labels)
                canvas_polar.draw_idle()
                return updated_artists

            ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, blit=False, cache_frame_data=False)


def Grafico3D():
    global canvas_3d, ax_3d, fig_3d, ani_3d, widgets_criados
    global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
    global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
    global pitch_opposite_line, raw_opposite_line, yaw_opposite_line
    global pitch_opposite_point, raw_opposite_point, yaw_opposite_point
    global slider_pitch_val, slider_roll_val, slider_yaw_val
    global label_pitch_val, label_roll_val, label_yaw_val
    global override_pitch_var, override_roll_var, override_yaw_var
    global single_3d_stats_labels

    janela._current_graph_mode = '3d'
    parar_animacoes()
    limpar_area_principal()

    # Create a main frame to hold the 3D graph and its controls
    main_3d_frame = ctk.CTkFrame(master=janela, fg_color="transparent")
    main_3d_frame.pack(fill="both", expand=True, pady=10, padx=10)
    widgets_criados.append(main_3d_frame)

    # Frame for the 3D plot
    plot_frame = ctk.CTkFrame(main_3d_frame)
    plot_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
    widgets_criados.append(plot_frame) # Add to widgets_criados if you want to clear it later

    # Create the 3D plot
    fig_3d = Figure(figsize=(8, 8), dpi=100)
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    ax_3d.set_title("Orientação 3D (Pitch, Roll, Yaw)")
    ax_3d.set_xlim([-1, 1]); ax_3d.set_ylim([-1, 1]); ax_3d.set_zlim([-1, 1])
    ax_3d.set_xlabel("X (Roll)"); ax_3d.set_ylabel("Y (Pitch)"); ax_3d.set_zlabel("Z (Yaw)")
    ax_3d.set_aspect('equal', adjustable='box')
    ax_3d.grid(True)

    # Initial lines for indicators (red for Pitch, green for Roll, blue for Yaw)
    pitch_indicator_line, = ax_3d.plot([0, 0], [0, 1], [0, 0], color='red', linewidth=3, label='Pitch')
    pitch_indicator_point = ax_3d.plot([0], [1], [0], color='red', marker='o', markersize=8)[0]
    
    raw_indicator_line, = ax_3d.plot([0, 1], [0, 0], [0, 0], color='green', linewidth=3, label='Roll')
    raw_indicator_point = ax_3d.plot([1], [0], [0], color='green', marker='o', markersize=8)[0]

    yaw_indicator_line, = ax_3d.plot([0, 0], [0, 0], [0, 1], color='blue', linewidth=3, label='Yaw')
    yaw_indicator_point = ax_3d.plot([0], [0], [1], color='blue', marker='o', markersize=8)[0]

    # Initialize opposite indicators (dashed lines, smaller markers, lighter shades)
    pitch_opposite_line, = ax_3d.plot([0, 0], [0, -1], [0, 0], color='salmon', linestyle='--', linewidth=2)
    pitch_opposite_point = ax_3d.plot([0], [-1], [0], color='salmon', marker='o', markersize=5)[0]

    raw_opposite_line, = ax_3d.plot([0, -1], [0, 0], [0, 0], color='lightgreen', linestyle='--', linewidth=2)
    raw_opposite_point = ax_3d.plot([-1], [0], [0], color='lightgreen', marker='o', markersize=5)[0]

    yaw_opposite_line, = ax_3d.plot([0, 0], [0, 0], [0, -1], color='lightblue', linestyle='--', linewidth=2)
    yaw_opposite_point = ax_3d.plot([0], [0], [-1], color='lightblue', marker='o', markersize=5)[0]

    ax_3d.legend()

    canvas_3d = FigureCanvasTkAgg(fig_3d, master=plot_frame)
    canvas_3d.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

    toolbar_3d = NavigationToolbar2Tk(canvas_3d, plot_frame)
    toolbar_3d.update()

    # Frame for controls and statistics on the right side
    controls_stats_frame = ctk.CTkFrame(main_3d_frame)
    controls_stats_frame.pack(side="right", fill="y", padx=(10, 0))
    widgets_criados.append(controls_stats_frame)

    # Sliders and their labels
    ctk.CTkLabel(controls_stats_frame, text="Controles Manuais (Override)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10,5), padx=10)

    # Pitch Slider
    override_pitch_var = ctk.BooleanVar(value=False)
    check_override_pitch = ctk.CTkCheckBox(controls_stats_frame, text="Override Pitch", variable=override_pitch_var, command=update_3d_override_state)
    check_override_pitch.pack(pady=(5,0), padx=10, anchor="w")
    slider_pitch = ctk.CTkSlider(controls_stats_frame, from_=-90, to=90, number_of_steps=180, command=lambda val: update_3d(val, 'pitch'))
    slider_pitch.set(slider_pitch_val)
    slider_pitch.pack(pady=5, padx=10)
    label_pitch_val = ctk.CTkLabel(controls_stats_frame, text=f"Pitch: {slider_pitch_val:.1f}°")
    label_pitch_val.pack(pady=(0,10), padx=10)

    # Roll Slider
    override_roll_var = ctk.BooleanVar(value=False)
    check_override_roll = ctk.CTkCheckBox(controls_stats_frame, text="Override Roll", variable=override_roll_var, command=update_3d_override_state)
    check_override_roll.pack(pady=(5,0), padx=10, anchor="w")
    slider_roll = ctk.CTkSlider(controls_stats_frame, from_=-90, to=90, number_of_steps=180, command=lambda val: update_3d(val, 'roll'))
    slider_roll.set(slider_roll_val)
    slider_roll.pack(pady=5, padx=10)
    label_roll_val = ctk.CTkLabel(controls_stats_frame, text=f"Roll: {slider_roll_val:.1f}°")
    label_roll_val.pack(pady=(0,10), padx=10)

    # Yaw Slider
    override_yaw_var = ctk.BooleanVar(value=False)
    check_override_yaw = ctk.CTkCheckBox(controls_stats_frame, text="Override Yaw", variable=override_yaw_var, command=update_3d_override_state)
    check_override_yaw.pack(pady=(5,0), padx=10, anchor="w")
    slider_yaw = ctk.CTkSlider(controls_stats_frame, from_=0, to=360, number_of_steps=360, command=lambda val: update_3d(val, 'yaw'))
    slider_yaw.set(slider_yaw_val)
    slider_yaw.pack(pady=5, padx=10)
    label_yaw_val = ctk.CTkLabel(controls_stats_frame, text=f"Yaw: {slider_yaw_val:.1f}°")
    label_yaw_val.pack(pady=(0,10), padx=10)
    
    # Statistics frame for 3D graph
    stats_frame_3d = create_statistics_frame(controls_stats_frame, "Estatísticas 3D Combinadas", single_3d_stats_labels)
    widgets_criados.append(stats_frame_3d)

    def update_3d(frame=None, source_slider=None):
        global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
        global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
        global pitch_opposite_line, raw_opposite_line, yaw_opposite_line
        global pitch_opposite_point, raw_opposite_point, yaw_opposite_point
        global slider_pitch_val, slider_roll_val, slider_yaw_val

        # Acquire new data only if not overriding with sliders
        if not override_pitch_var.get() or \
           not override_roll_var.get() or \
           not override_yaw_var.get():
            atualizar_dados_para_graficos() # This updates y_data, y_data2, y_data3

        # Determine values to plot
        current_pitch = slider_pitch_val if override_pitch_var.get() else (y_data[-1] if y_data else 0)
        current_roll = slider_roll_val if override_roll_var.get() else (y_data2[-1] if y_data2 else 0)
        current_yaw = slider_yaw_val if override_yaw_var.get() else (y_data3[-1] if y_data3 else 0)
        
        # Update slider values if they are being driven by acquired data
        if not override_pitch_var.get() and y_data:
            slider_pitch.set(current_pitch)
        if not override_roll_var.get() and y_data2:
            slider_roll.set(current_roll)
        if not override_yaw_var.get() and y_data3:
            slider_yaw.set(current_yaw)

        # Update labels (always show current value, whether from slider or acquired data)
        label_pitch_val.configure(text=f"Pitch: {current_pitch:.1f}°")
        label_roll_val.configure(text=f"Roll: {current_roll:.1f}°")
        label_yaw_val.configure(text=f"Yaw: {current_yaw:.1f}°")

        # Convert to radians for trigonometric functions
        pitch_rad = math.radians(current_pitch)
        roll_rad = math.radians(current_roll)
        yaw_rad = math.radians(current_yaw)

        # Calculate coordinates for Pitch (Y-axis for pitch, X-Z plane rotation)
        # Assuming Pitch is rotation around X (or roll axis in some conventions)
        # This is a bit tricky as Matplotlib 3D axes are fixed. We rotate the point.
        # For simplicity, let's just make it visually intuitive by mapping angles
        # to positions on a sphere or circle that represents the plane of rotation.
        # A simple approach is to use sine/cosine for each axis independently for visualization.

        # For Pitch (Y-axis on the graph): varies with Y coordinate
        # Let's say pitch affects the Y coordinate for a point at X=0, Z=0
        pitch_y = math.sin(pitch_rad)
        pitch_z = math.cos(pitch_rad) # Use Z to show pitch in a vertical plane

        # For Roll (X-axis on the graph): varies with X coordinate
        roll_x = math.sin(roll_rad)
        roll_z = math.cos(roll_rad) # Use Z to show roll in a horizontal plane

        # For Yaw (Z-axis on the graph): varies with Z coordinate
        yaw_x = math.sin(yaw_rad) # Yaw affects X and Y in the horizontal plane
        yaw_y = math.cos(yaw_rad)

        # Update indicator lines and points
        # Pitch (Red): Represents rotation around the X-axis (roll axis).
        # We can visualize it as a line moving in the Y-Z plane.
        pitch_indicator_line.set_data_3d([0, 0], [0, pitch_y], [0, pitch_z])
        pitch_indicator_point.set_data_3d([0], [pitch_y], [pitch_z])
        pitch_opposite_line.set_data_3d([0, 0], [0, -pitch_y], [0, -pitch_z])
        pitch_opposite_point.set_data_3d([0], [-pitch_y], [-pitch_z])


        # Roll (Green): Represents rotation around the Y-axis (pitch axis).
        # We can visualize it as a line moving in the X-Z plane.
        raw_indicator_line.set_data_3d([0, roll_x], [0, 0], [0, roll_z])
        raw_indicator_point.set_data_3d([roll_x], [0], [roll_z])
        raw_opposite_line.set_data_3d([0, -roll_x], [0, 0], [0, -roll_z])
        raw_opposite_point.set_data_3d([-roll_x], [0], [-roll_z])


        # Yaw (Blue): Represents rotation around the Z-axis (yaw axis).
        # We can visualize it as a line moving in the X-Y plane.
        yaw_indicator_line.set_data_3d([0, yaw_x], [0, yaw_y], [0, 0])
        yaw_indicator_point.set_data_3d([yaw_x], [yaw_y], [0])
        yaw_opposite_line.set_data_3d([0, -yaw_x], [0, -yaw_y], [0, 0])
        yaw_opposite_point.set_data_3d([-yaw_x], [-yaw_y], [0])

        # Update statistics for the 3D graph (combined values)
        all_3d_data_for_stats = []
        if y_data: all_3d_data_for_stats.append(current_pitch)
        if y_data2: all_3d_data_for_stats.append(current_roll)
        if y_data3: all_3d_data_for_stats.append(current_yaw)
        update_statistics_display(all_3d_data_for_stats, single_3d_stats_labels)

        canvas_3d.draw_idle()
        return [pitch_indicator_line, pitch_indicator_point, raw_indicator_line, raw_indicator_point,
                yaw_indicator_line, yaw_indicator_point,
                pitch_opposite_line, pitch_opposite_point, raw_opposite_line, raw_opposite_point,
                yaw_opposite_line, yaw_opposite_point]

    def update_3d_override_state():
        """Called when an override checkbox is toggled."""
        update_3d() # Force an update to use new override state

    # Start the animation for 3D graph
    ani_3d = FuncAnimation(fig_3d, update_3d, interval=100, blit=False, cache_frame_data=False)


def tela_inicial():
    global widgets_criados, main_title_frame, gif_label, gif_path
    parar_animacoes()
    limpar_area_principal()

    # Criação do frame do título da aba principal (barra de destaque)
    main_title_frame = ctk.CTkFrame(master=janela, height=50, fg_color="#3A7EB8") # Azul escuro para destaque
    main_title_frame.pack(fill="x", pady=(10, 0), padx=10)
    widgets_criados.append(main_title_frame)

    label_titulo_principal = ctk.CTkLabel(main_title_frame, text="BEM-VINDO AO DASHBOARD!", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
    label_titulo_principal.pack(expand=True, pady=5)

    # Frame para o conteúdo da tela inicial (abaixo do título)
    content_frame = ctk.CTkFrame(master=janela, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, pady=10, padx=10)
    widgets_criados.append(content_frame)

    # Adicionar o GIF
    if gif_path:
        load_gif(gif_path, content_frame) # content_frame é o parent para o gif_label

def load_gif(path, parent_frame):
    global gif_frames, gif_index, gif_label, gif_after_id
    try:
        image = Image.open(path)
        gif_frames = []
        for frame in ImageSequence.Iterator(image):
            # Redimensionar cada frame para um tamanho adequado, por exemplo, 400x400
            frame_resized = frame.copy().resize((400, 400), Image.Resampling.LANCZOS)
            gif_frames.append(ImageTk.PhotoImage(frame_resized))

        gif_index = 0
        if gif_label:
            gif_label.destroy()
        gif_label = ctk.CTkLabel(parent_frame, text="", compound="image")
        gif_label.pack(pady=20)
        animate_gif()
    except Exception as e:
        print(f"Erro ao carregar GIF: {e}")
        if gif_label:
            gif_label.destroy() # Remove label if GIF fails to load

def animate_gif():
    global gif_frames, gif_index, gif_label, gif_after_id
    if gif_label and gif_frames:
        frame = gif_frames[gif_index]
        gif_label.configure(image=frame)
        gif_index = (gif_index + 1) % len(gif_frames)
        gif_after_id = janela.after(100, animate_gif) # Ajuste o intervalo conforme necessário (100ms)

def parar_gif_animacao():
    global gif_after_id
    if gif_after_id:
        janela.after_cancel(gif_after_id)
        gif_after_id = None
    if gif_label:
        gif_label.destroy()
        gif_label = None


def conectar_serial():
    global serial_conn, modo_conexao
    if serial_conn and serial_conn.is_open:
        serial_conn.close()
        serial_conn = None
        modo_conexao = None
        print("Conexão Serial Fechada.")
        label_dados.configure(text="Conexão: Desconectado")
        return

    porta = entry_porta.get()
    baud = int(entry_baud.get())
    try:
        serial_conn = serial.Serial(porta, baud, timeout=1)
        modo_conexao = 'serial'
        print(f"Conexão Serial estabelecida em {porta}:{baud}")
        label_dados.configure(text=f"Conexão: Serial ({porta}:{baud})")
    except Exception as e:
        print(f"Erro ao conectar Serial: {e}")
        label_dados.configure(text="Conexão: Erro Serial")

def conectar_wifi():
    global client, modo_conexao
    if client:
        client.close()
        client = None
        modo_conexao = None
        print("Conexão Wi-Fi Fechada.")
        label_dados.configure(text="Conexão: Desconectado")
        return

    esp_ip = entry_ip.get()
    esp_port = int(entry_port.get())
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((esp_ip, esp_port))
        modo_conexao = 'wifi'
        print(f"Conexão Wi-Fi estabelecida em {esp_ip}:{esp_port}")
        label_dados.configure(text=f"Conexão: Wi-Fi ({esp_ip}:{esp_port})")
    except Exception as e:
        print(f"Erro ao conectar Wi-Fi: {e}")
        label_dados.configure(text="Conexão: Erro Wi-Fi")
        client = None # Ensure client is None on failure

def buscar_portas_seriais():
    ports = serial.tools.list_ports.comports()
    lista_portas = [port.device for port in ports]
    if lista_portas:
        entry_porta.set(lista_portas[0]) # Seleciona a primeira porta encontrada por padrão
        print(f"Portas seriais encontradas: {lista_portas}")
    else:
        entry_porta.set("Nenhuma Porta")
        print("Nenhuma porta serial encontrada.")

def conexao():
    global widgets_criados, label_dados, entry_porta, entry_baud, entry_ip, entry_port, main_title_frame
    parar_animacoes()
    limpar_area_principal()

    # Criação do frame do título da aba principal (barra de destaque)
    main_title_frame = ctk.CTkFrame(master=janela, height=50, fg_color="#3A7EB8") # Azul escuro para destaque
    main_title_frame.pack(fill="x", pady=(10, 0), padx=10)
    widgets_criados.append(main_title_frame)

    label_titulo_principal = ctk.CTkLabel(main_title_frame, text="CONFIGURAÇÕES DE CONEXÃO", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
    label_titulo_principal.pack(expand=True, pady=5)


    # Frame principal para os controles de conexão
    connection_frame = ctk.CTkFrame(master=janela, fg_color="transparent")
    connection_frame.pack(pady=20, padx=20, fill="both", expand=True)
    widgets_criados.append(connection_frame)

    # Seção de Conexão Serial
    serial_frame = ctk.CTkFrame(connection_frame)
    serial_frame.pack(pady=10, padx=10, fill="x")
    ctk.CTkLabel(serial_frame, text="Conexão Serial", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

    frame_porta = ctk.CTkFrame(serial_frame, fg_color="transparent")
    frame_porta.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(frame_porta, text="Porta Serial:").pack(side="left")
    entry_porta = ctk.CTkComboBox(frame_porta, values=["Nenhuma Porta"])
    entry_porta.pack(side="left", expand=True, fill="x", padx=5)
    botao_buscar_portas = ctk.CTkButton(frame_porta, text="Buscar Portas", command=buscar_portas_seriais)
    botao_buscar_portas.pack(side="left")

    frame_baud = ctk.CTkFrame(serial_frame, fg_color="transparent")
    frame_baud.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(frame_baud, text="Baud Rate:").pack(side="left")
    entry_baud = ctk.CTkEntry(frame_baud)
    entry_baud.insert(0, "115200")
    entry_baud.pack(side="left", expand=True, fill="x", padx=5)

    botao_conectar_serial = ctk.CTkButton(serial_frame, text="Conectar Serial", command=conectar_serial)
    botao_conectar_serial.pack(pady=10)

    # Seção de Conexão Wi-Fi
    wifi_frame = ctk.CTkFrame(connection_frame)
    wifi_frame.pack(pady=10, padx=10, fill="x")
    ctk.CTkLabel(wifi_frame, text="Conexão Wi-Fi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

    frame_ip = ctk.CTkFrame(wifi_frame, fg_color="transparent")
    frame_ip.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(frame_ip, text="IP do ESP32:").pack(side="left")
    entry_ip = ctk.CTkEntry(frame_ip)
    entry_ip.insert(0, "192.168.4.1") # IP padrão do ESP32 no modo AP
    entry_ip.pack(side="left", expand=True, fill="x", padx=5)

    frame_port = ctk.CTkFrame(wifi_frame, fg_color="transparent")
    frame_port.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(frame_port, text="Porta:").pack(side="left")
    entry_port = ctk.CTkEntry(frame_port)
    entry_port.insert(0, "12345")
    entry_port.pack(side="left", expand=True, fill="x", padx=5)

    botao_conectar_wifi = ctk.CTkButton(wifi_frame, text="Conectar Wi-Fi", command=conectar_wifi)
    botao_conectar_wifi.pack(pady=10)

    # Status da Conexão
    label_dados = ctk.CTkLabel(connection_frame, text="Conexão: Desconectado", font=ctk.CTkFont(size=14, weight="bold"))
    label_dados.pack(pady=20)


def mostrar_view(comando_view, button_obj):
    global active_sidebar_button
    parar_animacoes() # Certifica-se de parar animações antes de mudar de view
    limpar_area_principal() # Limpa a área principal antes de carregar nova view
    parar_gif_animacao() # Garante que o GIF pare quando sair da tela inicial

    if comando_view == 'tela_inicial':
        tela_inicial()
        janela.title("Dashboard ESP32 - Início")
    elif comando_view == 'conexao':
        conexao()
        janela.title("Dashboard ESP32 - Conexão")
    elif comando_view == 'graficos':
        Graficos()
        janela.title("Dashboard ESP32 - Gráficos")
    elif comando_view == 'polares':
        GraficosPolares()
        janela.title("Dashboard ESP32 - Gráficos Polares")
    elif comando_view == 'grafico_3d':
        Grafico3D()
        janela.title("Dashboard ESP32 - Gráfico 3D")
    elif comando_view == 'fechar':
        # This part will ideally not be reached if command_func is used directly for 'Fechar'
        # But as a fallback or for other cases where 'fechar' might be passed as a view command
        fechar_programa()
        return # Exit to prevent button styling if program is closing


    # Atualiza o estilo do botão ativo na barra lateral
    if active_sidebar_button:
        active_sidebar_button.configure(fg_color="transparent") # Reset previous active button
    button_obj.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"]) # Set new active button style
    active_sidebar_button = button_obj


def adicionar_botao(parent, caminho_icone, texto, comando_view=None, command_func=None):
    icone_tk = None
    if caminho_icone:
        try:
            icone_image = Image.open(caminho_icone)
            icone_image = icone_image.resize((20, 20), Image.Resampling.LANCZOS)
            icone_tk = ImageTk.PhotoImage(icone_image)
        except FileNotFoundError:
            print(f"Erro: Ícone não encontrado em {caminho_icone}. Continuando sem imagem.")
            icone_tk = None
        except Exception as e:
            print(f"Erro ao carregar ícone {caminho_icone}: {e}")
            icone_tk = None
    
    if command_func: # Se uma função direta for fornecida, use-a
        botao = ctk.CTkButton(parent, text=texto, image=icone_tk, compound="left", command=command_func)
    else: # Caso contrário, use a lógica existente com mostrar_view
        botao = ctk.CTkButton(parent, text=texto, image=icone_tk, compound="left", command=lambda btn=None, view=comando_view: mostrar_view(view, btn))
        # Note: 'btn=None' is a quick fix if the lambda's 'btn' argument isn't strictly needed for mostrar_view
        # or if the original logic for 'btn=botao' was causing issues when 'botao' is not yet fully defined
        # for self-reference in a lambda within the same function scope.
        # A more robust solution might pass `botao` as 'btn' after its creation.
        # However, for simply showing views, the 'btn' argument might not be strictly necessary for mostrar_view.
    
    botao.pack(fill='x', padx=10, pady=5)
    return botao

def setup_main_window():
    global janela, check_var1, check_var2, check_var3, random_data, angular_test_data, single_graph_mode
    global override_pitch_var, override_roll_var, override_yaw_var

    janela = ctk.CTk()
    janela.geometry("1200x800")
    janela.title("Dashboard ESP32")
    janela.attributes('-fullscreen', False) # Iniciar não em tela cheia
    janela.bind('<Escape>', sair_tela_cheia)

    # Configurar layout de grid para a janela principal
    janela.grid_rowconfigure(0, weight=1)
    janela.grid_columnconfigure(1, weight=1) # Coluna para o conteúdo principal

    # Frame para a barra lateral
    frame_sidebar = ctk.CTkFrame(master=janela, width=150, corner_radius=0)
    frame_sidebar.grid(row=0, column=0, sticky="nswe")
    frame_sidebar.grid_rowconfigure(8, weight=1) # Para empurrar o botão de fechar para baixo

    # Título da barra lateral
    label_sidebar_title = ctk.CTkLabel(frame_sidebar, text="MENU", font=ctk.CTkFont(size=20, weight="bold"))
    label_sidebar_title.pack(pady=(20, 10))

    # Frame para os botões de navegação
    frame_botoes_nav = ctk.CTkFrame(frame_sidebar, fg_color="transparent")
    frame_botoes_nav.pack(pady=10, fill="x")

    # Inicializa as variáveis de controle dos gráficos
    check_var1 = ctk.BooleanVar(value=True) # Pitch
    check_var2 = ctk.BooleanVar(value=True) # Raw
    check_var3 = ctk.BooleanVar(value=True) # Yaw
    random_data = ctk.BooleanVar(value=False) # Dados Aleatórios
    angular_test_data = ctk.BooleanVar(value=True) # Dados Angulares (NOVO)
    single_graph_mode = ctk.BooleanVar(value=False) # Modo de gráfico único

    # Inicializa as variáveis de override para o gráfico 3D
    override_pitch_var = ctk.BooleanVar(value=False)
    override_roll_var = ctk.BooleanVar(value=False)
    override_yaw_var = ctk.BooleanVar(value=False)


    # Adicionando botões (agora passamos o nome da view para o comando)
    btn_inicio = adicionar_botao(frame_botoes_nav, None, "Início", 'tela_inicial') # Botão Início sem imagem
    # -> VERIFIQUE E AJUSTE ESTES CAMINHOS DE ÍCONES SE ESTIVEREM ERRADOS
    btn_conexao = adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão", 'conexao')
    btn_graficos = adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\chart.png', "Gráficos", 'graficos')
    btn_polares = adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Gráficos Polares", 'polares')    
    # Adicionando o botão para o Gráfico 3D
    btn_grafico_3d = adicionar_botao(frame_botoes_nav, None, "Gráfico 3D", 'grafico_3d')
    
    # Botão Fechar - Corrigido para chamar fechar_programa diretamente
    btn_fechar = adicionar_botao(frame_botoes_nav, None, "Fechar", fechar_programa)
    btn_fechar.pack(side="bottom", fill="x", padx=10, pady=10) # Empurra o botão fechar para o final


    # Frame para o conteúdo principal (onde as views serão carregadas)
    frame_principal = ctk.CTkFrame(master=janela, corner_radius=0)
    frame_principal.grid(row=0, column=1, sticky="nswe")

    # Iniciar com a tela inicial
    mostrar_view('tela_inicial', btn_inicio)

    janela.mainloop()

if __name__ == "__main__":
    setup_main_window()