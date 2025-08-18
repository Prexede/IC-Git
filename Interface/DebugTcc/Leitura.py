import serial
import threading
import tkinter as tk
from tkinter import messagebox

# --- Configurações Iniciais ---
SERIAL_PORT = 'COM3'  # Altere para a porta serial correta do seu dispositivo
BAUD_RATE = 115200      # Altere para a taxa de transmissão do seu dispositivo
SAVE_FILE = 'dados_serial.txt' # Nome do arquivo onde os dados serão salvos

# Variáveis de controle
counting_enabled = False
line_count = 0
serial_data_buffer = [] # Buffer para armazenar os dados recebidos

# --- Função de Leitura Serial ---
def read_serial():
    global line_count, counting_enabled, serial_data_buffer
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Conectado à porta serial {SERIAL_PORT} em {BAUD_RATE} bps.")
    except serial.SerialException as e:
        messagebox.showerror("Erro de Porta Serial", f"Não foi possível abrir a porta serial {SERIAL_PORT}: {e}")
        return

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Recebido: {line}") # Para depuração

                if counting_enabled:
                    line_count += 1
                    serial_data_buffer.append(line)
                    update_count_label() # Atualiza a GUI
        except Exception as e:
            print(f"Erro ao ler da porta serial: {e}")
            break

# --- Funções da Interface Gráfica ---
def start_counting():
    global counting_enabled, line_count, serial_data_buffer
    if not counting_enabled:
        counting_enabled = True
        line_count = 0  # Reseta a contagem
        serial_data_buffer = [] # Limpa o buffer
        update_count_label()
        status_label.config(text="Status: Contando novas linhas...", fg="blue")
        print("Contagem iniciada.")
    else:
        messagebox.showinfo("Informação", "A contagem já está em andamento.")

def stop_and_save():
    global counting_enabled, line_count, serial_data_buffer
    if counting_enabled:
        counting_enabled = False
        status_label.config(text="Status: Contagem parada. Salvando dados...", fg="orange")
        print("Contagem parada. Salvando dados...")

        try:
            with open(SAVE_FILE, 'w') as f:
                for data_line in serial_data_buffer:
                    f.write(data_line + '\n')
            messagebox.showinfo("Sucesso", f"{line_count} linhas salvas em '{SAVE_FILE}'.")
            status_label.config(text=f"Status: Pronto. {line_count} linhas salvas.", fg="green")
            print(f"Dados salvos em {SAVE_FILE}")
        except IOError as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no arquivo: {e}")
            status_label.config(text="Status: Erro ao salvar.", fg="red")
    else:
        messagebox.showinfo("Informação", "Nenhuma contagem em andamento para parar e salvar.")

def update_count_label():
    count_label.config(text=f"Linhas Capturadas: {line_count}")

# --- Configuração da Janela Principal ---
root = tk.Tk()
root.title("Contador de Linhas Serial")
root.geometry("400x200") # Largura x Altura

# Label para exibir a contagem
count_label = tk.Label(root, text="Linhas Capturadas: 0", font=("Helvetica", 16))
count_label.pack(pady=10)

# Label de Status
status_label = tk.Label(root, text="Status: Aguardando...", font=("Helvetica", 12), fg="gray")
status_label.pack(pady=5)

# Botão para iniciar a contagem
start_button = tk.Button(root, text="Iniciar Contagem", command=start_counting, font=("Helvetica", 14), bg="lightgreen")
start_button.pack(pady=5)

# Botão para parar e salvar
stop_button = tk.Button(root, text="Parar e Salvar", command=stop_and_save, font=("Helvetica", 14), bg="lightcoral")
stop_button.pack(pady=5)

# --- Iniciar Thread de Leitura Serial ---
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# --- Iniciar Loop Principal da GUI ---
root.mainloop()