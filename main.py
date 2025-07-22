import streamlit as st
import pandas as pd

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

    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)

    # Datas válidas
    with tab_share:
        date = st.selectbox("Filtro Data", options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[date])
