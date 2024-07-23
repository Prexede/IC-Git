import tkinter as tk
from tkinter import PhotoImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random

def atualizar_grafico(i):
    # Gera novos dados aleatórios para o gráfico
    x_data.append(i)
    y_data.append(random.randint(0, 10))
    ax.clear()
    ax.plot(x_data, y_data)
    
def atualizar_grafico2(i):
    # Gera novos dados aleatórios para o gráfico
    x_data2.append(i)
    y_data2.append(random.randint(0, 10))
    ax2.clear()
    ax2.plot(x_data2, y_data2)
    
def atualizar_grafico3(i):
    # Gera novos dados aleatórios para o gráfico
    x_data3.append(i)
    y_data3.append(random.randint(0, 10))
    ax3.clear()
    ax3.plot(x_data3, y_data3)
    
def Graficos():
    global canvas, ax, x_data, y_data, ax2, x_data2, y_data2, ax3, x_data3, y_data3
    x_data, y_data = [], []
    x_data2, y_data2 = [], []
    x_data3, y_data3 = [], []
    # Cria um gráfico usando Matplotlib
    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(3, 1, 2)
    ax3 = fig.add_subplot(3, 1, 3)

    # Incorpora o gráfico na janela do Tkinter
    canvas = FigureCanvasTkAgg(fig, master=janela)  # A 'master' é a janela do Tkinter
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH)
    # Configura a animação
    ani1 = FuncAnimation(fig, atualizar_grafico, interval=100)
    ani2 = FuncAnimation(fig, atualizar_grafico2, interval=100)
    ani3 = FuncAnimation(fig, atualizar_grafico3, interval=200)

    canvas.draw()
    
def Conexao():
    
    ## Apaga os graficos 
    global canvas
    if canvas:
        canvas.get_tk_widget().destroy()
        canvas = None
    
    

# Cria a janela principal
janela = tk.Tk()
janela.title('Exemplo Tkinter')

# Define a largura e a altura desejadas
largura = 1280
altura = 720
# Configura a resolução da janela
janela.geometry(f'{largura}x{altura}')

# Carrega a imagem de fundo
caminho_imagem = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\FundoTelemetria.png'  # Substitua com o caminho correto da sua imagem
imagem_fundo = PhotoImage(file=caminho_imagem)

# Redimensiona a imagem para cobrir toda a janela
imagem_fundo = imagem_fundo.zoom(1)  # Ajuste o fator de zoom conforme necessário
imagem_fundo = imagem_fundo.subsample(1)  # Ajuste o fator de subsample conforme necessário

# Configura a imagem de fundo
label_fundo = tk.Label(janela, image=imagem_fundo)
label_fundo.place(x=0, y=0, relwidth=1, relheight=1)

#########################################################################################################3
# Cria um Frame3d para a barra lateral
barra_lateral = tk.Frame(janela, width=100, height=300, bg='#5179AA')
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

# Inicia o loop principal da interface gráfica
janela.mainloop()



### https://www.youtube.com/watch?v=95tJO7XJlko Video que pode ajudar a divisão de paginas