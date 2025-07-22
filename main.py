import streamlit as st
import pandas as pd
import requests
import datetime


@st.cache_data(ttl="1day")
def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()["conteudo"])
    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(
        datetime.datetime.today().date()
    )
    return df


def calc_df_statics(dados):
    # Dados por data
    df_data = df.groupby(by=["Data"])[["Valor"]].sum()
    # Desloca a linha
    df_data["Evolução Mensal"] = df_data["Valor"] - df_data["Valor"].shift(1)
    # olha para as ultimas x linha e faz uma conta
    df_data["Avg Evolução 6M"] = df_data["Evolução Mensal"].rolling(6).mean()
    df_data["Avg Evolução 12M"] = df_data["Evolução Mensal"].rolling(12).mean()
    df_data["Evolução 6M"] = df_data["Evolução Mensal"].rolling(6).sum()
    df_data["Evolução 12M"] = df_data["Evolução Mensal"].rolling(12).sum()
    df_data["Evolução Mensal Rel."] = df_data["Valor"] / df_data["Valor"].shift(1) - 1
    df_data["Evolução Relativa 6M"] = df_data["Evolução Mensal Rel."].rolling(6).mean()
    df_data["Evolução Relativa 12M"] = (
        df_data["Evolução Mensal Rel."].rolling(12).mean()
    )
    return df_data


def main_metas():
    col1, col2 = st.columns(2)

    data_inicio_meta = col1.date_input("Início da Meta", max_value=df_stats.index.max())
    st.text(data_inicio_meta)
    data_filtrada = df_stats.index[df_stats.index <= data_inicio_meta][-1]

    custos_fixos = col1.number_input("Custos Fixos", min_value=0.0, format="%.2f")
    salario_bruto = col2.number_input("Salário Bruto", min_value=0.0, format="%.2f")
    salario_liq = col2.number_input("Salário Liquido", min_value=0.0, format="%.2f")

    valor_inicio = df_stats.loc[data_filtrada]["Valor"]
    col1.markdown(f"**Patrimônio no Início da Meta**: R$ {valor_inicio:.2f}")

    selic_gov = get_selic()
    filter_selic_date = (selic_gov["DataInicioVigencia"] < data_inicio_meta) & (
        selic_gov["DataFimVigencia"] > data_inicio_meta
    )
    selic_default = selic_gov[filter_selic_date]["MetaSelic"].iloc[0]

    selic = st.number_input("Selic", min_value=0.0, value=selic_default, format="%.2f")
    selic_ano = selic / 100
    selic_mes = (selic_ano + 1) ** (1 / 12) - 1

    rendimento_ano = valor_inicio * selic_ano
    rendimento_mes = valor_inicio * selic_mes

    col1_pot, col2_pot = st.columns(2)
    mensal = salario_liq - custos_fixos + rendimento_mes
    anual = 12 * (salario_liq - custos_fixos) + rendimento_ano

    with col1_pot.container(border=True):
        st.markdown(
            f"""**Potencial Arrecadação Mês**:\n\n R$ {mensal:.2f}""",
            help=f"{salario_liq:.2f} + (-{custos_fixos:.2f}) + {rendimento_mes:.2f}",
        )

    with col2_pot.container(border=True):
        st.markdown(
            f"""**Potencial Arrecadação Ano**:\n\n R$ {anual:.2f}""",
            help=f"12 *({salario_liq:.2f} + (-{custos_fixos:.2f})) + {rendimento_ano:.2f}",
        )

    with st.container(border=True):
        col1_meta, col2_meta = st.columns(2)
        with col1_meta:
            meta_estipulada = st.number_input(
                "Meta Estipulada", min_value=-9999999.0, format="%.2f", value=anual
            )

        with col2_meta:
            patrimonio_final = meta_estipulada + valor_inicio
            st.markdown(f"Patrimônio Estimado pós meta:\n\n R$ {patrimonio_final:.2f}")

    return data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final


st.set_page_config(page_title="Finanças", page_icon="💰")

st.markdown(
    """
# Boas Vindas!
            
## Este será nosso APP Financeiro!
            
Pode ser utilizado para sua organização, fique a vontade!

"""
)

# Widget de captura de upload de dados
file = st.file_uploader(label="Faça upload dos dados aqui", type=["csv"])

# Captura os dados
if file:
    df = pd.read_csv(file)
    df["Valor"] = pd.to_numeric(df["Valor"])
    df["Data"] = pd.to_datetime(
        df["Data"], format="%d/%m/%Y"
    ).dt.date  # Extrai apenas a data

    # Exibiçaõ dos dados no APP
    exp1 = st.expander("Dados Brutos")  # Ele ajuda na organização
    columns_format = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
    exp1.dataframe(
        df, hide_index=True, column_config=columns_format
    )  # pra fazer igual antes era so colocar st.dataframe

    # Visão instituição
    exp2 = st.expander("Instituições")
    df_instituicao = df.pivot_table(
        index="Data", columns="Instituição", values="Valor", aggfunc="sum"
    )

    # Abas para as diferentes visualizações
    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)

    # Datas válidas
    with tab_share:
        date = st.selectbox("Filtro Data", options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[date])

    exp3 = st.expander("Estatísticas Gerais")
    df_stats = calc_df_statics(df)

    columns_config = {
        "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "Evolução Mensal": st.column_config.NumberColumn(
            "Evolução Mensal", format="R$ %.2f"
        ),
        "Avg Evolução 6M": st.column_config.NumberColumn(
            "Avg Evolução 6M", format="R$ %.2f"
        ),
        "Avg Evolução 12M": st.column_config.NumberColumn(
            "Avg Evolução 12M", format="R$ %.2f"
        ),
        "Evolução 6M": st.column_config.NumberColumn("Evolução 6M", format="R$ %.2f"),
        "Evolução 12M": st.column_config.NumberColumn("Evolução 12M", format="R$ %.2f"),
        "Evolução Mensal Rel.": st.column_config.NumberColumn(
            "Evolução Mensal Rel.", format="percent"
        ),
        "Evolução Relativa 6M": st.column_config.NumberColumn(
            "Evolução Relativa 6M", format="percent"
        ),
        "Evolução Relativa 12M": st.column_config.NumberColumn(
            "Evolução Relativa 12M", format="percent"
        ),
    }

    tab_stats, tab_evl, tab_rel = exp3.tabs(
        tabs=["Dados", "Histórico de Evolução", "Crescimento relativo"]
    )

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_evl:
        cols_evl = ["Evolução Mensal", "Avg Evolução 6M", "Avg Evolução 12M"]
        st.line_chart(df_stats[cols_evl])

    with tab_rel:
        cols_rel = [
            "Evolução Mensal Rel.",
            "Evolução Relativa 6M",
            "Evolução Relativa 12M",
        ]
        st.line_chart(df_stats[cols_rel])

    # Começa a parte de Metas
    with st.expander("Metas"):

        tab_main, tab_data_meta, tab_graph = st.tabs(
            tabs=["Configuração", "Dados", "Gráficso"]
        )

        with tab_main:
            data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final = (
                main_metas()
            )

        with tab_data_meta:
            meses = pd.DataFrame(
                {
                    "Data Referência": [
                        (data_inicio_meta + pd.DateOffset(months=i))
                        for i in range(1, 13)
                    ],
                    "Meta Mensal": [
                        valor_inicio + round(meta_estipulada / 12, 2) * i
                        for i in range(1, 13)
                    ],
                }
            )

            meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(
                df_patrimonio["Data"]
            ).dt.strftime("%Y-%m")

            meses = meses.merge(df_patrimonio, how="left", on="Data Referência")

            meses = meses[["Data Referência", "Meta Mensal", "Valor"]]
            meses["Atingimento (%)"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Ano"] = meses["Valor"] / patrimonio_final
            meses["Atingimento Esperado"] = meses["Meta Mensal"] / patrimonio_final
            meses.set_index("Data Referência")

            columns_config_meses = {
                "Meta Mensal": st.column_config.NumberColumn(
                    "Meta Mensal", format="R$ %.2f"
                ),
                "Valor": st.column_config.NumberColumn(
                    "Valor Atingido", format="R$ %.2f"
                ),
                "Atingimento (%)": st.column_config.NumberColumn(
                    "Atingimento (%)", format="percent"
                ),
                "Atingimento Ano": st.column_config.NumberColumn(
                    "Atingimento ano", format="percent"
                ),
                "Atingimento Esperado": st.column_config.NumberColumn(
                    "Atingimento Esperado", format="percent"
                ),
            }

            st.dataframe(meses)

        with tab_graph:
            st.line_chart(meses[["Atingimento Ano", "Atingimento Esperado"]])
