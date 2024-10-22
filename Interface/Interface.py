import tkinter as tk
from tkinter import ttk,PhotoImage
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random
import matplotlib.pyplot as plt
import serial.tools.list_ports


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
            
            
def atualizar_grafico(i):
    global serial_conn
    if serial_conn and serial_conn.is_open:
        try:
            dados = serial_conn.readline().decode('utf-8').strip()
            if dados:
                valores = [float(val) for val in dados.split()]
                if len(valores) == 3:
                    x_data.append(i)
                    y_data.append(valores[0])
                    x_data2.append(i)
                    y_data2.append(valores[1])
                    x_data3.append(i)
                    y_data3.append(valores[2])
        except Exception as e:
            print(f"Erro ao ler dados: {e}")
    # GRAFICO 1
    ax.clear()
    ax.plot(x_data, y_data)
    ax.set_xlabel("Tempo[ms]")
    ax.set_ylabel("Angulo[graus]")
    ax.grid(True)
    ax.set_title("Pitch")

    
    # GRAFICO 2
    ax2.clear()
    ax2.plot(x_data2, y_data2)
    ax2.set_xlabel("Tempo[ms]")
    ax2.set_ylabel("Angulo[graus]")
    ax2.grid(axis='both')
    ax2.set_title("Raw")
    
    # GRAFICO 3
    ax3.clear()
    ax3.plot(x_data3, y_data3)
    ax3.set_xlabel("Tempo[ms]")
    ax3.set_ylabel("Angulo[graus]")
    ax3.grid(True)
    ax3.set_title("Yaw")
    
    
def Graficos():
    global canvas, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3, widgets_criados,i
    x_data, y_data = [], []
    x_data2, y_data2 = [], []
    x_data3, y_data3 = [], []
    
    #Verifica se o botão está apertado 
    if canvas:
        return
    
    # Cria um gráfico usando Matplotlib
    fig = Figure(figsize=(30, 40), dpi=50)
    ax = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(3, 1, 2)
    ax3 = fig.add_subplot(3, 1, 3)

    # Ajusta o espaçamento entre os gráficos
    fig.subplots_adjust(hspace=1)  # Aumenta o espaçamento vertical entre os gráficos
    
    # Incorpora o gráfico na janela do Tkinter
    canvas = FigureCanvasTkAgg(fig, master=janela)  # A 'master' é a janela do Tkinter
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(anchor=tk.CENTER,expand=True)
    widgets_criados.append(canvas_widget)
    
    # Configura a animação
    ani1 = FuncAnimation(fig, atualizar_grafico, interval=50, cache_frame_data=False)
    # Adiciona os botões de salvar
    global botao_salvar1
    botao_salvar1 = tk.Button(barra_lateral, text="Salvar Dados Gráfico 1", command=lambda: salvar_dados('grafico1.txt', x_data, y_data, x_data2, y_data2, x_data3, y_data3))
    botao_salvar1.pack(side=tk.LEFT, padx=10, pady=10)
    widgets_criados.append(botao_salvar1)
    
    
    # Adiciona os botões de Resetar grafico
    global botao_Reset
    botao_Reset = tk.Button(barra_lateral, text="Resetar dados", command=resetar_dados)
    botao_Reset.pack(side=tk.LEFT, padx=10, pady=10)
    widgets_criados.append(botao_Reset)
    
    canvas.draw()

def listar_portas():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]
   
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
        
        

# Cria a janela principal
janela = tk.Tk()
janela.title('Exemplo Tkinter')

# Define a largura e a altura desejadas
largura = 1920
altura = 1080
# Configura a resolução da janela
janela.geometry(f'{largura}x{altura}')

# Carrega a imagem de fundo
caminho_imagem = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\FundoTelemetria.png'
imagem_fundo = PhotoImage(file=caminho_imagem)

# Redimensiona a imagem para cobrir toda a janela
imagem_fundo = imagem_fundo.zoom(2)  # Ajuste o fator de zoom conforme necessário
# Configura a imagem de fundo
label_fundo = tk.Label(janela, image=imagem_fundo)
label_fundo.place(x=0, y=0, relwidth=1, relheight=1)


#########################################################################################################3
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
caminho_imagemBotaoGrafico = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Grafico.png' 
imagem_botaoGrafico = PhotoImage(file=caminho_imagemBotaoGrafico)
botao2 = tk.Button(barra_lateral, image=imagem_botaoGrafico, compound='center', command=Graficos)
botao2.pack(pady=50)

############################################################################################################

# Lista para armazenar widgets criados pelo botão "Gráficos"
widgets_criados = []
canvas = None

# Inicia o loop principal da interface gráfica
janela.mainloop()
