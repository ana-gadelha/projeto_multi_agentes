import pandas as pd
#import re # biblioteca para limpeza de textos
#import unicodedata # biblioteca para normalização de caracteres
from crewai import Agent, Crew, Process, Task
from fpdf import FPDF
from dotenv import load_dotenv
from textwrap import dedent
import os


load_dotenv()

def load_pre_process_data(file_path: str) -> list:
    df = pd.read_csv(file_path, encoding='utf-8')
    titulos = df["Título"].dropna().astype(str).tolist()

    titulos_limpos = []
    for titulo in titulos:
        texto = titulo.strip().replace("“", '"').replace("”", '"').replace("’", "'")
        texto = " ".join(texto.split())
        titulos_limpos.append(texto)

    return titulos_limpos


def criar_agentes() -> dict:
    gerente = Agent(
        role="Gerente de Análise da CPI das BETs",
        goal="Extrair o máximo de dados relevantes sobre a CPI das BETS organizando as informações de forma estruturada para    facilitar a análise do executor e a redação do relator",
        backstory="Você é um especialista em investigação parlamentar, com 20 anos de experiência em CPIs. Sua principal missão é criar um plano de ação detalhado, decidindo o que deve ser analisado nas notícias (como nomes, datas, sentimentos, categorias) e organizar tudo isso para a equipe.",
        llm="gpt-4",
        verbose=True,
        allow_delegation=False
    )

    executor = Agent(
        role="Analista Técnico",
        goal="Examinar os títulos e extrair as principais informações, eventos e tendências sobre a CPI das BETs, conforme definido pelo gerente",
        backstory="Você é um ex-analista de inteligência, com mais de 20 anos de experiência, especializado em análise de dados e linguagem natural. Sua missão é identificar temas, nomes importantes, datas, sentimentos e categorias nas notícias sobre a CPI das BETs. Também deverá montar uma linha do tempo dos eventos.",
        llm="gpt-4",
        verbose=True,
        allow_delegation=False
    )

    relator = Agent(
        role="Redator Final",
        goal="Escrever um relatório claro, completo e bem estruturado, com base na análise da CPI das BETs.",
        backstory="Você é um especialista em comunicação legislativa, com experiência em transformar dados complexos em relatórios acessíveis. Seu papel é organizar todas as informações encontradas pelo executor em um relatório bem dividido, explicativo e com impacto político, e de fácil compreensão.",      
        llm="gpt-4",
        verbose=True,
        allow_delegation=False
    )
    
    return {"gerente": gerente, "executor": executor, "relator": relator}


def criar_tarefas(agentes: dict, titulos: list) -> list:
    titulos_texto = "\n- " + "\n- ".join(titulos)
    
    tarefa_gerente = Task(
        agent=agentes["gerente"],
        description=dedent(f"""
            Sua função é analisar os títulos a seguir sobre a CPI das BETs e criar um plano de ação detalhado que oriente os outros agentes.
                           
            O plano deve incluir:
            - Que tipo de análise será feita (resumo, temas principais, datas, nomes, categorias, sentimentos).
            - Quais informações deem ser priorizadas.
            - Como o executor deve extrair os dados.
            - Como o relatordeve montar o relatório.
                           
            Aqui estão os títulos:
            {titulos_texto}

            Escreva um plano de ação bem, estruturado para orientar a equipe.
        """),
        expected_output="Plano de ação com instruções claras para o executor e para o relator."
    )

    tarefa_executor = Task(
        agent=agentes["executor"],
        description=dedent(f"""
            Com base no plano de ação fornecido pelo gerente, analise os títulos de notícias abaixo.
                           
            Para cada título:
            - Gere um pequeno resumo
            - Extraia nomes de pessoas e instituições
            - Identifique datas relevantes
            - Classifique o sentimento (positivo, negativo, neutro)
            - Categorize o tema (ex: política, jogos, lavagem de dinheiro)
            - Organize essas informações em uma estrutura clara
                           
            O resultado deve ser um conjunto de dados organizado com as análises realizadas.
                           
            Títulos:
            {titulos_texto}
        """),
        expected_output="Análise detalhada dos títulos, incluindo resumos, sentimentos, categorias e eventos organizados."
    )

    tarefa_relator = Task(
        agent=agentes["relator"],
        description=dedent("""
            Com base na análise feita pelo executor, escreva um relatório final bem estruturado.
                           
            O relatório deve conter:
            - Resumo Executivo (com visão geral dos principais temas e descobertas)
            - Lista dos Principais Envolvidos (nomes e suas funções)
            - Linha do Tempo (eventos em ordem cronológica)
            - Análise de Sentimento (visão geral do tom das notícias)
            - Categorias (agrupamentos temáticos dos títulos)
                           
            Seja claro, objetivo e use uma linguagem acessível ao público em geral.
        """),
        expected_output="Relatório final claro, organizado, dividido por seções, e com linguagem acessível."           
    )

    return [tarefa_gerente, tarefa_executor, tarefa_relator]

    
def executar_crew(agentes: dict, tarefas: list) -> str:

    crew = Crew(
        agents=list(agentes.values()),
        tasks=tarefas,
        process=Process.sequential # este comndo garante a execução em ordem( 1º gerente, 2º executor, 3º relator)
    )

    crew.kickoff() # aqui roda o sistema multiagentes
    return tarefas[-1].output.raw #retorna o resultado (texto) da última tarefa (relatório final do Relator)
  

def gerar_pdf(conteudo: str, nome_arquivo: str = "rlatorio_final.pdf") -> str:

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, conteudo)
    pdf.output(nome_arquivo)
    print(f"Relatório .pdf salvo como: {nome_arquivo}")
    return nome_arquivo


def gerar_txt(conteudo: str, nome_arquivo: str = "relatorio_final.txt") -> str:
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
    print(f"Relatório .txt salvo como: {nome_arquivo}")
    return nome_arquivo
    
# este é o bloco principal para executar o processo completog
if __name__ == "__main__":
    #aqui ele carrega e pré-processa os títulos das notícias a partir do arquivo .csv de entrada
    csv_file = "limpeza/noticias_filtradas_cpi.csv"
    titulos = load_pre_process_data(csv_file)

    # cria os agentes
    agentes = criar_agentes()

    # cria as tarefas para cada agente utilizando os títulos pré-processados
    tarefas = criar_tarefas(agentes, titulos)

    # executa a CREW - sequencia de tarefas multiagentes - e obtém o texto do relatório final
    texto_relatorio = executar_crew(agentes, tarefas)

    print(texto_relatorio)
    print("\n\n")
    # Gera o relatório final em, formato PDF a partir do texto produzido
    gerar_pdf(texto_relatorio, "relatorio_final.pdf")
    gerar_txt(texto_relatorio, "relatorio_final.txt")
    