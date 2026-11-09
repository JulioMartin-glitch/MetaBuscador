import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Buscando simultáneamente en: **BioLynx (Mapa)**, **AseBio** y **ES-OPENSCREEN**.")

buscar = st.text_input("Introduce el término a buscar (ej: Madrid, Barcelona, CSIC, Farmacos, Biotech):")

if buscar:
    termino = buscar.strip().lower()
    st.info(f"Buscando en vivo para: **'{buscar}'**...")
    resultados_finales = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # =========================================================================
    # 1. FUENTE: MAPA BIOLYNX (KML Completo)
    # =========================================================================
    with st.spinner("Consultando base de datos de BioLynx..."):
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
                            "Ubicación / Sede": "España (Mapeado)",
                            "Rol / Detalle": descripcion[:120] + "..." if len(descripcion) > 120 else descripcion,
                            "Directorio de Origen": "BioLynx (Mapa)"
                        })
        except Exception as e:
            st.error(f"Error en BioLynx: {e}")

    # =========================================================================
    # 2. FUENTE: ASEBIO (Directorio Oficial de Socios)
    # =========================================================================
    with st.spinner("Consultando directorio oficial de AseBio..."):
        try:
            url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
            res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
            
            if res_ab.status_code == 200:
                soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
                enlaces_socios = soup_ab.find_all('a', href=True)
                
                for a in enlaces_socios:
                    href = a['href']
                    texto = a.text.strip()
                    if '/socios/' in href and termino in texto.lower() and len(texto) > 2:
                        resultados_finales.append({
                            "Entidad Encontrada": texto,
                            "Ubicación / Sede": "España (AseBio)",
                            "Rol / Detalle": "Socio / Empresa Biotecnológica Asociada",
                            "Directorio de Origen": "AseBio"
                        })
        except Exception as e:
            st.error(f"Error en AseBio: {e}")

    # =========================================================================
    # 3. FUENTE: ES-OPENSCREEN (Incluida con control de estado)
    # =========================================================================
    with st.spinner("Consultando ES-OPENSCREEN..."):
        try:
            url_openscreen = "https://www.es-openscreen.com/partner/"
            res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
            
            if res_os.status_code == 200:
                soup_os = BeautifulSoup(res_os.text, 'html.parser')
                # Buscamos de forma amplia por si hay alguna coincidencia estática o en texto general
                elementos_os = soup_os.find_all(['h3', 'h4', 'h5', 'strong', 'a', 'p'])
                
                encontrados_os = 0
                for el in elementos_os:
                    texto = el.text.strip()
                    if termino in texto.lower() and 3 <= len(texto) <= 100:
                        if not any(p in texto.lower() for p in ['cookie', 'aviso', 'home', 'contacto', 'menu']):
                            resultados_finales.append({
                                "Entidad Encontrada": texto,
                                "Ubicación / Sede": "Red ES-OPENSCREEN",
                                "Rol / Detalle": "Entidad / Mención en Observatorio",
                                "Directorio de Origen": "ES-OPENSCREEN"
                            })
                            encontrados_os += 1
                
                # Aviso informativo si la fuente responde pero no arroja datos debido a su estructura JS
                if encontrados_os == 0:
                    st.toast("ES-OPENSCREEN respondió pero no se hallaron coincidencias estáticas (contenido dinámico JS).", icon="ℹ️")
        except Exception as e:
            st.warning(f"Aviso en ES-OpenScreen: {e}")

    # =========================================================================
    # RENDERIZADO FINAL Y CONSOLIDACIÓN DE DATOS
    # =========================================================================
    df_temp = pd.DataFrame(resultados_finales)
    
    if not df_temp.empty:
        df_temp = df_temp.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Se han encontrado {len(df_temp)} registros consolidados!")
        st.dataframe(df_temp, use_container_width=True)
        
        # Botón de descarga en CSV
        csv = df_temp.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"biotech_resultados_{buscar}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No se han encontrado registros directos para '{buscar}'. Prueba con términos como 'Madrid', 'Barcelona', 'España' o 'Bio'.")
