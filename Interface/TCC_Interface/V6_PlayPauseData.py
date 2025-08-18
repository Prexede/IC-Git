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
from PIL import Image

###### SERVIDOR
ESP_IP = "192.168.0.112"  # Substitua pelo IP do ESP32
ESP_PORT = 12345

# Variáveis de dados
global dados
x_data, y_data = [], []
x_data2, y_data2 = [], []
x_data3 = []
y_data3 = []

# Variáveis de widgets e gráficos
ultima_linha = None
canvas = None
client = None
ax, ax2, ax3 = None, None, None
line1, line2, line3 = None, None, None
ani1, ani2, ani3 = None, None, None
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

# Variáveis de estado
global modo_conexao
modo_conexao = None # Pode ser 'serial', 'wifi', ou None
global paused_acquisition # Novo: Variável para controlar a pausa da aquisição
paused_acquisition = False

# Frame para os controles laterais dos gráficos
controles_graficos_frame = None

# Variável global para o frame do título da aba principal (a barra de destaque)
main_title_frame = None

def fechar_programa():
    janela.destroy()

def sair_tela_cheia(event):
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

def criar_controles_laterais(parent):
    """Cria o frame com os controles dos gráficos na barra lateral."""
    global check_var1, check_var2, check_var3, random_data

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
    BtRandomData = ctk.CTkCheckBox(frame, text="Dados Aleatórios", variable=random_data, command=update_graph_display)
    BtRandomData.pack(pady=5, padx=20, anchor="w")

    # Botões de ação
    botao_salvar = ctk.CTkButton(frame, text="Salvar Dados", command=lambda: salvar_dados(x_data, y_data, x_data2, y_data2, x_data3, y_data3))
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
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    x_data.clear(); y_data.clear()
    x_data2.clear(); y_data2.clear()
    x_data3.clear(); y_data3.clear()

    if ax: ax.relim(); ax.autoscale_view()
    if ax2: ax2.relim(); ax2.autoscale_view()
    if ax3: ax3.relim(); ax3.autoscale_view()

    if bar_polar1_patch: bar_polar1_patch.set_x(0 - bar_polar1_patch.get_width()/2)
    if bar_polar2_patch: bar_polar2_patch.set_x(0 - bar_polar2_patch.get_width()/2)
    if bar_polar3_patch: bar_polar3_patch.set_x(0 - bar_polar3_patch.get_width()/2)

    if 'canvas_pitch' in globals() and canvas_pitch: canvas_pitch.draw_idle()
    if 'canvas_raw' in globals() and canvas_raw: canvas_raw.draw_idle()
    if 'canvas_yaw' in globals() and canvas_yaw: canvas_yaw.draw_idle()
    if canvas_polar: canvas_polar.draw_idle()

def salvar_dados(x_data_to_save, y_data_to_save, x_data2_to_save, y_data2_to_save, x_data3_to_save, y_data3_to_save):
    nome_arquivo = filedialog.asksaveasfilename(
        title="Salvar Dados do Gráfico",
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if nome_arquivo:
        with open(nome_arquivo, 'w') as f:
            if check_var1.get():
                f.write("\nGráfico Pitch:\n")
                for x, y in zip(x_data_to_save, y_data_to_save): f.write(f"{x}\t{y}\n")
            if check_var2.get():
                f.write("\nGráfico Raw:\n")
                for x, y in zip(x_data2_to_save, y_data2_to_save): f.write(f"{x}\t{y}\n")
            if check_var3.get():
                f.write("\nGráfico Yaw:\n")
                for x, y in zip(x_data3_to_save, y_data3_to_save): f.write(f"{x}\t{y}\n")
        print(f"Arquivo salvo em: {nome_arquivo}")
    else:
        print("Operação de salvamento cancelada.")

def adquirir_dados_continuamente():
    global serial_conn, ultima_linha, client, modo_conexao, paused_acquisition
    valores = []
    if paused_acquisition: # Se a aquisição estiver pausada, retorne imediatamente
        return []
    
    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
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

def atualizar_grafico():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    valores = adquirir_dados_continuamente()
    if len(valores) == 3:
        if hasattr(janela, '_current_graph_mode'):
            if (janela._current_graph_mode == 'linear' and (check_var1.get() or check_var2.get() or check_var3.get())) or \
               (janela._current_graph_mode == 'polar' and (check_var1.get() or check_var2.get() or check_var3.get())):
                x_data.append(len(x_data))
                y_data.append(valores[0])
                x_data2.append(len(x_data2))
                y_data2.append(valores[1])
                x_data3.append(len(x_data3))
                y_data3.append(valores[2])

def update_graph_display():
    if hasattr(janela, '_current_graph_mode') and janela._current_graph_mode == 'linear':
        Graficos()
    elif hasattr(janela, '_current_graph_mode') and janela._current_graph_mode == 'polar':
        GraficosPolares()

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
    global ani1, ani2, ani3, ani_polar, fig_polar, fig_pitch, fig_raw, fig_yaw
    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if fig_pitch: plt.close(fig_pitch); fig_pitch = None
    if fig_raw: plt.close(fig_raw); fig_raw = None
    if fig_yaw: plt.close(fig_yaw); fig_yaw = None
    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if fig_polar: plt.close(fig_polar); fig_polar = None

def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw, fig_pitch, fig_raw, fig_yaw

    janela._current_graph_mode = 'linear'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes()
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
        atualizar_grafico()
        updated_artists = []
        if check_var1.get() and line1:
            line1.set_data(x_data, y_data); ax.relim(); ax.autoscale_view()
            updated_artists.append(line1); canvas_pitch.draw_idle()
        if check_var2.get() and line2:
            line2.set_data(x_data2, y_data2); ax2.relim(); ax2.autoscale_view()
            updated_artists.append(line2); canvas_raw.draw_idle()
        if check_var3.get() and line3:
            line3.set_data(x_data3, y_data3); ax3.relim(); ax3.autoscale_view()
            updated_artists.append(line3); canvas_yaw.draw_idle()
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

    janela._current_graph_mode = 'polar'
    x_data.clear(); y_data.clear(); x_data2.clear(); y_data2.clear(); x_data3.clear(); y_data3.clear()
    parar_animacoes()
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
            bar_polar1_patch = ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
            current_subplot += 1
        if check_var2.get():
            ax_polar2 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar2.set_title("Polar Raw"); ax_polar2.set_theta_direction(1)
            bar_polar2_patch = ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
            current_subplot += 1
        if check_var3.get():
            ax_polar3 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar3.set_title("Polar Yaw"); ax_polar3.set_theta_direction(1)
            bar_polar3_patch = ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]
            current_subplot += 1

        fig_polar.subplots_adjust(wspace=0.4, hspace=0.4)
        canvas_polar = FigureCanvasTkAgg(fig_polar, master=parent_frame_polar)
        canvas_polar.get_tk_widget().pack(anchor=tk.CENTER, expand=True, fill='both')

        # Adicionar a barra de ferramentas do Matplotlib para os gráficos Polares
        toolbar_polar = NavigationToolbar2Tk(canvas_polar, parent_frame_polar)
        toolbar_polar.update()

        def atualizar_polares(i):
            atualizar_grafico()
            updated_artists = []
            if check_var1.get() and len(y_data) > 0 and bar_polar1_patch:
                valor1 = (y_data[-1] * 3.14159) / 180
                bar_polar1_patch.set_x(valor1 - bar_width_rad/2); updated_artists.append(bar_polar1_patch)
            if check_var2.get() and len(y_data2) > 0 and bar_polar2_patch:
                valor2 = (y_data2[-1] * 3.14159) / 180
                bar_polar2_patch.set_x(valor2 - bar_width_rad/2); updated_artists.append(bar_polar2_patch)
            if check_var3.get() and len(y_data3) > 0 and bar_polar3_patch:
                valor3 = (y_data3[-1] * 3.14159) / 180
                bar_polar3_patch.set_x(valor3 - bar_width_rad/2); updated_artists.append(bar_polar3_patch)
            return updated_artists

        ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, blit=True, cache_frame_data=False)
        canvas_polar.draw_idle()

def listar_portas_com():
    return [port.device for port in serial.tools.list_ports.comports()] or ["Nenhuma porta encontrada"]

def Conexao():
    global widgets_criados, serial_conn, client, modo_conexao
    parar_animacoes()
    limpar_area_principal()

    frame_central = ctk.CTkFrame(janela, fg_color="transparent")
    frame_central.place(relx=0.5, rely=0.5, anchor="center")
    widgets_criados.append(frame_central)

    # O título "Escolha o método de conexão:" já está dentro desta função,
    # ele será mantido como um label dentro do frame_central.
    # O novo título global na barra superior não interfere aqui.
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

    def conectar_wifi():
        global client, modo_conexao
        try:
            if client: client.close()
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ESP_IP, ESP_PORT))
            texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi!", text_color="lightgreen")
            modo_conexao = 'wifi'
        except Exception as e:
            print(f"Erro na conexão Wi-Fi: {e}")
            texto_status.configure(text=f"Erro na conexão Wi-Fi: {e}", text_color="red")
            client = None

    ctk.CTkButton(frame_central, text="Conectar via Wi-Fi", command=conectar_wifi).pack(pady=10)


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
    if nome_view == 'conexao':
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

    # Cria o frame para a barra de destaque do título
    # A cor fg_color padrão para customtkinter no modo dark é "gray20"
    main_title_frame = ctk.CTkFrame(janela, fg_color="gray20", height=50, corner_radius=0)
    main_title_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)) # Preenche a largura, com padding inferior
    
    # Cria e empacota o label do título DENTRO do novo frame
    title_label_inside_frame = ctk.CTkLabel(main_title_frame, text=title_text, font=ctk.CTkFont(size=20, weight="bold"))
    title_label_inside_frame.pack(expand=True) # Centraliza o texto dentro do frame

    widgets_criados.append(main_title_frame) # Adiciona o frame do título à lista para ser limpo ao trocar de tela

# --- Configuração da Janela Principal ---
janela = ctk.CTk()
largura_tela = janela.winfo_screenwidth(); altura_tela = janela.winfo_screenheight()
largura_janela = int(largura_tela * 0.8); altura_janela = int(altura_tela * 0.8)
pos_x = int((largura_tela - largura_janela) / 2)
pos_y = int((altura_tela - altura_janela) / 2)
janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
janela.title("PolarAdjust V3 - Refatorado")
janela._set_appearance_mode('dark')

# Inicialização das variáveis de controle (BooleanVar)
random_data = ctk.BooleanVar(master=janela)
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
imagens_carregadas = []
def adicionar_botao(parent, caminho_imagem, texto, comando):
    try:
        imagem_pil = Image.open(caminho_imagem)
        imagem = ctk.CTkImage(light_image=imagem_pil, dark_image=imagem_pil, size=(30, 30))
        imagens_carregadas.append(imagem)
        botao = ctk.CTkButton(parent, image=imagem, text=texto, command=comando,
                              fg_color="transparent", corner_radius=10, anchor="w",
                              font=ctk.CTkFont(size=13))
        botao.pack(fill='x', padx=10, pady=5)
    except Exception as e:
        print(f"Erro ao carregar ícone {caminho_imagem}: {e}")
        # Adiciona um botão de texto como fallback
        botao = ctk.CTkButton(parent, text=texto, command=comando, anchor="w")
        botao.pack(fill='x', padx=10, pady=5)

# Adicionando botões com as novas chamadas de função
adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão", lambda: mostrar_view('conexao'))
adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\chart.png', "Gráficos", lambda: mostrar_view('graficos'))
adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Gráficos Polares", lambda: mostrar_view('polares'))
adicionar_botao(frame_botoes_nav, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\close.png', "Fechar", fechar_programa)


janela.bind('<Escape>', lambda event: fechar_programa())

# Inicia mostrando a tela de conexão
mostrar_view('conexao')

janela.mainloop()