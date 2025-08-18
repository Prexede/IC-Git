import tkinter as tk

# Variáveis de dados
x_data, y_data = [], [] # Pitch (time, value)
x_data2, y_data2 = [], [] # Raw (time, value)
x_data3, y_data3 = [], [] # Yaw (time, value)

# Variáveis de widgets e gráficos
ultima_linha = None
canvas = None
client = None
ax, ax2, ax3 = None, None, None # For linear 2D plots
ani1, ani2, ani3,= None, None, None
serial_conn = None
widgets_criados = [] # Widgets na área principal
label_dados = None

# Variáveis para gráficos polares
ax_polar1, ax_polar2, ax_polar3 = None, None, None
canvas_polar = None
ani_polar = None
fig_polar = None
bar_polar1_patch, bar_polar2_patch, bar_polar3_patch = None, None, None

# Variáveis para figuras
fig_pitch, fig_raw, fig_yaw = None, None, None
fig_single_linear = None # For single linear graph
fig_single_polar = None  # For single polar graph
fig_3d = None # Para o gráfico 3D

# Initialize single graph animations to None globally
ani_single_linear = None
ani_single_polar = None
ani_3d = None # Para o gráfico 3D


# Variáveis para indicadores do gráfico 3D
pitch_indicator_line, raw_indicator_line, yaw_indicator_line = None, None, None
pitch_indicator_point, raw_indicator_point, yaw_indicator_point = None, None, None

# Variables for opposite angle indicators
pitch_opposite_line, raw_opposite_line, yaw_opposite_line = None, None, None
pitch_opposite_point, raw_opposite_point, yaw_opposite_point = None, None, None

# Variables for single linear graph lines
line_pitch_single, line_raw_single, line_yaw_single = None, None, None

# Variables for single polar graph bars
bar_pitch_single, bar_raw_single, bar_yaw_single = None, None, None


# Variáveis de estado
modo_conexao = None # Pode ser 'serial', 'wifi', ou None
paused_acquisition = False

# Variáveis para nova geração de dados angulares
angular_time_step = 0

# Frame para os controles laterais dos gráficos
controles_graficos_frame = None

# Variável global para o frame do título da aba principal (a barra de destaque)
main_title_frame = None

# Variável global para a janela principal
janela = None

# Variáveis globais para a animação do GIF
gif_frames, gif_index, gif_label, gif_after_id, gif_path = [], 0, None, None, r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Alien.gif'

# Global variables for statistics labels
pitch_stats_labels = {}
raw_stats_labels = {}
yaw_stats_labels = {}
single_linear_stats_labels = {}
single_polar_stats_labels = {}
single_3d_stats_labels = {}

# NOVAS VARIÁVEIS GLOBAIS PARA OS VALORES DOS SLIDERS DO GRÁFICO 3D E SEUS LABELS
slider_pitch_val = 0.0
slider_roll_val = 0.0
slider_yaw_val = 0.0
label_pitch_val = None
label_roll_val = None
label_yaw_val = None

# Variáveis globais para os checkboxes de sobreposição e seleção de dados, etc.
override_pitch_var = None
override_roll_var = None
override_yaw_var = None
random_data = None
angular_test_data = None
single_graph_mode = None
check_var1 = None
check_var2 = None
check_var3 = None