import tkinter as tk
from tkinter import ttk,PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
import serial.tools.list_ports
import numpy as np
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec

# Variáveis globais
canvas = None
serial_conn = None
random_data = 1
x_data, y_data = [], []
x_data2, y_data2 = [], []
x_data3, y_data3 = [], []
ax = ax2 = ax3 = ax_polar1 = ax_polar2 = ax_polar3 = None
random_data = 1

# Função para fechar o programa
############################################FUNCIONALIDADES###############################################################
def fechar_programa():
    janela.destroy()
    
def resetar_dados():
    global x_data, y_data, x_data2, y_data2, x_data3, y_data3
    x_data.clear()
    x_data2.clear()
    x_data3.clear()
    y_data.clear()
    y_data2.clear()
    y_data3.clear()
    ax.clear()
    ax2.clear()
    ax3.clear()
    canvas.draw()
    
def salvar_dados(nome_arquivo, x_data, y_data, x_data2, y_data2, x_data3, y_data3):
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

def dados_random():
    global random_data 
    random_data = (-1)*random_data
          
def criar_grafico_polar(ax_polar,valor):
    if ax_polar:
        ax_polar.clear()
        ax_polar.set_theta_direction(1)
        #ax_polar.set_theta_offset(np.pi / 2)
        ax_polar.set_yticklabels([])
        #rad to degree
        valor = (valor*np.pi)/180
        # Dados
        angles = [valor,valor + np.pi]  
        values = [1, 1]  # Ambas as barras têm a mesma altura
        ax_polar.bar(angles, values, width=0.2)
                    
def criar_grafico_linha(i,x_data,y_data,ax,title):
    ax.clear()
    ax.plot(x_data, y_data)
    ax.set_xlabel("Tempo[ms]")
    ax.set_xlim([0, 180])
    ax.set_ylabel("Angulo[graus]")
    ax.set_ylim([0, 360])
    ax.grid(True)
    ax.set_title(title)
    
def atualizar_grafico(i):
    global serial_conn, ax, ax2, ax3, ax_polar1, ax_polar2, ax_polar3
    plt.clf()
    if random_data == 1:
        #valores = [random.uniform(-90, 90) for _ in range(3)]
        valores = [(i+ random.uniform(-2,2)) for _ in range(3)] 
    else:
        if serial_conn and serial_conn.is_open:
            try:
                dados = serial_conn.readline().decode('utf-8').strip()
                valores = [float(val) for val in dados.split()]
            except Exception as e:
                print(f"Erro ao ler dados: {e}")  
    
    if len(valores) == 3:
        x_data.append(i)
        y_data.append(valores[0])
        x_data2.append(i)
        y_data2.append(valores[1])
        x_data3.append(i)
        y_data3.append(valores[2])
        
    # Titulo grafico 1
    title = "Pitch"
    # GRAFICO LINHA 1
    criar_grafico_linha(i,x_data,y_data,ax,title)
    # GRAFICO POLAR 1
    criar_grafico_polar(ax_polar1,valores[0])

    # Titulo grafico 2
    title = "Raw"
    # GRAFICO LINHA 2
    criar_grafico_linha(i,x_data2,y_data2,ax2,title)
    # GRAFICO POLAR 2
    criar_grafico_polar(ax_polar2,valores[1])

    # Titulo grafico 3
    title = "Yaw"
    # GRAFICO LINHA 3
    criar_grafico_linha(i,x_data3,y_data3,ax3,title)    
    # GRAFICO POLAR 3
    criar_grafico_polar(ax_polar3,valores[2]) 
    
def listar_portas():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]
     
############################################JANELAS###############################################################    
def Conexao():
    global widgets_criados, canvas
    # Apaga todos os widgets criados pelo botão "Gráficos"
    for widget in widgets_criados:
        widget.destroy()
        canvas = None
    widgets_criados = []
    
# Cria um frame centralizado
    frame_central = tk.Frame(janela)
    frame_central.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    widgets_criados.append(frame_central)
    
    # Cria a interface para seleção de porta COM
    label = tk.Label(frame_central, text="Selecione a Porta COM:")
    label.pack(pady=10)
    
    combo = ttk.Combobox(frame_central, values=listar_portas())
    combo.pack(pady=10)
    
    botao_conectar = tk.Button(frame_central, text="Conectar", command=lambda: conectar_porta(combo.get()))
    botao_conectar.pack(pady=10)
    
    texto_status = tk.Label(frame_central, text="")
    texto_status.pack(pady=10)
    
    label_dados = tk.Label(frame_central, text="Dados do Serial:")
    label_dados.pack(pady=10)
    def conectar_porta(porta_selecionada):
        global serial_conn
        if porta_selecionada:
            try:
                serial_conn = serial.Serial(porta_selecionada, 115200, timeout=0.0001)
                texto_status.config(text=f"Conectado à {porta_selecionada}")
                janela.after(100, ler_dados_serial)  # Chama a função para ler dados do serial
            except Exception as e:
                texto_status.config(text=f"Erro: {e}")
        else:
            texto_status.config(text="Nenhuma porta selecionada")
    def ler_dados_serial():
        global serial_conn
        if serial_conn and serial_conn.is_open:
            try:
                dados = serial_conn.readline().decode('utf-8').strip()
                if dados:
                    label_dados.config(text=f"Dados do Serial: {dados}")
            except Exception as e:
                label_dados.config(text=f"Erro ao ler dados: {e}")
        janela.after(100, ler_dados_serial)  # Chama a função novamente após 1 segundo
     
def Graficos():
    global canvas, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3, widgets_criados,i,ax_polar1,ax_polar2,ax_polar3
    x_data, y_data = [], []
    x_data2, y_data2 = [], []
    x_data3, y_data3 = [], []
    
    #Verifica se o botão está apertado 
    if canvas:
        return

    # Cria um gráfico usando Matplotlib
    fig = Figure(figsize=(20, 40), dpi=100)
    gs = GridSpec(3, 2, figure=fig)

    # Configura os outros gráficos
    ax =        fig.add_subplot(gs[0, 0])
    ax_polar1 = fig.add_subplot(gs[0, 1], projection='polar')
    ax2 =       fig.add_subplot(gs[1, 0])
    ax_polar2 = fig.add_subplot(gs[1, 1], projection='polar')
    ax3 =       fig.add_subplot(gs[2, 0])
    ax_polar3 = fig.add_subplot(gs[2, 1], projection='polar')

    # Ajusta o espaçamento entre os gráficos
    fig.subplots_adjust(hspace=0.5)  # Aumenta o espaçamento vertical entre os gráficos
    
    # Incorpora o gráfico na janela do Tkinter
    canvas = FigureCanvasTkAgg(fig, master=janela)  # A 'master' é a janela do Tkinter
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(anchor=tk.CENTER, expand=True)
    widgets_criados.append(canvas_widget)
    
    # Configura a animação
    ani1 = animation.FuncAnimation(fig, atualizar_grafico,frames=360,interval=100,cache_frame_data=False)                                           
    
    # Adiciona os botões de salvar
    global botao_salvar1
    caminho_imagemBotaoSave = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Save.png'
    imagem_botaoSave = PhotoImage(file=caminho_imagemBotaoSave)
    botao_salvar1 = tk.Button(barra_lateral, text="Salvar Dados Gráfico 1",image=imagem_botaoSave, command=lambda: salvar_dados('dataTeste.txt', x_data, y_data, x_data2, y_data2, x_data3, y_data3))
    botao_salvar1.pack(side=tk.TOP, padx=10, pady=10)
    widgets_criados.append(botao_salvar1)
    
    # Adiciona os botões de Resetar grafico
    global botao_Reset
    botao_Reset = tk.Button(barra_lateral, text="Resetar dados", command=resetar_dados)
    botao_Reset.pack(side=tk.TOP, padx=10, pady=10)
    widgets_criados.append(botao_Reset)
    
    # Adiciona o botão de adicionar dados fakes
    global data_random
    data_random = tk.Button(barra_lateral, text="Dados Aleatórios", command=dados_random)
    data_random.pack(side=tk.TOP, padx=10, pady=10)
    widgets_criados.append(data_random)
    
    canvas.draw()
    
##########################################JANELA PRINCIPAL###########################################################
# Cria a janela principal
janela = tk.Tk()
janela.title('Exemplo Tkinter')

# Define a largura e a altura desejadas
largura = 1920
altura = 1080
# Configura a resolução da janela
janela.geometry(f'{largura}x{altura}')

# Carrega a imagem de fundo
caminho_imagem = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Fundo.png'
imagem_fundo = PhotoImage(file=caminho_imagem)

# Redimensiona a imagem para cobrir toda a janela
imagem_fundo = imagem_fundo.zoom(2)  # Ajuste o fator de zoom conforme necessário
# Configura a imagem de fundo
label_fundo = tk.Label(janela, image=imagem_fundo)
label_fundo.place(x=0, y=0, relwidth=1, relheight=1)

#########################################################################################################
# Cria um Frame3d para a barra lateral
barra_lateral = tk.Frame(janela, width=100, height=200, bg='#5179AA')
barra_lateral.pack(side='left', fill='none')  # Posiciona a barra lateral à esquerda

# Adiciona botões à barra lateral

################# CONEXAO ####################
# Carrega a imagem para o botão
caminho_imagemBotaoWifi = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Conexao.png'
imagem_botaoWifi = PhotoImage(file=caminho_imagemBotaoWifi)
# Cria um botão com a imagem e o posiciona no Frame3d
botao1 = tk.Button(barra_lateral, image=imagem_botaoWifi, compound='center', command=Conexao)
botao1.pack(pady=50)  # Adiciona espaço vertical entre os botões

############### GRAFICOS #####################################################
caminho_imagemBotaoGrafico = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\grafico.jpeg' 
imagem_botaoGrafico = PhotoImage(file=caminho_imagemBotaoGrafico)
botao2 = tk.Button(barra_lateral, image=imagem_botaoGrafico, compound='center', command=Graficos)
botao2.pack(pady=50)

###############FECHAR PROGRAMA#############################################################################

# Adiciona um botão para fechar o programa
botao_fechar = tk.Button(barra_lateral, text="Fechar", command=fechar_programa)
botao_fechar.pack(pady=50)

# Lista para armazenar widgets criados pelo botão "Gráficos"
widgets_criados = []
canvas = None

# Configura a janela para abrir em tela cheia
janela.attributes('-fullscreen', True)

# Inicia o loop principal da interface gráfica
janela.mainloop()
