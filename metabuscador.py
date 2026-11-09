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
    st.info(f"Buscando coincidencia exacta para: **'{buscar}'**...")
    resultados_finales = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # =========================================================================
    # 1. FUENTE: MAPA BIOLYNX / GOOGLE MY MAPS (KML Completo)
    # Explicación: Descargamos la base de datos geográfica completa del mapa 
    # y filtramos localmente en memoria para no perder ningún registro.
    # =========================================================================
    with st.spinner("Consultando Mapa BioLynx (Drug Discovery)..."):
        try:
            url_mapa_kml = "https://www.google.com/maps/d/u/0/kml?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&forcekml=1"
            res_mapa = requests.get(url_mapa_kml, headers=headers, timeout=12, verify=False)
            
            if res_mapa.status_code == 200:
                soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
                marcadores = soup_mapa.find_all('Placemark')
                
                for marcador in marcadores:
                    nombre = marcador.find('name').text.strip() if marcador.find('name') else ""
                    descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                    
                    # Verificamos si el término buscado está en el nombre o en la descripción/ubicación
                    if termino in nombre.lower() or termino in descripcion.lower():
                        resultados_finales.append({
                            "Entidad Encontrada": nombre,
                            "Ubicación / Sede": "Mapeado en España",
                            "Rol / Detalle": descripcion[:120] + "..." if len(descripcion) > 120 else descripcion,
                            "Directorio de Origen": "BioLynx (Mapa)"
                        })
        except Exception as e:
            st.error(f"Error cargando BioLynx: {e}")

    # =========================================================================
    # 2. FUENTE: ASEBIO
    # =========================================================================
    with st.spinner("Consultando directorio AseBio..."):
        try:
            url_asebio = f"https://www.asebio.com/socios/directorio-empresas-biotecnologia"
            res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
            
            if res_ab.status_code == 200:
                soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
                # Obtenemos los enlaces directos a las fichas de socios
                enlaces_socios = soup_ab.find_all('a', href=True)
                
                for a in enlaces_socios:
                    texto = a.text.strip()
                    if '/socios/' in a['href'] and termino in texto.lower() and len(texto) > 2:
                        resultados_finales.append({
                            "Entidad Encontrada": texto,
                            "Ubicación / Sede": "Consultar en web AseBio",
                            "Rol / Detalle": "Socio Biotecnológico",
                            "Directorio de Origen": "AseBio"
                        })
        except Exception as e:
            st.error(f"Error cargando AseBio: {e}")

    # =========================================================================
    # RENDERIZADO FINAL
    # =========================================================================
    if resultados_finales:
        df = pd.DataFrame(resultados_finales)
        # Eliminamos duplicados por nombre
        df = df.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Se han encontrado {len(df)} resultados para '{buscar}'!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se encontraron resultados para '{buscar}'. Prueba con términos como 'Madrid', 'Bio', 'Lab' o 'Fundación'.")
