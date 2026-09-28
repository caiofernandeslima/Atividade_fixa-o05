from pathlib import Path
import streamlit as st
import pandas as pd
from pipeline import (
    carregar_e_tratar_transacoes,
    carregar_cotacoes,
    consolidar_com_cotacoes,
    filtrar_setembro_sp_rj,
    criar_pivot_risco,
    detectar_anomalias,
    criar_grafico_diario,
)

st.set_page_config(page_title="Fintech | Relatório de Transações", layout="wide")
st.title("Relatório de Transações Financeiras")
st.caption("Limpeza, transformação, consolidação, métricas e detecção de anomalias")

st.sidebar.header("Arquivos")
trans_file = st.sidebar.file_uploader("transacoes.csv (latin1)", type="csv")
cot_file = st.sidebar.file_uploader("cotacoes.csv (utf-8)", type="csv")

if trans_file is None:
    st.info("Envie o arquivo transacoes.csv na barra lateral para iniciar a análise.")
    st.stop()

# O upload é lido diretamente pelo pandas; latin1 é obrigatório no enunciado.
df = pd.read_csv(trans_file, encoding="latin1")
# Reaproveita a mesma lógica do pipeline salvando temporariamente apenas em memória.
mediana_estado = df.groupby("estado_cliente")["valor"].transform("median")
df["valor"] = df["valor"].fillna(mediana_estado)
df["plataforma"] = "Mobile"
df["data_transacao"] = pd.to_datetime(df["data_transacao"]).dt.tz_localize("America/Sao_Paulo")
df["dia_semana"] = df["data_transacao"].dt.day_name()
df["mes"] = df["data_transacao"].dt.month
df = df.drop_duplicates(keep="first").reset_index(drop=True)
risco_dict = {"C100": "Baixo", "C101": "Alto", "C102": "Médio", "C103": "Baixo", "C104": "Alto"}
df["nivel_risco"] = df["id_cliente"].map(risco_dict).fillna("Não mapeado")

filtradas = filtrar_setembro_sp_rj(df)
pivot = criar_pivot_risco(df)
anomalias = detectar_anomalias(df)
fig, diario = criar_grafico_diario(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Transações válidas", f"{len(df):,}".replace(",", "."))
c2.metric("Valor total", f"R$ {df['valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric("Filtro solicitado", len(filtradas))
c4.metric("Anomalias (Z > 2,5)", len(anomalias))

st.subheader("Série diária e média móvel")
st.pyplot(fig)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Pivot: mês × nível de risco")
    st.dataframe(pivot, use_container_width=True)
with col2:
    st.subheader("Anomalias potenciais")
    st.dataframe(anomalias, use_container_width=True)

st.subheader("Filtro: setembro, SP/RJ e valor > R$ 5.000")
st.dataframe(filtradas, use_container_width=True)

if cot_file is not None:
    cotacoes = pd.read_csv(cot_file, encoding="utf-8")
    cotacoes["data"] = pd.to_datetime(cotacoes["data"])
    consolidado = consolidar_com_cotacoes(df, cotacoes)
    st.subheader("Dados consolidados com cotações")
    st.dataframe(consolidado, use_container_width=True)

st.download_button(
    "Baixar transações tratadas",
    df.to_csv(index=False).encode("utf-8-sig"),
    file_name="transacoes_tratadas.csv",
    mime="text/csv",
)
