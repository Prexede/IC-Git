import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
import serial.tools.list_ports

random_data = -1
global dados

# As listas de dados serão preenchidas com os valores recebidos
x_data, y_data = [], []
x_data2, y_data2 = [], []
x_data3, y_data3 = [], []

# Variáveis globais para os objetos dos gráficos
canvas = None
ax = None
ax2 = None
ax3 = None
line1 = None
line2 = None
line3 = None
ani1 = None
serial_conn = None
widgets_criados = []

def fechar_programa():
    janela.destroy()
    
def sair_tela_cheia(event):
    janela.attributes('-fullscreen', False)
    
def criar_botoes_secundarios():
    global botao_salvar, botao_resetar, botao_dados_aleatorios, widgets_criados

    # Adiciona checkbuttons
    check_var1 = tk.BooleanVar()
    check_var2 = tk.BooleanVar()
    check_var3 = tk.BooleanVar()

    check_button1 = tk.Checkbutton(barra_checklist, text="Mostrar Pitch", variable=check_var1, bg='#DDDDDD')
    check_button1.pack(pady=5,side="left", anchor=tk.CENTER)
    check_button2 = tk.Checkbutton(barra_checklist, text="Mostrar Raw", variable=check_var2, bg='#DDDDDD')
    check_button2.pack(pady=5,side="left",  anchor=tk.CENTER)
    check_button3 = tk.Checkbutton(barra_checklist, text="Mostrar Yaw", variable=check_var3, bg='#DDDDDD')
    check_button3.pack(pady=5 ,anchor=tk.CENTER,side="left", )

    # Botão para salvar os dados
    botao_salvar = tk.Button(barra_superior, text="Salvar Dados", command=lambda: salvar_dados( x_data, y_data, x_data2, y_data2, x_data3, y_data3))
    botao_salvar.pack(side=tk.TOP, pady=5, fill='both')
    widgets_criados.append(botao_salvar)

    # Botão para resetar os dados
    botao_resetar = tk.Button(barra_superior, text="Resetar Dados", command=resetar_dados)
    botao_resetar.pack(side=tk.TOP,pady=5, fill='both')
    widgets_criados.append(botao_resetar)

    # Botão para usar dados aleatórios
    botao_dados_aleatorios = tk.Button(barra_superior, text="Usar Dados Aleatórios", command=dados_random)
    botao_dados_aleatorios.pack(side=tk.TOP,pady=5, fill='both')
    widgets_criados.append(botao_dados_aleatorios)
  
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

def salvar_dados( x_data, y_data, x_data2, y_data2, x_data3, y_data3):
    # Abre janela para selecionar o nome do arquivo
    nome_arquivo = filedialog.asksaveasfilename(
        title="Escolha o nome do arquivo",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    if nome_arquivo:  # Verifica se o nome do arquivo foi definido
        with open(nome_arquivo, 'w') as f:
            f.write("\nGráfico 1:\n")
            for x, y in zip(x_data, y_data):
                f.write(f"{x}\t{y}\n")
            f.write("\nGráfico 2:\n")
            for x, y in zip(x_data2, y_data2):
                f.write(f"{x}\t{y}\n")
            f.write("\nGráfico 3:\n")
            for x, y in zip(x_data3, y_data3):
                f.write(f"{x}\t{y}\n")
        
        print(f"Arquivo salvo em: {nome_arquivo}")
    else:
        print("Nenhum nome de arquivo foi escolhido.")

def dados_random():
    global random_data 
    random_data = (-1) * random_data

def atualizar_grafico():
    global serial_conn, x_data, y_data, x_data2, y_data2, x_data3, y_data3

    # Verifica se deve usar dados aleatórios ou dados do serial
    if random_data == 1:
        valores = [random.uniform(-90, 90) for _ in range(3)]
    else:
        if serial_conn and serial_conn.is_open:
            try:
                linha = serial_conn.readline().decode('utf-8').strip()
                # Converte a linha para uma lista de floats
                valores = [float(val) for val in linha.split()]
            except Exception as e:
                print(f"Erro ao ler dados: {e}")
                valores = []
        else:
            valores = []

    # Se os dados forem válidos, armazena nas variáveis globais
    if len(valores) == 3:
        x_data.append(len(x_data))  # Usa o índice atual como "tempo"
        y_data.append(valores[0])  # Pitch
        x_data2.append(len(x_data2))
        y_data2.append(valores[1])  # Raw
        x_data3.append(len(x_data3))
        y_data3.append(valores[2])  # Yaw
             
def Graficos():
    global canvas, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3, line1, line2, line3, ani1, widgets_criados

    # Reinicia os dados
    x_data, y_data = [], []
    x_data2, y_data2 = [], []
    x_data3, y_data3 = [], []

    # Remove widgets existentes
    for widget in widgets_criados:
        widget.destroy()
    canvas = None
    widgets_criados = []

    # Cria figura e eixos
    fig = Figure(figsize=(12, 8), dpi=100)
    ax = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)
    fig.subplots_adjust(hspace=0.5)

    # Configuração dos gráficos
    ax.set_xlabel("Tempo[ms]")
    ax.set_ylabel("Angulo[graus]")
    ax.grid(True)
    ax.set_title("Pitch")

    ax2.set_xlabel("Tempo[ms]")
    ax2.set_ylabel("Angulo[graus]")
    ax2.grid(True)
    ax2.set_title("Raw")

    ax3.set_xlabel("Tempo[ms]")
    ax3.set_ylabel("Angulo[graus]")
    ax3.grid(True)
    ax3.set_title("Yaw")

    line1, = ax.plot([], [], 'r-', label="Pitch")
    line2, = ax2.plot([], [], 'g-', label="Raw")
    line3, = ax3.plot([], [], 'b-', label="Yaw")

    # Função de animação
    def atualizar(i):
        
        atualizar_grafico()
        line1.set_data(x_data, y_data)
        line2.set_data(x_data2, y_data2)
        line3.set_data(x_data3, y_data3)
        ax.relim()
        ax.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()
        ax3.relim()
        ax3.autoscale_view()
        

    # Incorpora o canvas
    canvas = FigureCanvasTkAgg(fig, master=janela)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(anchor=tk.CENTER, expand=True, fill='both')
    widgets_criados.append(canvas_widget)

    criar_botoes_secundarios()
    
    ani1 = FuncAnimation(fig, atualizar, interval=50, cache_frame_data=False)
    
    canvas.draw_idle()
    
def GraficosPolares():
    global canvas, widgets_criados, ani_polar, widgets_criados
    
    # Remove widgets existentes
    for widget in widgets_criados:
        widget.destroy()
    canvas = None
    widgets_criados = []

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

    criar_botoes_secundarios()
    
    ani_polar = FuncAnimation(fig, atualizar_polares, interval=50, cache_frame_data=False)
    
    canvas.draw_idle()

def listar_portas():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]

def Conexao():
    global widgets_criados, canvas
    # Remove todos os widgets criados anteriormente
    for widget in widgets_criados:
        widget.destroy()
    canvas = None
    widgets_criados = []
    
    # Cria um frame centralizado para seleção da porta COM
    frame_central = tk.Frame(janela)
    frame_central.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    widgets_criados.append(frame_central)
    
    label = tk.Label(frame_central, text="Selecione a Porta COM:")
    label.pack(pady=10)
    
    combo = ttk.Combobox(frame_central, values=listar_portas())
    combo.pack(pady=10)
    
    botao_conectar = tk.Button(frame_central, text="Conectar", 
                               command=lambda: conectar_porta(combo.get()))
    botao_conectar.pack(pady=10)
    
    texto_status = tk.Label(frame_central, text="")
    texto_status.pack(pady=10)
    
    label_dados = tk.Label(frame_central, text="Dados do Serial:")
    label_dados.pack(pady=10)
    
    def conectar_porta(porta_selecionada):
        global serial_conn
        if porta_selecionada:
            try:
                serial_conn = serial.Serial(porta_selecionada, 115200, timeout=0.01)
                texto_status.config(text=f"Conectado à {porta_selecionada}")
                janela.after(100, ler_dados_serial)  # Inicia a leitura do serial
            except Exception as e:
                texto_status.config(text=f"Erro: {e}")
        else:
            texto_status.config(text="Nenhuma porta selecionada")
    
    def ler_dados_serial():
        global serial_conn
        if serial_conn and serial_conn.is_open:
            try:
                # Aqui você pode processar os dados do serial para exibição
                linha = serial_conn.readline().decode('utf-8').strip()
                if linha:
                    label_dados.config(text=f"Dados do Serial: {linha}")
            except Exception as e:
                label_dados.config(text=f"Erro ao ler dados: {e}")
        janela.after(50, ler_dados_serial)
        
# Função para exibir o tooltip
def mostrar_tooltip(event):
    tooltip = tk.Label(janela, text="Descrição do botão", bg="yellow", fg="black")
    tooltip.place(x=event.x_root - janela.winfo_rootx(), y=event.y_root - janela.winfo_rooty())
    event.widget.tooltip = tooltip

# Função para remover o tooltip
def ocultar_tooltip(event):
    if hasattr(event.widget, "tooltip"):
        event.widget.tooltip.destroy()


# Cria a janela principal
janela = tk.Tk()
janela.title('Exemplo Tkinter')

# Define a resolução da janela
largura = 1920
altura = 1080
janela.geometry(f'{largura}x{altura}')

janela.attributes('-fullscreen', True)

# Configura a imagem de fundo
caminho_imagem = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\FundoTelemetria.png'
imagem_fundo = PhotoImage(file=caminho_imagem)
imagem_fundo = imagem_fundo.zoom(2)  # Ajuste o zoom conforme necessário
label_fundo = tk.Label(janela, image=imagem_fundo)
label_fundo.place(x=0, y=0, relwidth=1, relheight=1)

#########################################################################################################
# Cria um frame para a barra lateral
barra_lateral = tk.Frame(janela, bg='#5179AA')
barra_lateral.pack(side='left')

barra_superior = tk.Frame(janela, width=100, height=30, bg='#5179AA')
barra_superior.pack(side='top', fill='x')

barra_checklist = tk.Frame(barra_superior, width=100, height=30, bg='#5179AA')
barra_checklist.pack(side="bottom" , fill='x')


# Botão de conexão
caminho_imagemBotaoWifi = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Conexao.png'
imagem_botaoWifi = PhotoImage(file=caminho_imagemBotaoWifi)
botao1 = tk.Button(barra_lateral, image=imagem_botaoWifi, compound='right',text="Conexão Serial", command=Conexao,)
botao1.pack(anchor=tk.CENTER,padx=10)

# Botão de gráficos cartesianos
caminho_imagemBotaoGrafico = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Grafico.png'
imagem_botaoGrafico = PhotoImage(file=caminho_imagemBotaoGrafico)
botao2 = tk.Button(barra_lateral, image=imagem_botaoGrafico, compound='right',text="Gráficos", command=Graficos)
botao2.pack(anchor=tk.CENTER,padx=10)

# Botão de gráficos circulares 
botao_polar = tk.Button(barra_lateral, text="Gráficos Polares", command=GraficosPolares)
botao_polar.pack(anchor=tk.CENTER, padx=10)
widgets_criados.append(botao_polar)

# Botão Fechar programa
caminho_imagemBotaoOnOff = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\OnOff.png'
imagem_botaoOnOff = PhotoImage(file=caminho_imagemBotaoOnOff)
botao_fechar = tk.Button(barra_superior,image=imagem_botaoOnOff ,compound='right',text="Fechar" ,command=fechar_programa)
botao_fechar.pack(side='right',padx=10)

# Adiciona a opção de sair do modo tela cheia com a tecla ESC
janela.bind('<Escape>', sair_tela_cheia)

botao2.bind("<Enter>", mostrar_tooltip)
botao2.bind("<Leave>", ocultar_tooltip)


#########################################################################################################
widgets_criados = []
canvas = None

# Inicia o loop principal da interface gráfica
janela.mainloop()