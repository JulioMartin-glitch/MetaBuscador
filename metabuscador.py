import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Avanzado", layout="wide")
st.title("🧬 Meta-Buscador Biotech Global (Indexado)")
st.markdown("Búsqueda en profundidad en múltiples directorios utilizando caché en memoria.")

# =========================================================================
# FUNCIÓN CACHEADA: Descarga e indexa los datos una sola vez
# =========================================================================
@st.cache_data(ttl=3600) # La caché se actualiza automáticamente cada 1 hora
def cargar_y_procesar_directorios():
    registros = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # -------------------------------------------------------------------------
    # 1. FUENTE: MAPA BIOLYNX (KML)
    # -------------------------------------------------------------------------
    try:
        url_mapa_kml = "https://www.google.com/maps/d/u/0/kml?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&forcekml=1"
        res_mapa = requests.get(url_mapa_kml, headers=headers, timeout=12, verify=False)
        
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            marcadores = soup_mapa.find_all('Placemark')
            
            for marcador in marcadores:
                nombre = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                registros.append({
                    "Entidad Encontrada": nombre,
                    "Ubicación / Sede": "España (Mapeado Geo)",
                    "Rol / Detalle": descripcion,
                    "Directorio de Origen": "BioLynx (Mapa)",
                    "Texto Buscable": f"{nombre} {descripcion}".lower()
                })
    except Exception as e:
        print(f"Error cargando BioLynx: {e}")

    # -------------------------------------------------------------------------
    # 2. FUENTE: ASEBIO (Directorio de Socios)
    # -------------------------------------------------------------------------
    try:
        url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            enlaces_socios = soup_ab.find_all('a', href=True)
            
            for a in enlaces_socios:
                href = a['href']
                texto = a.text.strip()
                if '/socios/' in href and len(texto) > 2:
                    registros.append({
                        "Entidad Encontrada": texto,
                        "Ubicación / Sede": "España (AseBio)",
                        "Rol / Detalle": f"Socio oficial en enlace: {href}",
                        "Directorio de Origen": "AseBio",
                        "Texto Buscable": f"{texto} {href}".lower()
                    })
    except Exception as e:
        print(f"Error cargando AseBio: {e}")

    # -------------------------------------------------------------------------
    # 3. FUENTE: ES-OPENSCREEN (Observatorio)
    # -------------------------------------------------------------------------
    try:
        url_openscreen = "https://www.es-openscreen.com/partner/"
        res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            elementos_os = soup_os.find_all(['h3', 'h4', 'h5', 'strong', 'a', 'p'])
            
            for el in elementos_os:
                texto = el.text.strip()
                if 3 <= len(texto) <= 120 and not any(p in texto.lower() for p in ['cookie', 'aviso', 'home', 'contacto', 'menu']):
                    registros.append({
                        "Entidad Encontrada": texto,
                        "Ubicación / Sede": "Red ES-OPENSCREEN",
                        "Rol / Detalle": "Nodo / Mención en Observatorio",
                        "Directorio de Origen": "ES-OPENSCREEN",
                        "Texto Buscable": texto.lower()
                    })
    except Exception as e:
        print(f"Error cargando ES-OpenScreen: {e}")

    # Convertimos a DataFrame global de la caché
    df_global = pd.DataFrame(registros)
    if not df_global.empty:
        df_global = df_global.drop_duplicates(subset=["Entidad Encontrada"])
    return df_global

# =========================================================================
# INTERFAZ DE USUARIO EN STREAMLIT
# =========================================================================

# Cargamos los datos con indicador de progreso inicial
with st.spinner("Indexando directorios web en segundo plano (esto solo ocurre la primera vez)..."):
    df_master = cargar_y_procesar_directorios()

st.success(f"Base de datos indexada correctamente con **{len(df_master)} registros totales** listos para buscar.")

buscar = st.text_input("Introduce cualquier término (ej: Madrid, Barcelona, CSIC, Farmacos, Biotech):")

if buscar:
    termino = buscar.strip().lower()
    st.info(f"Filtrando resultados globales para: **'{buscar}'**...")
    
    # Búsqueda global ultrarrápida en todos los campos a través de la columna indexada
    df_filtrado = df_master[df_master["Texto Buscable"].str.contains(termino, na=False)].copy()
    
    if not df_filtrado.empty:
        st.success(f"¡Se han encontrado {len(df_filtrado)} coincidencias!")
        
        # Mostramos la tabla limpia sin la columna técnica de búsqueda
        df_mostrar = df_filtrado[["Entidad Encontrada", "Ubicación / Sede", "Rol / Detalle", "Directorio de Origen"]]
        st.dataframe(df_mostrar, use_container_width=True)
        
        # Botón de descarga en CSV
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"biotech_resultados_{buscar}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en los directorios indexados.")
