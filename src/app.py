import streamlit as st
from loguru import logger
from datetime import datetime, timedelta
import sys

from generic_crawler import GenericCrawler

st.set_page_config(page_title="Crawler de Voos", page_icon="✈️")

st.title("🛫 Crawler de Voos")

st.markdown("""
    <style>
    .main {
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

logger.remove()
logger.add(sys.stderr, level="INFO")

def execute_crawler(company, origin, destination, departure_date, return_date):
    try:
        logger.info(f"Iniciando crawler para {company}")
        crawler = GenericCrawler(company)
        crawler.start(origin, destination, departure_date, return_date)
        return True, "Crawler executado com sucesso!"
    except Exception as e:
        error_msg = f"Erro ao executar o crawler: {e}"
        logger.error(error_msg)
        return False, error_msg

with st.sidebar:
    st.header("Parâmetros do Crawler")
    
    company = st.selectbox(
        "Companhia Aérea:",
        ["Latam", "Gol", "Azul", "Avianca"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Origem (IATA):", value="GRU", max_chars=3)
    with col2:
        destination = st.text_input("Destino (IATA):", value="CGB", max_chars=3)
    
    today = datetime.now()
    future_date = today + timedelta(days=30)
    
    departure_date = st.date_input(
        "Data de Ida:",
        value=today,
        min_value=today
    )
    
    return_date = st.date_input(
        "Data de Volta:",
        value=future_date,
        min_value=departure_date
    )
    
    execute_button = st.button("Executar Crawler", type="primary")

main_container = st.container()

with main_container:
    st.subheader("Parâmetros Selecionados")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Companhia**: {company}")
        st.info(f"**Rota**: {origin} → {destination}")
    with col2:
        st.info(f"**Data de Ida**: {departure_date.strftime('%Y-%m-%d')}")
        st.info(f"**Data de Volta**: {return_date.strftime('%Y-%m-%d')}")
    
    if execute_button:
        st.subheader("Status da Execução")
        
        with st.spinner("Executando crawler..."):
            success, message = execute_crawler(
                company,
                origin,
                destination,
                departure_date.strftime("%Y-%m-%d"),
                return_date.strftime("%Y-%m-%d")
            )
        
        if success:
            st.success(message)
        else:
            st.error(message)

with st.expander("Sobre o Crawler"):
    st.write("""
    Esta aplicação permite executar o crawler de voos para diferentes companhias aéreas.
    Utilize os códigos IATA dos aeroportos para origem e destino.
    """)
    st.info("Desenvolvido para extrair dados de voos de companhias aereas.")