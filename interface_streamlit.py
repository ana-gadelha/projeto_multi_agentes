import streamlit as st
import pandas as pd
from sistema_multi_agentes import (
    load_pre_process_data, 
    criar_agentes, 
    criar_tarefas, 
    executar_crew, 
    gerar_pdf,
    gerar_txt
)
import os

#configurando a página Streamlit
st.set_page_config(page_title="Análise da CPI das BETs", layout="wide")
st.title("Análise da CPI das BETs com Multi-Agentes")

uploaded_file = st.file_uploader("Carregue o arquivo CSV com os títulos das notícias aqui", type="csv")

if uploaded_file is not None:
    st.success("Arquivo CSV carregado com sucesso")

    if st.button("Gerar Relatório"):
        try:
            output_pdf = "relatorio_final.pdf"
            output_txt = "relatorio_final.txt" # caminho para salvar o relatorio

            titulos_noticias = load_pre_process_data(uploaded_file)

            agentes = criar_agentes()

            tarefas = criar_tarefas(agentes, titulos_noticias)

            texto_relatorio = executar_crew(agentes, tarefas)

            gerar_pdf(texto_relatorio, output_pdf)
            gerar_txt(texto_relatorio, output_txt)

            st.success(f"Relatório gerado com sucesso!")

            #aqui oferece uma opção para download do arquivo PDF
            with open(output_pdf, "rb") as file_pdf:
                pdf_bytes = file_pdf.read()
            st.download_button(
                label="Baixar Relatório em PDF",
                data=pdf_bytes,
                file_name=output_pdf,
                mime="application/pdf"
            )

            with open(output_txt, "rb") as file_txt:
                txt_bytes = file_txt.read()
            st.download_button(
                label="Baixar Relatório em TXT",
                data=txt_bytes,
                file_name=output_txt,
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Ocorreu um erro durante a geração do relatório: {e}")

else:
    st.info("Por favor, carregue um arquivo CSV para iniciar o processo.")