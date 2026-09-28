from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}


def carregar_e_tratar_transacoes(caminho: str | Path) -> pd.DataFrame:
    """Lê, limpa e enriquece as transações conforme os requisitos do exercício."""
    df = pd.read_csv(caminho, encoding="latin1")

    # Imputação vetorizada: NaN recebe a mediana do valor dentro do próprio estado.
    mediana_estado = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(mediana_estado)

    # Coluna estática para rastreabilidade do pipeline.
    df["plataforma"] = "Mobile"

    # Conversão temporal e localização no fuso de São Paulo.
    df["data_transacao"] = pd.to_datetime(df["data_transacao"])
    df["data_transacao"] = df["data_transacao"].dt.tz_localize("America/Sao_Paulo")

    # Engenharia temporal com o acessor .dt.
    df["dia_semana"] = df["data_transacao"].dt.day_name()
    df["mes"] = df["data_transacao"].dt.month

    # Remove registros totalmente duplicados, preservando a primeira ocorrência.
    df = df.drop_duplicates(keep="first").reset_index(drop=True)

    # Atribuição de risco obrigatoriamente via .map().
    df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT).fillna("Não mapeado")
    return df


def filtrar_setembro_sp_rj(df: pd.DataFrame) -> pd.DataFrame:
    """Filtro vetorizado usando explicitamente operadores bitwise & e |."""
    filtro = (
        (df["mes"] == 9)
        & ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
        & (df["valor"] > 5000)
    )
    return df.loc[filtro].copy()


def criar_pivot_risco(df: pd.DataFrame) -> pd.DataFrame:
    return pd.pivot_table(
        df,
        index="mes",
        columns="nivel_risco",
        values="valor",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
        fill_value=0,
    )


def adicionar_zscore_por_estado(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula Z-Score por estado sem laços for, usando groupby.transform."""
    media = df.groupby("estado_cliente")["valor"].transform("mean")
    desvio = df.groupby("estado_cliente")["valor"].transform("std")

    resultado = df.copy()
    resultado["z_score"] = (resultado["valor"] - media) / desvio.replace(0, np.nan)
    return resultado


def detectar_anomalias(df: pd.DataFrame, limite: float = 2.5) -> pd.DataFrame:
    com_zscore = adicionar_zscore_por_estado(df)
    return com_zscore.loc[com_zscore["z_score"] > limite].copy()


def resumo_diario(df: pd.DataFrame) -> pd.DataFrame:
    diario = (
        df.assign(data=df["data_transacao"].dt.date)
        .groupby("data", as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "total_diario"})
    )
    diario["media_movel_7d"] = diario["total_diario"].rolling(7).mean()
    return diario


def criar_grafico_diario(df: pd.DataFrame):
    diario = resumo_diario(df)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(diario["data"], diario["total_diario"], label="Total diário")
    ax.plot(diario["data"], diario["media_movel_7d"], label="Média móvel de 7 dias")
    ax.set_ylim(bottom=0)
    ax.set_title("Desempenho diário das transações")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor total (R$)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig, diario


def carregar_cotacoes(caminho: str | Path) -> pd.DataFrame:
    """Lê o segundo arquivo disponibilizado pela engenharia, preservando NaNs existentes."""
    cotacoes = pd.read_csv(caminho, encoding="utf-8")
    cotacoes["data"] = pd.to_datetime(cotacoes["data"])
    return cotacoes


def consolidar_com_cotacoes(df: pd.DataFrame, cotacoes: pd.DataFrame) -> pd.DataFrame:
    """Consolida pela data civil; não inventa valores para cotações ausentes."""
    base = df.copy()
    base["data"] = base["data_transacao"].dt.tz_localize(None).dt.normalize()
    return base.merge(cotacoes, on="data", how="left")


def executar_pipeline(pasta_dados: str | Path = ".", pasta_saida: str | Path = "saida") -> dict:
    pasta_dados = Path(pasta_dados)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    transacoes = carregar_e_tratar_transacoes(pasta_dados / "transacoes.csv")
    filtradas = filtrar_setembro_sp_rj(transacoes)
    pivot = criar_pivot_risco(transacoes)
    anomalias = detectar_anomalias(transacoes)
    fig, diario = criar_grafico_diario(transacoes)

    transacoes.to_csv(pasta_saida / "transacoes_tratadas.csv", index=False, encoding="utf-8-sig")
    filtradas.to_csv(pasta_saida / "transacoes_filtradas.csv", index=False, encoding="utf-8-sig")
    pivot.to_csv(pasta_saida / "pivot_risco.csv", encoding="utf-8-sig")
    anomalias.to_csv(pasta_saida / "anomalias.csv", index=False, encoding="utf-8-sig")
    diario.to_csv(pasta_saida / "resumo_diario.csv", index=False, encoding="utf-8-sig")
    fig.savefig(pasta_saida / "transacoes_diarias.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    cotacoes_path = pasta_dados / "cotacoes.csv"
    consolidado = None
    if cotacoes_path.exists():
        cotacoes = carregar_cotacoes(cotacoes_path)
        consolidado = consolidar_com_cotacoes(transacoes, cotacoes)
        consolidado.to_csv(pasta_saida / "dados_consolidados.csv", index=False, encoding="utf-8-sig")

    return {
        "transacoes": transacoes,
        "filtradas": filtradas,
        "pivot": pivot,
        "anomalias": anomalias,
        "diario": diario,
        "consolidado": consolidado,
    }


if __name__ == "__main__":
    resultado = executar_pipeline()
    print(f"Transações tratadas: {len(resultado['transacoes'])}")
    print(f"Filtro setembro/SP-RJ/>5000: {len(resultado['filtradas'])}")
    print(f"Anomalias Z > 2.5: {len(resultado['anomalias'])}")
    print("Arquivos gerados na pasta 'saida'.")
