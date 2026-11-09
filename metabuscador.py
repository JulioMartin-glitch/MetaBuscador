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
    st.info(f"Procesando búsqueda para: **'{buscar}'**...")
    resultados_finales = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # =========================================================================
    # 1. FUENTE PRINCIPAL: MAPA BIOLYNX (KML Completo - 100% Funcional)
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
    # 2 & 3. AVISO INFORMATIVO SOBRE ASEBIO Y OPENSCREEN
    # =========================================================================
    # Explicamos al usuario de forma transparente por qué estas webs requieren 
    # navegación real o APIs privadas cerradas.
    st.toast("AseBio y ES-OpenScreen aplican restricciones anti-bot o carga por JavaScript.", icon="ℹ️")

    # =========================================================================
    # RENDERIZADO FINAL
    # =========================================================================
    df_temp = pd.DataFrame(resultados_finales)
    if not df_temp.empty:
        df_temp = df_temp.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Se han encontrado {len(df_temp)} registros coincidentes en las fuentes activas!")
        st.dataframe(df_temp, use_container_width=True)
        
        # Opcional: Botón de descarga directa
        csv = df_temp.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"biotech_resultados_{buscar}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No se han encontrado registros para '{buscar}'. Prueba con términos como 'Madrid', 'Barcelona', 'Bio' o 'Pharma'.")
