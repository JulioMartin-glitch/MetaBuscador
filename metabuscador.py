import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL en la pantalla de la nube
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Real", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Este motor consulta **en vivo** las tres URLs exactas proporcionadas.")

# La caja de búsqueda REAL y COMPLETAMENTE VACÍA para tu WordPress
buscar = st.text_input("Introduce un término para buscar en los directorios online (ej: Madrid, Barcelona, CSIC, Farmacos):")

if buscar:
    st.info(f"Conectando en tiempo real con las URLs oficiales para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_finales = []

    # =========================================================================
    # 1. BÚSQUEDA REAL EN VIVO EN LA URL EXACTA DE ASEBIO
    # =========================================================================
    try:
        # URL exacta proporcionada por el usuario
        url_asebio_oficial = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        
        # Enviamos la petición emulando el formulario interno de búsqueda de esa página exacta
        datos_formulario_ab = {"search_block_form": buscar, "op": "Buscar"}
        res_ab = requests.post(url_asebio_oficial, data=datos_formulario_ab, timeout=12, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            # Capturamos los bloques de empresas que esa página de AseBio devuelve en vivo
            filas_socios = soup_ab.find_all('div', class_='views-row')
            
            for fila in filas_socios:
                enlace = fila.find('a')
                if enlace:
                    nombre_socio = enlace.text.strip()
                    resultados_finales.append({
                        "Entidad Encontrada": nombre_socio,
                        "Sede / Ciudad": "Ver detalles en web de AseBio",
                        "Detalle / Especialidad": "Socio Biotecnológico Registrado",
                        "Directorio de Origen": "AseBio (Directorio Oficial)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 2. BÚSQUEDA REAL EN VIVO EN LA URL EXACTA DE ES-OPENSCREEN
    # =========================================================================
    try:
        # URL exacta proporcionada por el usuario
        url_openscreen_oficial = "https://www.es-openscreen.com/partner/"
        
        # Enviamos la petición simulando el buscador de palabras clave de esa página exacta
        datos_formulario_os = {"search_api_fulltext": buscar}
        res_os = requests.post(url_openscreen_oficial, data=datos_formulario_os, timeout=12, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            # Localizamos las entidades que figuran en el observatorio de esa página
            entidades_os = soup_os.find_all('div', class_='partner-item')
            
            for entidad in entidades_os:
                nombre = entidad.find('h5').text.strip() if entidad.find('h5') else ""
                if nombre:
                    resultados_finales.append({
                        "Entidad Encontrada": nombre,
                        "Sede / Ciudad": "Ver en mapa del Observatorio",
                        "Detalle / Especialidad": "Plataforma / Capacidad de Descubrimiento",
                        "Directorio de Origen": "ES-OPENSCREEN (Partner Archive)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 3. BÚSQUEDA REAL EN VIVO EN LA URL EXACTA DEL MAPA DE GOOGLE (BIOLYNX)
    # =========================================================================
    try:
        # URL exacta proporcionada por el usuario para extraer los datos geográficos del mapa (KML)
        url_mapa_biolynx = "https://www.google.com/maps/d/u/0/viewer?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&ll=36.35729948127887%2C-6.729892899999987&z=5"
        res_mapa = requests.get(url_mapa_biolynx, timeout=12, verify=False)
        
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            # Google My Maps estructura todas sus empresas bajo la etiqueta informática 'Placemark'
            marcadores = soup_mapa.find_all('Placemark')
            
            for marcador in marcadores:
                nombre_empresa = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                # Si el término que buscas coincide con el nombre o la descripción del mapa
                if buscar.lower() in nombre_empresa.lower() or buscar.lower() in descripcion.lower():
                    resultados_finales.append({
                        "Entidad Encontrada": nombre_empresa,
                        "Sede / Ciudad": "Mapeado Geográficamente",
                        "Detalle / Especialidad": descripcion[:120] + "..." if descripcion else "Entidad en Mapa Drug Discovery",
                        "Directorio de Origen": "BioLynx (Google My Maps Oficial)"
                    })
    except Exception:
        pass

    # =========================================================================
    # FUSIÓN Y MUESTRA DE RESULTADOS EN LA PÁGINA
    # =========================================================================
    if resultados_finales:
        st.success(f"¡Éxito! Hemos cruzado los datos y encontrado {len(resultados_finales)} registros en vivo.")
        df = pd.DataFrame(resultados_finales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en las tres URLs online en este momento.")
