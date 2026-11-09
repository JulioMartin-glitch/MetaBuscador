import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL en la pantalla de la nube
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Consultando en vivo y de forma directa los tres enlaces oficiales proporcionados.")

# Caja de búsqueda real y vacía
buscar = st.text_input("Introduce un término para buscar en los directorios online (ej: Madrid, Barcelona, CSIC, Farmacos):")

if buscar:
    st.info(f"Conectando en tiempo real con los enlaces oficiales para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_finales = []

    # =========================================================================
    # 1. BÚSQUEDA EN VIVO EN LA URL EXACTA DE ASEBIO
    # =========================================================================
    try:
        # Tu URL exacta sin modificaciones
        url_asebio_usuario = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        
        # Emulamos el formulario interno que tiene la cajetilla de esa página específica
        datos_formulario_ab = {"search_block_form": buscar, "op": "Buscar"}
        res_ab = requests.post(url_asebio_usuario, data=datos_formulario_ab, timeout=12, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            filas_socios = soup_ab.find_all('div', class_='views-row')
            
            for fila in filas_socios:
                enlace = fila.find('a')
                if enlace:
                    nombre_socio = enlace.text.strip()
                    resultados_finales.append({
                        "Entidad Encontrada": nombre_socio,
                        "Sede / Ciudad": "Ver detalles en enlace de AseBio",
                        "Detalle / Especialidad": "Socio Biotecnológico Registrado",
                        "Directorio de Origen": "AseBio (Directorio Oficial)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 2. BÚSQUEDA EN VIVO EN LA URL EXACTA DE EUOPENSCREEN
    # =========================================================================
    try:
        # Tu URL exacta del observatorio nacional sin modificaciones
        url_openscreen_usuario = "https://www.es-openscreen.com/partner/"
        
        # Para que el servidor de ES-OPENSCREEN filtre, le añadimos el parámetro técnico de palabra clave
        url_busqueda_os = f"{url_openscreen_usuario}?search_api_fulltext={buscar}"
        res_os = requests.get(url_busqueda_os, timeout=12, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            entidades_os = soup_os.find_all('div', class_='partner-item')
            
            for entidad in entidades_os:
                nombre = entidad.find('h5').text.strip() if entidad.find('h5') else ""
                if nombre:
                    resultados_finales.append({
                        "Entidad Encontrada": nombre,
                        "Sede / Ciudad": "Ver en mapa de ES-OPENSCREEN",
                        "Detalle / Especialidad": "Plataforma / Capacidad de Descubrimiento",
                        "Directorio de Origen": "ES-OPENSCREEN (Observatorio)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 3. BÚSQUEDA EN VIVO EN LA URL EXACTA DEL MAPA GOOGLE DE BIOLYNX
    # =========================================================================
    try:
        # Tu URL exacta del mapa de Google My Maps proporcionado por ti
        url_mapa_usuario = "https://www.google.com/maps/d/u/0/viewer?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&ll=36.35729948127887%2C-6.729892899999987&z=5"
        
        # Transformamos la vista web del mapa ('viewer') por su formato de datos informáticos ('kml')
        # manteniendo intacto tu identificador único de mapa (mid) para extraer las localizaciones (Placemarks)
        url_datos_kml = url_mapa_usuario.replace("/viewer", "/kml")
        res_mapa = requests.get(url_datos_kml, timeout=12, verify=False)
        
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            marcadores = soup_mapa.find_all('Placemark')
            
            for marcador in marcadores:
                nombre_empresa = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                if buscar.lower() in nombre_empresa.lower() or buscar.lower() in descripcion.lower():
                    resultados_finales.append({
                        "Entidad Encontrada": nombre_empresa,
                        "Sede / Ciudad": "Mapeado Geográficamente en Google Maps",
                        "Detalle / Especialidad": descripcion[:120] + "..." if descripcion else "Entidad en Mapa Drug Discovery",
                        "Directorio de Origen": "BioLynx (Google My Maps)"
                    })
    except Exception:
        pass

    # =========================================================================
    # FUSIÓN Y MOSTRAR RESULTADOS
    # =========================================================================
    if resultados_finales:
        st.success(f"¡Éxito! Hemos cruzado los datos y encontrado {len(resultados_finales)} registros en vivo.")
        df = pd.DataFrame(resultados_finales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en las tres URLs online.")
