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

###### SERVIDOR

ESP_IP = "192.168.0.112"  # Substitua pelo IP do ESP32
ESP_PORT = 12345

global dados
# As listas de dados serão preenchidas com os valores recebidos
x_data, y_data = [], []
x_data2, y_data2 = [], []
x_data3, y_data3 = [], []

# Variáveis globais para os objetos dos gráficos
ultima_linha = None
canvas = None
client = None
ax = None
ax2 = None
ax3 = None
line1 = None
line2 = None
line3 = None
ani1 = None
ani2 = None
ani3 = None
serial_conn = None
widgets_criados = []
label_dados = None

# Variáveis globais para os objetos dos gráficos polares
ax_polar1 = None
ax_polar2 = None
ax_polar3 = None
canvas_polar = None
ani_polar = None
fig_polar = None
frame_polar_pitch = None
frame_polar_raw = None
frame_polar_yaw = None

# NOVAS VARIÁVEIS GLOBAIS PARA AS BARRAS POLARES
bar_polar1_patch = None
bar_polar2_patch = None
bar_polar3_patch = None

# Nova variável global para a figura dos gráficos cartesianos
fig_pitch = None
fig_raw = None
fig_yaw = None

global modo_conexao
modo_conexao = None # Pode ser 'serial', 'wifi', ou None


def fechar_programa():
    janela.destroy()

def sair_tela_cheia(event):
    janela.attributes('-fullscreen', False)

def BarraSuperior():
    global barra_superior
    # Criar barra superior
    barra_superior = ctk.CTkFrame(janela, width=100, height=30)
    barra_superior.pack(side="top", fill="x")
    widgets_criados.append(barra_superior)

def criar_botoes_secundarios():
    global botao_salvar, botao_resetar, widgets_criados, random_data
    global check_var1,check_var2,check_var3

    # Criar barra checklist transparente
    barra_checklist = ctk.CTkFrame(barra_superior, width=100, height=30, fg_color="transparent")
    barra_checklist.pack(side="bottom", fill="x")
    widgets_criados.append(barra_checklist)

    # As variáveis check_var1, check_var2, check_var3 e random_data
    # são inicializadas globalmente após a criação da janela principal (janela).
    # Portanto, não precisamos mais dos 'if check_varX is None:' aqui.

    check_button1 = ctk.CTkCheckBox(barra_checklist, text="Salvar Pitch", variable=check_var1, corner_radius=20, command=lambda: update_graph_display())
    check_button1.pack(side="left", fill="x", expand=True)
    widgets_criados.append(check_button1)

    check_button2 = ctk.CTkCheckBox(barra_checklist, text="Salvar Raw", variable=check_var2, corner_radius=20, command=lambda: update_graph_display())
    check_button2.pack(side="left", fill="x", expand=True)
    widgets_criados.append(check_button2)

    check_button3 = ctk.CTkCheckBox(barra_checklist, text="Salvar Yaw", variable=check_var3, corner_radius=20, command=lambda: update_graph_display())
    check_button3.pack(side="left", fill="x", expand=True)
    widgets_criados.append(check_button3)

    # Botão para salvar os dados
    botao_salvar = ctk.CTkButton(barra_superior, text="Salvar Dados", command=lambda: salvar_dados(x_data, y_data, x_data2, y_data2, x_data3, y_data3), corner_radius=20)
    botao_salvar.pack(side="top", pady=5, fill="both")
    widgets_criados.append(botao_salvar)

    # Botão para resetar os dados
    botao_resetar = ctk.CTkButton(barra_superior, text="Resetar Dados", command=resetar_dados, corner_radius=20)
    botao_resetar.pack(side="top", pady=5, fill="both")
    widgets_criados.append(botao_resetar)

    # AQUI ESTÁ A CORREÇÃO: Adicionando o 'command' ao checkbox de dados aleatórios
    BtRandomData = ctk.CTkCheckBox(barra_superior, text="Usar Dados Aleatórios", variable=random_data, corner_radius=20, command=lambda: update_graph_display())
    BtRandomData.pack(side="top", pady=5, fill="both")  # Expand para ocupar espaço e centralizar
    widgets_criados.append(BtRandomData)
    
def resetar_dados():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    # Limpa as listas
    x_data.clear()
    x_data2.clear()
    x_data3.clear()
    y_data.clear()
    y_data2.clear()
    y_data3.clear()

    # Reinicia os objetos dos gráficos lineares (se existirem)
    if ax:
        ax.relim()
        ax.autoscale_view()
    if ax2:
        ax2.relim()
        ax2.autoscale_view()
    if ax3:
        ax3.relim()
        ax3.autoscale_view()

    # Reinicia os objetos dos gráficos polares (se existirem)
    # APENAS LIMPA OS DADOS, NÃO O EIXO INTEIRO SE FOR PARA MANTER OS TÍTULOS E CONFIGS
    if bar_polar1_patch: # Se o patch existe
        bar_polar1_patch.set_x(0 - bar_polar1_patch.get_width()/2) # Reset position to 0 angle
    if bar_polar2_patch:
        bar_polar2_patch.set_x(0 - bar_polar2_patch.get_width()/2)
    if bar_polar3_patch:
        bar_polar3_patch.set_x(0 - bar_polar3_patch.get_width()/2)

    # Redesenha os canvases
    # Estas variáveis podem não existir se os gráficos não foram criados (e.g., nenhum checkbox marcado)
    if 'canvas_pitch' in globals() and canvas_pitch: # Verifica se a variável existe e não é None
        canvas_pitch.draw_idle()
    if 'canvas_raw' in globals() and canvas_raw:
        canvas_raw.draw_idle()
    if 'canvas_yaw' in globals() and canvas_yaw:
        canvas_yaw.draw_idle()
    if canvas_polar:
        canvas_polar.draw_idle()


def salvar_dados(x_data_to_save, y_data_to_save, x_data2_to_save, y_data2_to_save, x_data3_to_save, y_data3_to_save):
    # Abre janela para selecionar o nome do arquivo
    nome_arquivo = filedialog.asksaveasfilename(
        title="Escolha o nome do arquivo",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if nome_arquivo:  # Verifica se o nome do arquivo foi definido
        with open(nome_arquivo, 'w') as f:
            if check_var1.get():  # Se a checkbox do Pitch está ativada
                f.write("\nGráfico Pitch:\n")
                for x, y in zip(x_data_to_save, y_data_to_save):
                    f.write(f"{x}\t{y}\n")

            if check_var2.get():  # Se a checkbox do Raw está ativada
                f.write("\nGráfico Raw:\n")
                for x, y in zip(x_data2_to_save, y_data2_to_save):
                    f.write(f"{x}\t{y}\n")

            if check_var3.get():  # Se a checkbox do Yaw está ativada
                f.write("\nGráfico Yaw:\n")
                for x, y in zip(x_data3_to_save, y_data3_to_save):
                    f.write(f"{x}\t{y}\n")

        print(f"Arquivo salvo em: {nome_arquivo}")

    else:
        print("Nenhum nome de arquivo foi escolhido.")

def adquirir_dados_continuamente():
    global serial_conn, ultima_linha, client, modo_conexao
    valores = []

    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
        # print(f"Dados aleatórios: {valores}") # Para depuração
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
                if len(numeros) == 3:
                    valores = numeros
        except Exception as e:
            print(f"Erro ao ler dados do Wi-Fi: {e}")
            client = None # Reset client if there's an error
    return valores

def atualizar_grafico():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3

    valores = adquirir_dados_continuamente()

    # Se os dados forem válidos, armazena nas variáveis globais
    if len(valores) == 3:
        # Adiciona dados apenas se um checkbox de gráfico estiver ativo para o modo atual
        # A lógica de checagem do modo atual e dos checkboxes está correta
        if hasattr(janela, '_current_graph_mode'):
            if (janela._current_graph_mode == 'linear' and (check_var1.get() or check_var2.get() or check_var3.get())) or \
               (janela._current_graph_mode == 'polar' and (check_var1.get() or check_var2.get() or check_var3.get())):

                x_data.append(len(x_data))  # Simula tempo
                y_data.append(valores[0])  # Pitch
                x_data2.append(len(x_data2))
                y_data2.append(valores[1])  # Raw
                x_data3.append(len(x_data3))
                y_data3.append(valores[2])  # Yaw


def update_graph_display():
    # This function will be called when a checkbox is toggled
    # It will clear and recreate the graphs based on the current checkbox states.
    if hasattr(janela, '_current_graph_mode') and janela._current_graph_mode == 'linear':
        Graficos()
    elif hasattr(janela, '_current_graph_mode') and janela._current_graph_mode == 'polar':
        GraficosPolares()


def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw
    global canvas_polar, ani_polar, fig_polar, ax_polar1, ax_polar2, ax_polar3, frame_polar_pitch, frame_polar_raw, frame_polar_yaw
    global fig_pitch, fig_raw, fig_yaw # Variáveis para as figuras cartesianas

    janela._current_graph_mode = 'linear' # Set current mode

    # Reinicia os dados
    x_data.clear() # Use clear()
    y_data.clear()
    x_data2.clear()
    y_data2.clear()
    x_data3.clear()
    y_data3.clear()

    # Para todas as animações existentes e fecha as figuras do Matplotlib
    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    # Close figures only if they exist
    if fig_pitch: plt.close(fig_pitch); fig_pitch = None
    if fig_raw: plt.close(fig_raw); fig_raw = None
    if fig_yaw: plt.close(fig_yaw); fig_yaw = None

    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if fig_polar: plt.close(fig_polar); fig_polar = None


    # Remove todos os widgets da área principal (exceto a barra lateral e o fundo)
    # Primeiro, destrua a barra superior para recriá-la com os botões corretos
    if 'barra_superior' in globals() and barra_superior.winfo_exists():
        barra_superior.destroy()

    # Destrói todos os widgets criados dinamicamente
    for widget in widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    widgets_criados.clear() # Limpa a lista após destruir

    # Recria a barra superior e os botões de seleção de gráfico/salvar
    BarraSuperior()
    criar_botoes_secundarios()

    # Create figures and axes only if not already created or if they were closed
    # This prevents recreating them on every update_graph_display call
    if check_var1.get() and fig_pitch is None: # Only create if checkbox is checked AND figure doesn't exist
        frame_pitch = ctk.CTkFrame(master=janela)
        frame_pitch.pack(fill="both", expand=True, pady=10, padx=10)
        frame_pitch.pack_propagate(False)
        fig_pitch = Figure(figsize=(12, 2), dpi=100)
        ax = fig_pitch.add_subplot(111)
        ax.set_xlabel("Tempo[ms]")
        ax.set_ylabel("Angulo[graus]")
        ax.grid(True)
        ax.set_title("Pitch")
        canvas_pitch = FigureCanvasTkAgg(fig_pitch, master=frame_pitch)
        canvas_pitch.get_tk_widget().pack(fill="both", expand=True)
        line1, = ax.plot([], [], 'r-', label="Pitch")
        widgets_criados.append(frame_pitch) # Add to widgets_criados
    elif not check_var1.get() and fig_pitch: # If checkbox unchecked and figure exists, destroy it
        plt.close(fig_pitch)
        fig_pitch = None
        if frame_pitch.winfo_exists():
            frame_pitch.destroy()
        if frame_pitch in widgets_criados:
            widgets_criados.remove(frame_pitch)


    if check_var2.get() and fig_raw is None:
        frame_raw = ctk.CTkFrame(master=janela)
        frame_raw.pack(fill="both", expand=True, pady=10, padx=10)
        frame_raw.pack_propagate(False)
        fig_raw = Figure(figsize=(12, 2), dpi=100)
        ax2 = fig_raw.add_subplot(111)
        ax2.set_xlabel("Tempo[ms]")
        ax2.set_ylabel("Angulo[graus]")
        ax2.grid(True)
        ax2.set_title("Raw")
        canvas_raw = FigureCanvasTkAgg(fig_raw, master=frame_raw)
        canvas_raw.get_tk_widget().pack(fill="both", expand=True)
        line2, = ax2.plot([], [], 'g-', label="Raw")
        widgets_criados.append(frame_raw)
    elif not check_var2.get() and fig_raw:
        plt.close(fig_raw)
        fig_raw = None
        if frame_raw.winfo_exists():
            frame_raw.destroy()
        if frame_raw in widgets_criados:
            widgets_criados.remove(frame_raw)

    if check_var3.get() and fig_yaw is None:
        frame_yaw = ctk.CTkFrame(master=janela)
        frame_yaw.pack(fill="both", expand=True, pady=10, padx=10)
        frame_yaw.pack_propagate(False)
        fig_yaw = Figure(figsize=(12, 2), dpi=100)
        ax3 = fig_yaw.add_subplot(111)
        ax3.set_xlabel("Tempo[ms]")
        ax3.set_ylabel("Angulo[graus]")
        ax3.grid(True)
        ax3.set_title("Yaw")
        canvas_yaw = FigureCanvasTkAgg(fig_yaw, master=frame_yaw)
        canvas_yaw.get_tk_widget().pack(fill="both", expand=True)
        line3, = ax3.plot([], [], 'b-', label="Yaw")
        widgets_criados.append(frame_yaw)
    elif not check_var3.get() and fig_yaw:
        plt.close(fig_yaw)
        fig_yaw = None
        if frame_yaw.winfo_exists():
            frame_yaw.destroy()
        if frame_yaw in widgets_criados:
            widgets_criados.remove(frame_yaw)

    def atualizar_cartesianos(i):
        atualizar_grafico() # This populates x_data, y_data etc.
        updated_artists = []

        if check_var1.get() and line1:
            line1.set_data(x_data, y_data)
            ax.relim()
            ax.autoscale_view()
            updated_artists.append(line1)
            # You might need to return the canvas or specific artists for blitting
            # If blit=True is used, the function must return an iterable of all artists that were modified or created.
            # In simple cases, just updating the line data and redrawing the canvas is sufficient without blit=True
            # or if blit=True, make sure to return the line object itself.
            canvas_pitch.draw_idle()

        if check_var2.get() and line2:
            line2.set_data(x_data2, y_data2)
            ax2.relim()
            ax2.autoscale_view()
            updated_artists.append(line2)
            canvas_raw.draw_idle()

        if check_var3.get() and line3:
            line3.set_data(x_data3, y_data3)
            ax3.relim()
            ax3.autoscale_view()
            updated_artists.append(line3)
            canvas_yaw.draw_idle()
        
        # When blit=True, you must return all artists that were modified.
        # However, for multiple independent animations like this, it's often simpler
        # to just call draw_idle on each canvas, which handles redrawing more globally.
        # If you truly want to use blit=True for all, you'd need a single FuncAnimation
        # that manages all lines and returns all of them.
        # For now, let's keep separate animations and rely on draw_idle.
        return updated_artists if ani1 or ani2 or ani3 else [] # Return empty if no animations active

    # Only create animations if the corresponding graph is selected
    # Using separate animations for each graph.
    if check_var1.get() and 'fig_pitch' in globals() and fig_pitch:
        if ani1: ani1.event_source.stop() # Stop previous animation if exists
        ani1 = FuncAnimation(fig_pitch, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False) # Set blit to False for simpler updates
        canvas_pitch.draw_idle()
    if check_var2.get() and 'fig_raw' in globals() and fig_raw:
        if ani2: ani2.event_source.stop()
        ani2 = FuncAnimation(fig_raw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
        canvas_raw.draw_idle()
    if check_var3.get() and 'fig_yaw' in globals() and fig_yaw:
        if ani3: ani3.event_source.stop()
        ani3 = FuncAnimation(fig_yaw, atualizar_cartesianos, interval=100, blit=False, cache_frame_data=False)
        canvas_yaw.draw_idle()


def GraficosPolares():
    global canvas_polar, widgets_criados, ani_polar, fig_polar
    global ax_polar1, ax_polar2, ax_polar3
    global frame_polar_pitch, frame_polar_raw, frame_polar_yaw
    global ani1, ani2, ani3, fig_pitch, fig_raw, fig_yaw
    global bar_polar1_patch, bar_polar2_patch, bar_polar3_patch # Global for the bar patches

    janela._current_graph_mode = 'polar'

    # Reinicia os dados
    x_data.clear() # Use clear()
    y_data.clear()
    x_data2.clear()
    y_data2.clear()
    x_data3.clear()
    y_data3.clear()

    # Stop existing animations and close figures
    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if fig_pitch: plt.close(fig_pitch); fig_pitch = None
    if fig_raw: plt.close(fig_raw); fig_raw = None
    if fig_yaw: plt.close(fig_yaw); fig_yaw = None

    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if fig_polar: plt.close(fig_polar); fig_polar = None

    # Remove all widgets from the main area (except the sidebar and background)
    if 'barra_superior' in globals() and barra_superior.winfo_exists():
        barra_superior.destroy()

    for widget in widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    widgets_criados.clear()

    # Recreate the top bar and graph selection/save buttons
    BarraSuperior()
    criar_botoes_secundarios()

    num_active_polar_graphs = check_var1.get() + check_var2.get() + check_var3.get()

    if num_active_polar_graphs > 0:
        parent_frame_polar = ctk.CTkFrame(master=janela, fg_color="transparent")
        parent_frame_polar.pack(fill="both", expand=True, pady=10, padx=10)
        widgets_criados.append(parent_frame_polar)

        # Ajuste o figsize para acomodar gráficos lado a lado, pode precisar de mais largura
        fig_polar = Figure(figsize=(4 * num_active_polar_graphs, 6), dpi=100) # Largura ajustável
        
        current_subplot = 1
        bar_width_rad = 0.2 # Define a largura da barra em radianos (ajuste conforme necessário)

        if check_var1.get():
            ax_polar1 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar1.set_title("Polar Pitch")
            ax_polar1.set_theta_direction(1) # Theta direction for consistent display
            # Crie a barra inicial e armazene a referência ao seu patch de retângulo
            bar_polar1_patch = ax_polar1.bar([0], [1], width=bar_width_rad, color='red', align='center')[0]
            current_subplot += 1

        if check_var2.get():
            ax_polar2 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar2.set_title("Polar Raw")
            ax_polar2.set_theta_direction(1)
            bar_polar2_patch = ax_polar2.bar([0], [1], width=bar_width_rad, color='green', align='center')[0]
            current_subplot += 1

        if check_var3.get():
            ax_polar3 = fig_polar.add_subplot(1, num_active_polar_graphs, current_subplot, projection='polar')
            ax_polar3.set_title("Polar Yaw")
            ax_polar3.set_theta_direction(1)
            bar_polar3_patch = ax_polar3.bar([0], [1], width=bar_width_rad, color='blue', align='center')[0]
            current_subplot += 1

        fig_polar.subplots_adjust(wspace=0.4, hspace=0.4) # Ajuste o espaçamento horizontal e vertical

        canvas_polar = FigureCanvasTkAgg(fig_polar, master=parent_frame_polar)
        canvas_widget = canvas_polar.get_tk_widget()
        canvas_widget.pack(anchor=tk.CENTER, expand=True, fill='both')
        widgets_criados.append(canvas_widget)

        # Animation function
        def atualizar_polares(i):
            atualizar_grafico() # Isso irá popular as listas y_data com os valores (aleatórios ou não)

            updated_artists = [] # Lista para retornar os artistas atualizados

            # Atualiza a barra do Pitch
            if check_var1.get() and len(y_data) > 0 and bar_polar1_patch:
                valor1 = (y_data[-1] * 3.14159) / 180
                # Move a barra para a nova posição angular
                # A 'x' do patch do retângulo é a borda esquerda da barra.
                # Como 'align=center' foi usado, o valor do ângulo 'valor1' é o centro da barra.
                # Então, o início da barra é 'valor1 - largura/2'.
                bar_polar1_patch.set_x(valor1 - bar_width_rad/2)
                updated_artists.append(bar_polar1_patch)

            # Atualiza a barra do Raw
            if check_var2.get() and len(y_data2) > 0 and bar_polar2_patch:
                valor2 = (y_data2[-1] * 3.14159) / 180
                bar_polar2_patch.set_x(valor2 - bar_width_rad/2)
                updated_artists.append(bar_polar2_patch)

            # Atualiza a barra do Yaw
            if check_var3.get() and len(y_data3) > 0 and bar_polar3_patch:
                valor3 = (y_data3[-1] * 3.14159) / 180
                bar_polar3_patch.set_x(valor3 - bar_width_rad/2)
                updated_artists.append(bar_polar3_patch)

            # Retorne APENAS os artistas que foram modificados.
            # Isso é crucial para o desempenho, especialmente se você usar blit=True.
            return updated_artists


        # Intervalo da animação ajustado para 50ms para maior fluidez
        ani_polar = FuncAnimation(fig_polar, atualizar_polares, interval=50, blit=True, cache_frame_data=False)
        canvas_polar.draw_idle()
    else:
        canvas_polar = None
def listar_portas_com():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def Conexao():
    global widgets_criados, canvas, serial_conn, client, modo_conexao
    global ani1, ani2, ani3, ani_polar, fig_polar # Need to stop animations when changing mode
    global fig_pitch, fig_raw, fig_yaw # Add this to close linear figures

    # Para todas as animações existentes e fecha as figuras do Matplotlib
    if ani1: ani1.event_source.stop(); ani1 = None
    if ani2: ani2.event_source.stop(); ani2 = None
    if ani3: ani3.event_source.stop(); ani3 = None
    if fig_pitch: plt.close(fig_pitch); fig_pitch = None
    if fig_raw: plt.close(fig_raw); fig_raw = None
    if fig_yaw: plt.close(fig_yaw); fig_yaw = None

    if ani_polar: ani_polar.event_source.stop(); ani_polar = None
    if fig_polar: plt.close(fig_polar); fig_polar = None

    # Remove todos os widgets da área principal (exceto a barra lateral e o fundo)
    if 'barra_superior' in globals() and barra_superior.winfo_exists():
        barra_superior.destroy()

    for widget in widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    widgets_criados.clear()


    # Criar barra superior (para manter a interface consistente)
    BarraSuperior()

    # Cria um frame centralizado
    frame_central = ctk.CTkFrame(janela, fg_color="transparent")
    frame_central.place(relx=0.5, rely=0.5, anchor="center")
    widgets_criados.append(frame_central)

    label = ctk.CTkLabel(frame_central, text="Escolha o método de conexão:")
    label.pack(pady=10)

    texto_status = ctk.CTkLabel(frame_central, text="Status da Conexão: Desconectado")
    texto_status.pack(pady=10)

    label_dados = ctk.CTkLabel(frame_central, text="Pronto para receber dados nos gráficos.")
    label_dados.pack(pady=10)

    # Adicionar Dropdown para seleção da Porta COM
    available_ports = listar_portas_com()
    if not available_ports:
        available_ports = ["Nenhuma porta COM encontrada"] # Mensagem caso não encontre portas

    com_port_label = ctk.CTkLabel(frame_central, text="Selecione a Porta COM:")
    com_port_label.pack(pady=5)
    com_port_combobox = ctk.CTkComboBox(frame_central, values=available_ports)
    if available_ports:
        com_port_combobox.set(available_ports[0]) # Seleciona a primeira porta por padrão
    com_port_combobox.pack(pady=5)
    widgets_criados.append(com_port_label)
    widgets_criados.append(com_port_combobox)

    # Adicionar Dropdown para Baud Rate
    baud_rates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
    baud_rate_label = ctk.CTkLabel(frame_central, text="Selecione o Baud Rate:")
    baud_rate_label.pack(pady=5)
    baud_rate_combobox = ctk.CTkComboBox(frame_central, values=baud_rates)
    baud_rate_combobox.set("115200") # Valor padrão
    baud_rate_combobox.pack(pady=5)
    widgets_criados.append(baud_rate_label)
    widgets_criados.append(baud_rate_combobox)


    # Função para conectar via Serial
    def conectar_serial():
        global serial_conn, modo_conexao
        porta_selecionada = com_port_combobox.get()
        selected_baud_rate = int(baud_rate_combobox.get())
        if "Nenhuma porta COM encontrada" in porta_selecionada:
            texto_status.configure(text="Erro: Nenhuma porta COM válida selecionada.")
            modo_conexao = None
            return

        try:
            if serial_conn and serial_conn.is_open:
                serial_conn.close()
            serial_conn = serial.Serial(porta_selecionada, selected_baud_rate, timeout=0.01)
            texto_status.configure(text=f"Conectado à {porta_selecionada} com {selected_baud_rate} Baud.")
            modo_conexao = 'serial'
            label_dados.configure(text="Conexão Serial estabelecida. Dados serão lidos nos gráficos.")
        except Exception as e:
            texto_status.configure(text=f"Erro na conexão Serial: {e}")
            modo_conexao = None
            label_dados.configure(text="Falha ao conectar via Serial.")


    # Função para conectar via Wi-Fi
    def conectar_wifi():
        global client, modo_conexao
        try:
            if client:
                client.close()
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ESP_IP, ESP_PORT))
            texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi!")
            modo_conexao = 'wifi'
            label_dados.configure(text="Conexão Wi-Fi estabelecida. Dados serão lidos nos gráficos.")
        except Exception as e:
            print(f"Erro na conexão Wi-Fi: {e}")
            client = None
            label_dados.configure(text="Falha ao conectar via Wi-Fi.")

    # Botão para conexão via Serial
    botao_serial = ctk.CTkButton(frame_central, text="Conectar via Porta COM", command=conectar_serial)
    botao_serial.pack(pady=10)

    # Botão para conexão via Wi-Fi (TCP/IP)
    botao_wifi = ctk.CTkButton(frame_central, text="Conectar via Wi-Fi", command=conectar_wifi)
    botao_wifi.pack(pady=10)

# Função para exibir o tooltip
def mostrar_tooltip(event):
    tooltip = tk.Label(janela, text="Descrição do botão", bg="yellow", fg="black")
    tooltip.place(x=event.x_root - janela.winfo_rootx(), y=event.y_root - janela.winfo_roott())

# Função para remover o tooltip
def ocultar_tooltip(event):
    if hasattr(event.widget, "tooltip"):
        event.widget.tooltip.destroy()

# Configurar CustomTkinter
#ctk.set_appearance_mode("dark")
#ctk.set_default_color_theme("blue")

# Criar janela principal ocupando 3/4 da tela
janela = ctk.CTk()
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
largura_janela = int(largura_tela * 0.75)
altura_janela = int(altura_tela * 0.75)
janela.geometry(f"{largura_janela}x{altura_janela}+{int(largura_tela * 0.125)}+{int(altura_tela * 0.125)}")
janela._set_appearance_mode('dark')

# -------------------------------------------------------------
# CORREÇÃO: Inicialização de ctk.BooleanVar() após a criação da janela
# Mova as inicializações de random_data, check_var1, check_var2, check_var3 para AQUI.
random_data = ctk.BooleanVar(master=janela)
check_var1 = ctk.BooleanVar(master=janela)
check_var2 = ctk.BooleanVar(master=janela)
check_var3 = ctk.BooleanVar(master=janela)
# -------------------------------------------------------------


# 🔹 Carregar imagem de fundo
caminho_fundo = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\fundo.png'
imagem_fundo_pil = Image.open(caminho_fundo).resize((largura_janela, altura_janela))
imagem_fundo = ctk.CTkImage(light_image=imagem_fundo_pil, dark_image=imagem_fundo_pil, size=(largura_janela, altura_janela))

# Criar Label para exibir a imagem de fundo
label_fundo = ctk.CTkLabel(janela, image=imagem_fundo, text="", width=largura_janela, height=altura_janela)
label_fundo.place(x=0, y=0)

# Criar barra lateral com bordas arredondadas
barra_lateral = ctk.CTkFrame(janela, fg_color=None, corner_radius=40)
barra_lateral.pack(side="left", padx=10, fill="y")  # Expande para preencher melhor

# Criar frames dentro da barra lateral com espaçamento uniforme
barra_lateral_superior = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_superior.pack(fill="both", pady=10,expand="true")  # Posição superior

barra_lateral_central = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_central.pack(fill="both", pady=10,expand="true")  # Posição central (para os botões)

barra_lateral_inferior = ctk.CTkFrame(barra_lateral, fg_color="transparent")
barra_lateral_inferior.pack(fill="both", pady=10,expand="true")  # Posição inferior

# Lista para armazenar imagens e evitar erro do garbage collector
imagens_carregadas = []

# Função para adicionar botões com ícones no frame central
def adicionar_botao(caminho_imagem, texto, comando):
    try:
        imagem_pil = Image.open(caminho_imagem)
        imagem = ctk.CTkImage(light_image=imagem_pil, dark_image=imagem_pil, size=(40, 40))
        imagens_carregadas.append(imagem)

        botao = ctk.CTkButton(barra_lateral_central, image=imagem, text=texto,
                              fg_color="transparent", corner_radius=20, command=comando)
        botao.pack(anchor='center',fill = 'x')  # Centraliza dentro do frame central

    except Exception as e:
        print(f"Erro ao carregar {caminho_imagem}: {e}")

# Adicionando botões com as funções corretas
adicionar_botao(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\wifi.png', "Conexão Serial", Conexao)
adicionar_botao(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\chart.png', "Gráficos", Graficos)
adicionar_botao(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\radar.png', "Graficos Polares", GraficosPolares)
adicionar_botao(r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\close.png', "Fechar", fechar_programa)


# 🔹 Tecla ESC para fechar programa
janela.bind('<Escape>', lambda event: janela.quit())

janela.mainloop()