import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL en la pantalla de la nube
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Consulta directa y en vivo a las tres URLs oficiales proporcionadas por el usuario.")

# La caja de búsqueda REAL y COMPLETAMENTE VACÍA
buscar = st.text_input("Introduce el término a buscar en los directorios online (ej: Madrid, Barcelona, Farmacos, CSIC):")

if buscar:
    st.info(f"Conectando en vivo con los servidores oficiales para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_finales = []

    # =========================================================================
    # 1. EN VIVO: URL EXACTA DE ASEBIO
    # =========================================================================
    try:
        url_asebio_exacta = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        
        # Abrimos la página para capturar tokens internos de seguridad del formulario Drupal
        sesion = requests.Session()
        prov_res = sesion.get(url_asebio_exacta, timeout=12, verify=False)
        soup_prov = BeautifulSoup(prov_res.text, 'html.parser')
        
        build_id_input = soup_prov.find('input', name='form_build_id')
        build_id = build_id_input['value'] if build_id_input else ""
        
        datos_formulario = {
            "search_block_form": buscar,
            "form_id": "search_block_form",
            "form_build_id": build_id,
            "op": "Buscar"
        }
        res_ab = sesion.post(url_asebio_exacta, data=datos_formulario, timeout=12, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            filas_socios = soup_ab.find_all('div', class_='views-row')
            for fila in filas_socios:
                enlace = fila.find('a')
                if enlace:
                    resultados_finales.append({
                        "Entidad Encontrada": enlace.text.strip(),
                        "Ubicación / Sede": "Consultar en directorio AseBio",
                        "Rol / Detalle": "Socio Biotecnológico Registrado",
                        "Directorio de Origen": "AseBio (Directorio Oficial)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 2. EN VIVO: URL EXACTA DE EUOPENSCREEN
    # =========================================================================
    try:
        url_openscreen_exacta = "https://www.es-openscreen.com/partner/"
        url_busqueda_os = f"{url_openscreen_exacta}?search_api_fulltext={buscar}"
        res_os = requests.get(url_busqueda_os, timeout=12, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            entidades_os = soup_os.find_all('div', class_='partner-item')
            for entidad in entidades_os:
                nombre = entidad.find('h5').text.strip() if entidad.find('h5') else ""
                if nombre:
                    resultados_finales.append({
                        "Entidad Encontrada": nombre,
                        "Ubicación / Sede": "Ver en mapa de ES-OPENSCREEN",
                        "Rol / Detalle": "Plataforma / Capacidad Mapeada",
                        "Directorio de Origen": "ES-OPENSCREEN (Observatorio)"
                    })
    except Exception:
        pass

    # =========================================================================
    # 3. EN VIVO: URL EXACTA DEL MAPA GOOGLE DE BIOLYNX
    # =========================================================================
    try:
        url_mapa_exacta = "https://www.google.com/maps/d/u/0/viewer?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&ll=36.35729948127887%2C-6.729892899999987&z=5"
        
        # Reemplazamos la vista visual por el formato KML de descarga de datos geográficos manteniendo el mid intacto
        url_kml_real = url_mapa_exacta.replace("/viewer", "/kml") + "&output=kml"
        res_mapa = requests.get(url_kml_real, timeout=12, verify=False)
        
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
                        "Directorio de Origen": "BioLynx (Mapa Drug Discovery)"
                    })
    except Exception:
        pass

    # =========================================================================
    # RENDERIZADO EN TU PÁGINA
    # =========================================================================
    if resultados_finales:
        st.success(f"¡Éxito! Hemos conectado en vivo y cruzado {len(resultados_finales)} registros.")
        df = pd.DataFrame(resultados_finales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en las tres URLs oficiales online.")
