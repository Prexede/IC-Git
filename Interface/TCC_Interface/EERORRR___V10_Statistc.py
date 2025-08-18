import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import for 3D plotting
import serial.tools.list_ports
import socket
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence # Importa ImageSequence para GIFs
import math # Importar para funções senoidais
import numpy as np # Importar para operações numéricas, como linspace

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
ax_3d = None # For 3D plot
# Removidos line_3d, pois será substituído por indicadores de ângulo
ani1, ani2, ani3, ani_3d = None, None, None, None
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
fig_pitch, fig_raw, fig_yaw, fig_3d = None, None, None, None # Added fig_3d
fig_single_linear = None # NEW: For single linear graph
fig_single_polar = None  # NEW: For single polar graph

# NEW: Initialize single graph animations to None globally
ani_single_linear = None
ani_single_polar = None


# Variáveis para indicadores do gráfico 3D
global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
global pitch_indicator_point, raw_indicator_point, yaw_indicator_point

# NEW: Add variables for opposite angle indicators
global pitch_opposite_line, raw_opposite_line, yaw_opposite_line
global pitch_opposite_point, raw_opposite_point, yaw_opposite_point

# NEW: Variables for single linear graph lines
global line_pitch_single, line_raw_single, line_yaw_single

# NEW: Variables for single polar graph bars
global bar_pitch_single, bar_raw_single, bar_yaw_single

# NEW: Global variables for statistics labels
stats_labels_pitch = {}
stats_labels_raw = {}
stats_labels_yaw = {}
stats_labels_combined_linear = {} # For single linear graph
stats_labels_combined_polar = {} # For single polar graph
stats_labels_3d = {} # For 3D graph


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

# NEW: Global variable for graph status label
global graph_status_label
graph_status_label = None


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
    global paused_acquisition, graph_status_label
    paused_acquisition = True
    if graph_status_label:
        graph_status_label.configure(text="Status do Gráfico: Pausado")
    print("Aquisição de dados pausada.")

def continuar_aquisicao():
    """Resume a aquisição de dados."""
    global paused_acquisition, graph_status_label
    paused_acquisition = False
    if graph_status_label:
        graph_status_label.configure(text="Status do Gráfico: Ativo")
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
    global check_var1, check_var2, check_var3, random_data, angular_test_data, single_graph_mode # Adicionado angular_test_data e single_graph_mode

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

    # NEW: Checkbox para modo de gráfico único
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

def resetar_dados():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3, angular_time_step
    global line_pitch_single, line_raw_single, line_yaw_single # NEW: single linear lines
    global bar_pitch_single, bar_raw_single, bar_yaw_single # NEW: single polar bars

    x_data.clear(); y_data.clear()
    x_data2.clear(); y_data2.clear()
    x_data3.clear(); y_data3.clear()
    angular_time_step = 0 # Resetar o contador de tempo para dados angulares

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

    # NEW: Reset for single linear graph
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


    # Resetar eixo e patch do gráfico 3D (para a nova visualização)
    if ax_3d:
        ax_3d.clear()
        ax_3d.set_xlabel('X')
        ax_3d.set_ylabel('Y')
        ax_3d.set_zlabel('Z')
        ax_3d.set_title("Orientação 3D (Pitch, Raw, Yaw)")
        
        # Redesenha os círculos fixos
        R_circle = 100
        theta_circle = np.linspace(0, 2 * np.pi, 100)
        ax_3d.plot(np.zeros_like(theta_circle), R_circle * np.cos(theta_circle), R_circle * np.sin(theta_circle), 'r--', alpha=0.5, label='Pitch Plane')
        ax_3d.plot(R_circle * np.cos(theta_circle), np.zeros_like(theta_circle), R_circle * np.sin(theta_circle), 'g--', alpha=0.5, label='Raw Plane')
        ax_3d.plot(R_circle * np.cos(theta_circle), R_circle * np.sin(theta_circle), np.zeros_like(theta_circle), 'b--', alpha=0.5, label='Yaw Plane')
        
        # Redefine os limites dos eixos
        ax_3d.set_xlim([-R_circle, R_circle])
        ax_3d.set_ylim([-R_circle, R_circle])
        ax_3d.set_zlim([-R_circle, R_circle])

        # Reinicializa os indicadores de ponto/linha (incluindo os novos para ângulos opostos)
        global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
        global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
        global pitch_opposite_line, raw_opposite_line, yaw_opposite_line
        global pitch_opposite_point, raw_opposite_point, yaw_opposite_point

        pitch_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r-', linewidth=2)
        pitch_indicator_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=8)
        pitch_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r:', linewidth=1, alpha=0.7) # Dotted line for opposite
        pitch_opposite_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=4, alpha=0.7) # Smaller dot for opposite

        raw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g-', linewidth=2)
        raw_indicator_point, = ax_3d.plot([0], [0], [0], 'go', markersize=8)
        raw_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g:', linewidth=1, alpha=0.7)
        raw_opposite_point, = ax_3d.plot([0], [0], [0], 'go', markersize=4, alpha=0.7)

        yaw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b-', linewidth=2)
        yaw_indicator_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=8)
        yaw_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b:', linewidth=1, alpha=0.7)
        yaw_opposite_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=4, alpha=0.7)


    # Resetar eixos e patches dos gráficos polares (múltiplos)
    if bar_polar1_patch: bar_polar1_patch.set_x(0 - bar_polar1_patch.get_width()/2)
    if bar_polar2_patch: bar_polar2_patch.set_x(0 - bar_polar2_patch.get_width()/2)
    if bar_polar3_patch: bar_polar3_patch.set_x(0 - bar_polar3_patch.get_width()/2)

    # NEW: Reset for single polar graph
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


    # Redesenhar os canvases
    if 'canvas_pitch' in globals() and canvas_pitch: canvas_pitch.draw_idle()
    if 'canvas_raw' in globals() and canvas_raw: canvas_raw.draw_idle()
    if 'canvas_yaw' in globals() and canvas_yaw: canvas_yaw.draw_idle()
    if 'canvas_single_linear' in globals() and canvas_single_linear: canvas_single_linear.draw_idle() # NEW
    if canvas_polar: canvas_polar.draw_idle()
    if 'canvas_single_polar' in globals() and canvas_single_polar: canvas_single_polar.draw_idle() # NEW
    if 'canvas_3d' in globals() and canvas_3d: canvas_3d.draw_idle()

    # Reset statistics labels to N/A
    for stats_dict in [stats_labels_pitch, stats_labels_raw, stats_labels_yaw, stats_labels_combined_linear, stats_labels_combined_polar, stats_labels_3d]:
        for key in stats_dict:
            if stats_dict[key].winfo_exists():
                stats_dict[key].configure(text=key.split('_')[-1].capitalize() + ": N/A") # Reset based on the last part of key (min, max, mean, std)
    
    # Reset combined labels more specifically
    for key_prefix in ['pitch', 'raw', 'yaw']:
        for stat_type in ['min', 'max', 'mean', 'std']:
            label_key = f'{key_prefix}_{stat_type}'
            if label_key in stats_labels_combined_linear and stats_labels_combined_linear[label_key].winfo_exists():
                stats_labels_combined_linear[label_key].configure(text=f"{stat_type.capitalize()}: N/A")
            if label_key in stats_labels_combined_polar and stats_labels_combined_polar[label_key].winfo_exists():
                stats_labels_combined_polar[label_key].configure(text=f"{stat_type.capitalize()}: N/A")
            if label_key in stats_labels_3d and stats_labels_3d[label_key].winfo_exists():
                stats_labels_3d[label_key].configure(text=f"{stat_type.capitalize()}: N/A")

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
    elif angular_test_data.get(): # NOVO: Geração de dados angulares
        angular_time_step += 1
        # Gerar valores de 0 a 360 usando seno/cosseno para um movimento suave
        # Mapear seno/cosseno de [-1, 1] para [0, 360]
        pitch = (math.sin(angular_time_step * 0.05) + 1) / 2 * 360
        raw = (math.cos(angular_time_step * 0.03) + 1) / 2 * 360
        yaw = (math.sin(angular_time_step * 0.02 + math.pi/4) + 1) / 2 * 360 # Pequeno offset para yaw
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
        # Adiciona dados para todos os 3 eixos, pois eles podem ser usados por qualquer tipo de gráfico
        # (linear, polar, ou 3D)
        x_data.append(len(x_data))
        y_data.append(valores[0]) # Pitch
        x_data2.append(len(x_data2))
        y_data2.append(valores[1]) # Raw
        x_data3.append(len(x_data3))
        y_data3.append(valores[2]) # Yaw

def update_graph_display():
    # Update visibility of individual checkboxes based on single_graph_mode
    # This is a bit tricky to do directly from here as widgets are packed
    # A better approach would be to manage this in `criar_controles_laterais`
    # or by unpacking/repacking them. For now, we will just redraw the graphs
    # based on the `single_graph_mode` state.
    if hasattr(janela, '_current_graph_mode'):
        if janela._current_graph_mode == 'linear':
            Graficos()
        elif janela._current_graph_mode == 'polar':
            GraficosPolares()
        elif janela._current_graph_mode == '3d':
            Graficos3D() # Call the 3D graph update

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
    global ani1, ani2, ani3, ani_polar, ani_3d, ani_single_linear, ani_single_polar # NEW animations
    global fig_polar, fig_pitch, fig_raw, fig_yaw, fig_3d, fig_single_linear, fig_single_polar # NEW figures
    global graph_status_label # Added for status update

    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if ani_3d: ani_3d.event_source.stop(); ani_3d = None # Stop 3D animation
    if ani_single_linear: ani_single_linear.event_source.stop(); ani_single_linear = None # NEW
    if ani_single_polar: ani_single_polar.event_source.stop(); ani_single_polar = None # NEW

    # Limpar os eixos antes de fechar a figura para evitar referências pendentes
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
    if fig_3d: # Close 3D figure
        if ax_3d: ax_3d.clear()
        plt.close(fig_3d)
        fig_3d = None
    if fig_single_linear: # NEW: Close single linear figure
        global ax_single_linear
        if 'ax_single_linear' in globals() and ax_single_linear: ax_single_linear.clear()
        plt.close(fig_single_linear)
        fig_single_linear = None
    if fig_single_polar: # NEW: Close single polar figure
        global ax_single_polar
        if 'ax_single_polar' in globals() and ax_single_polar: ax_single_polar.clear()
        plt.close(fig_single_polar)
        fig_single_polar = None
    
    if graph_status_label: # Update status when animations are stopped
        graph_status_label.configure(text="Status do Gráfico: Inativo")


def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw, fig_pitch, fig_raw, fig_yaw
    global single_graph_mode # NEW
    global fig_single_linear, canvas_single_linear, ax_single_linear, ani_single_linear # NEW: for single graph
    global line_pitch_single, line_raw_single, line_yaw_single # NEW: lines for single graph
    global stats_labels_pitch, stats_labels_raw, stats_labels_yaw, stats_labels_combined_linear # NEW: stats labels
    global graph_status_label # Added for status update

    janela._current_graph_mode = 'linear'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes() # Garante que animações anteriores são paradas
    limpar_area_principal() # Hide/show individual checkboxes based on single_graph_mode state
    # This is a bit tricky to do directly from here as widgets are packed
    # A better approach would be to manage this in `criar_controles_laterais`
    # or by unpacking/repacking them. For now, we will just redraw the graphs
    # based on the `single_graph_mode` state.

    # Update graph status
    if graph_status_label:
        graph_status_label.configure(text="Status do Gráfico: Ativo")

    if single_graph_mode.get(): # NEW: Single graph mode
        frame_single_linear = ctk.CTkFrame(master=janela); frame_single_linear.pack(fill="both", expand=True, pady=5, padx=10)
        widgets_criados.append(frame_single_linear) # Add to widgets_criados

        fig_single_linear = Figure(figsize=(12, 6), dpi=100) # Larger figure for combined data
        ax_single_linear = fig_single_linear.add_subplot(111)
        ax_single_linear.set_title("Pitch, Raw, Yaw (Combined)")
        ax_single_linear.grid(True)
        ax_single_linear.set_xlabel("Time")
        ax_single_linear.set_ylabel("Value")

        # Initialize lines, but only create if selected
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

        # Add legend for only the lines that were created
        if lines_to_plot_in_legend:
            ax_single_linear.legend()
        
        canvas_single_linear = FigureCanvasTkAgg(fig_single_linear, master=frame_single_linear)
        canvas_single_linear.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

        toolbar_single_linear = NavigationToolbar2Tk(canvas_single_linear, frame_single_linear)
        toolbar_single_linear.update()

        # NEW: Statistics frame for single linear graph (combined)
        stats_frame_combined_linear = ctk.CTkFrame(master=frame_single_linear, fg_color="gray20")
        stats_frame_combined_linear.pack(fill="x", pady=(5,0), padx=10)
        widgets_criados.append(stats_frame_combined_linear)

        # Labels for Pitch stats
        ctk.CTkLabel(stats_frame_combined_linear, text="Pitch Stats:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['pitch_min'] = ctk.CTkLabel(stats_frame_combined_linear, text="Min: N/A")
        stats_labels_combined_linear['pitch_min'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['pitch_max'] = ctk.CTkLabel(stats_frame_combined_linear, text="Max: N/A")
        stats_labels_combined_linear['pitch_max'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['pitch_mean'] = ctk.CTkLabel(stats_frame_combined_linear, text="Mean: N/A")
        stats_labels_combined_linear['pitch_mean'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['pitch_std'] = ctk.CTkLabel(stats_frame_combined_linear, text="Std Dev: N/A")
        stats_labels_combined_linear['pitch_std'].grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # Labels for Raw stats
        ctk.CTkLabel(stats_frame_combined_linear, text="Raw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['raw_min'] = ctk.CTkLabel(stats_frame_combined_linear, text="Min: N/A")
        stats_labels_combined_linear['raw_min'].grid(row=1, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['raw_max'] = ctk.CTkLabel(stats_frame_combined_linear, text="Max: N/A")
        stats_labels_combined_linear['raw_max'].grid(row=1, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['raw_mean'] = ctk.CTkLabel(stats_frame_combined_linear, text="Mean: N/A")
        stats_labels_combined_linear['raw_mean'].grid(row=1, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['raw_std'] = ctk.CTkLabel(stats_frame_combined_linear, text="Std Dev: N/A")
        stats_labels_combined_linear['raw_std'].grid(row=1, column=4, padx=5, pady=2, sticky="w")

        # Labels for Yaw stats
        ctk.CTkLabel(stats_frame_combined_linear, text="Yaw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['yaw_min'] = ctk.CTkLabel(stats_frame_combined_linear, text="Min: N/A")
        stats_labels_combined_linear['yaw_min'].grid(row=2, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['yaw_max'] = ctk.CTkLabel(stats_frame_combined_linear, text="Max: N/A")
        stats_labels_combined_linear['yaw_max'].grid(row=2, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['yaw_mean'] = ctk.CTkLabel(stats_frame_combined_linear, text="Mean: N/A")
        stats_labels_combined_linear['yaw_mean'].grid(row=2, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_linear['yaw_std'] = ctk.CTkLabel(stats_frame_combined_linear, text="Std Dev: N/A")
        stats_labels_combined_linear['yaw_std'].grid(row=2, column=4, padx=5, pady=2, sticky="w")

        # Configure columns to expand evenly
        for i in range(5):
            stats_frame_combined_linear.grid_columnconfigure(i, weight=1)

        ani_single_linear = FuncAnimation(fig_single_linear, atualizar_single_linear, interval=50, blit=True, cache_frame_data=False)


    else: # Multiple graphs mode
        # Frame for Pitch graph
        if check_var1.get():
            frame_pitch = ctk.CTkFrame(master=janela); frame_pitch.pack(fill="both", expand=True, pady=5, padx=10)
            widgets_criados.append(frame_pitch) # Add to widgets_criados

            fig_pitch = Figure(figsize=(12, 2), dpi=100)
            ax = fig_pitch.add_subplot(111); ax.set_title("Pitch"); ax.grid(True)
            canvas_pitch = FigureCanvasTkAgg(fig_pitch, master=frame_pitch)
            canvas_pitch.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
            # Adicionar a barra de ferramentas do Matplotlib para o gráfico Pitch
            toolbar_pitch = NavigationToolbar2Tk(canvas_pitch, frame_pitch)
            toolbar_pitch.update()
            line1, = ax.plot([], [], 'r-')

            # NEW: Statistics frame for Pitch graph
            stats_frame_pitch = ctk.CTkFrame(master=frame_pitch, fg_color="gray20")
            stats_frame_pitch.pack(fill="x", pady=(5,0), padx=10)
            widgets_criados.append(stats_frame_pitch)

            stats_labels_pitch['min'] = ctk.CTkLabel(stats_frame_pitch, text="Min: N/A")
            stats_labels_pitch['min'].grid(row=0, column=0, padx=5, pady=2, sticky="w")
            stats_labels_pitch['max'] = ctk.CTkLabel(stats_frame_pitch, text="Max: N/A")
            stats_labels_pitch['max'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
            stats_labels_pitch['mean'] = ctk.CTkLabel(stats_frame_pitch, text="Mean: N/A")
            stats_labels_pitch['mean'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
            stats_labels_pitch['std'] = ctk.CTkLabel(stats_frame_pitch, text="Std Dev: N/A")
            stats_labels_pitch['std'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
            for i in range(4): stats_frame_pitch.grid_columnconfigure(i, weight=1)

            ani1 = FuncAnimation(fig_pitch, atualizar_pitch, interval=50, blit=True, cache_frame_data=False)

        # Frame for Raw graph
        if check_var2.get():
            frame_raw = ctk.CTkFrame(master=janela); frame_raw.pack(fill="both", expand=True, pady=5, padx=10)
            widgets_criados.append(frame_raw) # Add to widgets_criados

            fig_raw = Figure(figsize=(12, 2), dpi=100)
            ax2 = fig_raw.add_subplot(111); ax2.set_title("Raw"); ax2.grid(True)
            canvas_raw = FigureCanvasTkAgg(fig_raw, master=frame_raw)
            canvas_raw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
            # Adicionar a barra de ferramentas do Matplotlib para o gráfico Raw
            toolbar_raw = NavigationToolbar2Tk(canvas_raw, frame_raw)
            toolbar_raw.update()
            line2, = ax2.plot([], [], 'g-')

            # NEW: Statistics frame for Raw graph
            stats_frame_raw = ctk.CTkFrame(master=frame_raw, fg_color="gray20")
            stats_frame_raw.pack(fill="x", pady=(5,0), padx=10)
            widgets_criados.append(stats_frame_raw)

            stats_labels_raw['min'] = ctk.CTkLabel(stats_frame_raw, text="Min: N/A")
            stats_labels_raw['min'].grid(row=0, column=0, padx=5, pady=2, sticky="w")
            stats_labels_raw['max'] = ctk.CTkLabel(stats_frame_raw, text="Max: N/A")
            stats_labels_raw['max'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
            stats_labels_raw['mean'] = ctk.CTkLabel(stats_frame_raw, text="Mean: N/A")
            stats_labels_raw['mean'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
            stats_labels_raw['std'] = ctk.CTkLabel(stats_frame_raw, text="Std Dev: N/A")
            stats_labels_raw['std'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
            for i in range(4): stats_frame_raw.grid_columnconfigure(i, weight=1)

            ani2 = FuncAnimation(fig_raw, atualizar_raw, interval=50, blit=True, cache_frame_data=False)

        # Frame for Yaw graph
        if check_var3.get():
            frame_yaw = ctk.CTkFrame(master=janela); frame_yaw.pack(fill="both", expand=True, pady=5, padx=10)
            widgets_criados.append(frame_yaw) # Add to widgets_criados

            fig_yaw = Figure(figsize=(12, 2), dpi=100)
            ax3 = fig_yaw.add_subplot(111); ax3.set_title("Yaw"); ax3.grid(True)
            canvas_yaw = FigureCanvasTkAgg(fig_yaw, master=frame_yaw)
            canvas_yaw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
            # Adicionar a barra de ferramentas do Matplotlib para o gráfico Yaw
            toolbar_yaw = NavigationToolbar2Tk(canvas_yaw, frame_yaw)
            toolbar_yaw.update()
            line3, = ax3.plot([], [], 'b-')

            # NEW: Statistics frame for Yaw graph
            stats_frame_yaw = ctk.CTkFrame(master=frame_yaw, fg_color="gray20")
            stats_frame_yaw.pack(fill="x", pady=(5,0), padx=10)
            widgets_criados.append(stats_frame_yaw)

            stats_labels_yaw['min'] = ctk.CTkLabel(stats_frame_yaw, text="Min: N/A")
            stats_labels_yaw['min'].grid(row=0, column=0, padx=5, pady=2, sticky="w")
            stats_labels_yaw['max'] = ctk.CTkLabel(stats_frame_yaw, text="Max: N/A")
            stats_labels_yaw['max'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
            stats_labels_yaw['mean'] = ctk.CTkLabel(stats_frame_yaw, text="Mean: N/A")
            stats_labels_yaw['mean'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
            stats_labels_yaw['std'] = ctk.CTkLabel(stats_frame_yaw, text="Std Dev: N/A")
            stats_labels_yaw['std'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
            for i in range(4): stats_frame_yaw.grid_columnconfigure(i, weight=1)

            ani3 = FuncAnimation(fig_yaw, atualizar_yaw, interval=50, blit=True, cache_frame_data=False)


def atualizar_pitch(i):
    atualizar_dados_para_graficos()
    # Atualiza apenas se existirem dados e o gráfico Pitch estiver selecionado
    if check_var1.get() and line1:
        line1.set_data(x_data, y_data)
        ax.relim()
        ax.autoscale_view()
        canvas_pitch.draw_idle()
        # NEW: Update statistics for Pitch
        if len(y_data) > 0:
            stats_labels_pitch['min'].configure(text=f"Min: {np.min(y_data):.2f}")
            stats_labels_pitch['max'].configure(text=f"Max: {np.max(y_data):.2f}")
            stats_labels_pitch['mean'].configure(text=f"Mean: {np.mean(y_data):.2f}")
            stats_labels_pitch['std'].configure(text=f"Std Dev: {np.std(y_data):.2f}")
        else:
            stats_labels_pitch['min'].configure(text="Min: N/A")
            stats_labels_pitch['max'].configure(text="Max: N/A")
            stats_labels_pitch['mean'].configure(text="Mean: N/A")
            stats_labels_pitch['std'].configure(text="Std Dev: N/A")
        return line1,
    return []

def atualizar_raw(i):
    atualizar_dados_para_graficos()
    # Atualiza apenas se existirem dados e o gráfico Raw estiver selecionado
    if check_var2.get() and line2:
        line2.set_data(x_data2, y_data2)
        ax2.relim()
        ax2.autoscale_view()
        canvas_raw.draw_idle()
        # NEW: Update statistics for Raw
        if len(y_data2) > 0:
            stats_labels_raw['min'].configure(text=f"Min: {np.min(y_data2):.2f}")
            stats_labels_raw['max'].configure(text=f"Max: {np.max(y_data2):.2f}")
            stats_labels_raw['mean'].configure(text=f"Mean: {np.mean(y_data2):.2f}")
            stats_labels_raw['std'].configure(text=f"Std Dev: {np.std(y_data2):.2f}")
        else:
            stats_labels_raw['min'].configure(text="Min: N/A")
            stats_labels_raw['max'].configure(text="Max: N/A")
            stats_labels_raw['mean'].configure(text="Mean: N/A")
            stats_labels_raw['std'].configure(text="Std Dev: N/A")
        return line2,
    return []

def atualizar_yaw(i):
    atualizar_dados_para_graficos()
    # Atualiza apenas se existirem dados e o gráfico Yaw estiver selecionado
    if check_var3.get() and line3:
        line3.set_data(x_data3, y_data3)
        ax3.relim()
        ax3.autoscale_view()
        canvas_yaw.draw_idle()
        # NEW: Update statistics for Yaw
        if len(y_data3) > 0:
            stats_labels_yaw['min'].configure(text=f"Min: {np.min(y_data3):.2f}")
            stats_labels_yaw['max'].configure(text=f"Max: {np.max(y_data3):.2f}")
            stats_labels_yaw['mean'].configure(text=f"Mean: {np.mean(y_data3):.2f}")
            stats_labels_yaw['std'].configure(text=f"Std Dev: {np.std(y_data3):.2f}")
        else:
            stats_labels_yaw['min'].configure(text="Min: N/A")
            stats_labels_yaw['max'].configure(text="Max: N/A")
            stats_labels_yaw['mean'].configure(text="Mean: N/A")
            stats_labels_yaw['std'].configure(text="Std Dev: N/A")
        return line3,
    return []

def atualizar_single_linear(i):
    atualizar_dados_para_graficos()
    updated_artists = []
    if check_var1.get() and line_pitch_single:
        line_pitch_single.set_data(x_data, y_data)
        updated_artists.append(line_pitch_single)
    if check_var2.get() and line_raw_single:
        line_raw_single.set_data(x_data2, y_data2)
        updated_artists.append(line_raw_single)
    if check_var3.get() and line_yaw_single:
        line_yaw_single.set_data(x_data3, y_data3)
        updated_artists.append(line_yaw_single)

    # Autoscale only the single axis
    if ax_single_linear:
        ax_single_linear.relim()
        ax_single_linear.autoscale_view()
    canvas_single_linear.draw_idle()

    # NEW: Update statistics for single linear graph
    if len(y_data) > 0:
        stats_labels_combined_linear['pitch_min'].configure(text=f"Min: {np.min(y_data):.2f}")
        stats_labels_combined_linear['pitch_max'].configure(text=f"Max: {np.max(y_data):.2f}")
        stats_labels_combined_linear['pitch_mean'].configure(text=f"Mean: {np.mean(y_data):.2f}")
        stats_labels_combined_linear['pitch_std'].configure(text=f"Std Dev: {np.std(y_data):.2f}")
    else:
        stats_labels_combined_linear['pitch_min'].configure(text="Min: N/A")
        stats_labels_combined_linear['pitch_max'].configure(text="Max: N/A")
        stats_labels_combined_linear['pitch_mean'].configure(text="Mean: N/A")
        stats_labels_combined_linear['pitch_std'].configure(text="Std Dev: N/A")

    if len(y_data2) > 0:
        stats_labels_combined_linear['raw_min'].configure(text=f"Min: {np.min(y_data2):.2f}")
        stats_labels_combined_linear['raw_max'].configure(text=f"Max: {np.max(y_data2):.2f}")
        stats_labels_combined_linear['raw_mean'].configure(text=f"Mean: {np.mean(y_data2):.2f}")
        stats_labels_combined_linear['raw_std'].configure(text=f"Std Dev: {np.std(y_data2):.2f}")
    else:
        stats_labels_combined_linear['raw_min'].configure(text="Min: N/A")
        stats_labels_combined_linear['raw_max'].configure(text="Max: N/A")
        stats_labels_combined_linear['raw_mean'].configure(text="Mean: N/A")
        stats_labels_combined_linear['raw_std'].configure(text="Std Dev: N/A")

    if len(y_data3) > 0:
        stats_labels_combined_linear['yaw_min'].configure(text=f"Min: {np.min(y_data3):.2f}")
        stats_labels_combined_linear['yaw_max'].configure(text=f"Max: {np.max(y_data3):.2f}")
        stats_labels_combined_linear['yaw_mean'].configure(text=f"Mean: {np.mean(y_data3):.2f}")
        stats_labels_combined_linear['yaw_std'].configure(text=f"Std Dev: {np.std(y_data3):.2f}")
    else:
        stats_labels_combined_linear['yaw_min'].configure(text="Min: N/A")
        stats_labels_combined_linear['yaw_max'].configure(text="Max: N/A")
        stats_labels_combined_linear['yaw_mean'].configure(text="Mean: N/A")
        stats_labels_combined_linear['yaw_std'].configure(text="Std Dev: N/A")
    
    return updated_artists

def GraficosPolares():
    global canvas_polar, widgets_criados, ani_polar, fig_polar
    global ax_polar1, ax_polar2, ax_polar3
    global bar_polar1_patch, bar_polar2_patch, bar_polar3_patch
    global single_graph_mode # NEW
    global fig_single_polar, canvas_single_polar, ax_single_polar, ani_single_polar # NEW: for single polar graph
    global bar_pitch_single, bar_raw_single, bar_yaw_single # NEW: bars for single polar graph
    global stats_labels_pitch, stats_labels_raw, stats_labels_yaw, stats_labels_combined_polar # NEW: stats labels
    global graph_status_label # Added for status update

    janela._current_graph_mode = 'polar'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes() # Garante que animações anteriores são paradas
    limpar_area_principal()

    # Update graph status
    if graph_status_label:
        graph_status_label.configure(text="Status do Gráfico: Ativo")

    bar_width_rad = 0.2

    if single_graph_mode.get(): # NEW: Single polar graph mode
        parent_frame_single_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
        parent_frame_single_polar.pack(fill="both", expand=True, pady=10, padx=10)
        widgets_criados.append(parent_frame_single_polar)

        fig_single_polar = Figure(figsize=(8, 8), dpi=100) # Adjust size for single plot
        ax_single_polar = fig_single_polar.add_subplot(111, projection='polar')
        ax_single_polar.set_title("Polar Combined (Pitch, Raw, Yaw)")
        ax_single_polar.set_theta_direction(1) # Clockwise
        ax_single_polar.set_rlim(0, 1) # Define o limite máximo do raio para 1 (representando 100%)
        ax_single_polar.set_rticks([]) # Remove radial ticks for cleaner look

        # Initialize lines for Pitch, Raw, Yaw only if selected
        bar_pitch_single = None
        bar_raw_single = None
        bar_yaw_single = None
        bars_to_plot_in_legend = []

        if check_var1.get():
            bar_pitch_single, = ax_single_polar.plot([0, 0], [0, 1], color='red', linewidth=2, label='Pitch', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_pitch_single)
        if check_var2.get():
            bar_raw_single, = ax_single_polar.plot([0, 0], [0, 1], color='green', linewidth=2, label='Raw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_raw_single)
        if check_var3.get():
            bar_yaw_single, = ax_single_polar.plot([0, 0], [0, 1], color='blue', linewidth=2, label='Yaw', marker='o', markersize=8)
            bars_to_plot_in_legend.append(bar_yaw_single)

        if bars_to_plot_in_legend:
            ax_single_polar.legend(loc='upper right') # Add legend for plotted bars

        canvas_single_polar = FigureCanvasTkAgg(fig_single_polar, master=parent_frame_single_polar)
        canvas_single_polar.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
        toolbar_single_polar = NavigationToolbar2Tk(canvas_single_polar, parent_frame_single_polar)
        toolbar_single_polar.update()

        # NEW: Statistics frame for single polar graph (combined)
        stats_frame_combined_polar = ctk.CTkFrame(master=parent_frame_single_polar, fg_color="gray20")
        stats_frame_combined_polar.pack(fill="x", pady=(5,0), padx=10)
        widgets_criados.append(stats_frame_combined_polar)

        # Labels for Pitch stats
        ctk.CTkLabel(stats_frame_combined_polar, text="Pitch Stats:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['pitch_min'] = ctk.CTkLabel(stats_frame_combined_polar, text="Min: N/A")
        stats_labels_combined_polar['pitch_min'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['pitch_max'] = ctk.CTkLabel(stats_frame_combined_polar, text="Max: N/A")
        stats_labels_combined_polar['pitch_max'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['pitch_mean'] = ctk.CTkLabel(stats_frame_combined_polar, text="Mean: N/A")
        stats_labels_combined_polar['pitch_mean'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['pitch_std'] = ctk.CTkLabel(stats_frame_combined_polar, text="Std Dev: N/A")
        stats_labels_combined_polar['pitch_std'].grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # Labels for Raw stats
        ctk.CTkLabel(stats_frame_combined_polar, text="Raw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['raw_min'] = ctk.CTkLabel(stats_frame_combined_polar, text="Min: N/A")
        stats_labels_combined_polar['raw_min'].grid(row=1, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['raw_max'] = ctk.CTkLabel(stats_frame_combined_polar, text="Max: N/A")
        stats_labels_combined_polar['raw_max'].grid(row=1, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['raw_mean'] = ctk.CTkLabel(stats_frame_combined_polar, text="Mean: N/A")
        stats_labels_combined_polar['raw_mean'].grid(row=1, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['raw_std'] = ctk.CTkLabel(stats_frame_combined_polar, text="Std Dev: N/A")
        stats_labels_combined_polar['raw_std'].grid(row=1, column=4, padx=5, pady=2, sticky="w")

        # Labels for Yaw stats
        ctk.CTkLabel(stats_frame_combined_polar, text="Yaw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['yaw_min'] = ctk.CTkLabel(stats_frame_combined_polar, text="Min: N/A")
        stats_labels_combined_polar['yaw_min'].grid(row=2, column=1, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['yaw_max'] = ctk.CTkLabel(stats_frame_combined_polar, text="Max: N/A")
        stats_labels_combined_polar['yaw_max'].grid(row=2, column=2, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['yaw_mean'] = ctk.CTkLabel(stats_frame_combined_polar, text="Mean: N/A")
        stats_labels_combined_polar['yaw_mean'].grid(row=2, column=3, padx=5, pady=2, sticky="w")
        stats_labels_combined_polar['yaw_std'] = ctk.CTkLabel(stats_frame_combined_polar, text="Std Dev: N/A")
        stats_labels_combined_polar['yaw_std'].grid(row=2, column=4, padx=5, pady=2, sticky="w")

        # Configure columns to expand evenly
        for i in range(5):
            stats_frame_combined_polar.grid_columnconfigure(i, weight=1)

        ani_single_polar = FuncAnimation(fig_single_polar, atualizar_single_polar, interval=50, blit=True, cache_frame_data=False)

    else: # Multiple polar graphs mode
        num_active_polar_graphs = check_var1.get() + check_var2.get() + check_var3.get()
        if num_active_polar_graphs == 0:
            return # Don't create figure if no graphs selected

        fig_polar = Figure(figsize=(12, 4 if num_active_polar_graphs > 1 else 6), dpi=100)
        canvas_polar = FigureCanvasTkAgg(fig_polar, master=janela)
        canvas_polar.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True, pady=10, padx=10)
        widgets_criados.append(canvas_polar.get_tk_widget())

        toolbar_polar = NavigationToolbar2Tk(canvas_polar, janela)
        toolbar_polar.update()
        widgets_criados.append(toolbar_polar.winfo_parent()) # Add toolbar frame to be cleared

        # Create a frame to hold the statistics labels horizontally
        parent_frame_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
        parent_frame_polar.pack(fill="x", pady=0, padx=10) # No vertical padding here, adjust as needed
        widgets_criados.append(parent_frame_polar)

        current_subplot = 1
        if check_var1.get():
            ax_polar1 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar1.set_title("Polar Pitch"); ax_polar1.set_theta_direction(1)
            ax_polar1.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar1.set_rticks([]) # Remove radial ticks
            bar_polar1_patch = ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
            current_subplot += 1

            # NEW: Statistics frame for Pitch polar graph
            stats_frame_pitch_polar = ctk.CTkFrame(master=parent_frame_polar, fg_color="gray20", width=fig_polar.get_size_inches()[0] * fig_polar.dpi / num_active_polar_graphs)
            stats_frame_pitch_polar.pack(side="left", fill="x", pady=(5,0), padx=5, expand=True)
            widgets_criados.append(stats_frame_pitch_polar)

            stats_labels_pitch['min'] = ctk.CTkLabel(stats_frame_pitch_polar, text="Min: N/A")
            stats_labels_pitch['min'].grid(row=0, column=0, padx=2, pady=1, sticky="w")
            stats_labels_pitch['max'] = ctk.CTkLabel(stats_frame_pitch_polar, text="Max: N/A")
            stats_labels_pitch['max'].grid(row=0, column=1, padx=2, pady=1, sticky="w")
            stats_labels_pitch['mean'] = ctk.CTkLabel(stats_frame_pitch_polar, text="Mean: N/A")
            stats_labels_pitch['mean'].grid(row=1, column=0, padx=2, pady=1, sticky="w")
            stats_labels_pitch['std'] = ctk.CTkLabel(stats_frame_pitch_polar, text="Std Dev: N/A")
            stats_labels_pitch['std'].grid(row=1, column=1, padx=2, pady=1, sticky="w")
            for i in range(2): stats_frame_pitch_polar.grid_columnconfigure(i, weight=1)


        if check_var2.get():
            ax_polar2 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar2.set_title("Polar Raw"); ax_polar2.set_theta_direction(1)
            ax_polar2.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar2.set_rticks([])
            bar_polar2_patch = ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
            current_subplot += 1

            # NEW: Statistics frame for Raw polar graph
            stats_frame_raw_polar = ctk.CTkFrame(master=parent_frame_polar, fg_color="gray20", width=fig_polar.get_size_inches()[0] * fig_polar.dpi / num_active_polar_graphs)
            stats_frame_raw_polar.pack(side="left", fill="x", pady=(5,0), padx=5, expand=True)
            widgets_criados.append(stats_frame_raw_polar)

            stats_labels_raw['min'] = ctk.CTkLabel(stats_frame_raw_polar, text="Min: N/A")
            stats_labels_raw['min'].grid(row=0, column=0, padx=2, pady=1, sticky="w")
            stats_labels_raw['max'] = ctk.CTkLabel(stats_frame_raw_polar, text="Max: N/A")
            stats_labels_raw['max'].grid(row=0, column=1, padx=2, pady=1, sticky="w")
            stats_labels_raw['mean'] = ctk.CTkLabel(stats_frame_raw_polar, text="Mean: N/A")
            stats_labels_raw['mean'].grid(row=1, column=0, padx=2, pady=1, sticky="w")
            stats_labels_raw['std'] = ctk.CTkLabel(stats_frame_raw_polar, text="Std Dev: N/A")
            stats_labels_raw['std'].grid(row=1, column=1, padx=2, pady=1, sticky="w")
            for i in range(2): stats_frame_raw_polar.grid_columnconfigure(i, weight=1)

        if check_var3.get():
            ax_polar3 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar3.set_title("Polar Yaw"); ax_polar3.set_theta_direction(1)
            ax_polar3.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar3.set_rticks([])
            bar_polar3_patch = ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]

            # NEW: Statistics frame for Yaw polar graph
            stats_frame_yaw_polar = ctk.CTkFrame(master=parent_frame_polar, fg_color="gray20", width=fig_polar.get_size_inches()[0] * fig_polar.dpi / num_active_polar_graphs)
            stats_frame_yaw_polar.pack(side="left", fill="x", pady=(5,0), padx=5, expand=True)
            widgets_criados.append(stats_frame_yaw_polar)

            stats_labels_yaw['min'] = ctk.CTkLabel(stats_frame_yaw_polar, text="Min: N/A")
            stats_labels_yaw['min'].grid(row=0, column=0, padx=2, pady=1, sticky="w")
            stats_labels_yaw['max'] = ctk.CTkLabel(stats_frame_yaw_polar, text="Max: N/A")
            stats_labels_yaw['max'].grid(row=0, column=1, padx=2, pady=1, sticky="w")
            stats_labels_yaw['mean'] = ctk.CTkLabel(stats_frame_yaw_polar, text="Mean: N/A")
            stats_labels_yaw['mean'].grid(row=1, column=0, padx=2, pady=1, sticky="w")
            stats_labels_yaw['std'] = ctk.CTkLabel(stats_frame_yaw_polar, text="Std Dev: N/A")
            stats_labels_yaw['std'].grid(row=1, column=1, padx=2, pady=1, sticky="w")
            for i in range(2): stats_frame_yaw_polar.grid_columnconfigure(i, weight=1)

        ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, blit=True, cache_frame_data=False)
        canvas_polar.draw_idle()


def atualizar_single_polar(i):
    atualizar_dados_para_graficos()
    updated_artists = []

    # Only update if data exists and the corresponding bar was created
    if len(y_data) > 0:
        if check_var1.get() and bar_pitch_single:
            pitch_rad = math.radians(y_data[-1])
            bar_pitch_single.set_data([0, pitch_rad], [0, 1]) # Angle, Radius
            updated_artists.append(bar_pitch_single)
        # NEW: Update statistics for Pitch
        stats_labels_combined_polar['pitch_min'].configure(text=f"Min: {np.min(y_data):.2f}")
        stats_labels_combined_polar['pitch_max'].configure(text=f"Max: {np.max(y_data):.2f}")
        stats_labels_combined_polar['pitch_mean'].configure(text=f"Mean: {np.mean(y_data):.2f}")
        stats_labels_combined_polar['pitch_std'].configure(text=f"Std Dev: {np.std(y_data):.2f}")
    else:
        stats_labels_combined_polar['pitch_min'].configure(text="Min: N/A")
        stats_labels_combined_polar['pitch_max'].configure(text="Max: N/A")
        stats_labels_combined_polar['pitch_mean'].configure(text="Mean: N/A")
        stats_labels_combined_polar['pitch_std'].configure(text="Std Dev: N/A")

    if len(y_data2) > 0:
        if check_var2.get() and bar_raw_single:
            raw_rad = math.radians(y_data2[-1])
            bar_raw_single.set_data([0, raw_rad], [0, 1])
            updated_artists.append(bar_raw_single)
        # NEW: Update statistics for Raw
        stats_labels_combined_polar['raw_min'].configure(text=f"Min: {np.min(y_data2):.2f}")
        stats_labels_combined_polar['raw_max'].configure(text=f"Max: {np.max(y_data2):.2f}")
        stats_labels_combined_polar['raw_mean'].configure(text=f"Mean: {np.mean(y_data2):.2f}")
        stats_labels_combined_polar['raw_std'].configure(text=f"Std Dev: {np.std(y_data2):.2f}")
    else:
        stats_labels_combined_polar['raw_min'].configure(text="Min: N/A")
        stats_labels_combined_polar['raw_max'].configure(text="Max: N/A")
        stats_labels_combined_polar['raw_mean'].configure(text="Mean: N/A")
        stats_labels_combined_polar['raw_std'].configure(text="Std Dev: N/A")

    if len(y_data3) > 0:
        if check_var3.get() and bar_yaw_single:
            yaw_rad = math.radians(y_data3[-1])
            bar_yaw_single.set_data([0, yaw_rad], [0, 1])
            updated_artists.append(bar_yaw_single)
        # NEW: Update statistics for Yaw
        stats_labels_combined_polar['yaw_min'].configure(text=f"Min: {np.min(y_data3):.2f}")
        stats_labels_combined_polar['yaw_max'].configure(text=f"Max: {np.max(y_data3):.2f}")
        stats_labels_combined_polar['yaw_mean'].configure(text=f"Mean: {np.mean(y_data3):.2f}")
        stats_labels_combined_polar['yaw_std'].configure(text=f"Std Dev: {np.std(y_data3):.2f}")
    else:
        stats_labels_combined_polar['yaw_min'].configure(text="Min: N/A")
        stats_labels_combined_polar['yaw_max'].configure(text="Max: N/A")
        stats_labels_combined_polar['yaw_mean'].configure(text="Mean: N/A")
        stats_labels_combined_polar['yaw_std'].configure(text="Std Dev: N/A")

    canvas_single_polar.draw_idle()
    return updated_artists

def atualizar_polares(i):
    atualizar_dados_para_graficos()
    updated_artists = []
    # Atualizar Pitch
    if check_var1.get() and bar_polar1_patch and len(y_data) > 0:
        # Mapear o valor de pitch para um ângulo de 0 a 2*PI (0-360 graus)
        pitch_angle_rad = math.radians(y_data[-1])
        # A "altura" da barra pode ser fixa (ex: 1 para representar o vetor)
        bar_polar1_patch.set_x(pitch_angle_rad - bar_polar1_patch.get_width()/2)
        # O Matplotlib bar no proj='polar' desenha uma fatia. Para um vetor, usamos plot.
        # Vamos mudar para plot para desenhar uma linha no ângulo.
        # Se você realmente quer uma "barra" (fatia), o código original está ok,
        # mas para um "vetor de ângulo", `plot` é mais direto.
        # Para manter a lógica de "barra" mas atualizar como um vetor:
        # Apenas a posição angular (theta) muda, o raio (r) é fixo se for um indicador.
        # Se for para mostrar o *valor* no raio, precisa de mais tratamento.
        # Assumindo que o `bar_polar1_patch` desenha um vetor que aponta para o ângulo.
        # Neste caso, a 'height' da barra seria o 'r' e 'x' seria o theta.

        # Para representar como um ponteiro/vetor:
        if hasattr(ax_polar1, 'line_pointer'): # Check if the line pointer already exists
            ax_polar1.line_pointer.set_data([0, pitch_angle_rad], [0, 1]) # Update angle
        else:
            ax_polar1.line_pointer, = ax_polar1.plot([0, pitch_angle_rad], [0, 1], color='red', linewidth=2, marker='o', markersize=8)
        updated_artists.append(ax_polar1.line_pointer)
        # NEW: Update statistics for Pitch
        stats_labels_pitch['min'].configure(text=f"Min: {np.min(y_data):.2f}")
        stats_labels_pitch['max'].configure(text=f"Max: {np.max(y_data):.2f}")
        stats_labels_pitch['mean'].configure(text=f"Mean: {np.mean(y_data):.2f}")
        stats_labels_pitch['std'].configure(text=f"Std Dev: {np.std(y_data):.2f}")
    elif check_var1.get(): # If selected but no data
        stats_labels_pitch['min'].configure(text="Min: N/A")
        stats_labels_pitch['max'].configure(text="Max: N/A")
        stats_labels_pitch['mean'].configure(text="Mean: N/A")
        stats_labels_pitch['std'].configure(text="Std Dev: N/A")

    # Atualizar Raw
    if check_var2.get() and bar_polar2_patch and len(y_data2) > 0:
        raw_angle_rad = math.radians(y_data2[-1])
        if hasattr(ax_polar2, 'line_pointer'):
            ax_polar2.line_pointer.set_data([0, raw_angle_rad], [0, 1])
        else:
            ax_polar2.line_pointer, = ax_polar2.plot([0, raw_angle_rad], [0, 1], color='green', linewidth=2, marker='o', markersize=8)
        updated_artists.append(ax_polar2.line_pointer)
        # NEW: Update statistics for Raw
        stats_labels_raw['min'].configure(text=f"Min: {np.min(y_data2):.2f}")
        stats_labels_raw['max'].configure(text=f"Max: {np.max(y_data2):.2f}")
        stats_labels_raw['mean'].configure(text=f"Mean: {np.mean(y_data2):.2f}")
        stats_labels_raw['std'].configure(text=f"Std Dev: {np.std(y_data2):.2f}")
    elif check_var2.get():
        stats_labels_raw['min'].configure(text="Min: N/A")
        stats_labels_raw['max'].configure(text="Max: N/A")
        stats_labels_raw['mean'].configure(text="Mean: N/A")
        stats_labels_raw['std'].configure(text="Std Dev: N/A")


    # Atualizar Yaw
    if check_var3.get() and bar_polar3_patch and len(y_data3) > 0:
        yaw_angle_rad = math.radians(y_data3[-1])
        if hasattr(ax_polar3, 'line_pointer'):
            ax_polar3.line_pointer.set_data([0, yaw_angle_rad], [0, 1])
        else:
            ax_polar3.line_pointer, = ax_polar3.plot([0, yaw_angle_rad], [0, 1], color='blue', linewidth=2, marker='o', markersize=8)
        updated_artists.append(ax_polar3.line_pointer)
        # NEW: Update statistics for Yaw
        stats_labels_yaw['min'].configure(text=f"Min: {np.min(y_data3):.2f}")
        stats_labels_yaw['max'].configure(text=f"Max: {np.max(y_data3):.2f}")
        stats_labels_yaw['mean'].configure(text=f"Mean: {np.mean(y_data3):.2f}")
        stats_labels_yaw['std'].configure(text=f"Std Dev: {np.std(y_data3):.2f}")
    elif check_var3.get():
        stats_labels_yaw['min'].configure(text="Min: N/A")
        stats_labels_yaw['max'].configure(text="Max: N/A")
        stats_labels_yaw['mean'].configure(text="Mean: N/A")
        stats_labels_yaw['std'].configure(text="Std Dev: N/A")

    return updated_artists

def Graficos3D():
    global canvas_3d, widgets_criados, ani_3d, fig_3d, ax_3d
    global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
    global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
    global pitch_opposite_line, raw_opposite_line, yaw_opposite_line # NEW
    global pitch_opposite_point, raw_opposite_point, yaw_opposite_point # NEW
    global y_data, y_data2, y_data3 # Pitch, Raw, Yaw
    global stats_labels_3d # NEW
    global graph_status_label # Added for status update

    janela._current_graph_mode = '3d'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes() # Stop previous animations
    limpar_area_principal()

    # Update graph status
    if graph_status_label:
        graph_status_label.configure(text="Status do Gráfico: Ativo")

    frame_3d_container = ctk.CTkFrame(master=janela)
    frame_3d_container.pack(fill="both", expand=True, pady=10, padx=10)
    widgets_criados.append(frame_3d_container)

    fig_3d = Figure(figsize=(10, 8), dpi=100)
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    ax_3d.set_xlabel('X')
    ax_3d.set_ylabel('Y')
    ax_3d.set_zlabel('Z')
    ax_3d.set_title("Orientação 3D (Pitch, Raw, Yaw)")

    # Desenha círculos fixos para indicar os planos de rotação
    R_circle = 100 # Raio de referência para os círculos
    theta_circle = np.linspace(0, 2 * np.pi, 100)

    # Círculo para Pitch (rotação em torno do eixo X, no plano YZ)
    ax_3d.plot(np.zeros_like(theta_circle), R_circle * np.cos(theta_circle), R_circle * np.sin(theta_circle), 'r--', alpha=0.5, label='Pitch Plane')
    # Círculo para Raw (rotação em torno do eixo Y, no plano XZ)
    ax_3d.plot(R_circle * np.cos(theta_circle), np.zeros_like(theta_circle), R_circle * np.sin(theta_circle), 'g--', alpha=0.5, label='Raw Plane')
    # Círculo para Yaw (rotação em torno do eixo Z, no plano XY)
    ax_3d.plot(R_circle * np.cos(theta_circle), R_circle * np.sin(theta_circle), np.zeros_like(theta_circle), 'b--', alpha=0.5, label='Yaw Plane')

    # Configura os limites dos eixos para centralizar a esfera de referência
    ax_3d.set_xlim([-R_circle, R_circle])
    ax_3d.set_ylim([-R_circle, R_circle])
    ax_3d.set_zlim([-R_circle, R_circle])

    # Inicializa os indicadores de ponto e linha para cada ângulo
    # Pitch indicators (red, rotation around X, point in YZ plane)
    pitch_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r-', linewidth=2)
    pitch_indicator_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=8)
    pitch_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r:', linewidth=1, alpha=0.7) # Dotted line for opposite
    pitch_opposite_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=4, alpha=0.7) # Smaller dot for opposite

    # Raw indicators (green, rotation around Y, point in XZ plane)
    raw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g-', linewidth=2)
    raw_indicator_point, = ax_3d.plot([0], [0], [0], 'go', markersize=8)
    raw_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g:', linewidth=1, alpha=0.7)
    raw_opposite_point, = ax_3d.plot([0], [0], [0], 'go', markersize=4, alpha=0.7)

    # Yaw indicators (blue, rotation around Z, point in XY plane)
    yaw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b-', linewidth=2)
    yaw_indicator_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=8)
    yaw_opposite_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b:', linewidth=1, alpha=0.7)
    yaw_opposite_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=4, alpha=0.7)

    canvas_3d = FigureCanvasTkAgg(fig_3d, master=frame_3d_container)
    canvas_3d.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
    toolbar_3d = NavigationToolbar2Tk(canvas_3d, frame_3d_container)
    toolbar_3d.update()

    # NEW: Statistics frame for 3D graph
    stats_frame_3d = ctk.CTkFrame(master=frame_3d_container, fg_color="gray20")
    stats_frame_3d.pack(fill="x", pady=(5,0), padx=10)
    widgets_criados.append(stats_frame_3d)

    # Labels for Pitch stats
    ctk.CTkLabel(stats_frame_3d, text="Pitch Stats:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
    stats_labels_3d['pitch_min'] = ctk.CTkLabel(stats_frame_3d, text="Min: N/A")
    stats_labels_3d['pitch_min'].grid(row=0, column=1, padx=5, pady=2, sticky="w")
    stats_labels_3d['pitch_max'] = ctk.CTkLabel(stats_frame_3d, text="Max: N/A")
    stats_labels_3d['pitch_max'].grid(row=0, column=2, padx=5, pady=2, sticky="w")
    stats_labels_3d['pitch_mean'] = ctk.CTkLabel(stats_frame_3d, text="Mean: N/A")
    stats_labels_3d['pitch_mean'].grid(row=0, column=3, padx=5, pady=2, sticky="w")
    stats_labels_3d['pitch_std'] = ctk.CTkLabel(stats_frame_3d, text="Std Dev: N/A")
    stats_labels_3d['pitch_std'].grid(row=0, column=4, padx=5, pady=2, sticky="w")

    # Labels for Raw stats
    ctk.CTkLabel(stats_frame_3d, text="Raw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
    stats_labels_3d['raw_min'] = ctk.CTkLabel(stats_frame_3d, text="Min: N/A")
    stats_labels_3d['raw_min'].grid(row=1, column=1, padx=5, pady=2, sticky="w")
    stats_labels_3d['raw_max'] = ctk.CTkLabel(stats_frame_3d, text="Max: N/A")
    stats_labels_3d['raw_max'].grid(row=1, column=2, padx=5, pady=2, sticky="w")
    stats_labels_3d['raw_mean'] = ctk.CTkLabel(stats_frame_3d, text="Mean: N/A")
    stats_labels_3d['raw_mean'].grid(row=1, column=3, padx=5, pady=2, sticky="w")
    stats_labels_3d['raw_std'] = ctk.CTkLabel(stats_frame_3d, text="Std Dev: N/A")
    stats_labels_3d['raw_std'].grid(row=1, column=4, padx=5, pady=2, sticky="w")

    # Labels for Yaw stats
    ctk.CTkLabel(stats_frame_3d, text="Yaw Stats:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=5, pady=2, sticky="w")
    stats_labels_3d['yaw_min'] = ctk.CTkLabel(stats_frame_3d, text="Min: N/A")
    stats_labels_3d['yaw_min'].grid(row=2, column=1, padx=5, pady=2, sticky="w")
    stats_labels_3d['yaw_max'] = ctk.CTkLabel(stats_frame_3d, text="Max: N/A")
    stats_labels_3d['yaw_max'].grid(row=2, column=2, padx=5, pady=2, sticky="w")
    stats_labels_3d['yaw_mean'] = ctk.CTkLabel(stats_frame_3d, text="Mean: N/A")
    stats_labels_3d['yaw_mean'].grid(row=2, column=3, padx=5, pady=2, sticky="w")
    stats_labels_3d['yaw_std'] = ctk.CTkLabel(stats_frame_3d, text="Std Dev: N/A")
    stats_labels_3d['yaw_std'].grid(row=2, column=4, padx=5, pady=2, sticky="w")
    
    # Configure columns to expand evenly
    for i in range(5):
        stats_frame_3d.grid_columnconfigure(i, weight=1)

    ani_3d = FuncAnimation(fig_3d, atualizar_3d, interval=50, blit=True, cache_frame_data=False)
    canvas_3d.draw_idle()


def atualizar_3d(i):
    atualizar_dados_para_graficos()
    updated_artists = []

    if len(y_data) == 0: # If no data, return empty list to FuncAnimation
        # Optionally update stats to N/A if no data
        for key in stats_labels_3d:
            stats_labels_3d[key].configure(text=f"{key.split('_')[-1].capitalize()}: N/A")
        return updated_artists

    # Obter os últimos valores de Pitch, Raw, Yaw
    pitch_val = y_data[-1] if len(y_data) > 0 else 0
    raw_val = y_data2[-1] if len(y_data2) > 0 else 0
    yaw_val = y_data3[-1] if len(y_data3) > 0 else 0

    R_circle = 100 # Raio da esfera de referência

    # Atualiza indicador de Pitch (rotação em torno do eixo X, ponto no plano YZ)
    P_rad = math.radians(pitch_val)
    P_opposite_rad = math.radians((pitch_val + 180) % 360) # Opposite angle
    current_P_y = R_circle * math.cos(P_rad)
    current_P_z = R_circle * math.sin(P_rad)
    pitch_indicator_line.set_data_3d([0, 0], [0, current_P_y], [0, current_P_z])
    pitch_indicator_point.set_data_3d([0], [current_P_y], [current_P_z])
    updated_artists.extend([pitch_indicator_line, pitch_indicator_point])

    # Pitch opposite indicator
    opposite_P_y = R_circle * math.cos(P_opposite_rad)
    opposite_P_z = R_circle * math.sin(P_opposite_rad)
    pitch_opposite_line.set_data_3d([0, 0], [0, opposite_P_y], [0, opposite_P_z])
    pitch_opposite_point.set_data_3d([0], [opposite_P_y], [opposite_P_z])
    updated_artists.extend([pitch_opposite_line, pitch_opposite_point])


    # Atualiza indicador de Raw (rotação em torno do eixo Y, ponto no plano XZ)
    # Y-coordinate is 0 for Raw rotation around Y
    Ra_rad = math.radians(raw_val)
    Ra_opposite_rad = math.radians((raw_val + 180) % 360)
    current_Ra_x = R_circle * math.cos(Ra_rad)
    current_Ra_z = R_circle * math.sin(Ra_rad)
    raw_indicator_line.set_data_3d([0, current_Ra_x], [0, 0], [0, current_Ra_z])
    raw_indicator_point.set_data_3d([current_Ra_x], [0], [current_Ra_z])
    updated_artists.extend([raw_indicator_line, raw_indicator_point])

    # Raw opposite indicator
    opposite_Ra_x = R_circle * math.cos(Ra_opposite_rad)
    opposite_Ra_z = R_circle * math.sin(Ra_opposite_rad)
    raw_opposite_line.set_data_3d([0, opposite_Ra_x], [0, 0], [0, opposite_Ra_z])
    raw_opposite_point.set_data_3d([opposite_Ra_x], [0], [opposite_Ra_z])
    updated_artists.extend([raw_opposite_line, raw_opposite_point])


    # Atualiza indicador de Yaw (rotação em torno do eixo Z, ponto no plano XY)
    # Z-coordinate is 0 for Yaw rotation around Z
    Ya_rad = math.radians(yaw_val)
    Ya_opposite_rad = math.radians((yaw_val + 180) % 360)
    current_Ya_x = R_circle * math.cos(Ya_rad)
    current_Ya_y = R_circle * math.sin(Ya_rad)
    yaw_indicator_line.set_data_3d([0, current_Ya_x], [0, current_Ya_y], [0, 0])
    yaw_indicator_point.set_data_3d([current_Ya_x], [current_Ya_y], [0])
    updated_artists.extend([yaw_indicator_line, yaw_indicator_point])

    # Yaw opposite indicator
    opposite_Ya_x = R_circle * math.cos(Ya_opposite_rad)
    opposite_Ya_y = R_circle * math.sin(Ya_opposite_rad)
    yaw_opposite_line.set_data_3d([0, opposite_Ya_x], [0, opposite_Ya_y], [0, 0])
    yaw_opposite_point.set_data_3d([opposite_Ya_x], [opposite_Ya_y], [0])
    updated_artists.extend([yaw_opposite_line, yaw_opposite_point])

    # Update statistics for 3D graph
    if len(y_data) > 0:
        stats_labels_3d['pitch_min'].configure(text=f"Min: {np.min(y_data):.2f}")
        stats_labels_3d['pitch_max'].configure(text=f"Max: {np.max(y_data):.2f}")
        stats_labels_3d['pitch_mean'].configure(text=f"Mean: {np.mean(y_data):.2f}")
        stats_labels_3d['pitch_std'].configure(text=f"Std Dev: {np.std(y_data):.2f}")
    else:
        stats_labels_3d['pitch_min'].configure(text="Min: N/A")
        stats_labels_3d['pitch_max'].configure(text="Max: N/A")
        stats_labels_3d['pitch_mean'].configure(text="Mean: N/A")
        stats_labels_3d['pitch_std'].configure(text="Std Dev: N/A")

    if len(y_data2) > 0:
        stats_labels_3d['raw_min'].configure(text=f"Min: {np.min(y_data2):.2f}")
        stats_labels_3d['raw_max'].configure(text=f"Max: {np.max(y_data2):.2f}")
        stats_labels_3d['raw_mean'].configure(text=f"Mean: {np.mean(y_data2):.2f}")
        stats_labels_3d['raw_std'].configure(text=f"Std Dev: {np.std(y_data2):.2f}")
    else:
        stats_labels_3d['raw_min'].configure(text="Min: N/A")
        stats_labels_3d['raw_max'].configure(text="Max: N/A")
        stats_labels_3d['raw_mean'].configure(text="Mean: N/A")
        stats_labels_3d['raw_std'].configure(text="Std Dev: N/A")

    if len(y_data3) > 0:
        stats_labels_3d['yaw_min'].configure(text=f"Min: {np.min(y_data3):.2f}")
        stats_labels_3d['yaw_max'].configure(text=f"Max: {np.max(y_data3):.2f}")
        stats_labels_3d['yaw_mean'].configure(text=f"Mean: {np.mean(y_data3):.2f}")
        stats_labels_3d['yaw_std'].configure(text=f"Std Dev: {np.std(y_data3):.2f}")
    else:
        stats_labels_3d['yaw_min'].configure(text="Min: N/A")
        stats_labels_3d['yaw_max'].configure(text="Max: N/A")
        stats_labels_3d['yaw_mean'].configure(text="Mean: N/A")
        stats_labels_3d['yaw_std'].configure(text="Std Dev: N/A")

    return updated_artists

# Funções de Conexão Serial e Wi-Fi (já existentes, sem alteração)
def conectar_serial():
    global serial_conn, modo_conexao
    porta = com_port_combobox.get()
    baud = int(baud_rate_combobox.get())
    if "Nenhuma porta" in porta:
        texto_status.configure(text="Erro: Nenhuma porta COM válida selecionada.", text_color="orange")
        return
    try:
        if serial_conn and serial_conn.is_open:
            serial_conn.close()
        serial_conn = serial.Serial(porta, baud, timeout=0.01)
        texto_status.configure(text=f"Conectado em {porta} a {baud} Baud.", text_color="lightgreen")
        modo_conexao = 'serial'
    except Exception as e:
        texto_status.configure(text=f"Erro na conexão Serial: {e}", text_color="red")
        modo_conexao = None

def conectar_wifi():
    global client, modo_conexao
    esp_ip = ip_entry.get()
    esp_port = int(port_entry.get())
    try:
        if client:
            client.close()
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1) # Timeout para a conexão
        client.connect((esp_ip, esp_port))
        texto_status_wifi.configure(text=f"Conectado ao ESP32 em {esp_ip}:{esp_port}", text_color="lightgreen")
        modo_conexao = 'wifi'
    except socket.timeout:
        texto_status_wifi.configure(text="Erro: Tempo limite de conexão esgotado.", text_color="red")
        modo_conexao = None
    except Exception as e:
        texto_status_wifi.configure(text=f"Erro na conexão Wi-Fi: {e}", text_color="red")
        modo_conexao = None

def desconectar_serial():
    global serial_conn, modo_conexao
    if serial_conn and serial_conn.is_open:
        serial_conn.close()
        texto_status.configure(text="Desconectado do Serial.", text_color="orange")
    modo_conexao = None

def desconectar_wifi():
    global client, modo_conexao
    if client:
        client.close()
        client = None
        texto_status_wifi.configure(text="Desconectado do Wi-Fi.", text_color="orange")
    modo_conexao = None

def mostrar_view(nome_view):
    global main_title_frame, controles_graficos_frame, graph_status_label
    limpar_area_principal() # Limpa a área principal antes de carregar uma nova view

    # Esconde os controles laterais dos gráficos por padrão
    if controles_graficos_frame and controles_graficos_frame.winfo_exists():
        controles_graficos_frame.pack_forget()

    title_text = ""
    if nome_view == 'tela_inicial':
        title_text = "Bem-vindo ao ADCSense!"
        exibir_tela_inicial()
    elif nome_view == 'conexao':
        title_text = "Configurações de Conexão"
        configurar_conexao()
    elif nome_view == 'graficos':
        title_text = "Gráficos Lineares"
        Graficos() # Mostra o painel de controles para as telas de gráfico
        if controles_graficos_frame and controles_graficos_frame.winfo_exists():
            controles_graficos_frame.pack(side="top", fill="x", pady=10, padx=5, anchor="n")
    elif nome_view == 'polares':
        title_text = "Gráficos Polares"
        GraficosPolares() # Mostra o painel de controles para as telas de gráfico
        if controles_graficos_frame and controles_graficos_frame.winfo_exists():
            controles_graficos_frame.pack(side="top", fill="x", pady=10, padx=5, anchor="n")
    elif nome_view == 'graficos_3d': # New 3D graph view
        title_text = "Gráficos 3D"
        Graficos3D()
        if controles_graficos_frame and controles_graficos_frame.winfo_exists():
            controles_graficos_frame.pack(side="top", fill="x", pady=10, padx=5, anchor="n")
    
    # Cria o frame para a barra de destaque do título
    main_title_frame = ctk.CTkFrame(janela, fg_color="gray20", height=50, corner_radius=0)
    main_title_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
    # Adiciona o título ao frame
    ctk.CTkLabel(main_title_frame, text=title_text, font=ctk.CTkFont(size=20, weight="bold")).pack(expand=True)

    # Re-pack the graph_status_label if it exists and is for a graph view
    if nome_view in ['graficos', 'polares', 'graficos_3d']:
        if graph_status_label:
            graph_status_label.pack_forget() # Ensure it's not packed elsewhere first
        graph_status_label = ctk.CTkLabel(main_title_frame, text="Status do Gráfico: Inativo", font=ctk.CTkFont(size=12, slant="italic"))
        graph_status_label.pack(pady=(0, 5))
        # Initial status will be set to 'Ativo' by the Graficos/Polares/3D functions themselves


def exibir_tela_inicial():
    # Placeholder para a tela inicial
    label = ctk.CTkLabel(janela, text="Selecione uma opção no menu lateral.")
    label.pack(pady=20)
    widgets_criados.append(label)

def configurar_conexao():
    global com_port_combobox, baud_rate_combobox, texto_status, ip_entry, port_entry, texto_status_wifi

    frame_central = ctk.CTkFrame(janela)
    frame_central.pack(pady=20, padx=20, fill="both", expand=True)
    widgets_criados.append(frame_central)

    # --- Configurações de Conexão Serial ---
    ctk.CTkLabel(frame_central, text="Conexão Serial", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

    ctk.CTkLabel(frame_central, text="Porta COM:").pack(pady=(10, 0))
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        ports = ["Nenhuma porta COM encontrada"]
    com_port_combobox = ctk.CTkComboBox(frame_central, values=ports)
    com_port_combobox.set(ports[0])
    com_port_combobox.pack(pady=5)

    ctk.CTkLabel(frame_central, text="Baud Rate:").pack(pady=(10, 0))
    baud_rates = ["9600", "19200", "38400", "57600", "115200"]
    baud_rate_combobox = ctk.CTkComboBox(frame_central, values=baud_rates)
    baud_rate_combobox.set("115200")
    baud_rate_combobox.pack(pady=5)

    botao_conectar_serial = ctk.CTkButton(frame_central, text="Conectar Serial", command=conectar_serial)
    botao_conectar_serial.pack(pady=10)
    
    botao_desconectar_serial = ctk.CTkButton(frame_central, text="Desconectar Serial", command=desconectar_serial)
    botao_desconectar_serial.pack(pady=5)

    texto_status = ctk.CTkLabel(frame_central, text="Status: Desconectado", text_color="orange")
    texto_status.pack(pady=5)

    # Separador visual
    ctk.CTkFrame(frame_central, height=2, fg_color="gray30").pack(fill="x", pady=20)

    # --- Configurações de Conexão Wi-Fi (para ESP32) ---
    ctk.CTkLabel(frame_central, text="Conexão Wi-Fi (ESP32)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

    ctk.CTkLabel(frame_central, text="Endereço IP do ESP32:").pack(pady=(10, 0))
    ip_entry = ctk.CTkEntry(frame_central, width=200, placeholder_text="Ex: 192.168.0.112")
    ip_entry.insert(0, "192.168.0.112") # Valor padrão
    ip_entry.pack(pady=5)

    ctk.CTkLabel(frame_central, text="Porta:").pack(pady=(10, 0))
    port_entry = ctk.CTkEntry(frame_central, width=200, placeholder_text="Ex: 12345")
    port_entry.insert(0, "12345") # Valor padrão
    port_entry.pack(pady=5)

    botao_conectar_wifi = ctk.CTkButton(frame_central, text="Conectar Wi-Fi", command=conectar_wifi)
    botao_conectar_wifi.pack(pady=10)

    botao_desconectar_wifi = ctk.CTkButton(frame_central, text="Desconectar Wi-Fi", command=desconectar_wifi)
    botao_desconectar_wifi.pack(pady=5)

    texto_status_wifi = ctk.CTkLabel(frame_central, text="Status Wi-Fi: Desconectado", text_color="orange")
    texto_status_wifi.pack(pady=5)


def carregar_gif(path, label_widget, root_window):
    global gif_frames, gif_index, gif_label, gif_after_id, gif_path
    if not path:
        print("Caminho do GIF não fornecido.")
        return

    try:
        image = Image.open(path)
        gif_frames = []
        for frame in ImageSequence.Iterator(image):
            gif_frames.append(ctk.CTkImage(light_image=frame, dark_image=frame, size=(300, 300))) # Adapte o tamanho aqui
        
        gif_label = label_widget
        gif_index = 0
        animar_gif(root_window)

    except FileNotFoundError:
        print(f"Erro: GIF não encontrado em {path}")
        # Carregar uma imagem de fallback ou exibir uma mensagem de erro na GUI
        fallback_image = Image.new('RGB', (300, 300), color = 'red')
        gif_label.configure(image=ctk.CTkImage(light_image=fallback_image, dark_image=fallback_image, size=(300,300)))
    except Exception as e:
        print(f"Erro ao carregar GIF: {e}")
        # Lidar com outros erros de carregamento/processamento

def animar_gif(root_window):
    global gif_frames, gif_index, gif_label, gif_after_id
    if gif_label and gif_frames:
        gif_label.configure(image=gif_frames[gif_index])
        gif_index = (gif_index + 1) % len(gif_frames)
        gif_after_id = root_window.after(100, lambda: animar_gif(root_window)) # 100ms de atraso entre os frames

def parar_animacao_gif():
    global gif_after_id
    if gif_after_id:
        janela.after_cancel(gif_after_id)
        gif_after_id = None


def setup_ui():
    global janela, check_var1, check_var2, check_var3, random_data, angular_test_data, single_graph_mode
    global controles_graficos_frame, frame_area_principal, gif_label, gif_path, graph_status_label

    # Configuração inicial da janela
    ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

    janela = ctk.CTk()
    janela.title("ADCSense Interface")
    janela.geometry("1200x800")
    janela.protocol("WM_DELETE_WINDOW", fechar_programa) # Garante que as animações parem ao fechar
    janela.bind('<Escape>', sair_tela_cheia) # Bind ESC key to exit fullscreen
    janela.grid_rowconfigure(0, weight=1)  # Configura a linha principal para expandir
    janela.grid_columnconfigure(1, weight=1) # Configura a coluna do conteúdo principal para expandir

    # Variáveis de controle para os checkboxes
    check_var1 = ctk.BooleanVar(value=True)
    check_var2 = ctk.BooleanVar(value=True)
    check_var3 = ctk.BooleanVar(value=True)
    random_data = ctk.BooleanVar(value=False) # Inicia com dados aleatórios desativados
    angular_test_data = ctk.BooleanVar(value=False) # Inicia com dados angulares desativados
    single_graph_mode = ctk.BooleanVar(value=False) # NEW: Default to multiple graphs


    # Splash Screen
    splash_root = ctk.CTk()
    splash_root.overrideredirect(True) # Remove a barra de título
    splash_root.wm_attributes("-topmost", True) # Mantém a tela de splash no topo
    splash_root._set_appearance_mode('dark') # Define o tema para a splash

    # Dimensões da tela de splash
    splash_width = 600
    splash_height = 550 # Aumentado de 400 para 550
    
    # Centralizar a tela de splash
    screen_width = splash_root.winfo_screenwidth()
    screen_height = splash_root.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash_root.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    # Frame para o conteúdo da splash screen
    splash_frame = ctk.CTkFrame(splash_root, fg_color="gray10", corner_radius=10)
    splash_frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Título do Projeto
    ctk.CTkLabel(splash_frame, text="ADCSense", font=ctk.CTkFont(size=30, weight="bold"), text_color="#1F6AA5").pack(pady=(50, 20))

    # Carregar e exibir o GIF (substitua pelo caminho do seu GIF)
    gif_size = (300, 300) # Tamanho do GIF na splash screen, aumentado de (150, 150)
    
    # Criar um CTkLabel para o GIF
    gif_label = ctk.CTkLabel(splash_frame, text="", bg_color="gray10")
    gif_label.pack(pady=20)
    carregar_gif(gif_path, gif_label, splash_root) # Passa o gif_label e splash_root

    # Mensagem de carregamento
    loading_label = ctk.CTkLabel(splash_frame, text="Carregando interface...", font=ctk.CTkFont(size=14))
    loading_label.pack(pady=(20, 50))

    # Forçar atualização da splash screen
    splash_root.update()

    # Main application setup starts here, after splash screen.

    # Frame principal (contém a barra lateral e a área de conteúdo)
    frame_principal = ctk.CTkFrame(janela, corner_radius=0)
    frame_principal.grid(row=0, column=0, columnspan=2, sticky="nsew") # Ocupa toda a janela
    
    # Grid para o frame_principal
    frame_principal.grid_rowconfigure(1, weight=1) # Linha para a área principal expande
    frame_principal.grid_columnconfigure(1, weight=1) # Coluna para a área principal expande

    # --- Barra Lateral ---
    barra_lateral = ctk.CTkFrame(frame_principal, width=200, corner_radius=0, fg_color=("gray90", "gray10"))
    barra_lateral.grid(row=0, column=0, rowspan=2, sticky="nsew") # Ocupa a altura total

    # Título da barra lateral
    ctk.CTkLabel(barra_lateral, text="ADCSense", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1F6AA5").pack(pady=20, padx=20)

    # Área para os botões de navegação
    frame_botoes_nav = ctk.CTkFrame(barra_lateral, fg_color="transparent")
    frame_botoes_nav.pack(fill="both", expand=True, pady=10)

    def adicionar_botao(parent, imagem_path, texto, comando):
        """Função auxiliar para criar botões com ou sem imagem."""
        if imagem_path:
            try:
                # Carregar imagem e redimensionar para o ícone
                # Use Image.open para PNGs, CTkImage para compatibilidade
                icone_image = Image.open(imagem_path).resize((20, 20), Image.Resampling.LANCZOS)
                icone_ctk = ctk.CTkImage(light_image=icone_image, dark_image=icone_image, size=(20, 20))
                botao = ctk.CTkButton(parent, image=icone_ctk, text=texto, compound="left", command=comando, corner_radius=10, anchor="w")
            except FileNotFoundError:
                print(f"Aviso: Imagem não encontrada em {imagem_path}. Usando botão sem imagem.")
                botao = ctk.CTkButton(parent, text=texto, command=comando, corner_radius=10, anchor="w")
            except Exception as e:
                print(f"Erro ao carregar imagem {imagem_path}: {e}. Usando botão sem imagem.")
                botao = ctk.CTkButton(parent, text=texto, command=comando, corner_radius=10, anchor="w")
        else:
            botao = ctk.CTkButton(parent, text=texto, command=comando, corner_radius=10, anchor="w")
        botao.pack(fill='x', padx=10, pady=5)
        return botao

    # Adicionando botões
    adicionar_botao(frame_botoes_nav, None, "Início", lambda: mostrar_view('tela_inicial')) # Botão Início sem imagem
    # -> VERIFIQUE E AJUSTE ESTES CAMINHOS DE ÍCONES SE ESTIVEREM ERRADOS
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão", lambda: mostrar_view('conexao'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\chart.png', "Gráficos", lambda: mostrar_view('graficos'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Gráficos Polares", lambda: mostrar_view('polares'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\3d_icon.png', "Gráficos 3D", lambda: mostrar_view('graficos_3d')) # New 3D button
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\close.png', "Sair", fechar_programa)

    # --- Área de Conteúdo Principal ---
    frame_area_principal = ctk.CTkScrollableFrame(frame_principal, fg_color="transparent")
    frame_area_principal.grid(row=1, column=1, sticky="nsew", padx=10, pady=10) # Coluna 1, linha 1 (abaixo do título)

    # Define o frame para os controles de gráfico (inicialmente escondido)
    controles_graficos_frame = criar_controles_laterais(frame_area_principal)
    controles_graficos_frame.pack_forget() # Esconde inicialmente

    # Background image (optional)
    try:
        # Load and resize image to fit window
        largura_janela = janela.winfo_width()
        altura_janela = janela.winfo_height()
        imagem_fundo_pil = Image.open(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\fundo.png').resize((largura_janela, altura_janela))
        imagem_fundo = ctk.CTkImage(light_image=imagem_fundo_pil, dark_image=imagem_fundo_pil, size=(largura_janela, altura_janela))
        label_fundo = ctk.CTkLabel(janela, image=imagem_fundo, text=""); label_fundo.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Erro ao carregar imagem de fundo: {e}")

    # Esconde a splash screen e mostra a janela principal após um pequeno atraso
    def hide_splash():
        splash_root.destroy()
        janela.deiconify() # Revela a janela principal

    splash_root.after(3000, hide_splash) # Mostra a splash por 3 segundos

    janela.mainloop()

if __name__ == "__main__":
    janela = None # Inicializa janela como None para evitar NameError em fechar_programa antes de setup_ui
    setup_ui()