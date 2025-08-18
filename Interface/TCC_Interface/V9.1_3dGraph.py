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

# Variáveis para indicadores do gráfico 3D
global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
global pitch_indicator_point, raw_indicator_point, yaw_indicator_point


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
global gif_frames, gif_index, gif_label, gif_after_id
gif_frames = []
gif_index = 0
gif_label = None
gif_after_id = None


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
    global check_var1, check_var2, check_var3, random_data, angular_test_data # Adicionado angular_test_data

    # Frame para os controles
    frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))

    # Título
    label_titulo = ctk.CTkLabel(frame, text="Opções do Gráfico", font=ctk.CTkFont(size=14, weight="bold"))
    label_titulo.pack(pady=(10, 5), padx=10, fill="x")

    # Checkboxes de seleção de gráfico
    check_button1 = ctk.CTkCheckBox(frame, text="Pitch", variable=check_var1, command=update_graph_display)
    check_button1.pack(pady=5, padx=20, anchor="w")

    check_button2 = ctk.CTkCheckBox(frame, text="Raw", variable=check_var2, command=update_graph_display)
    check_button2.pack(pady=5, padx=20, anchor="w")

    check_button3 = ctk.CTkCheckBox(frame, text="Yaw", variable=check_var3, command=update_graph_display)
    check_button3.pack(pady=5, padx=20, anchor="w")

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
    x_data.clear(); y_data.clear()
    x_data2.clear(); y_data2.clear()
    x_data3.clear(); y_data3.clear()
    angular_time_step = 0 # Resetar o contador de tempo para dados angulares

    # Resetar eixos e patches dos gráficos 2D lineares
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

        # Reinicializa os indicadores de ponto/linha
        global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
        global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
        pitch_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r-')
        pitch_indicator_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=8)
        raw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g-')
        raw_indicator_point, = ax_3d.plot([0], [0], [0], 'go', markersize=8)
        yaw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b-')
        yaw_indicator_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=8)


    # Resetar eixos e patches dos gráficos polares
    if bar_polar1_patch: bar_polar1_patch.set_x(0 - bar_polar1_patch.get_width()/2)
    if bar_polar2_patch: bar_polar2_patch.set_x(0 - bar_polar2_patch.get_width()/2)
    if bar_polar3_patch: bar_polar3_patch.set_x(0 - bar_polar3_patch.get_width()/2)

    # Redesenhar os canvases
    if 'canvas_pitch' in globals() and canvas_pitch: canvas_pitch.draw_idle()
    if 'canvas_raw' in globals() and canvas_raw: canvas_raw.draw_idle()
    if 'canvas_yaw' in globals() and canvas_yaw: canvas_yaw.draw_idle()
    if canvas_polar: canvas_polar.draw_idle()
    if 'canvas_3d' in globals() and canvas_3d: canvas_3d.draw_idle()


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
    global ani1, ani2, ani3, ani_polar, ani_3d
    global fig_polar, fig_pitch, fig_raw, fig_yaw, fig_3d
    
    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if ani_3d: ani_3d.event_source.stop(); ani_3d = None # Stop 3D animation

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


def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw, fig_pitch, fig_raw, fig_yaw

    janela._current_graph_mode = 'linear'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes() # Garante que animações anteriores são paradas
    limpar_area_principal()
    
    # Criação condicional dos gráficos (lógica mantida)
    if check_var1.get():
        frame_pitch = ctk.CTkFrame(master=janela); frame_pitch.pack(fill="both", expand=True, pady=5, padx=10)
        fig_pitch = Figure(figsize=(12, 2), dpi=100)
        ax = fig_pitch.add_subplot(111); ax.set_title("Pitch"); ax.grid(True)
        canvas_pitch = FigureCanvasTkAgg(fig_pitch, master=frame_pitch)
        canvas_pitch.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

        # Adicionar a barra de ferramentas do Matplotlib para o gráfico Pitch
        toolbar_pitch = NavigationToolbar2Tk(canvas_pitch, frame_pitch)
        toolbar_pitch.update()
        line1, = ax.plot([], [], 'r-'); widgets_criados.append(frame_pitch)

    if check_var2.get():
        frame_raw = ctk.CTkFrame(master=janela); frame_raw.pack(fill="both", expand=True, pady=5, padx=10)
        fig_raw = Figure(figsize=(12, 2), dpi=100)
        ax2 = fig_raw.add_subplot(111); ax2.set_title("Raw"); ax2.grid(True)
        canvas_raw = FigureCanvasTkAgg(fig_raw, master=frame_raw)
        canvas_raw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

        # Adicionar a barra de ferramentas do Matplotlib para o gráfico Raw
        toolbar_raw = NavigationToolbar2Tk(canvas_raw, frame_raw)
        toolbar_raw.update()
        line2, = ax2.plot([], [], 'g-'); widgets_criados.append(frame_raw)

    if check_var3.get():
        frame_yaw = ctk.CTkFrame(master=janela); frame_yaw.pack(fill="both", expand=True, pady=5, padx=10)
        fig_yaw = Figure(figsize=(12, 2), dpi=100)
        ax3 = fig_yaw.add_subplot(111); ax3.set_title("Yaw"); ax3.grid(True)
        canvas_yaw = FigureCanvasTkAgg(fig_yaw, master=frame_yaw)
        canvas_yaw.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

        # Adicionar a barra de ferramentas do Matplotlib para o gráfico Yaw
        toolbar_yaw = NavigationToolbar2Tk(canvas_yaw, frame_yaw)
        toolbar_yaw.update()
        line3, = ax3.plot([], [], 'b-'); widgets_criados.append(frame_yaw)

    def atualizar_cartesianos(i):
        # AQUI É ONDE SE PREVINE OS ERROS: Verificamos se o eixo ainda existe.
        atualizar_dados_para_graficos() # Atualiza os dados para todos os gráficos
        updated_artists = []
        if check_var1.get() and ax and line1:
            line1.set_data(x_data, y_data)
            ax.relim(); ax.autoscale_view()
            updated_artists.append(line1)
            if canvas_pitch: canvas_pitch.draw_idle() # Desenha apenas se o canvas existe
        if check_var2.get() and ax2 and line2:
            line2.set_data(x_data2, y_data2)
            ax2.relim(); ax2.autoscale_view()
            updated_artists.append(line2)
            if canvas_raw: canvas_raw.draw_idle()
        if check_var3.get() and ax3 and line3:
            line3.set_data(x_data3, y_data3)
            ax3.relim(); ax3.autoscale_view()
            updated_artists.append(line3)
            if canvas_yaw: canvas_yaw.draw_idle()
        return updated_artists

    # As animações só são criadas se o gráfico correspondente for ativado
    if check_var1.get() and fig_pitch:
        ani1 = FuncAnimation(fig_pitch, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
    if check_var2.get() and fig_raw:
        ani2 = FuncAnimation(fig_raw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
    if check_var3.get() and fig_yaw:
        ani3 = FuncAnimation(fig_yaw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)


def GraficosPolares():
    global canvas_polar, widgets_criados, ani_polar, fig_polar, ax_polar1, ax_polar2, ax_polar3
    global bar_polar1_patch, bar_polar2_patch, bar_polar3_patch

    janela._current_graph_mode = 'polar'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes() # Garante que animações anteriores são paradas
    limpar_area_principal()

    num_active_polar_graphs = check_var1.get() + check_var2.get() + check_var3.get()
    if num_active_polar_graphs > 0:
        parent_frame_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
        parent_frame_polar.pack(fill="both", expand=True, pady=10, padx=10)
        widgets_criados.append(parent_frame_polar)

        fig_polar = Figure(figsize=(4 * num_active_polar_graphs, 6), dpi=100)
        current_subplot = 1
        bar_width_rad = 0.2

        if check_var1.get():
            ax_polar1 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar1.set_title("Polar Pitch"); ax_polar1.set_theta_direction(1)
            # Definir limites de r (raio) para o círculo do gráfico polar
            ax_polar1.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar1.set_rticks([]) # Remove os ticks do raio para um visual mais limpo, se desejar
            bar_polar1_patch = ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
            current_subplot += 1
        if check_var2.get():
            ax_polar2 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar2.set_title("Polar Raw"); ax_polar2.set_theta_direction(1)
            ax_polar2.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar2.set_rticks([])
            bar_polar2_patch = ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
            current_subplot += 1
        if check_var3.get():
            ax_polar3 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar3.set_title("Polar Yaw"); ax_polar3.set_theta_direction(1)
            ax_polar3.set_rlim(0, 1) # Define o limite máximo do raio para 1
            ax_polar3.set_rticks([])
            bar_polar3_patch = ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]
            current_subplot += 1

        fig_polar.subplots_adjust(wspace=0.4, hspace=0.4)
        canvas_polar = FigureCanvasTkAgg(fig_polar, master=parent_frame_polar)
        canvas_polar.get_tk_widget().pack(anchor=tk.CENTER, expand=True, fill='both')

        # Adicionar a barra de ferramentas do Matplotlib para os gráficos Polares
        toolbar_polar = NavigationToolbar2Tk(canvas_polar, parent_frame_polar)
        toolbar_polar.update()

        def atualizar_polares(i):
            atualizar_dados_para_graficos() # Atualiza os dados para todos os gráficos
            updated_artists = []
            if check_var1.get() and len(y_data) > 0 and bar_polar1_patch:
                valor1 = (y_data[-1] * 3.14159) / 180
                bar_polar1_patch.set_x(valor1 - bar_width_rad/2) # Atualiza a posição angular
                updated_artists.append(bar_polar1_patch)
            if check_var2.get() and len(y_data2) > 0 and bar_polar2_patch:
                valor2 = (y_data2[-1] * 3.14159) / 180
                bar_polar2_patch.set_x(valor2 - bar_width_rad/2)
                updated_artists.append(bar_polar2_patch)
            if check_var3.get() and len(y_data3) > 0 and bar_polar3_patch:
                valor3 = (y_data3[-1] * 3.14159) / 180
                bar_polar3_patch.set_x(valor3 - bar_width_rad/2)
                updated_artists.append(bar_polar3_patch)
            return updated_artists

        ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, blit=True, cache_frame_data=False)
        canvas_polar.draw_idle()


def Graficos3D():
    global canvas_3d, widgets_criados, ani_3d, fig_3d, ax_3d
    global pitch_indicator_line, raw_indicator_line, yaw_indicator_line
    global pitch_indicator_point, raw_indicator_point, yaw_indicator_point
    global y_data, y_data2, y_data3 # Pitch, Raw, Yaw

    janela._current_graph_mode = '3d'
    # Manter os dados existentes caso o usuário queira ver a última posição
    parar_animacoes()
    limpar_area_principal()

    frame_3d = ctk.CTkFrame(master=janela, fg_color="transparent")
    frame_3d.pack(fill="both", expand=True, pady=10, padx=10)
    widgets_criados.append(frame_3d)

    fig_3d = Figure(figsize=(10, 8), dpi=100)
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    ax_3d.set_xlabel('X') # Eixo X
    ax_3d.set_ylabel('Y') # Eixo Y
    ax_3d.set_zlabel('Z') # Eixo Z
    ax_3d.set_title("Orientação 3D (Pitch, Raw, Yaw)")

    # Define um raio para os círculos de referência
    R_circle = 100 
    # Define os limites fixos dos eixos com base no raio dos círculos
    ax_3d.set_xlim([-R_circle, R_circle])
    ax_3d.set_ylim([-R_circle, R_circle])
    ax_3d.set_zlim([-R_circle, R_circle])

    # Cria pontos para um círculo completo (0 a 2*pi radianos)
    theta_circle = np.linspace(0, 2 * np.pi, 100)

    # Pitch (Rotação em torno do eixo X: Círculo no plano YZ)
    pitch_circle_x = np.zeros_like(theta_circle)
    pitch_circle_y = R_circle * np.cos(theta_circle)
    pitch_circle_z = R_circle * np.sin(theta_circle)
    ax_3d.plot(pitch_circle_x, pitch_circle_y, pitch_circle_z, 'r--', alpha=0.5, label='Pitch Plane (X-axis rotation)')

    # Raw (Rotação em torno do eixo Y: Círculo no plano XZ)
    raw_circle_x = R_circle * np.cos(theta_circle)
    raw_circle_y = np.zeros_like(theta_circle)
    raw_circle_z = R_circle * np.sin(theta_circle)
    ax_3d.plot(raw_circle_x, raw_circle_y, raw_circle_z, 'g--', alpha=0.5, label='Raw Plane (Y-axis rotation)')

    # Yaw (Rotação em torno do eixo Z: Círculo no plano XY)
    yaw_circle_x = R_circle * np.cos(theta_circle)
    yaw_circle_y = R_circle * np.sin(theta_circle)
    yaw_circle_z = np.zeros_like(theta_circle)
    ax_3d.plot(yaw_circle_x, yaw_circle_y, yaw_circle_z, 'b--', alpha=0.5, label='Yaw Plane (Z-axis rotation)')

    # Inicializa os plots para os indicadores de ângulo atuais
    # Linha do centro até o ponto e o próprio ponto
    pitch_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'r-', linewidth=2)
    pitch_indicator_point, = ax_3d.plot([0], [0], [0], 'ro', markersize=8)

    raw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'g-', linewidth=2)
    raw_indicator_point, = ax_3d.plot([0], [0], [0], 'go', markersize=8)

    yaw_indicator_line, = ax_3d.plot([0,0], [0,0], [0,0], 'b-', linewidth=2)
    yaw_indicator_point, = ax_3d.plot([0], [0], [0], 'bo', markersize=8)

    canvas_3d = FigureCanvasTkAgg(fig_3d, master=frame_3d)
    canvas_3d.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)

    toolbar_3d = NavigationToolbar2Tk(canvas_3d, frame_3d)
    toolbar_3d.update()

    def atualizar_3d(i):
        atualizar_dados_para_graficos() # Adquire e atualiza todas as listas de dados
        updated_artists = []

        # Certifica-se de que há dados para plotar
        if len(y_data) > 0 and len(y_data2) > 0 and len(y_data3) > 0:
            current_pitch_deg = y_data[-1]
            current_raw_deg = y_data2[-1]
            current_yaw_deg = y_data3[-1]

            # Converte graus para radianos para as funções trigonométricas
            P_rad = math.radians(current_pitch_deg)
            Ra_rad = math.radians(current_raw_deg)
            Y_rad = math.radians(current_yaw_deg)

            # Atualiza indicador de Pitch (rotação em torno do eixo X, ponto no plano YZ)
            # X-coordinate is 0 for Pitch rotation around X
            current_P_y = R_circle * math.cos(P_rad)
            current_P_z = R_circle * math.sin(P_rad)
            pitch_indicator_line.set_data_3d([0, 0], [0, current_P_y], [0, current_P_z])
            pitch_indicator_point.set_data_3d([0], [current_P_y], [current_P_z])
            updated_artists.extend([pitch_indicator_line, pitch_indicator_point])

            # Atualiza indicador de Raw (rotação em torno do eixo Y, ponto no plano XZ)
            # Y-coordinate is 0 for Raw rotation around Y
            current_Ra_x = R_circle * math.cos(Ra_rad)
            current_Ra_z = R_circle * math.sin(Ra_rad)
            raw_indicator_line.set_data_3d([0, current_Ra_x], [0, 0], [0, current_Ra_z])
            raw_indicator_point.set_data_3d([current_Ra_x], [0], [current_Ra_z])
            updated_artists.extend([raw_indicator_line, raw_indicator_point])

            # Atualiza indicador de Yaw (rotação em torno do eixo Z, ponto no plano XY)
            # Z-coordinate is 0 for Yaw rotation around Z
            current_Y_x = R_circle * math.cos(Y_rad)
            current_Y_y = R_circle * math.sin(Y_rad)
            yaw_indicator_line.set_data_3d([0, current_Y_x], [0, current_Y_y], [0, 0])
            yaw_indicator_point.set_data_3d([current_Y_x], [current_Y_y], [0])
            updated_artists.extend([yaw_indicator_line, yaw_indicator_point])
        
        canvas_3d.draw_idle()
        return updated_artists

    ani_3d = FuncAnimation(fig_3d, atualizar_3d, interval=100, blit=False, cache_frame_data=False)


def Conexao():
    global widgets_criados, serial_conn, client, modo_conexao
    parar_animacoes()
    limpar_area_principal()

    frame_central = ctk.CTkFrame(janela, fg_color="transparent")
    frame_central.place(relx=0.5, rely=0.5, anchor="center")
    widgets_criados.append(frame_central)

    ctk.CTkLabel(frame_central, text="Escolha o método de conexão:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
    texto_status = ctk.CTkLabel(frame_central, text="Status: Desconectado")
    texto_status.pack(pady=10)

    # Controles para conexão Serial
    ctk.CTkLabel(frame_central, text="Selecione a Porta COM:").pack(pady=(10,0))
    com_port_combobox = ctk.CTkComboBox(frame_central, values=listar_portas_com())
    com_port_combobox.pack(pady=5)
    ctk.CTkLabel(frame_central, text="Selecione o Baud Rate:").pack(pady=(10,0))
    baud_rate_combobox = ctk.CTkComboBox(frame_central, values=["9600", "57600", "115200", "921600"])
    baud_rate_combobox.set("115200")
    baud_rate_combobox.pack(pady=5)

    def conectar_serial():
        global serial_conn, modo_conexao
        porta = com_port_combobox.get(); baud = int(baud_rate_combobox.get())
        if "Nenhuma porta" in porta:
            texto_status.configure(text="Erro: Nenhuma porta COM válida selecionada.", text_color="orange")
            return
        try:
            if serial_conn and serial_conn.is_open: serial_conn.close()
            serial_conn = serial.Serial(porta, baud, timeout=0.01)
            texto_status.configure(text=f"Conectado em {porta} a {baud} Baud.", text_color="lightgreen")
            modo_conexao = 'serial'
        except Exception as e:
            texto_status.configure(text=f"Erro na conexão Serial: {e}", text_color="red")
            modo_conexao = None

    ctk.CTkButton(frame_central, text="Conectar via Porta COM", command=conectar_serial).pack(pady=10)

    # --- Campos para IP e Porta do ESP32 (Novidade!) ---
    ctk.CTkLabel(frame_central, text="IP do ESP32:").pack(pady=(10, 0))
    ip_entry = ctk.CTkEntry(frame_central, width=200, placeholder_text="Ex: 192.168.0.112")
    ip_entry.insert(0, "192.168.0.112")  # Valor padrão
    ip_entry.pack(pady=5)

    ctk.CTkLabel(frame_central, text="Porta do ESP32:").pack(pady=(10, 0))
    port_entry = ctk.CTkEntry(frame_central, width=200, placeholder_text="Ex: 12345")
    port_entry.insert(0, "12345")  # Valor padrão
    port_entry.pack(pady=5)

    def conectar_wifi():
        global client, modo_conexao
        esp_ip = ip_entry.get()
        esp_port = int(port_entry.get())
        try:
            if client: client.close()
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((esp_ip, esp_port))
            texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi! IP: {esp_ip}, Porta: {esp_port}", text_color="lightgreen")
            modo_conexao = 'wifi'
        except Exception as e:
            print(f"Erro na conexão Wi-Fi: {e}")
            texto_status.configure(text=f"Erro na conexão Wi-Fi: {e}", text_color="red")
            client = None

    ctk.CTkButton(frame_central, text="Conectar via Wi-Fi", command=conectar_wifi).pack(pady=10)

def TelaInicial():
    """Exibe a tela inicial com uma breve explicação do software."""
    limpar_area_principal() # Garante que a área principal está limpa

    frame_inicial = ctk.CTkFrame(janela, fg_color="transparent")
    frame_inicial.pack(fill="both", expand=True, pady=20, padx=20)
    widgets_criados.append(frame_inicial)

    ctk.CTkLabel(frame_inicial, text="Bem-vindo ao ADCSense", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

    explanation_text = (
        "Este software foi projetado para aquisição e visualização de dados em tempo real.\n\n"
        "Você pode se conectar a dispositivos via Serial (USB) ou Wi-Fi (TCP/IP) para receber informações.\n\n"
        "Os dados adquiridos podem ser exibidos em gráficos lineares (Pitch, Raw, Yaw) ou em representações polares.\n\n"
        "Utilize os controles laterais para selecionar os gráficos desejados, pausar/retomar a aquisição e salvar os dados."
    )
    ctk.CTkLabel(frame_inicial, text=explanation_text, font=ctk.CTkFont(size=14), wraplength=600, justify="center").pack(pady=10)

    # Você pode adicionar um botão para ir para a tela de conexão, por exemplo:
    ctk.CTkButton(frame_inicial, text="Iniciar Conexão", command=lambda: mostrar_view('conexao')).pack(pady=20)


def mostrar_view(nome_view):
    """Gerencia a exibição da tela principal e dos controles laterais, incluindo o título da aba."""
    global controles_graficos_frame, main_title_frame
    
    # Esconde o painel de controles por padrão
    if controles_graficos_frame and controles_graficos_frame.winfo_exists():
        controles_graficos_frame.pack_forget()

    # Destrói o frame do título anterior se existir
    if main_title_frame and main_title_frame.winfo_exists():
        main_title_frame.destroy()

    title_text = ""
    if nome_view == 'tela_inicial':
        title_text = "Início"
        TelaInicial()
    elif nome_view == 'conexao':
        title_text = "Conexão"
        Conexao()
    elif nome_view == 'graficos':
        title_text = "Gráficos Lineares"
        Graficos()
        # Mostra o painel de controles para as telas de gráfico
        if controles_graficos_frame and controles_graficos_frame.winfo_exists():
            controles_graficos_frame.pack(side="top", fill="x", pady=10, padx=5, anchor="n")
    elif nome_view == 'polares':
        title_text = "Gráficos Polares"
        GraficosPolares()
        # Mostra o painel de controles para as telas de gráfico
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
    
    # Cria e empacota o label do título DENTRO do novo frame
    title_label_inside_frame = ctk.CTkLabel(main_title_frame, text=title_text, font=ctk.CTkFont(size=20, weight="bold"))
    title_label_inside_frame.pack(expand=True) # Centraliza o texto dentro do frame

    widgets_criados.append(main_title_frame) # Adiciona o frame do título à lista para ser limpo ao trocar de tela

# --- Funções para Animação de GIF na Splash Screen ---
def load_gif_frames(path, size):
    global gif_frames
    gif_frames.clear()
    try:
        gif = Image.open(path)
        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGBA").resize(size, Image.LANCZOS) # Redimensiona e converte para RGBA
            gif_frames.append(ctk.CTkImage(light_image=frame, dark_image=frame, size=size))
    except Exception as e:
        print(f"Erro ao carregar GIF: {e}")
        gif_frames = [] # Limpa se houver erro

def animate_gif(splash_root):
    global gif_index, gif_label, gif_frames, gif_after_id
    if not gif_frames:
        return

    # Certifica-se de que gif_label existe antes de tentar configurar a imagem
    if gif_label and gif_label.winfo_exists():
        gif_label.configure(image=gif_frames[gif_index])
        gif_index = (gif_index + 1) % len(gif_frames)
        # Calcula o atraso para o próximo frame (se disponível na imagem GIF)
        # Caminho do GIF precisa ser global ou passado como argumento para ser acessado aqui
        # Ajustei o gif_path para ser uma variável global no setup_main_window
        # Para evitar um erro, o ideal é que gif_path seja acessível aqui.
        # Por simplicidade, assumindo que já foi carregado em load_gif_frames.
        delay = Image.open(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Alien.gif').info.get('duration', 100) # Re-abrir para pegar o delay
        gif_after_id = splash_root.after(delay, lambda: animate_gif(splash_root))
    else:
        # Se o label não existe mais, cancela a próxima chamada
        if gif_after_id:
            splash_root.after_cancel(gif_after_id)
            gif_after_id = None


# --- Função da Tela de Splash ---
def show_splash_screen():
    global janela, gif_label # Acessa a janela principal e o caminho do GIF

    splash_root = ctk.CTk()
    splash_root.overrideredirect(True) # Remove barra de título e bordas
    splash_root.attributes("-topmost", True) # Mantém a janela no topo
    splash_root._set_appearance_mode('dark')

    # Dimensões da tela de splash
    splash_width = 600
    splash_height = 400

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
    global gif_path # Tornar gif_path global para animate_gif
    gif_path = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Alien.gif' # <-- Altere para o seu caminho do GIF
    gif_size = (150, 150) # Tamanho do GIF na splash screen

    load_gif_frames(gif_path, gif_size)
    
    if gif_frames:
        gif_label = ctk.CTkLabel(splash_frame, image=gif_frames[0], text="")
        gif_label.pack(pady=10)
        animate_gif(splash_root) # Inicia a animação do GIF
    else:
        # Fallback se o GIF não carregar
        ctk.CTkLabel(splash_frame, text="[GIF/Vídeo Aqui]", font=ctk.CTkFont(size=16)).pack(pady=10)

    ctk.CTkLabel(splash_frame, text="Carregando...", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=20)


    def destroy_splash():
        global gif_after_id
        if gif_after_id:
            splash_root.after_cancel(gif_after_id) # Cancela a animação do GIF antes de destruir
            gif_after_id = None
        splash_root.destroy()
        setup_main_window() # Inicia a janela principal

    # Tempo total que a splash screen fica visível (incluindo a duração do GIF)
    splash_root.after(3000, destroy_splash) # 3000ms = 3 segundos
    splash_root.mainloop()

# --- Configuração da Janela Principal (movida para uma função) ---
def setup_main_window():
    global janela, controles_graficos_frame, random_data, angular_test_data, check_var1, check_var2, check_var3 # Adicionado angular_test_data

    ctk.set_default_color_theme("blue") # Define o tema de cor padrão para azul

    janela = ctk.CTk()
    largura_tela = janela.winfo_screenwidth(); altura_tela = janela.winfo_screenheight()
    largura_janela = int(largura_tela * 0.8); altura_janela = int(altura_tela * 0.8)
    pos_x = int((largura_tela - largura_janela) / 2)
    pos_y = int((altura_tela - altura_janela) / 2)
    janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    janela.title("ADCS_Telemetry")
    janela._set_appearance_mode('dark')

    # Inicialização das variáveis de controle (BooleanVar)
    random_data = ctk.BooleanVar(master=janela)
    angular_test_data = ctk.BooleanVar(master=janela) # NOVO: Variável para dados angulares
    check_var1 = ctk.BooleanVar(master=janela)
    check_var2 = ctk.BooleanVar(master=janela)
    check_var3 = ctk.BooleanVar(master=janela)

    # Imagem de fundo
    try:
        # Use um caminho absoluto ou ajuste para seu ambiente
        caminho_fundo = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\fundo.png'
        imagem_fundo_pil = Image.open(caminho_fundo).resize((largura_janela, altura_janela))
        imagem_fundo = ctk.CTkImage(light_image=imagem_fundo_pil, dark_image=imagem_fundo_pil, size=(largura_janela, altura_janela))
        label_fundo = ctk.CTkLabel(janela, image=imagem_fundo, text=""); label_fundo.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Erro ao carregar imagem de fundo: {e}")

    # Barra Lateral
    barra_lateral = ctk.CTkFrame(janela, width=200, corner_radius=0)
    barra_lateral.pack(side="left", fill="y")

    # Container para os botões de navegação na barra lateral
    frame_botoes_nav = ctk.CTkFrame(barra_lateral, fg_color="transparent")
    frame_botoes_nav.pack(side="top", fill="x", pady=20)

    # Cria o frame de controles do gráfico, que ficará escondido inicialmente
    controles_graficos_frame = criar_controles_laterais(barra_lateral)

    # Função para adicionar botões na barra lateral
    imagens_carregadas = [] # Lista para manter referências de imagens
    def adicionar_botao(parent, caminho_imagem, texto, comando):
        try:
            if caminho_imagem: # Se um caminho de imagem for fornecido
                imagem_pil = Image.open(caminho_imagem)
                imagem = ctk.CTkImage(light_image=imagem_pil, dark_image=imagem_pil, size=(30, 30))
                imagens_carregadas.append(imagem) # Mantém a referência
                botao = ctk.CTkButton(parent, image=imagem, text=texto, command=comando,
                                      fg_color="transparent", hover_color=("#3B5998", "#3E5C8D"), # Cor de hover para botões com imagem
                                      corner_radius=10, anchor="w",
                                      font=ctk.CTkFont(size=13))
            else: # Se não houver caminho de imagem (para o botão "Início")
                botao = ctk.CTkButton(parent, text=texto, command=comando,
                                      corner_radius=10, anchor="w", # Usa o fg_color padrão (azul)
                                      font=ctk.CTkFont(size=13))
            botao.pack(fill='x', padx=10, pady=5)
            return botao # Retorna o botão criado
        except Exception as e:
            print(f"Erro ao carregar ícone {caminho_imagem}: {e}")
            # Adiciona um botão de texto como fallback, também azul
            botao = ctk.CTkButton(parent, text=texto, command=comando, corner_radius=10, anchor="w")
            botao.pack(fill='x', padx=10, pady=5)
            return botao

    # Adicionando botões
    adicionar_botao(frame_botoes_nav, None, "Início", lambda: mostrar_view('tela_inicial')) # Botão Início sem imagem
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão", lambda: mostrar_view('conexao'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\chart.png', "Gráficos", lambda: mostrar_view('graficos'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Gráficos Polares", lambda: mostrar_view('polares'))
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\3d_icon.png', "Gráficos 3D", lambda: mostrar_view('graficos_3d')) # New 3D button
    adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\close.png', "Fechar", fechar_programa)

    janela.bind('<Escape>', lambda event: fechar_programa())

    # Inicia mostrando a tela inicial após a splash screen
    mostrar_view('tela_inicial')

    janela.mainloop()

# Inicia a tela de splash
if __name__ == "__main__":
    show_splash_screen()