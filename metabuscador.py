import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos avisos visuales de certificados en la pantalla
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Este motor consulta **en vivo** los directorios externos oficiales al realizar tu búsqueda.")

# Cuadro de texto para el usuario
buscar = st.text_input("Escribe una ciudad, entidad o tecnología (ej: Madrid, Barcelona, Farmacos, Screening):")

if buscar:
    st.info(f"Rastreando en tiempo real en los servidores de AseBio, BioLynx y EU-OPENSCREEN...")
    termino = buscar.lower()
    resultados_globales = []

    # =========================================================================
    # 1. CONSULTA EN VIVO A EU-OPENSCREEN (Vía su base de datos abierta)
    # =========================================================================
    try:
        # Petición al servidor de datos del consorcio europeo
        res_os = requests.get("https://ecbd.eu", timeout=10, verify=False)
        if res_os.status_code == 200:
            nodos = res_os.json()
            for nodo in nodos:
                # Filtramos solo los que coincidan con la búsqueda del usuario
                nombre = nodo.get("name", "")
                ciudad = nodo.get("city", "")
                if termino in nombre.lower() or termino in ciudad.lower():
                    resultados_globales.append({
                        "Entidad": nombre,
                        "Sede": ciudad,
                        "Detalle / Enfoque": nodo.get("siteType", {}).get("name", "Infraestructura de Cribado"),
                        "Directorio de Origen": "EU-OPENSCREEN"
                    })
    except Exception:
        pass # Si el servidor europeo tarda, el buscador sigue con los demás

    # =========================================================================
    # 2. CONSULTA EN VIVO A BIOLYNX (Web Scraping sobre su buscador oficial)
    # =========================================================================
    try:
        # Conectamos con la URL del mapa de empresas de BioLynx mandando el término
        url_bl = f"https://biolynx.es{buscar}"
        res_bl = requests.get(url_bl, timeout=10, verify=False)
        if res_bl.status_code == 200:
            soup = BeautifulSoup(res_bl.text, 'html.parser')
            # El código lee las tarjetas (cards) de empresas que BioLynx genera en su HTML
            tarjetas = soup.find_all('div', class_='company-card') 
            for tarjeta in tarjetas:
                nombre = tarjeta.find('h3').text.strip()
                ciudad = tarjeta.find('span', class_='location').text.strip()
                resultados_globales.append({
                    "Entidad": nombre,
                    "Sede": ciudad,
                    "Detalle / Enfoque": "Empresa / Servicio Bioinformático",
                    "Directorio de Origen": "BioLynx"
                })
    except Exception:
        pass

    # =========================================================================
    # 3. CONSULTA EN VIVO A ASEBIO (Web Scraping sobre su buscador oficial)
    # =========================================================================
    try:
        # Conectamos con la URL de la base de datos de socios de AseBio
        url_ab = f"https://asebio.com{buscar}"
        res_ab = requests.get(url_ab, timeout=10, verify=False)
        if res_ab.status_code == 200:
            soup = BeautifulSoup(res_ab.text, 'html.parser')
            # El código lee el listado de empresas asociadas que devuelve AseBio en su HTML
            filas_empresas = soup.find_all('div', class_='views-row')
            for fila in filas_empresas:
                nombre = fila.find('a').text.strip()
                resultados_globales.append({
                    "Entidad": nombre,
                    "Sede": "Consultar en web", # AseBio requiere un segundo clic para la sede
                    "Detalle / Enfoque": "Socio Industrial / Empresa BIO",
                    "Directorio de Origen": "AseBio"
                })
    except Exception:
        pass

    # =========================================================================
    # MOSTRAR LA FUSIÓN DE RESULTADOS EN TU WORDPRESS
    # =========================================================================
    if resultados_globales:
        st.success(f"¡Éxito! Hemos encontrado {len(resultados_globales)} resultados combinados.")
        df = pd.DataFrame(resultados_globales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se han encontrado entidades que coincidan con '{buscar}' en los directorios externos.")
