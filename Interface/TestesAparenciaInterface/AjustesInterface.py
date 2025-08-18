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

check_var1 = None
check_var2 = None
check_var3 = None

frame_pitch = None
frame_raw = None
frame_yaw = None



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
    global botao_salvar, botao_resetar, botao_dados_aleatorios, widgets_criados, random_data
    global check_var1,check_var2,check_var3
    
    # Criar barra checklist transparente
    barra_checklist = ctk.CTkFrame(barra_superior, width=100, height=30, fg_color="transparent")
    barra_checklist.pack(side="bottom", fill="x")
    widgets_criados.append(barra_checklist)

    # Inicializa as variáveis dentro da função sem recriar a cada chamada
    if check_var1 is None:
        check_var1 = ctk.BooleanVar()
    if check_var2 is None:
        check_var2 = ctk.BooleanVar()
    if check_var3 is None:
        check_var3 = ctk.BooleanVar()


    check_button1 = ctk.CTkCheckBox(barra_checklist, text="Salvar Pitch", variable=check_var1, corner_radius=20, command=Graficos)
    check_button1.pack(side="left", fill="x", expand=True)
    widgets_criados.append(check_button1)

    check_button2 = ctk.CTkCheckBox(barra_checklist, text="Salvar Raw", variable=check_var2, corner_radius=20, command=Graficos)
    check_button2.pack(side="left", fill="x", expand=True)
    widgets_criados.append(check_button2)

    check_button3 = ctk.CTkCheckBox(barra_checklist, text="Salvar Yaw", variable=check_var3, corner_radius=20, command=Graficos)
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

    random_data = ctk.BooleanVar()
    BtRandomData = ctk.CTkCheckBox(barra_superior, text="Usar Dados Aleatórios", variable=random_data, corner_radius=20)
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
    # Reinicia os objetos dos gráficos (opcional, se desejar limpar completamente)
    ax.relim()
    ax.autoscale_view()
    ax2.relim()
    ax2.autoscale_view()
    ax3.relim()
    ax3.autoscale_view()
    canvas.draw_idle()

def salvar_dados(x_data, y_data, x_data2, y_data2, x_data3, y_data3):
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
                for x, y in zip(x_data, y_data):
                    f.write(f"{x}\t{y}\n")

            if check_var2.get():  # Se a checkbox do Raw está ativada
                f.write("\nGráfico Raw:\n")
                for x, y in zip(x_data2, y_data2):
                    f.write(f"{x}\t{y}\n")

            if check_var3.get():  # Se a checkbox do Yaw está ativada
                f.write("\nGráfico Yaw:\n")
                for x, y in zip(x_data3, y_data3):
                    f.write(f"{x}\t{y}\n")

        print(f"Arquivo salvo em: {nome_arquivo}")

    else:
        print("Nenhum nome de arquivo foi escolhido.")

def atualizar_grafico():
    global serial_conn, ultima_linha,client, x_data, y_data, x_data2, y_data2, x_data3, y_data3
    
    valores = []  # Inicializa como lista vazia
    # Verifica se deve usar dados aleatórios ou dados do sensor
    if random_data.get():
        valores = [random.uniform(-90, 90) for _ in range(3)]
    else:
        # Verifica se há comunicação serial
        if serial_conn and serial_conn.is_open:
            try:
                while serial_conn.in_waiting:  # Aguarda novos dados
                    ultima_linha = serial_conn.readline().decode('utf-8').strip()  # Lê apenas a última linha
            
                if ultima_linha:
                    valores = [float(val) for val in ultima_linha.split()]

            except Exception as e:
                print(f"Erro ao ler dados do Serial")
        
        # Se não houver valores válidos pela Serial, tenta Wi-Fi
        if not valores:
            try:
                data = client.recv(32).decode('utf-8').strip()  # Ajusta o buffer para capturar apenas uma linha
                print(data)  # Exibe os dados recebidos para diagnóstico

                if data:
                    numeros = [float(val) for val in data.split()]  # Separa os números por espaço

                    # Apenas adiciona se houver exatamente 3 valores
                    if len(numeros) == 3:
                        valores = numeros

            except Exception:
                pass

    # Se os dados forem válidos, armazena nas variáveis globais
    if len(valores) == 3:
        x_data.append(len(x_data))  # Simula tempo
        y_data.append(valores[0])  # Pitch
        x_data2.append(len(x_data2))
        y_data2.append(valores[1])  # Raw
        x_data3.append(len(x_data3))
        y_data3.append(valores[2])  # Yaw

def Graficos():
    global canvas_pitch, canvas_raw, canvas_yaw, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    global line1, line2, line3, ani1, ani2, ani3, widgets_criados
    global frame_pitch, frame_raw, frame_yaw

    # Reinicia os dados
    x_data, y_data = [], []
    x_data2, y_data2 = [], []
    x_data3, y_data3 = [], []

    # Remove widgets existentes
    for widget in widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    widgets_criados = []

    BarraSuperior()
    
    criar_botoes_secundarios()
    
    # Apagar os gráficos se já existirem
    if frame_pitch and frame_pitch.winfo_exists():
        frame_pitch.destroy()
    if frame_raw and frame_raw.winfo_exists():
        frame_raw.destroy()
    if frame_yaw and frame_yaw.winfo_exists():
        frame_yaw.destroy()


    # Criando os frames para os gráficos apenas se a checkbox estiver ativada
    if check_var1.get():
        frame_pitch = ctk.CTkFrame(master=janela)
        frame_pitch.pack(fill="both", expand=True, pady=10)
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

    if check_var2.get():
        frame_raw = ctk.CTkFrame(master=janela)
        frame_raw.pack(fill="both", expand=True, pady=10)
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

    if check_var3.get():
        frame_yaw = ctk.CTkFrame(master=janela)
        frame_yaw.pack(fill="both", expand=True, pady=10)
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

    # Criando animações apenas se os gráficos existirem
    def atualizar(i):
        atualizar_grafico()
        if check_var1.get():
            line1.set_data(x_data, y_data)
            ax.relim()
            ax.autoscale_view()
        if check_var2.get():
            line2.set_data(x_data2, y_data2)
            ax2.relim()
            ax2.autoscale_view()
        if check_var3.get():
            line3.set_data(x_data3, y_data3)
            ax3.relim()
            ax3.autoscale_view()

    if check_var1.get():
        ani1 = FuncAnimation(fig_pitch, atualizar, interval=100, cache_frame_data=False)
        canvas_pitch.draw_idle()
    if check_var2.get():
        ani2 = FuncAnimation(fig_raw, atualizar, interval=100, cache_frame_data=False)
        canvas_raw.draw_idle()
    if check_var3.get():
        ani3 = FuncAnimation(fig_yaw, atualizar, interval=100, cache_frame_data=False)
        canvas_yaw.draw_idle()
    
def GraficosPolares():
    global canvas, widgets_criados, ani_polar, widgets_criados
    
    # Remove widgets existentes
    for widget in widgets_criados:
        if widget.winfo_exists():  # Confere se o widget ainda está ativo
            widget.destroy()
    canvas = None
    widgets_criados = []

    BarraSuperior()
    
    criar_botoes_secundarios()

    # Cria figura e eixos
    fig = Figure(figsize=(12, 8), dpi=100)
    ax_polar1 = fig.add_subplot(311, projection='polar')
    ax_polar2 = fig.add_subplot(312, projection='polar')
    ax_polar3 = fig.add_subplot(313, projection='polar')
    fig.subplots_adjust(hspace=0.5)

    # Função de animação
    def atualizar_polares(i):
        
        atualizar_grafico()
        if len(y_data) > i and len(y_data2) > i and len(y_data3) > i:
            valor1 = (y_data[i] * 3.14159) / 180
            valor2 = (y_data2[i] * 3.14159) / 180
            valor3 = (y_data3[i] * 3.14159) / 180

            ax_polar1.clear()
            ax_polar2.clear()
            ax_polar3.clear()

            ax_polar1.set_theta_direction(1)
            ax_polar2.set_theta_direction(1)
            ax_polar3.set_theta_direction(1)

            angles1 = [valor1, valor1 + 3.14159]
            angles2 = [valor2, valor2 + 3.14159]
            angles3 = [valor3, valor3 + 3.14159]
            
            values = [1, 1]
            ax_polar1.bar(angles1, values, width=0.2)
            ax_polar2.bar(angles2, values, width=0.2)
            ax_polar3.bar(angles3, values, width=0.2)

    
    canvas = FigureCanvasTkAgg(fig, master=janela)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(anchor=tk.CENTER, expand=True, fill='both')
    widgets_criados.append(canvas_widget)
    
    ani_polar = FuncAnimation(fig, atualizar_polares, interval=50, cache_frame_data=False)
    
    canvas.draw_idle()

def listar_portas():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]

def Conexao():
    global widgets_criados, canvas

    # Remove widgets existentes
    for widget in widgets_criados:
        if widget.winfo_exists():  # Confere se o widget ainda está ativo
            widget.destroy()
    canvas = None
    widgets_criados = []

    # Cria um frame centralizado
    frame_central = ctk.CTkFrame(janela, fg_color="transparent")
    frame_central.place(relx=0.5, rely=0.5, anchor="center")
    widgets_criados.append(frame_central)

    label = ctk.CTkLabel(frame_central, text="Escolha o método de conexão:")
    label.pack(pady=10)

    texto_status = ctk.CTkLabel(frame_central, text="")
    texto_status.pack(pady=10)

    label_dados = ctk.CTkLabel(frame_central, text="Dados recebidos:")
    label_dados.pack(pady=10)

    # Função para conectar via Serial
    def conectar_serial():
        global serial_conn
        porta_selecionada = "COM3"  # Ajuste conforme necessário
        try:
            serial_conn = serial.Serial(porta_selecionada, 115200, timeout=0.01)
            texto_status.configure(text=f"Conectado à {porta_selecionada}")
            janela.after(100, ler_dados_serial)
        except Exception as e:
            texto_status.configure(text=f"Erro: {e}")

    # Função para conectar via Wi-Fi
    def conectar_wifi():
        global client
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ESP_IP, ESP_PORT))
            texto_status.configure(text=f"Conectado ao ESP32 via Wi-Fi!")
            janela.after(100, ler_dados_wifi)
        except Exception as e:
            texto_status.configure(text=f"Erro na conexão Wi-Fi: {e}")

    # Função para ler dados via Serial
    def ler_dados_serial():
        global serial_conn
        if serial_conn and serial_conn.is_open:
            try:
                linha = serial_conn.readline().decode('utf-8').strip()
                if linha:
                    label_dados.configure(text=f"Dados Serial: {linha}")
            except Exception as e:
                label_dados.configure(text=f"Erro ao ler dados: {e}")
        janela.after(100, ler_dados_serial)

    # Função para ler dados via Wi-Fi (TCP/IP)
    def ler_dados_wifi():
        global client
        if client is not None:  # Verifica se client foi inicializado
            try:
                data = client.recv(1024).decode()
                if data:
                    label_dados.configure(text=f"Dados Wi-Fi: {data}")
            except socket.error as e:
                label_dados.configure(text=f"Erro na comunicação Wi-Fi: {e}")
        janela.after(100, ler_dados_wifi)

    # Botão para conexão via Serial
    botao_serial = ctk.CTkButton(frame_central, text="Conectar via Porta COM", command=conectar_serial)
    botao_serial.pack(pady=10)

    # Botão para conexão via Wi-Fi (TCP/IP)
    botao_wifi = ctk.CTkButton(frame_central, text="Conectar via Wi-Fi", command=conectar_wifi)
    botao_wifi.pack(pady=10)
                  
# Função para exibir o tooltip
def mostrar_tooltip(event):
    tooltip = tk.Label(janela, text="Descrição do botão", bg="yellow", fg="black")
    tooltip.place(x=event.x_root - janela.winfo_rootx(), y=event.y_root - janela.winfo_rooty())
    event.widget.tooltip = tooltip

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

###COISAS A ADICIONAR 
## descrição dos botoes
# Tela de inicio e fim 
# Indicação de conexão de servidor tcp/ip ou serial
