import customtkinter as ctk
import statistics
import shared_state as state

def limpar_area_principal():
    """Remove todos os widgets da área principal da janela."""
    for widget in state.widgets_criados:
        if widget.winfo_exists():
            widget.destroy()
    state.widgets_criados.clear()
    
    if state.main_title_frame and state.main_title_frame.winfo_exists():
        state.main_title_frame.destroy()
        state.main_title_frame = None

def parar_animacoes():
    """Para todas as animações de gráficos que estiverem ativas."""
    animations = [
        'ani1', 'ani2', 'ani3', 'ani_polar', 
        'ani_single_linear', 'ani_single_polar', 'ani_3d'
    ]
    for anim_name in animations:
        anim = getattr(state, anim_name, None)
        if anim:
            anim.event_source.stop()
            setattr(state, anim_name, None)

def create_statistics_frame(parent_frame, title_text, label_dict):
    """Cria e retorna um frame para exibir estatísticas."""
    stats_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    stats_frame.pack(pady=(5, 0), padx=10, fill="x")
    
    ctk.CTkLabel(stats_frame, text=title_text, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
    
    inner_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
    inner_frame.pack(fill="x")

    label_dict['min'] = ctk.CTkLabel(inner_frame, text="Min: N/A")
    label_dict['min'].pack(side="left", padx=(0, 10))
    label_dict['max'] = ctk.CTkLabel(inner_frame, text="Max: N/A")
    label_dict['max'].pack(side="left", padx=(0, 10))
    label_dict['mean'] = ctk.CTkLabel(inner_frame, text="Média: N/A")
    label_dict['mean'].pack(side="left", padx=(0, 10))
    label_dict['std'] = ctk.CTkLabel(inner_frame, text="Desvio Padrão: N/A")
    label_dict['std'].pack(side="left", padx=(0, 0))
    
    return stats_frame

def update_statistics_display(data_list, label_dict):
    """Atualiza os labels de estatísticas com novos valores."""
    if not data_list:
        min_val, max_val, mean_val, std_dev_val = "N/A", "N/A", "N/A", "N/A"
    else:
        min_val = f"{min(data_list):.2f}"
        max_val = f"{max(data_list):.2f}"
        mean_val = f"{statistics.mean(data_list):.2f}"
        std_dev_val = f"{statistics.stdev(data_list):.2f}" if len(data_list) > 1 else "0.00"

    # CORREÇÃO: Verifica se a chave existe no dicionário antes de configurar o label
    if 'min' in label_dict:
        label_dict['min'].configure(text=f"Min: {min_val}")
    if 'max' in label_dict:
        label_dict['max'].configure(text=f"Max: {max_val}")
    if 'mean' in label_dict:
        label_dict['mean'].configure(text=f"Média: {mean_val}")
    if 'std' in label_dict:
        label_dict['std'].configure(text=f"Desvio Padrão: {std_dev_val}")