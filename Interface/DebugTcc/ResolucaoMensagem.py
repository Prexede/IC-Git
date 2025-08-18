import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
import serial.tools.list_ports
import socket
import customtkinter as ctk
from PIL import Image
import math
import time
import select # Importar o módulo select

###### SERVIDOR
ESP_IP = "192.168.0.110"
ESP_PORT = 12345

# Variáveis globais para os dados dos gráficos
x_data, y_data = [], []
x_data2, y_data2 = [], []
x_data3, y_data3 = [], []

# Nova variável global para os dados de tempo de leitura
time_diff_data = []
last_read_time = None # ESSENCIAL: Inicializar no escopo global

# Variáveis globais para objetos gráficos e de conexão
canvas = None
client = None
ax = None
ax2 = None
ax3 = None
line1 = None
line2 = None
line3 = None

# Variáveis globais para as animações
ani1 = None
ani2 = None
ani3 = None
ani_polar = None
ani_time_diff = None # ESSENCIAL: Inicializar no escopo global

# Variável global para a conexão serial
serial_conn = None

# Variáveis para armazenar os IDs dos agendamentos `after()` para cancelamento
after_id_serial_reader = None # ESSENCIAL: Inicializar no escopo global
after_id_wifi_reader = None    # ESSENCIAL: Inicializar no escopo global
after_id_check_wifi = None     # ESSENCIAL: Inicializar no escopo global
after_id_wifi_connect_timeout = None # ESSENCIAL: Inicializar no escopo global

# Variáveis para frames dos gráficos
frame_pitch = None
frame_raw = None
frame_yaw = None

# Variáveis para componentes da barra superior
barra_superior = None
barra_checklist = None
label_dados = None # ESSENCIAL: Inicializar no escopo global

# Variável para o dropdown de baudrate
dropdown_baudrate = None
baudrate_selecionado_var = None

dados_atuais_imu = [0.0, 0.0, 0.0]

# Variáveis de controle para checkboxes
check_var1 = None
check_var2 = None
check_var3 = None
random_data = None

# Variável global para a entrada da quantidade de dados a salvar (IMU)
entry_num_dados_salvar_imu = None
# Variável global para a entrada da quantidade de dados a salvar (Tempo de Leitura)
entry_num_dados_salvar_tempo = None

# Variável global para o frame principal onde o conteúdo das abas será mostrado
main_content_frame = None

# --- Funções Auxiliares (mantidas as que não foram alteradas) ---

def fechar_programa():
    """Fecha a janela principal da aplicação e encerra as conexões."""
    # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
    global serial_conn, client, after_id_serial_reader, after_id_wifi_reader, after_id_check_wifi, after_id_wifi_connect_timeout
    global ani1, ani2, ani3, ani_polar, ani_time_diff
    global last_read_time # Adicionado aqui pois é modificado/resetado

    # Tenta parar todas as animações
    if ani1 is not None:
        ani1.event_source.stop()
        ani1 = None
    if ani2 is not None:
        ani2.event_source.stop()
        ani2 = None
    if ani3 is not None:
        ani3.event_source.stop()
        ani3 = None
    if ani_polar is not None:
        ani_polar.event_source.stop()
        ani_polar = None
    if ani_time_diff is not None:
        ani_time_diff.event_source.stop()
        ani_time_diff = None

    # Cancela agendamentos de leitura de dados se estiverem ativos
    # O loop abaixo AGORA pode acessar os valores das variáveis globais
    # porque elas foram declaradas global logo no início da função.
    for _id in [after_id_serial_reader, after_id_wifi_reader, after_id_check_wifi, after_id_wifi_connect_timeout]:
        if _id is not None:
            try:
                janela.after_cancel(_id)
            except Exception:
                pass
    
    # Reset IDs para None (apenas atribuindo, não precisa de `global` novamente)
    after_id_serial_reader = None
    after_id_wifi_reader = None
    after_id_check_wifi = None
    after_id_wifi_connect_timeout = None

    # Fecha a conexão serial se estiver aberta
    if serial_conn and serial_conn.is_open:
        try:
            serial_conn.close()
            print("Conexão serial fechada.")
        except Exception as e:
            print(f"Erro ao fechar serial: {e}")
        serial_conn = None # Reset para None

    # Fecha a conexão Wi-Fi se estiver aberta
    if client:
        try:
            client.shutdown(socket.SHUT_RDWR) # Tenta um shutdown gracioso
            client.close()
            print("Conexão Wi-Fi fechada.")
        except socket.error as e: # Catch socket.error for specific handling
            print(f"Erro (socket.error) ao fechar Wi-Fi: {e}")
        except Exception as e:
            print(f"Erro ao fechar Wi-Fi: {e}")
        client = None # Reset para None

    # Reset last_read_time ao fechar o programa
    last_read_time = None

    janela.destroy()

def limpar_widgets_dinamicos():
    global barra_superior, frame_pitch, frame_raw, frame_yaw
    global ani1, ani2, ani3, ani_polar, ani_time_diff
    global main_content_frame

    # 1. Parar animações Matplotlib ANTES de destruir os canvases
    if ani1 is not None:
        ani1.event_source.stop()
        ani1 = None
    if ani2 is not None:
        ani2.event_source.stop()
        ani2 = None
    if ani3 is not None:
        ani3.event_source.stop()
        ani3 = None
    if ani_polar is not None:
        ani_polar.event_source.stop()
        ani_polar = None
    if ani_time_diff is not None:
        ani_time_diff.event_source.stop()
        ani_time_diff = None

    # 2. Destruir todos os widgets DENTRO DO main_content_frame
    if main_content_frame and main_content_frame.winfo_exists():
        for widget in main_content_frame.winfo_children():
            widget.destroy()

    # 3. Destruir a barra superior se ela existir (ela é criada em cima do main_content_frame)
    if barra_superior and barra_superior.winfo_exists():
        barra_superior.destroy()
        barra_superior = None

def criar_barra_superior_e_botoes(tab_type):
    """
    Cria a barra superior com botões e checkboxes,
    personalizada para o tipo de aba (IMU ou Tempo de Leitura).
    """
    global barra_superior, barra_checklist
    global check_var1, check_var2, check_var3, random_data
    global entry_num_dados_salvar_imu, entry_num_dados_salvar_tempo
    global main_content_frame

    # Destrói a barra superior existente se houver para evitar duplicatas
    if barra_superior and barra_superior.winfo_exists():
        barra_superior.destroy()

    barra_superior = ctk.CTkFrame(main_content_frame, height=30)
    barra_superior.pack(side="top", fill="x")

    # Inicializa as variáveis de controle (se ainda não estiverem inicializadas)
    if check_var1 is None: check_var1 = ctk.BooleanVar(value=True)
    if check_var2 is None: check_var2 = ctk.BooleanVar(value=True)
    if check_var3 is None: check_var3 = ctk.BooleanVar(value=True)
    if random_data is None: random_data = ctk.BooleanVar(value=False)

    if tab_type == "IMU_GRAPHS":
        barra_checklist = ctk.CTkFrame(barra_superior, height=30, fg_color="transparent")
        barra_checklist.pack(side="bottom", fill="x")

        check_button1 = ctk.CTkCheckBox(barra_checklist, text="Salvar Pitch", variable=check_var1, corner_radius=20, command=Graficos)
        check_button1.pack(side="left", fill="x", expand=True)

        check_button2 = ctk.CTkCheckBox(barra_checklist, text="Salvar Raw", variable=check_var2, corner_radius=20, command=Graficos)
        check_button2.pack(side="left", fill="x", expand=True)

        check_button3 = ctk.CTkCheckBox(barra_checklist, text="Salvar Yaw", variable=check_var3, corner_radius=20, command=Graficos)
        check_button3.pack(side="left", fill="x", expand=True)

        # Botões de salvamento para IMU
        botao_salvar = ctk.CTkButton(barra_superior, text="Salvar Todos os Dados IMU", command=lambda: salvar_dados_imu(None), corner_radius=20)
        botao_salvar.pack(side="top", pady=5, fill="both")

        frame_salvar_x_dados = ctk.CTkFrame(barra_superior, fg_color="transparent")
        frame_salvar_x_dados.pack(side="top", pady=5, fill="x")

        label_num_dados = ctk.CTkLabel(frame_salvar_x_dados, text="Salvar últimos (N) dados:")
        label_num_dados.pack(side="left", padx=(5, 0))

        entry_num_dados_salvar_imu = ctk.CTkEntry(frame_salvar_x_dados, width=80)
        entry_num_dados_salvar_imu.pack(side="left", padx=(0, 5))
        entry_num_dados_salvar_imu.insert(0, "100") # Valor padrão

        botao_salvar_x_dados = ctk.CTkButton(frame_salvar_x_dados, text="Salvar N Dados IMU", command=lambda: salvar_dados_imu(int(entry_num_dados_salvar_imu.get())), corner_radius=20)
        botao_salvar_x_dados.pack(side="left", padx=(0, 5))

        # Botões Resetar e Dados Aleatórios (APENAS para abas de gráficos IMU)
        botao_resetar = ctk.CTkButton(barra_superior, text="Resetar Dados", command=resetar_dados, corner_radius=20)
        botao_resetar.pack(side="top", pady=5, fill="both")

        bt_random_data = ctk.CTkCheckBox(barra_superior, text="Usar Dados Aleatórios", variable=random_data, corner_radius=20, command=lambda: resetar_dados())
        bt_random_data.pack(side="top", pady=5, fill="both")


    elif tab_type == "TIME_GRAPH":
        # Botões de salvamento para Tempo de Leitura
        botao_salvar_tempo = ctk.CTkButton(barra_superior, text="Salvar Todos os Dados de Tempo", command=lambda: salvar_dados_tempo_leitura(None), corner_radius=20)
        botao_salvar_tempo.pack(side="top", pady=5, fill="both")

        frame_salvar_x_dados_tempo = ctk.CTkFrame(barra_superior, fg_color="transparent")
        frame_salvar_x_dados_tempo.pack(side="top", pady=5, fill="x")

        label_num_dados_tempo = ctk.CTkLabel(frame_salvar_x_dados_tempo, text="Salvar últimos (N) dados de tempo:")
        label_num_dados_tempo.pack(side="left", padx=(5, 0))

        entry_num_dados_salvar_tempo = ctk.CTkEntry(frame_salvar_x_dados_tempo, width=80)
        entry_num_dados_salvar_tempo.pack(side="left", padx=(0, 5))
        entry_num_dados_salvar_tempo.insert(0, "100") # Valor padrão

        botao_salvar_x_dados_tempo = ctk.CTkButton(frame_salvar_x_dados_tempo, text="Salvar N Dados de Tempo", command=lambda: salvar_dados_tempo_leitura(int(entry_num_dados_salvar_tempo.get())), corner_radius=20)
        botao_salvar_x_dados_tempo.pack(side="left", padx=(0, 5))
        
        # New Reset button for Time Graph
        botao_resetar_tempo = ctk.CTkButton(barra_superior, text="Resetar Dados de Tempo", command=resetar_dados_tempo, corner_radius=20)
        botao_resetar_tempo.pack(side="top", pady=5, fill="both")


def resetar_dados():
    """Limpa os dados dos gráficos e reinicia os limites dos eixos."""
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3, ax, ax2, ax3
    global line1, line2, line3 # Certifique-se que as linhas são resetadas também

    x_data.clear()
    y_data.clear()
    x_data2.clear()
    y_data2.clear()
    x_data3.clear()
    y_data3.clear()

    # Reinicia os objetos dos gráficos se existirem
    if 'ax_pitch' in globals() and ax_pitch:
        ax_pitch.clear()
        ax_pitch.set_xlabel("Tempo[ms]")
        ax_pitch.set_ylabel("Angulo[graus]")
        ax_pitch.set_title("Pitch")
        ax_pitch.grid(True)
        line1, = ax_pitch.plot([], [], 'r-', label="Pitch")
        ax_pitch.relim()
        ax_pitch.autoscale_view()

    if 'ax_raw' in globals() and ax_raw:
        ax_raw.clear()
        ax_raw.set_xlabel("Tempo[ms]")
        ax_raw.set_ylabel("Angulo[graus]")
        ax_raw.set_title("Raw")
        ax_raw.grid(True)
        line2, = ax_raw.plot([], [], 'g-', label="Raw")
        ax_raw.relim()
        ax_raw.autoscale_view()

    if 'ax_yaw' in globals() and ax_yaw:
        ax_yaw.clear()
        ax_yaw.set_xlabel("Tempo[ms]")
        ax_yaw.set_ylabel("Angulo[graus]")
        ax_yaw.set_title("Yaw")
        ax_yaw.grid(True)
        line3, = ax_yaw.plot([], [], 'b-', label="Yaw")
        ax_yaw.relim()
        ax_yaw.autoscale_view()
    
    # Reinicia os gráficos polares
    if 'ax_polar1' in globals() and ax_polar1:
        for ax_p in [ax_polar1, ax_polar2, ax_polar3]:
            ax_p.clear()
            ax_p.set_theta_zero_location("N")
            ax_p.set_theta_direction(-1)
            ax_p.set_rlim(0, 1.1)
            ax_p.set_xticks([])
            ax_p.set_yticks([])
        ax_polar1.set_title("Pitch", va='bottom')
        ax_polar2.set_title("Raw", va='bottom')
        ax_polar3.set_title("Yaw", va='bottom')
        global pointer1, pointer2, pointer3
        pointer1, = ax_polar1.plot([0, 0], [0, 1], color='red', linewidth=3)
        pointer2, = ax_polar2.plot([0, 0], [0, 1], color='green', linewidth=3)
        pointer3, = ax_polar3.plot([0, 0], [0, 1], color='blue', linewidth=3)


    # Garante que os canvas dos gráficos sejam atualizados
    if 'canvas_line_plots' in globals() and canvas_line_plots is not None:
        canvas_line_plots.draw_idle()
    if 'canvas' in globals() and canvas is not None: # Para gráficos polares
        canvas.draw_idle()

def resetar_dados_tempo():
    """
    Limpa os dados do gráfico de tempo de leitura e reinicia os limites dos eixos.
    Esta função será chamada APENAS para o gráfico de tempo.
    """
    global time_diff_data, last_read_time, ax_time_diff, line_time_diff

    time_diff_data.clear()
    last_read_time = None # Reseta o timestamp da última leitura

    if 'ax_time_diff' in globals() and ax_time_diff:
        ax_time_diff.clear()
        ax_time_diff.set_xlabel("Amostra")
        ax_time_diff.set_ylabel("Tempo de Leitura [ms]")
        ax_time_diff.set_title("Tempo entre Leituras de Dados")
        ax_time_diff.grid(True)
        line_time_diff, = ax_time_diff.plot([], [], 'm-', label="Tempo de Leitura")
        ax_time_diff.relim()
        ax_time_diff.autoscale_view()
        if 'canvas_time_diff' in globals() and canvas_time_diff is not None:
            canvas_time_diff.draw_idle()


def salvar_dados_imu(num_pontos_a_salvar=None):
    """
    Salva os dados dos gráficos de Pitch, Raw e Yaw em um arquivo de texto.
    Respeita os checkboxes e o número de pontos a salvar.
    """
    nome_arquivo = filedialog.asksaveasfilename(
        title="Escolha o nome do arquivo para dados IMU",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not nome_arquivo:
        print("Nenhum nome de arquivo foi escolhido.")
        return

    # Determina o índice inicial para fatiar as listas IMU
    start_index = 0
    if num_pontos_a_salvar is not None and num_pontos_a_salvar > 0:
        start_index = max(0, len(x_data) - num_pontos_a_salvar)
        
    print(f"Salvando dados IMU: {len(x_data) - start_index} pontos.")

    with open(nome_arquivo, 'w') as f:
        f.write(f"Dados IMU salvos a partir da leitura #{start_index + 1}\n")
        f.write(f"Total de pontos salvos: {len(x_data) - start_index}\n\n")

        if check_var1.get():
            f.write("Gráfico Pitch:\n")
            for i in range(start_index, len(x_data)):
                f.write(f"{x_data[i]}\t{y_data[i]}\n")
            f.write("\n")

        if check_var2.get():
            f.write("Gráfico Raw:\n")
            for i in range(start_index, len(x_data2)):
                f.write(f"{x_data2[i]}\t{y_data2[i]}\n")
            f.write("\n")

        if check_var3.get():
            f.write("Gráfico Yaw:\n")
            for i in range(start_index, len(x_data3)):
                f.write(f"{x_data3[i]}\t{y_data3[i]}\n")
            f.write("\n")
    
    print(f"Arquivo IMU salvo em: {nome_arquivo}")
    tk.messagebox.showinfo("Sucesso", f"Dados IMU salvos com sucesso em: {nome_arquivo}")


def salvar_dados_tempo_leitura(num_pontos_a_salvar=None):
    """
    Salva os dados do gráfico de Tempo de Leitura em um arquivo de texto.
    """
    nome_arquivo = filedialog.asksaveasfilename(
        title="Escolha o nome do arquivo para dados de Tempo de Leitura",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not nome_arquivo:
        print("Nenhum nome de arquivo foi escolhido.")
        return

    # Determina o índice inicial para fatiar a lista de tempo
    start_index_time = 0
    if num_pontos_a_salvar is not None and num_pontos_a_salvar > 0:
        start_index_time = max(0, len(time_diff_data) - num_pontos_a_salvar)
    
    print(f"Salvando dados de Tempo de Leitura: {len(time_diff_data) - start_index_time} pontos.")

    with open(nome_arquivo, 'w') as f:
        f.write(f"Dados de Tempo entre Leituras (ms) salvos a partir da amostra #{start_index_time + 1}\n")
        f.write(f"Total de pontos salvos: {len(time_diff_data) - start_index_time}\n\n")

        if time_diff_data:
            f.write("Tempo entre Leituras de Dados (ms):\n")
            for i in range(start_index_time, len(time_diff_data)):
                f.write(f"{i}\t{time_diff_data[i]:.2f}\n")
            f.write("\n")
        else:
            f.write("Nenhum dado de tempo de leitura disponível.\n")

    print(f"Arquivo de tempo de leitura salvo em: {nome_arquivo}")
    tk.messagebox.showinfo("Sucesso", f"Dados de Tempo de Leitura salvos com sucesso em: {nome_arquivo}")


def atualizar_grafico():
    """
    Pega os últimos dados IMU da variável global `dados_atuais_imu`
    e os armazena nas listas globais para os gráficos.
    Esta função é chamada pelas animações do Matplotlib.
    """
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3, dados_atuais_imu
    global time_diff_data, last_read_time

    valores = dados_atuais_imu # Pega os valores da variável global

    # Se dados válidos foram lidos/gerados, armazena
    if len(valores) == 3:
        current_time = time.time() * 1000 # Tempo atual em milissegundos

        # Calcula a diferença de tempo
        if last_read_time is not None:
            time_diff = current_time - last_read_time
            time_diff_data.append(time_diff)
            # Limita a quantidade de dados de tempo
            if len(time_diff_data) > 500:
                time_diff_data.pop(0)

        last_read_time = current_time

        max_points = 500 # Limita a quantidade de dados para evitar sobrecarga

        # Adiciona novos dados
        x_data.append(len(x_data))
        y_data.append(valores[0])
        x_data2.append(len(x_data2))
        y_data2.append(valores[1])
        x_data3.append(len(x_data3))
        y_data3.append(valores[2])

        # Mantém apenas os últimos 'max_points'
        if len(x_data) > max_points:
            x_data.pop(0)
            y_data.pop(0)
            x_data2.pop(0)
            y_data2.pop(0)
            x_data3.pop(0)
            y_data3.pop(0)

            # Reajusta os valores de x para que sejam sequenciais após a remoção
            for i in range(len(x_data)):
                x_data[i] = i
                x_data2[i] = i
                x_data3[i] = i

# --- Funções das Abas ---

# Globais para os objetos Figure e Canvas para acesso fora das funções
fig_line_plots, ax_pitch, ax_raw, ax_yaw, canvas_line_plots = None, None, None, None, None
fig_polar, ax_polar1, ax_polar2, ax_polar3, canvas = None, None, None, None, None
fig_time_diff, ax_time_diff, canvas_time_diff = None, None, None

def Graficos():
    """
    Exibe os gráficos de Pitch, Raw e Yaw em subplots dentro de uma única figura.
    """
    global fig_line_plots, canvas_line_plots
    global ax_pitch, ax_raw, ax_yaw, line1, line2, line3, ani1
    global main_content_frame

    limpar_widgets_dinamicos() # Limpa o conteúdo anterior

    # A barra superior com checkboxes será criada no main_content_frame
    criar_barra_superior_e_botoes("IMU_GRAPHS") # Passa o tipo de aba

    # Crie uma única figura.
    fig_line_plots = Figure(figsize=(12, 8), dpi=100)

    ax_pitch = fig_line_plots.add_subplot(311)
    ax_raw = fig_line_plots.add_subplot(312)
    ax_yaw = fig_line_plots.add_subplot(313)

    # Configuração de cada subplot (eixo)
    # Pitch
    ax_pitch.set_xlabel("Tempo[ms]")
    ax_pitch.set_ylabel("Angulo[graus]")
    ax_pitch.grid(True)
    ax_pitch.set_title("Pitch")
    line1, = ax_pitch.plot([], [], 'r-', label="Pitch")

    # Raw
    ax_raw.set_xlabel("Tempo[ms]")
    ax_raw.set_ylabel("Angulo[graus]")
    ax_raw.grid(True)
    ax_raw.set_title("Raw")
    line2, = ax_raw.plot([], [], 'g-', label="Raw")

    # Yaw
    ax_yaw.set_xlabel("Tempo[ms]")
    ax_yaw.set_ylabel("Angulo[graus]")
    ax_yaw.grid(True)
    ax_yaw.set_title("Yaw")
    line3, = ax_yaw.plot([], [], 'b-', label="Yaw")

    fig_line_plots.tight_layout()

    # Cria um único canvas para a figura e o empacota no main_content_frame
    canvas_line_plots = FigureCanvasTkAgg(fig_line_plots, master=main_content_frame)
    canvas_line_plots.get_tk_widget().pack(fill="both", expand=True)

    def animate_plots(i):
        """Função de atualização para FuncAnimation dos gráficos de linha."""

        atualizar_grafico() # Lê os dados da variável global e atualiza as listas
        
        # Lista para armazenar eixos que precisam de atualização de layout
        axes_to_update_layout = []

        # Pitch
        if check_var1.get():
            line1.set_data(x_data, y_data)
            if x_data:
                ax_pitch.set_xlim(max(0, x_data[-1] - 500), x_data[-1] + 10)
            else:
                ax_pitch.set_xlim(0, 500)

            if y_data:
                min_y, max_y = min(y_data), max(y_data)
                if min_y == max_y:
                    ax_pitch.set_ylim(min_y - 5, max_y + 5)
                else:
                    ax_pitch.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)
            else:
                ax_pitch.set_ylim(-10, 10)
            
            # Torna o eixo visível
            if not ax_pitch.get_visible():
                ax_pitch.set_visible(True)
                axes_to_update_layout.append(ax_pitch)
            
        else:
            if ax_pitch.get_visible():
                ax_pitch.set_visible(False)
                axes_to_update_layout.append(ax_pitch)
            line1.set_data([], [])


        # Raw
        if check_var2.get():
            line2.set_data(x_data2, y_data2)
            if x_data2:
                ax_raw.set_xlim(max(0, x_data2[-1] - 500), x_data2[-1] + 10)
            else:
                ax_raw.set_xlim(0, 500)

            if y_data2:
                min_y, max_y = min(y_data2), max(y_data2)
                if min_y == max_y:
                    ax_raw.set_ylim(min_y - 5, max_y + 5)
                else:
                    ax_raw.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)
            else:
                ax_raw.set_ylim(-10, 10)

            if not ax_raw.get_visible():
                ax_raw.set_visible(True)
                axes_to_update_layout.append(ax_raw)

        else:
            if ax_raw.get_visible():
                ax_raw.set_visible(False)
                axes_to_update_layout.append(ax_raw)
            line2.set_data([], [])

        # Yaw
        if check_var3.get():
            line3.set_data(x_data3, y_data3)
            if x_data3:
                ax_yaw.set_xlim(max(0, x_data3[-1] - 500), x_data3[-1] + 10)
            else:
                ax_yaw.set_xlim(0, 500)

            if y_data3:
                min_y, max_y = min(y_data3), max(y_data3)
                if min_y == max_y:
                    ax_yaw.set_ylim(min_y - 5, max_y + 5)
                else:
                    ax_yaw.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)
            else:
                ax_yaw.set_ylim(-10, 10)
            
            if not ax_yaw.get_visible():
                ax_yaw.set_visible(True)
                axes_to_update_layout.append(ax_yaw)

        else:
            if ax_yaw.get_visible():
                ax_yaw.set_visible(False)
                axes_to_update_layout.append(ax_yaw)
            line3.set_data([], [])

        if axes_to_update_layout:
            fig_line_plots.tight_layout()
            canvas_line_plots.draw_idle()
            return [] 
        
        return [line1, line2, line3]

    if fig_line_plots:
        ani1 = FuncAnimation(fig_line_plots, animate_plots, interval=50, cache_frame_data=False, blit=False)
        canvas_line_plots.draw_idle()

def GraficosPolares():
    """
    Exibe os gráficos polares.
    """
    global canvas, ani_polar
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    global fig_polar, ax_polar1, ax_polar2, ax_polar3, pointer1, pointer2, pointer3
    global main_content_frame

    limpar_widgets_dinamicos() # Limpa o conteúdo anterior
    criar_barra_superior_e_botoes("IMU_GRAPHS") # Passa o tipo de aba

    fig_polar = Figure(figsize=(12, 8), dpi=100)
    ax_polar1 = fig_polar.add_subplot(311, projection='polar')
    ax_polar2 = fig_polar.add_subplot(312, projection='polar')
    ax_polar3 = fig_polar.add_subplot(313, projection='polar')
    fig_polar.subplots_adjust(hspace=0.0)

    for ax_p in [ax_polar1, ax_polar2, ax_polar3]:
        ax_p.set_theta_zero_location("N")
        ax_p.set_theta_direction(-1)
        ax_p.set_rlim(0, 1.1)
        ax_p.set_xticks([])
        ax_p.set_yticks([])

    ax_polar1.set_title("Pitch", va='bottom')
    ax_polar2.set_title("Raw", va='bottom')
    ax_polar3.set_title("Yaw", va='bottom')

    pointer1, = ax_polar1.plot([0, 0], [0, 1], color='red', linewidth=3)
    pointer2, = ax_polar2.plot([0, 0], [0, 1], color='green', linewidth=3)
    pointer3, = ax_polar3.plot([0, 0], [0, 1], color='blue', linewidth=3)


    def atualizar_polares(i):
        """Função de atualização para FuncAnimation dos gráficos polares."""
        atualizar_grafico()
        if len(dados_atuais_imu) == 3:
            valor1_rad = (dados_atuais_imu[0] * (math.pi / 180)) % (2 * math.pi)
            valor2_rad = (dados_atuais_imu[1] * (math.pi / 180)) % (2 * math.pi)
            valor3_rad = (dados_atuais_imu[2] * (math.pi / 180)) % (2 * math.pi)

            pointer1.set_data([valor1_rad, valor1_rad], [0, 1])
            pointer2.set_data([valor2_rad, valor2_rad], [0, 1])
            pointer3.set_data([valor3_rad, valor3_rad], [0, 1])

        return pointer1, pointer2, pointer3

    canvas = FigureCanvasTkAgg(fig_polar, master=main_content_frame) # Empacotar no main_content_frame
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(anchor=tk.CENTER, expand=True, fill='both')

    ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, cache_frame_data=False, blit=True)
    canvas.draw_idle()


def GraficoTempoLeitura():
    """
    Exibe o gráfico de tempo de leitura entre cada dado recebido.
    """
    global fig_time_diff, ax_time_diff, canvas_time_diff, ani_time_diff
    global time_diff_data
    global main_content_frame

    limpar_widgets_dinamicos() # Limpa o conteúdo anterior

    # Cria a barra superior ESPECÍFICA para o gráfico de tempo de leitura
    criar_barra_superior_e_botoes("TIME_GRAPH")

    fig_time_diff = Figure(figsize=(10, 6), dpi=100)
    ax_time_diff = fig_time_diff.add_subplot(111)

    ax_time_diff.set_xlabel("Amostra")
    ax_time_diff.set_ylabel("Tempo de Leitura [ms]")
    ax_time_diff.set_title("Tempo entre Leituras de Dados")
    ax_time_diff.grid(True)

    line_time_diff, = ax_time_diff.plot([], [], 'm-', label="Tempo de Leitura")

    fig_time_diff.tight_layout()

    canvas_time_diff = FigureCanvasTkAgg(fig_time_diff, master=main_content_frame)
    canvas_time_diff_widget = canvas_time_diff.get_tk_widget()
    canvas_time_diff_widget.pack(fill="both", expand=True)

    def animate_time_diff(i):
        """Função de atualização para FuncAnimation do gráfico de tempo de leitura."""
        
        # A atualização de dados já ocorre em atualizar_grafico, que é chamada indiretamente
        # pela animação de IMU, ou pode ser chamada aqui também.
        # No entanto, se o random_data estiver ativo, ele já gera e armazena time_diff_data
        # mesmo sem um sensor real.
        
        x_indices = list(range(len(time_diff_data)))
        line_time_diff.set_data(x_indices, time_diff_data)

        if x_indices:
            ax_time_diff.set_xlim(max(0, x_indices[-1] - 500), x_indices[-1] + 10)
        else:
            ax_time_diff.set_xlim(0, 500)

        if time_diff_data:
            min_y, max_y = min(time_diff_data), max(time_diff_data)
            if min_y == max_y:
                ax_time_diff.set_ylim(min_y * 0.9, max_y * 1.1 + 1)
            else:
                ax_time_diff.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)
        else:
            ax_time_diff.set_ylim(0, 100)

        return [line_time_diff]

    ani_time_diff = FuncAnimation(fig_time_diff, animate_time_diff, interval=100, cache_frame_data=False, blit=True)
    canvas_time_diff.draw_idle()


def Conexao():
    # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
    global label_dados, serial_conn, client
    global after_id_serial_reader, after_id_wifi_reader, after_id_check_wifi, after_id_wifi_connect_timeout, dropdown_baudrate, baudrate_selecionado_var
    global main_content_frame

    limpar_widgets_dinamicos()

    frame_central = ctk.CTkFrame(main_content_frame, fg_color="transparent")
    frame_central.place(relx=0.5, rely=0.5, anchor="center")

    title_label = ctk.CTkLabel(frame_central, text="Configurações de Conexão", font=ctk.CTkFont(size=16, weight="bold"))
    title_label.pack(pady=(0, 15))

    label = ctk.CTkLabel(frame_central, text="Escolha o método de conexão:")
    label.pack(pady=5)

    label_baudrate = ctk.CTkLabel(frame_central, text="Baudrate:")
    label_baudrate.pack(pady=(10, 0))

    baudrates_disponiveis = ["9600", "57600", "115200", "250000", "460800", "921600"]
    if baudrate_selecionado_var is None:
        baudrate_selecionado_var = ctk.StringVar(value=baudrates_disponiveis[2])

    dropdown_baudrate = ctk.CTkOptionMenu(frame_central, values=baudrates_disponiveis, variable=baudrate_selecionado_var)
    dropdown_baudrate.pack(pady=(0, 10))

    label_portas = ctk.CTkLabel(frame_central, text="Porta Serial (COM):")
    label_portas.pack(pady=(10, 0))

    portas_disponiveis = listar_portas()
    if not portas_disponiveis:
        portas_disponiveis = ["Nenhuma porta encontrada"]

    porta_selecionada_var = ctk.StringVar(value=portas_disponiveis[0]) if portas_disponiveis else ctk.StringVar(value="")

    dropdown_portas = ctk.CTkOptionMenu(frame_central, values=portas_disponiveis, variable=porta_selecionada_var)
    dropdown_portas.pack(pady=(0, 10))

    texto_status = ctk.CTkLabel(frame_central, text="Status: Desconectado")
    texto_status.pack(pady=5)

    label_dados = ctk.CTkLabel(frame_central, text="Últimos dados recebidos: Nenhum")
    label_dados.pack(pady=5)

    def desconectar_tudo():
        """Fecha qualquer conexão ativa (Serial ou Wi-Fi) e cancela loops de leitura."""
        # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
        global serial_conn, client, after_id_serial_reader, after_id_wifi_reader, after_id_check_wifi, after_id_wifi_connect_timeout
        global last_read_time # Adicionado aqui pois é modificado/resetado
        
        texto_status.configure(text="Status: Desconectando...")

        # Cancela todos os agendamentos pendentes
        for _id in [after_id_serial_reader, after_id_wifi_reader, after_id_check_wifi, after_id_wifi_connect_timeout]:
            if _id is not None:
                try:
                    janela.after_cancel(_id)
                except Exception:
                    pass
        # Reset IDs to None (apenas atribuindo, não precisa de `global` novamente)
        after_id_serial_reader = None
        after_id_wifi_reader = None
        after_id_check_wifi = None
        after_id_wifi_connect_timeout = None

        if serial_conn and serial_conn.is_open:
            try:
                serial_conn.close()
                print("Conexão serial fechada manualmente.")
            except Exception as e:
                print(f"Erro ao fechar serial: {e}")
            serial_conn = None

        if client: # Verifica se o objeto client existe
            try:
                client.shutdown(socket.SHUT_RDWR) # Fecha ambas as direções de leitura/escrita
                client.close()
                print("Conexão Wi-Fi fechada manualmente.")
            except socket.error as e:
                print(f"Erro (socket.error) ao fechar Wi-Fi: {e}")
            except Exception as e:
                print(f"Erro ao fechar Wi-Fi: {e}")
            client = None

        texto_status.configure(text="Status: Desconectado")
        label_dados.configure(text="Últimos dados recebidos: Nenhum")
        last_read_time = None # Reset last_read_time
        dados_atuais_imu[:] = [0.0, 0.0, 0.0] # Reseta dados IMU
        time_diff_data.clear() # Limpa dados de tempo

    def conectar_serial():
        """Tenta conectar via Serial, fechando qualquer outra conexão."""
        # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
        global serial_conn, after_id_serial_reader, dados_atuais_imu, last_read_time

        desconectar_tudo() # Sempre desconectar antes de tentar nova conexão

        porta = porta_selecionada_var.get()
        if porta == "Nenhuma porta encontrada" or not porta:
            texto_status.configure(text="Erro: Nenhuma porta serial selecionada ou disponível.")
            return

        try:
            baudrate_val = int(baudrate_selecionado_var.get())
            serial_conn = serial.Serial(porta, baudrate_val, timeout=0.01) # Timeout baixo para leitura não bloqueante
            texto_status.configure(text=f"Conectado à {porta} @ {baudrate_val} bps (Serial)")
            dados_atuais_imu[:] = [0.0, 0.0, 0.0] # Reseta dados IMU
            time_diff_data.clear()
            last_read_time = None
            after_id_serial_reader = janela.after(10, ler_dados_serial_background)
        except ValueError:
            texto_status.configure(text="Erro: Baudrate inválido. Selecione um da lista.")
            serial_conn = None
        except Exception as e:
            texto_status.configure(text=f"Erro ao conectar serial: {e}")
            serial_conn = None

    def conectar_wifi():
        """Tenta conectar via Wi-Fi, fechando qualquer outra conexão."""
        # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
        global client, after_id_check_wifi, after_id_wifi_connect_timeout, dados_atuais_imu, last_read_time

        desconectar_tudo() # Sempre desconectar antes de tentar nova conexão

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.setblocking(False) # Torna o socket não bloqueante

            # Inicia a tentativa de conexão
            result = client.connect_ex((ESP_IP, ESP_PORT))

            if result == 0: # Conexão imediata (raro para máquinas na mesma rede)
                texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi! (TCP/IP)")
                dados_atuais_imu[:] = [0.0, 0.0, 0.0]
                time_diff_data.clear()
                last_read_time = None
                global after_id_wifi_reader # Precisamos declarar aqui porque estamos ATRIBUINDO a ele
                after_id_wifi_reader = janela.after(10, ler_dados_wifi_background)
            elif result in (10035, 115): # WSAEWOULDBLOCK ou EINPROGRESS - Conexão em progresso
                texto_status.configure(text=f"Tentando conectar ao ESP32 via Wi-Fi...")
                global after_id_check_wifi # Precisamos declarar aqui porque estamos ATRIBUINDO a ele
                after_id_check_wifi = janela.after(100, verificar_conexao_wifi)
                # Adiciona um timeout para a conexão inicial
                global after_id_wifi_connect_timeout # Precisamos declarar aqui porque estamos ATRIBUINDO a ele
                after_id_wifi_connect_timeout = janela.after(5000, lambda: handle_wifi_connect_timeout(client)) # 5 segundos de timeout
            else:
                texto_status.configure(text=f"Erro de conexão Wi-Fi: {socket.error(result).strerror} (Erro: {result})")
                client.close()
                client = None

        except Exception as e:
            texto_status.configure(text=f"Erro ao criar socket Wi-Fi: {e}")
            if client: client.close()
            client = None

    def handle_wifi_connect_timeout(socket_obj):
        """Lida com o timeout da tentativa de conexão Wi-Fi."""
        # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
        global client, after_id_check_wifi, after_id_wifi_connect_timeout
        global after_id_wifi_reader # Adicionado aqui pois pode ser atribuído
        global last_read_time # Adicionado aqui pois é modificado/resetado

        if after_id_wifi_connect_timeout is not None:
            janela.after_cancel(after_id_wifi_connect_timeout)
            after_id_wifi_connect_timeout = None

        if client and client == socket_obj: # Garante que é o mesmo socket
            try:
                # Tenta verificar se a conexão foi estabelecida no último ciclo
                r, w, x = select.select([client], [client], [client], 0)
                if client in r or client in w:
                    # Se o socket está pronto para ler ou escrever, a conexão foi estabelecida
                    texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi! (TCP/IP) após timeout")
                    dados_atuais_imu[:] = [0.0, 0.0, 0.0]
                    time_diff_data.clear()
                    last_read_time = None
                    after_id_wifi_reader = janela.after(10, ler_dados_wifi_background)
                    # Cancela o check_wifi, pois a conexão foi estabelecida
                    if after_id_check_wifi is not None:
                        janela.after_cancel(after_id_check_wifi)
                        after_id_check_wifi = None
                    return
                elif client in x:
                    # Houve um erro no socket durante a conexão
                    texto_status.configure(text="Erro de conexão Wi-Fi (timeout): Socket com erro.")
                    client.close()
                    client = None
                    if after_id_check_wifi is not None:
                        janela.after_cancel(after_id_check_wifi)
                        after_id_check_wifi = None
                    return
            except Exception as e:
                print(f"Erro ao verificar socket no timeout: {e}")
                texto_status.configure(text="Erro de conexão Wi-Fi (timeout).")
                if client: client.close()
                client = None
                if after_id_check_wifi is not None:
                    janela.after_cancel(after_id_check_wifi)
                    after_id_check_wifi = None
                return
            
            # Se chegou aqui, a conexão ainda não foi estabelecida e o timeout ocorreu
            if client: client.close() # Fechar o socket pendente
            client = None
            texto_status.configure(text="Erro: Timeout de conexão Wi-Fi excedido. Tente novamente.")
            if after_id_check_wifi is not None:
                janela.after_cancel(after_id_check_wifi)
                after_id_check_wifi = None


    def verificar_conexao_wifi():
        """Verifica o status da conexão Wi-Fi assincronamente."""
        # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
        global client, after_id_check_wifi, after_id_wifi_reader, after_id_wifi_connect_timeout
        global last_read_time # Adicionado aqui pois é modificado/resetado
        global dados_atuais_imu # Adicionado pois é resetado

        if client:
            try:
                # Usa select para verificar se o socket está pronto para escrita (conexão estabelecida)
                # ou para leitura (dados recebidos ou conexão fechada)
                rlist, wlist, xlist = select.select([client], [client], [client], 0)

                if client in xlist: # Erro no socket
                    print("Socket Wi-Fi em estado de erro durante verificação.")
                    texto_status.configure(text="Erro na conexão Wi-Fi (socket com erro).")
                    client.close()
                    client = None
                    # Cancela agendamentos relacionados para evitar mais chamadas
                    if after_id_check_wifi is not None: janela.after_cancel(after_id_check_wifi)
                    if after_id_wifi_connect_timeout is not None: janela.after_cancel(after_id_wifi_connect_timeout)
                    after_id_check_wifi = None
                    after_id_wifi_connect_timeout = None
                    return # Sai da função, não reagenda

                if client in wlist: # Socket pronto para escrita = conexão estabelecida!
                    texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi! (TCP/IP)")
                    dados_atuais_imu[:] = [0.0, 0.0, 0.0]
                    time_diff_data.clear()
                    last_read_time = None
                    # Cancela o agendamento de checagem e timeout de conexão
                    if after_id_check_wifi is not None:
                        janela.after_cancel(after_id_check_wifi)
                        after_id_check_wifi = None
                    if after_id_wifi_connect_timeout is not None:
                        janela.after_cancel(after_id_wifi_connect_timeout)
                        after_id_wifi_connect_timeout = None
                    # Inicia a leitura de dados
                    after_id_wifi_reader = janela.after(10, ler_dados_wifi_background)
                    return # Sai da função, não reagenda

                # Se a conexão ainda não está pronta, reagenda a verificação
                after_id_check_wifi = janela.after(100, verificar_conexao_wifi)

            except Exception as e: # Catch all other potential socket errors
                print(f"Erro inesperado durante a verificação de conexão Wi-Fi: {e}")
                texto_status.configure(text=f"Erro inesperado na conexão Wi-Fi: {e}")
                if client: client.close()
                client = None
                # Cancela todos os agendamentos relacionados ao Wi-Fi
                if after_id_check_wifi is not None:
                    janela.after_cancel(after_id_check_wifi)
                    after_id_check_wifi = None
                if after_id_wifi_connect_timeout is not None:
                    janela.after_cancel(after_id_wifi_connect_timeout)
                    after_id_wifi_connect_timeout = None
        else:
            # Cliente é None, significa que a conexão não existe mais ou falhou.
            texto_status.configure(text="Conexão Wi-Fi falhou ou foi fechada.")
            if after_id_check_wifi is not None:
                janela.after_cancel(after_id_check_wifi)
                after_id_check_wifi = None
            if after_id_wifi_connect_timeout is not None:
                janela.after_cancel(after_id_wifi_connect_timeout)
                after_id_wifi_connect_timeout = None


    # Botões de conexão
    botao_serial = ctk.CTkButton(frame_central, text="Conectar via Porta COM", command=conectar_serial)
    botao_serial.pack(pady=5)

    botao_wifi = ctk.CTkButton(frame_central, text="Conectar via Wi-Fi", command=conectar_wifi)
    botao_wifi.pack(pady=5)

    botao_desconectar = ctk.CTkButton(frame_central, text="Desconectar", command=desconectar_tudo)
    botao_desconectar.pack(pady=5)


def ler_dados_serial_background():
    """Lê dados da porta serial e atualiza dados_atuais_imu globalmente."""
    # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
    global serial_conn, after_id_serial_reader, dados_atuais_imu, random_data, label_dados, last_read_time, time_diff_data

    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
        dados_atuais_imu[:] = valores # Atualiza a lista in-place
        current_time = time.time() * 1000
        if last_read_time is not None:
            time_diff_data.append(current_time - last_read_time)
            if len(time_diff_data) > 500:
                time_diff_data.pop(0)
        last_read_time = current_time

        if label_dados and label_dados.winfo_exists():
            label_dados.configure(text=f"Dados Aleatórios: {dados_atuais_imu[0]:.2f}, {dados_atuais_imu[1]:.2f}, {dados_atuais_imu[2]:.2f}")
        after_id_serial_reader = janela.after(100, ler_dados_serial_background)
        return

    if serial_conn and serial_conn.is_open:
        try:
            ultima_linha = None
            while serial_conn.in_waiting: # Lês todas as linhas disponíveis no buffer
                ultima_linha = serial_conn.readline().decode('utf-8').strip()

            if ultima_linha:
                try:
                    valores = [float(val) for val in ultima_linha.split()]
                    if len(valores) == 3:
                        dados_atuais_imu[:] = valores # Atualiza a lista in-place

                        current_time = time.time() * 1000
                        if last_read_time is not None:
                            time_diff = current_time - last_read_time
                            time_diff_data.append(time_diff)
                            if len(time_diff_data) > 500:
                                time_diff_data.pop(0)
                        last_read_time = current_time

                        if label_dados and label_dados.winfo_exists():
                            label_dados.configure(text=f"Dados Serial: {ultima_linha}")
                except ValueError:
                    if label_dados and label_dados.winfo_exists():
                        label_dados.configure(text=f"Erro de formato de dado: '{ultima_linha}'")
                except Exception as parse_e:
                    if label_dados and label_dados.winfo_exists():
                        label_dados.configure(text=f"Erro ao processar dados: {parse_e}")

        except Exception as e:
            # Qualquer erro na leitura serial indica uma desconexão ou problema grave
            if label_dados and label_dados.winfo_exists():
                label_dados.configure(text=f"Erro fatal na leitura serial: {e}")
            if serial_conn and serial_conn.is_open:
                try:
                    serial_conn.close()
                except Exception:
                    pass
            serial_conn = None
            # Cancela o agendamento para evitar mais erros
            if after_id_serial_reader is not None:
                try:
                    janela.after_cancel(after_id_serial_reader)
                except Exception:
                    pass
                after_id_serial_reader = None
            return # Sai da função

        # Reagenda a próxima leitura se a conexão ainda estiver ativa
        if serial_conn and serial_conn.is_open:
            after_id_serial_reader = janela.after(10, ler_dados_serial_background)
        else:
            # Se a conexão caiu no meio, assegura que o agendamento é cancelado e o status atualizado
            if after_id_serial_reader is not None:
                try:
                    janela.after_cancel(after_id_serial_reader)
                except Exception:
                    pass
                after_id_serial_reader = None
            if label_dados and label_dados.winfo_exists():
                label_dados.configure(text="Conexão Serial Inativa/Fechada.")
    else: # Se serial_conn é None ou não está aberta desde o início
        if after_id_serial_reader is not None:
            try:
                janela.after_cancel(after_id_serial_reader)
            except Exception:
                pass
            after_id_serial_reader = None
        if label_dados and label_dados.winfo_exists():
            label_dados.configure(text="Conexão Serial Inativa/Fechada.")


def ler_dados_wifi_background():
    """Lê dados da conexão Wi-Fi e atualiza dados_atuais_imu globalmente."""
    # Garanta que as declarações global são as PRIMEIRAS linhas executáveis
    global client, after_id_wifi_reader, dados_atuais_imu, random_data, label_dados, last_read_time, time_diff_data

    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
        dados_atuais_imu[:] = valores # Atualiza a lista in-place
        current_time = time.time() * 1000
        if last_read_time is not None:
            time_diff_data.append(current_time - last_read_time)
            if len(time_diff_data) > 500:
                time_diff_data.pop(0)
        last_read_time = current_time

        if label_dados and label_dados.winfo_exists():
            label_dados.configure(text=f"Dados Aleatórios: {dados_atuais_imu[0]:.2f}, {dados_atuais_imu[1]:.2f}, {dados_atuais_imu[2]:.2f}")
        after_id_wifi_reader = janela.after(100, ler_dados_wifi_background)
        return

    if client is not None:
        try:
            # Usa select para verificar se há dados para ler no socket sem bloquear
            # Timeout de 0 significa não bloquear, verifica imediatamente
            rlist, _, _ = select.select([client], [], [], 0)
            
            if client in rlist: # Se o socket está na lista de leitura, há dados ou a conexão foi fechada
                data_raw = client.recv(1024) # Tenta ler dados
                
                if data_raw: # Se recebeu dados
                    data = data_raw.decode('utf-8').strip() # Decodifica e remove espaços/newlines

                    try:
                        numeros = [float(val) for val in data.split()]
                        if len(numeros) == 3:
                            dados_atuais_imu[:] = numeros # Atualiza a lista in-place

                            current_time = time.time() * 1000
                            if last_read_time is not None:
                                time_diff = current_time - last_read_time
                                time_diff_data.append(time_diff)
                                if len(time_diff_data) > 500:
                                    time_diff_data.pop(0)
                            last_read_time = current_time

                            if label_dados and label_dados.winfo_exists():
                                label_dados.configure(text=f"Dados Wi-Fi: {data}")
                    except ValueError:
                        if label_dados and label_dados.winfo_exists():
                            label_dados.configure(text=f"Erro de formato de dado Wi-Fi: '{data}'")
                    except Exception as parse_e:
                        if label_dados and label_dados.winfo_exists():
                            label_dados.configure(text=f"Erro ao processar dados Wi-Fi: {parse_e}")
                else: # Se data_raw é vazio (b''), o outro lado fechou a conexão (desconexão limpa)
                    print("Conexão Wi-Fi encerrada pelo ESP32 (recv retornou b'').")
                    if label_dados and label_dados.winfo_exists():
                        label_dados.configure(text="Conexão Wi-Fi Encerrada pelo servidor.")
                    client.close()
                    client = None
                    # Cancela o agendamento para evitar mais chamadas em um socket fechado
                    if after_id_wifi_reader is not None:
                        try:
                            janela.after_cancel(after_id_wifi_reader)
                        except Exception:
                            pass
                        after_id_wifi_reader = None
                    return # Sai da função, não reagenda
            
            # Se não há dados no rlist (socket não pronto para leitura), ou já leu os dados
            # reagenda a próxima leitura
            after_id_wifi_reader = janela.after(10, ler_dados_wifi_background)

        except socket.error as e: # Erros de socket que indicam uma desconexão ou problema (ex: ConnectionResetError)
            print(f"Erro de socket na leitura Wi-Fi: {e}")
            if label_dados and label_dados.winfo_exists():
                label_dados.configure(text=f"Erro fatal na comunicação Wi-Fi: {e}")
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            client = None
            # Cancela o agendamento para evitar mais chamadas em um socket fechado
            if after_id_wifi_reader is not None:
                try:
                    janela.after_cancel(after_id_wifi_reader)
                except Exception:
                    pass
                after_id_wifi_reader = None
            return # Sai da função, não reagenda
        except Exception as e: # Outros erros inesperados
            print(f"Erro inesperado na leitura Wi-Fi: {e}")
            if label_dados and label_dados.winfo_exists():
                label_dados.configure(text=f"Erro inesperado na leitura Wi-Fi: {e}")
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            client = None
            # Cancela o agendamento para evitar mais chamadas em um socket fechado
            if after_id_wifi_reader is not None:
                try:
                    janela.after_cancel(after_id_wifi_reader)
                except Exception:
                    pass
                after_id_wifi_reader = None
            return # Sai da função, não reagenda
    else: # Cliente é None, a conexão não está ativa
        if after_id_wifi_reader is not None:
            try:
                janela.after_cancel(after_id_wifi_reader)
            except Exception:
                pass
            after_id_wifi_reader = None
        if label_dados and label_dados.winfo_exists():
            label_dados.configure(text="Conexão Wi-Fi Inativa/Fechada.")


def listar_portas():
    """Retorna uma lista de portas seriais disponíveis."""
    return [porta.device for porta in serial.tools.list_ports.comports()]

# --- Configuração da Interface Principal ---

def mostrar_tooltip(event, texto):
    tooltip = tk.Label(janela, text=texto, bg="yellow", fg="black", padx=5, pady=2, relief="solid", borderwidth=1)
    # Ajusta a posição do tooltip para ser relativa à janela, não à tela
    x = event.x_root - janela.winfo_rootx() + 20
    y = event.y_root - janela.winfo_rooty() + 10
    tooltip.place(x=x, y=y)
    # Armazena o tooltip no widget para poder destruí-lo depois
    event.widget.tooltip = tooltip

def ocultar_tooltip(event):
    if hasattr(event.widget, "tooltip"):
        event.widget.tooltip.destroy()
        del event.widget.tooltip


janela = ctk.CTk()
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
largura_janela = int(largura_tela * 0.75)
altura_janela = int(altura_tela * 0.75)
janela.geometry(f"{largura_janela}x{altura_janela}+{int(largura_tela * 0.125)}+{int(altura_tela * 0.125)}")
janela._set_appearance_mode('dark')
janela.title("IMU Data Viewer")

# Inicialização das variáveis BooleanVar (garantindo que existam antes de serem usadas em criar_barra_superior_e_botoes)
check_var1 = ctk.BooleanVar(value=True)
check_var2 = ctk.BooleanVar(value=True)
check_var3 = ctk.BooleanVar(value=True)
random_data = ctk.BooleanVar(value=False)

caminho_fundo = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\fundo.png'
try:
    imagem_fundo_pil = Image.open(caminho_fundo).resize((largura_janela, altura_janela), Image.LANCZOS)
    imagem_fundo = ctk.CTkImage(light_image=imagem_fundo_pil, dark_image=imagem_fundo_pil, size=(largura_janela, altura_janela))
    label_fundo = ctk.CTkLabel(janela, image=imagem_fundo, text="", width=largura_janela, height=altura_janela)
    label_fundo.place(x=0, y=0)
except FileNotFoundError:
    print(f"Aviso: Imagem de fundo não encontrada em {caminho_fundo}. O fundo será a cor padrão.")
    label_fundo = None
except Exception as e:
    print(f"Erro ao carregar imagem de fundo: {e}")
    label_fundo = None

barra_lateral = ctk.CTkFrame(janela, fg_color="transparent", corner_radius=20)
barra_lateral.pack(side="left", padx=10, pady=10, fill="y")

barra_lateral_superior = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_superior.pack(fill="both", pady=(10, 5), expand=True)

barra_lateral_central = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_central.pack(fill="both", pady=5, expand=True)

barra_lateral_inferior = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_inferior.pack(fill="both", pady=(5, 10), expand=True)

imagens_carregadas = []

def adicionar_botao_barra_lateral(caminho_imagem, texto, comando, tooltip_text=""):
    try:
        imagem_pil = Image.open(caminho_imagem)
        imagem = ctk.CTkImage(light_image=imagem_pil, dark_image=imagem_pil, size=(30, 30))
        imagens_carregadas.append(imagem)

        botao = ctk.CTkButton(barra_lateral_central, image=imagem, text=texto,
                               fg_color="transparent", corner_radius=15, command=comando,
                               compound="left", anchor="w",
                               font=ctk.CTkFont(size=14, weight="bold"))
        botao.pack(fill='x', pady=5, padx=5)

        if tooltip_text:
            botao.bind("<Enter>", lambda event, btn_widget=botao, text=tooltip_text: mostrar_tooltip(event, text))
            botao.bind("<Leave>", ocultar_tooltip)

    except Exception as e:
        print(f"Erro ao carregar {caminho_imagem}: {e}")

# Adicionar o main_content_frame ao lado da barra lateral
main_content_frame = ctk.CTkFrame(janela, fg_color="transparent")
main_content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)


adicionar_botao_barra_lateral(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão", Conexao, "Configura a conexão Serial ou Wi-Fi")
adicionar_botao_barra_lateral(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Grafico.png', "Gráficos de Linha", Graficos, "Exibe os gráficos de Linha (Pitch, Raw e Yaw)")
adicionar_botao_barra_lateral(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Gráficos Polares", GraficosPolares, "Exibe os gráficos polares de orientação")
adicionar_botao_barra_lateral(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Tempo de Leitura", GraficoTempoLeitura, "Exibe o tempo entre cada leitura de dados")
adicionar_botao_barra_lateral(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Grafico.png', "Fechar", fechar_programa, "Fecha o programa")

janela.bind('<Escape>', lambda event: fechar_programa())
janela.bind('<F11>', lambda event: janela.attributes('-fullscreen', not janela.attributes('-fullscreen')))

# Inicializa a tela de conexão ao iniciar a aplicação no main_content_frame
Conexao()

janela.mainloop()