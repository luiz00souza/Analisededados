import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
import tempfile
import io
import matplotlib.pyplot as plt

# ---------------------- CONFIG GERAL ----------------------
st.set_page_config(page_title="🌊 Taxa Mensal de Assoreamento", layout="wide")

# ---------------------- CABEÇALHO ----------------------
st.title("🌊 Taxa Mensal de Assoreamento")
st.markdown("""
Bem-vindo(a)!  
Aqui você pode **analisar a variação mensal de assoreamento** a partir de arquivos XYZ sem cabeçalho.  
O sistema reconhece automaticamente as datas, calcula as taxas e gera um **GIF animado** da evolução temporal.
""")

# ---------------------- SEÇÃO 1: Upload ----------------------
st.markdown("---")
st.header("📥 Etapa 1 — Envio dos arquivos")

with st.expander("Clique aqui para entender o formato esperado 🧭", expanded=False):
    st.markdown("""
    - O nome dos arquivos deve seguir o formato:  
      `2023_JANEIRO_x_2024_MARCO.xyz`  
    - Onde:
        - `x` indica o intervalo entre os períodos comparados.  
        - Os meses devem estar em português (ex: JANEIRO, FEVEREIRO...).
    """)

uploaded_files = st.file_uploader(
    "Selecione um ou mais arquivos XYZ:",
    accept_multiple_files=True,
    type=["xyz", "txt", "csv"]
)

if not uploaded_files:
    st.info("💡 Dica: arraste seus arquivos aqui para começar.")
    st.stop()

st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s) com sucesso! Vamos em frente 🚀")

# ---------------------- PARÂMETROS DE PROCESSAMENTO ----------------------
cmap = "bwr"  # Azul = erosão, Vermelho = assoreamento
vmin, vmax = -0.1, 0.1
meses_dict = {
    "JANEIRO":1, "FEVEREIRO":2, "MARÇO":3, "ABRIL":4, "MAIO":5, "JUNHO":6,
    "JULHO":7, "AGOSTO":8, "SETEMBRO":9, "OUTUBRO":10, "NOVEMBRO":11, "DEZEMBRO":12
}

# ---------------------- FUNÇÕES AUXILIARES ----------------------
def extrair_datas(nome_arquivo):
    nome = nome_arquivo.name if hasattr(nome_arquivo, "name") else str(nome_arquivo)
    nome = nome.replace(".XYZ", "").replace(".xyz", "")
    partes = nome.split("_")
    try:
        idx_x = partes.index("x")
    except ValueError:
        st.error(f"⚠️ O arquivo **{nome}** não segue o padrão esperado (contendo 'x').")
        return None, None
    try:
        ano_inicio = int(partes[idx_x-2])
        mes_inicio = meses_dict[partes[idx_x-1].upper()]
        ano_fim = int(partes[idx_x+1])
        mes_fim = meses_dict[partes[idx_x+2].upper()]
        return datetime(ano_inicio, mes_inicio, 1), datetime(ano_fim, mes_fim, 1)
    except Exception:
        st.error(f"❌ Erro ao interpretar as datas no arquivo: {nome}")
        return None, None

def meses_entre(data_inicio, data_fim):
    return (data_fim.year - data_inicio.year)*12 + (data_fim.month - data_inicio.month)

# ---------------------- SEÇÃO 2: Processamento ----------------------
st.markdown("---")
st.header("⚙️ Etapa 2 — Processamento dos dados")

progress = st.progress(0)
dfs, datas = [], []

for i, arq in enumerate(uploaded_files):
    df = pd.read_csv(arq, sep="\t", names=["X","Y","Z"], engine='python')
    df = df.apply(pd.to_numeric, errors='coerce')
    data_inicio, data_fim = extrair_datas(arq)
    if data_inicio is None:
        st.stop()
    n_meses = max(1, meses_entre(data_inicio, data_fim))
    df["Z_mensal"] = df["Z"] / n_meses
    dfs.append(df[["X","Y","Z_mensal"]])
    datas += [data_inicio, data_fim]
    progress.progress((i+1)/len(uploaded_files))
    
st.success("✅ Processamento concluído! Próxima etapa 👇")

# ---------------------- MONTAGEM MATRIZ TEMPORAL ----------------------
matriz = pd.concat([
    pd.concat([
        df.assign(Data=data_inicio),
        df.assign(Data=data_fim)
    ])
    for df, arq in zip(dfs, uploaded_files)
    for data_inicio, data_fim in [extrair_datas(arq)]
], ignore_index=True)

matriz_pivot = matriz.pivot_table(index=["X","Y"], columns="Data", values="Z_mensal")
data_min, data_max = min(datas), max(datas)
meses_completos = pd.date_range(start=data_min, end=data_max, freq='MS')
matriz_pivot = matriz_pivot.reindex(columns=meses_completos).interpolate(axis=1, method='linear')

# ---------------------- SEÇÃO 3: Visualização ----------------------
st.markdown("---")
st.header("📊 Etapa 3 — Visualização dos resultados")

volume_mensal = matriz_pivot.sum(axis=0)
delta_volume = volume_mensal.diff()

# ---------- Gráfico interativo com Plotly ----------
st.subheader("📈 Evolução do Volume por Mês")

fig = go.Figure()

# Linha principal
fig.add_trace(go.Scatter(
    x=volume_mensal.index, 
    y=volume_mensal.values,
    mode='lines+markers',
    name='Volume Total',
    line=dict(color='black', width=2)
))

# Destaques de assoreamento e erosão
for i in range(1, len(delta_volume)):
    cor = 'red' if delta_volume[i] > 0 else 'blue'
    fig.add_trace(go.Scatter(
        x=[volume_mensal.index[i-1], volume_mensal.index[i]],
        y=[volume_mensal.values[i-1], volume_mensal.values[i]],
        mode='lines',
        line=dict(color=cor, width=4),
        name='Assoreamento' if cor=='red' else 'Erosão',
        showlegend=i==1 or i==2
    ))

fig.update_layout(
    title="Variação Temporal do Volume Total",
    xaxis_title="Mês",
    yaxis_title="Volume Total (cm/mês)",
    template="plotly_white",
    hovermode="x unified",
    font=dict(size=14),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
)
fig.update_xaxes(tickangle=45)

st.plotly_chart(fig, use_container_width=True)

# ---------- GIF ----------
st.subheader("🎬 Evolução Espacial do Assoreamento")

fig_gif, ax_gif = plt.subplots(figsize=(8,6))
def update(frame):
    ax_gif.clear()
    data = matriz_pivot.columns[frame]
    valores = matriz_pivot[data].values
    sc = ax_gif.scatter(
        matriz_pivot.index.get_level_values("X"),
        matriz_pivot.index.get_level_values("Y"),
        c=valores, cmap=cmap, s=5, edgecolor='none', vmin=vmin, vmax=vmax
    )
    ax_gif.set_title(f"{data.strftime('%b/%Y')}", fontsize=12)
    ax_gif.set_xlabel("X")
    ax_gif.set_ylabel("Y")
    ax_gif.invert_yaxis()
    return sc,

anim = FuncAnimation(fig_gif, update, frames=len(matriz_pivot.columns), blit=False)
with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmpfile:
    anim.save(tmpfile.name, writer=PillowWriter(fps=2))
    gif_path = tmpfile.name

st.image(gif_path, caption="Assoreamento mês a mês", use_container_width=True)

with open(gif_path, "rb") as f:
    st.download_button("⤓ Baixar GIF Animado", f, "assoreamento_mes_a_mes.gif", "image/gif")

# ---------- CSV ----------
st.subheader("📄 Exportar resultados")
df_volume = pd.DataFrame({
    "Mes": volume_mensal.index,
    "Volume_total": volume_mensal.values,
    "Delta_volume": delta_volume.values
})
csv_buffer = io.StringIO()
df_volume.to_csv(csv_buffer, index=False)
st.download_button("💾 Baixar CSV com volumes mensais", csv_buffer.getvalue(), "volume_mensal.csv", "text/csv")

st.balloons()
st.success("🎉 Análise concluída com sucesso! Excelente trabalho 🌱")
