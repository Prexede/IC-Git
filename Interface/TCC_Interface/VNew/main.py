import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Módulos do aplicativo
import shared_state as state
from app_logic import (
    resetar_dados,
    salvar_dados,
    pausar_aquisicao,
    continuar_aquisicao,
    _update_data_generation_mode,
)
from ui_utils import parar_animacoes
from linear_graphs import Graficos
from polar_graphs import GraficosPolares
from three_d_graph import Grafico3D

def fechar_programa():
    """Para as animações e fecha a janela principal."""
    parar_animacoes()
    if state.janela:
        state.janela.destroy()

def sair_tela_cheia(event):
    """Garante que a tela continue cheia ao pressionar Esc."""
    if state.janela:
        state.janela.attributes('-fullscreen', True)

def update_graph_display():
    """Atualiza a área principal para mostrar o gráfico selecionado."""
    if hasattr(state.janela, '_current_graph_mode'):
        if state.janela._current_graph_mode == 'linear':
            Graficos()
        elif state.janela._current_graph_mode == 'polar':
            GraficosPolares()
        elif state.janela._current_graph_mode == '3d':
            Grafico3D()

def criar_controles_laterais(parent):
    """Cria o painel de controle lateral com todas as opções."""
    frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))

    ctk.CTkLabel(frame, text="Opções do Gráfico", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), padx=10, fill="x")

    ctk.CTkCheckBox(frame, text="Pitch", variable=state.check_var1, command=update_graph_display).pack(pady=5, padx=20, anchor="w")
    ctk.CTkCheckBox(frame, text="Raw", variable=state.check_var2, command=update_graph_display).pack(pady=5, padx=20, anchor="w")
    ctk.CTkCheckBox(frame, text="Yaw", variable=state.check_var3, command=update_graph_display).pack(pady=5, padx=20, anchor="w")
    ctk.CTkCheckBox(frame, text="Gráfico Único", variable=state.single_graph_mode, command=update_graph_display).pack(pady=10, padx=20, anchor="w")

    ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10, padx=10)

    ctk.CTkCheckBox(frame, text="Dados Aleatórios", variable=state.random_data, command=lambda: _update_data_generation_mode(state.random_data)).pack(pady=5, padx=20, anchor="w")
    ctk.CTkCheckBox(frame, text="Dados Angulares (0-360°)", variable=state.angular_test_data, command=lambda: _update_data_generation_mode(state.angular_test_data)).pack(pady=5, padx=20, anchor="w")

    ctk.CTkButton(frame, text="Salvar Dados", command=salvar_dados).pack(pady=10, fill="x", padx=10)
    ctk.CTkButton(frame, text="Resetar Dados", command=lambda: resetar_dados(update_graph_display)).pack(pady=5, fill="x", padx=10)
    ctk.CTkButton(frame, text="Pausar Aquisição", command=pausar_aquisicao).pack(pady=5, fill="x", padx=10)
    ctk.CTkButton(frame, text="Continuar Aquisição", command=continuar_aquisicao).pack(pady=5, fill="x", padx=10)

    return frame

def setup_main_window():
    """Configura e inicializa a janela principal da aplicação."""
    state.janela = ctk.CTk()
    state.janela.title("Software de Interface para Controle de Prótese")
    state.janela.attributes('-fullscreen', True)
    state.janela.bind('<Escape>', sair_tela_cheia)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Inicializa variáveis de estado no CustomTkinter
    state.check_var1 = tk.BooleanVar(value=True)
    state.check_var2 = tk.BooleanVar(value=True)
    state.check_var3 = tk.BooleanVar(value=True)
    state.random_data = tk.BooleanVar(value=False)
    state.angular_test_data = tk.BooleanVar(value=False)
    state.single_graph_mode = tk.BooleanVar(value=False)
    state.override_pitch_var = tk.BooleanVar(value=False)
    state.override_roll_var = tk.BooleanVar(value=False)
    state.override_yaw_var = tk.BooleanVar(value=False)

    # Layout principal
    barra_lateral = ctk.CTkFrame(master=state.janela, width=250, corner_radius=0)
    barra_lateral.pack(side="left", fill="y")

    ctk.CTkLabel(barra_lateral, text="Painel de Controle", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20, padx=20)

    # Botões de navegação
    ctk.CTkButton(barra_lateral, text="Gráficos Lineares", command=Graficos).pack(pady=10, padx=20, fill="x")
    ctk.CTkButton(barra_lateral, text="Gráficos Polares", command=GraficosPolares).pack(pady=10, padx=20, fill="x")
    ctk.CTkButton(barra_lateral, text="Gráfico 3D", command=Grafico3D).pack(pady=10, padx=20, fill="x")

    # Controles laterais
    controles_graficos_frame = criar_controles_laterais(barra_lateral)
    controles_graficos_frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Botão de sair
    ctk.CTkButton(barra_lateral, text="Sair", command=fechar_programa).pack(side="bottom", pady=20, padx=20, fill="x")

    # Inicia com a tela de gráficos lineares
    Graficos()
    
    state.janela.mainloop()

if __name__ == "__main__":
    setup_main_window()