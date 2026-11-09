import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de certificados de seguridad en la pantalla de la nube
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Español", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Consultando en vivo **AseBio**, **ES-OPENSCREEN** y el Mapa Drug Discovery de **BioLynx**.")

# Caja de búsqueda vacía y real para el usuario de tu WordPress
buscar = st.text_input("Introduce un término para rastrear en los 3 directorios online (ej: Madrid, Barcelona, Farmacos, CSIC):")

if buscar:
    st.info(f"Conectando en tiempo real con los directorios oficiales para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_totales = 

    # =========================================================================
    # 1. CONSULTA EN VIVO A ASEBIO (Tu URL Oficial)
    # =========================================================================
    try:
        # Apuntamos directamente a la URL de su buscador de socios corporativos
        url_asebio = f"https://asebio.com{buscar}"
        respuesta_ab = requests.get(url_asebio, timeout=10, verify=False)
        
        if respuesta_ab.status_code == 200:
            soup_ab = BeautifulSoup(respuesta_ab.text, 'html.parser')
            # Extraemos las tarjetas o bloques de los socios biotecnológicos asociados
            bloques_socios = soup_ab.find_all('div', class_='views-row')
            
            for socio in bloques_socios:
                # Buscamos el nombre del socio dentro del enlace de la tarjeta
                enlace_nombre = socio.find('a')
                if enlace_nombre:
                    nombre = enlace_nombre.text.strip()
                    resultados_totales.append({
                        "Entidad Encontrada": nombre,
                        "Ubicación / Datos": "Consultar Ficha en Web",
                        "Enfoque / Descripción": "Socio Industrial de la Asociación",
                        "Directorio de Origen": "AseBio España"
                    })
    except Exception:
        pass

    # =========================================================================
    # 2. CONSULTA EN VIVO A ES-OPENSCREEN (Tu URL Oficial del Observatorio)
    # =========================================================================
    try:
        # Conectamos con el Observatorio de Capacidades de Descubrimiento de Fármacos
        url_openscreen = f"https://es-openscreen.com{buscar}"
        respuesta_os = requests.get(url_openscreen, timeout=10, verify=False)
        
        if respuesta_os.status_code == 200:
            soup_os = BeautifulSoup(respuesta_os.text, 'html.parser')
            # Buscamos las filas o registros de laboratorios y plataformas científicas
            plataformas = soup_os.find_all('div', class_='partner-item') # Ajustado al estándar de su motor de mapas
            
            for plat in plataformas:
                nombre = plat.find('h5').text.strip() if plat.find('h5') else ""
                tipo_org = plat.find('span', class_='org-type').text.strip() if plat.find('span', class_='org-type') else "Plataforma de Descubrimiento"
                if nombre:
                    resultados_totales.append({
                        "Entidad Encontrada": nombre,
                        "Ubicación / Datos": "Nodo Nacional Asociado",
                        "Enfoque / Descripción": tipo_org,
                        "Directorio de Origen": "ES-OPENSCREEN (Observatorio)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 3. BÚSQUEDA EN VIVO EN EL MAPA GOOGLE MY MAPS (BIOLYNX)
    # =========================================================================
    try:
        # Mantenemos la conexión directa al mapa de puntos que nos facilitaste antes
        url_mapa = "https://google.com"
        respuesta_mapa = requests.get(url_mapa, timeout=10, verify=False)
        
        if respuesta_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(respuesta_mapa.text, 'xml')
            lugares = soup_mapa.find_all('Placemark')
            
            for lugar in lugares:
                nombre_empresa = lugar.find('name').text.strip() if lugar.find('name') else ""
                descripcion = lugar.find('description').text.strip() if lugar.find('description') else ""
                
                if termino in nombre_empresa.lower() or termino in descripcion.lower():
                    resultados_totales.append({
                        "Entidad Encontrada": nombre_empresa,
                        "Ubicación / Datos": "Mapeado Geográficamente",
                        "Enfoque / Descripción": descripcion[:100] + "..." if descripcion else "Mapeado en Red Drug Discovery",
                        "Directorio de Origen": "BioLynx (Google My Maps)"
                    })
    except Exception:
        pass

    # =========================================================================
    # RENDERIZADO DE LA TABLA FUSIONADA EN TU WORDPRESS
    # =========================================================================
    if resultados_totales:
        st.success(f"¡Éxito! Hemos cruzado los datos y encontrado {len(resultados_totales)} registros en vivo.")
        df = pd.DataFrame(resultados_totales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en los directorios online en este momento.")

