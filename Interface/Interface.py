import tkinter as tk
from tkinter import PhotoImage
import awesometkinter as atk

def exibir_mensagem():
    label['text'] = 'Olá, Tkinter!'

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
barra_lateral = atk.Frame3d(janela, width=100, height=300, bg='#5179AA', corner_radius=10)
barra_lateral.pack(side='left', fill='none')  # Posiciona a barra lateral à esquerda

# Adiciona botões à barra lateral
# Carrega a imagem para o botão
caminho_imagemBotaoWifi = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Conexao.png'  # Substitua pelo caminho correto da sua imagem
imagem_botaoWifi = PhotoImage(file=caminho_imagemBotaoWifi)

# Cria um botão com a imagem e o posiciona no Frame3d
botao1 = atk.Button3d(barra_lateral, image=imagem_botaoWifi, compound='center')
botao1.pack(pady=100)  # Adiciona espaço vertical entre os botões

# Cria um botão de texto e o posiciona no Frame3d
botao2 = atk.Button3d(barra_lateral, text='Botão 2')
botao2.pack(pady=100)
############################################################################################################


# Cria um rótulo (label) na janela
label = tk.Label(janela, text='Clique no botão')
label.pack()

# Cria um botão que chama a função exibir_mensagem
botao = tk.Button(janela, text='Clique aqui', command=exibir_mensagem)
botao.pack()

# Inicia o loop principal da interface gráfica
janela.mainloop()

