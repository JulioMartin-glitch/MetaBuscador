import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")

buscar = st.text_input("Introduce el término a buscar (ej: Madrid, Barcelona, CSIC, Farmacos):")

if buscar:
    termino = buscar.strip().lower()
    st.info(f"Buscando en vivo para: **'{buscar}'**...")
    resultados_finales = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # =========================================================================
    # 1. FUENTE: MAPA BIOLYNX / GOOGLE MY MAPS (KML Completo - ¡Funcionando!)
    # =========================================================================
    with st.spinner("Consultando Mapa BioLynx..."):
        try:
            url_mapa_kml = "https://www.google.com/maps/d/u/0/kml?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&forcekml=1"
            res_mapa = requests.get(url_mapa_kml, headers=headers, timeout=12, verify=False)
            
            if res_mapa.status_code == 200:
                soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
                marcadores = soup_mapa.find_all('Placemark')
                
                for marcador in marcadores:
                    nombre = marcador.find('name').text.strip() if marcador.find('name') else ""
                    descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                    
                    if termino in nombre.lower() or termino in descripcion.lower():
                        resultados_finales.append({
                            "Entidad Encontrada": nombre,
                            "Ubicación / Sede": "Mapeado en España",
                            "Rol / Detalle": descripcion[:120] + "..." if len(descripcion) > 120 else descripcion,
                            "Directorio de Origen": "BioLynx (Mapa)"
                        })
        except Exception as e:
            st.error(f"Error en BioLynx: {e}")

    # =========================================================================
    # 2. FUENTE: ASEBIO (Directorio General)
    # =========================================================================
    with st.spinner("Consultando directorio AseBio..."):
        try:
            url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
            res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
            
            if res_ab.status_code == 200:
                soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
                # Buscamos todos los bloques o enlaces que contengan nombres de empresas asociadas
                # Asebio suele listar las entidades en elementos de tipo tarjeta o listados de texto
                elementos_socios = soup_ab.find_all(['div', 'span', 'a'], class_=lambda x: x and ('socio' in x or 'title' in x or 'name' in x))
                
                for el in elementos_socios:
                    texto = el.text.strip()
                    # Filtramos textos lógicos que parezcan nombres de empresas y contengan el término buscado
                    if termino in texto.lower() and 3 < len(texto) < 80:
                        resultados_finales.append({
                            "Entidad Encontrada": texto,
                            "Ubicación / Sede": "Directorio AseBio",
                            "Rol / Detalle": "Socio / Empresa Biotecnológica",
                            "Directorio de Origen": "AseBio"
                        })
        except Exception as e:
            st.error(f"Error en AseBio: {e}")

    # =========================================================================
    # 3. FUENTE: ES-OPENSCREEN (Observatorio de Partners)
    # =========================================================================
    with st.spinner("Consultando ES-OPENSCREEN..."):
        try:
            url_openscreen = "https://www.es-openscreen.com/partner/"
            res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
            
            if res_os.status_code == 200:
                soup_os = BeautifulSoup(res_os.text, 'html.parser')
                # Capturamos los títulos de los post/partners de la estructura WordPress
                titulos_partners = soup_os.find_all(['h3', 'h4', 'h5', 'strong'])
                
                for t in titulos_partners:
                    texto = t.text.strip()
                    if termino in texto.lower() and len(texto) > 3:
                        resultados_finales.append({
                            "Entidad Encontrada": texto,
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": "Nodo / Entidad Asociada",
                            "Directorio de Origen": "ES-OPENSCREEN"
                        })
        except Exception as e:
            st.error(f"Error en ES-OpenScreen: {e}")

    # =========================================================================
    # RENDERIZADO FINAL EN TABLA
    # =========================================================================
    df_temp = pd.DataFrame(resultados_finales)
    if not df_temp.empty:
        # Eliminamos duplicados exactos por nombre de entidad
        df_temp = df_temp.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Se han consolidado {len(df_temp)} registros de las tres fuentes!")
        st.dataframe(df_temp, use_container_width=True)
    else:
        st.warning(f"No se han encontrado coincidencias para '{buscar}'. Prueba con términos más amplios como 'Bio', 'Madrid', 'Pharma' o 'Universidad'.")
