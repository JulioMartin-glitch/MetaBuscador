import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Consulta directa y en vivo a los directorios web configurados.")

buscar = st.text_input("Introduce el término a buscar en los directorios online (ej: Madrid, Barcelona, Farmacos, CSIC):")

if buscar:
    st.info(f"Conectando en vivo con los servidores para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_finales = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # =========================================================================
    # 1. FUENTE: ASEBIO (Directorio web)
    # =========================================================================
    try:
        url_asebio = f"https://www.asebio.com/socios/directorio-empresas-biotecnologia?title={buscar}"
        res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            # Buscamos filas o contenedores comunes en listados de Drupal
            filas_socios = soup_ab.find_all('div', class_='views-row')
            if not filas_socios:
                # Intento alternativo de selector si cambia la estructura
                filas_socios = soup_ab.select('.view-content .item, .views-field-title')

            for fila in filas_socios:
                enlace = fila.find('a') if hasattr(fila, 'find') else None
                texto_entidad = enlace.text.strip() if enlace else fila.text.strip()
                if texto_entidad and len(texto_entidad) < 100:
                    resultados_finales.append({
                        "Entidad Encontrada": texto_entidad,
                        "Ubicación / Sede": "Consultar en directorio AseBio",
                        "Rol / Detalle": "Socio Biotecnológico Registrado",
                        "Directorio de Origen": "AseBio"
                    })
    except Exception as e:
        st.warning(f"Aviso en fuente AseBio: {e}")

    # =========================================================================
    # 2. FUENTE: ES-OPENSCREEN
    # =========================================================================
    try:
        url_openscreen = f"https://www.es-openscreen.com/partner/?search_api_fulltext={buscar}"
        res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            entidades_os = soup_os.find_all(['div', 'article'], class_=lambda x: x and 'partner' in x)
            for entidad in entidades_os:
                nombre_elem = entidad.find(['h5', 'h4', 'h3', 'a'])
                if nombre_elem:
                    nombre = nombre_elem.text.strip()
                    resultados_finales.append({
                        "Entidad Encontrada": nombre,
                        "Ubicación / Sede": "Ver en mapa de ES-OPENSCREEN",
                        "Rol / Detalle": "Plataforma / Capacidad Mapeada",
                        "Directorio de Origen": "ES-OPENSCREEN"
                    })
    except Exception as e:
        st.warning(f"Aviso en fuente ES-OpenScreen: {e}")

    # =========================================================================
    # 3. FUENTE: MAPA GOOGLE (BIOLYNX / KML)
    # =========================================================================
    try:
        url_mapa_exacta = "https://www.google.com/maps/d/u/0/viewer?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI"
        url_kml_real = url_mapa_exacta.replace("/viewer", "/kml") + "&output=kml"
        res_mapa = requests.get(url_kml_real, headers=headers, timeout=10, verify=False)
        
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            marcadores = soup_mapa.find_all('Placemark')
            for marcador in marcadores:
                nombre_empresa = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                if termino in nombre_empresa.lower() or termino in descripcion.lower():
                    resultados_finales.append({
                        "Entidad Encontrada": nombre_empresa,
                        "Ubicación / Sede": "Mapeado en Google My Maps",
                        "Rol / Detalle": descripcion[:100] + "..." if descripcion else "Entidad en Mapa Drug Discovery",
                        "Directorio de Origen": "BioLynx (Mapa)"
                    })
    except Exception as e:
        st.warning(f"Aviso en fuente Mapa: {e}")

    # =========================================================================
    # RENDERIZADO EN PANTALLA
    # =========================================================================
    # Eliminamos duplicados basados en el nombre de la entidad
    df_temp = pd.DataFrame(resultados_finales)
    if not df_temp.empty:
        df_temp = df_temp.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Éxito! Se han encontrado {len(df_temp)} registros coincidentes.")
        st.dataframe(df_temp, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia directa para '{buscar}'. Prueba con un término más general (ej: 'Madrid', 'Bio', 'Pharma').")
