import random
import math
import socket
import statistics
from tkinter import filedialog
import shared_state as state
from ui_utils import update_statistics_display

def pausar_aquisicao():
    """Pausa a aquisição de novos dados."""
    state.paused_acquisition = True
    print("Aquisição de dados pausada.")

def continuar_aquisicao():
    """Retoma a aquisição de dados."""
    state.paused_acquisition = False
    print("Aquisição de dados retomada.")

def _update_data_generation_mode(selected_var):
    """Garante que apenas um modo de geração de dados esteja ativo."""
    if selected_var == state.random_data and state.random_data.get():
        state.angular_test_data.set(False)
    elif selected_var == state.angular_test_data and state.angular_test_data.get():
        state.random_data.set(False)
    # A atualização do gráfico é chamada diretamente pelo checkbox em main.py

def resetar_dados(update_graph_display_func):
    """Limpa todos os dados dos gráficos e reseta os controles."""
    state.x_data.clear(); state.y_data.clear()
    state.x_data2.clear(); state.y_data2.clear()
    state.x_data3.clear(); state.y_data3.clear()
    state.angular_time_step = 0
    state.slider_pitch_val = 0.0
    state.slider_roll_val = 0.0
    state.slider_yaw_val = 0.0
    
    # Reseta sliders se existirem (exemplo, não implementado no código fornecido)
    # if 'slider_pitch' in globals() and slider_pitch: slider_pitch.set(0)

    state.override_pitch_var.set(False)
    state.override_roll_var.set(False)
    state.override_yaw_var.set(False)

    update_statistics_display([], state.pitch_stats_labels)
    update_statistics_display([], state.raw_stats_labels)
    update_statistics_display([], state.yaw_stats_labels)
    update_statistics_display([], state.single_linear_stats_labels)
    update_statistics_display([], state.single_polar_stats_labels)
    update_statistics_display([], state.single_3d_stats_labels)

    update_graph_display_func()

def salvar_dados():
    """Abre um diálogo para salvar os dados atuais em um arquivo .txt."""
    nome_arquivo = filedialog.asksaveasfilename(
        title="Salvar Dados do Gráfico",
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not nome_arquivo:
        print("Operação de salvamento cancelada.")
        return

    with open(nome_arquivo, 'w') as f:
        f.write("Tempo\tPitch\tRaw\tYaw\n")
        min_len = min(len(state.y_data), len(state.y_data2), len(state.y_data3))
        for i in range(min_len):
            f.write(f"{i}\t{state.y_data[i]}\t{state.y_data2[i]}\t{state.y_data3[i]}\n")
    print(f"Arquivo salvo em: {nome_arquivo}")

def adquirir_dados_continuamente():
    """Adquire um novo conjunto de dados de acordo com o modo selecionado."""
    if state.paused_acquisition:
        return []

    if state.random_data.get():
        return [random.uniform(-90, 90) for _ in range(3)]
    
    if state.angular_test_data.get():
        state.angular_time_step += 1
        pitch = 90 * math.sin(state.angular_time_step * 0.1)
        raw = (180 + 180 * math.cos(state.angular_time_step * 0.15)) % 360
        yaw = (state.angular_time_step * 5) % 360
        return [pitch, raw, yaw]
        
    if state.modo_conexao == 'serial' and state.serial_conn and state.serial_conn.is_open:
        try:
            if state.serial_conn.in_waiting > 0:
                state.ultima_linha = state.serial_conn.readline().decode('utf-8').strip()
                return [float(val) for val in state.ultima_linha.split()]
        except Exception as e:
            print(f"Erro ao ler dados do Serial: {e}")
            return []
            
    if state.modo_conexao == 'wifi' and state.client:
        try:
            data = state.client.recv(32).decode('utf-8').strip()
            if data:
                return [float(val) for val in data.split() if len(val.split()) == 3]
        except Exception as e:
            print(f"Erro ao ler dados do Wi-Fi: {e}")
            state.client = None
            return []
    
    return []

def atualizar_dados_para_graficos():
    """Pega novos dados e os adiciona às listas de dados."""
    valores = adquirir_dados_continuamente()
    if len(valores) == 3:
        state.x_data.append(len(state.x_data))
        state.y_data.append(valores[0])  # Pitch
        state.x_data2.append(len(state.x_data2))
        state.y_data2.append(valores[1]) # Raw
        state.x_data3.append(len(state.x_data3))
        state.y_data3.append(valores[2]) # Yaw