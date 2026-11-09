import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Oficial", layout="wide")
st.title("🧬 Meta-Buscador Biotech en Tiempo Real")
st.markdown("Buscando simultáneamente en profundidad en: **BioLynx (Mapa)**, **AseBio** y **ES-OPENSCREEN**.")

buscar = st.text_input("Introduce el término a buscar (ej: Madrid, Barcelona, CSIC, Farmacos, Biotech):")

if buscar:
    termino = buscar.strip().lower()
    st.info(f"Buscando en profundidad para: **'{buscar}'**...")
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
    # 2. FUENTE: ASEBIO (Análisis profundo del directorio de socios)
    # =========================================================================
    with st.spinner("Analizando directorio en profundidad de AseBio..."):
        try:
            url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
            res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
            
            if res_ab.status_code == 200:
                soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
                
                # Buscamos en elementos de lista, tarjetas de empresas y enlaces internos
                elementos_asebio = soup_ab.find_all(['li', 'div', 'a', 'span'], class_=lambda x: x and ('socio' in x or 'item' in x or 'views-field' in x or 'node' in x))
                
                # Si los selectores específicos son muy restrictivos, respaldamos con todos los enlaces de socios
                todos_enlaces = soup_ab.find_all('a', href=True)
                
                candidatos = set()
                for el in elementos_asebio:
                    txt = el.text.strip()
                    if len(txt) > 2 and len(txt) < 100:
                        candidatos.add(txt)
                        
                for a in todos_enlaces:
                    if '/socios/' in a['href']:
                        txt_enlace = a.text.strip()
                        if len(txt_enlace) > 2:
                            candidatos.add(txt_enlace)

                for texto_candidato in candidatos:
                    if termino in texto_candidato.lower():
                        resultados_finales.append({
                            "Entidad Encontrada": texto_candidato,
                            "Ubicación / Sede": "España (AseBio)",
                            "Rol / Detalle": "Socio / Empresa Asociada",
                            "Directorio de Origen": "AseBio"
                        })
        except Exception as e:
            st.error(f"Error en AseBio: {e}")

    # =========================================================================
    # 3. FUENTE: ES-OPENSCREEN (Análisis profundo de partners y observatorio)
    # =========================================================================
    with st.spinner("Analizando red y socios de ES-OPENSCREEN..."):
        try:
            url_openscreen = "https://www.es-openscreen.com/partner/"
            res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
            
            if res_os.status_code == 200:
                soup_os = BeautifulSoup(res_os.text, 'html.parser')
                
                # Extraemos bloques de texto, títulos, párrafos y tarjetas de partners
                bloques_os = soup_os.find_all(['h3', 'h4', 'h5', 'strong', 'a', 'p', 'div'], class_=lambda x: x and ('partner' in x or 'item' in x or 'content' in x))
                
                candidatos_os = set()
                for bloque in bloques_os:
                    txt = bloque.text.strip()
                    if len(txt) > 2 and len(txt) < 120:
                        candidatos_os.add(txt)
                        
                for texto_os in candidatos_os:
                    if termino in texto_os.lower():
                        resultados_finales.append({
                            "Entidad Encontrada": texto_os,
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": "Entidad / Nodo Asociado",
                            "Directorio de Origen": "ES-OPENSCREEN"
                        })
        except Exception as e:
            st.error(f"Error en ES-OpenScreen: {e}")

    # =========================================================================
    # RENDERIZADO FINAL Y CONSOLIDACIÓN DE DATOS
    # =========================================================================
    df_temp = pd.DataFrame(resultados_finales)
    
    if not df_temp.empty:
        # Eliminamos duplicados exactos
        df_temp = df_temp.drop_duplicates(subset=["Entidad Encontrada"])
        st.success(f"¡Se han consolidado {len(df_temp)} registros coincidentes en las tres fuentes!")
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
        st.warning(f"No se han encontrado registros para '{buscar}'. Prueba con términos como 'Madrid', 'Barcelona', 'España' o 'Bio'.")
