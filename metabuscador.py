import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Global", layout="wide")

# =========================================================================
# CABECERA E INDICADORES DE DIRECTORIOS
# =========================================================================
st.title("🧬 Meta-Buscador Biotech Global")
st.markdown("Búsqueda unificada en profundidad en los tres grandes directorios del sector biotecnológico:")

# Indicadores visuales de los 3 directorios en la cabecera
col1, col2, col3 = st.columns(3)
with col1:
    st.info("📍 **BioLynx**\n\nDirectorio Geográfico & KML")
with col2:
    st.info("🏢 **AseBio**\n\nDirectorio Empresarial & Fichas")
with col3:
    st.info("🔬 **ES-OPENSCREEN**\n\nRed de Nodos & Plataformas")

st.divider()

# =========================================================================
# FUNCIONES AUXILIARES DE RASTREO PARALELO
# =========================================================================
def procesar_ficha_asebio(url_socio, headers):
    try:
        res = requests.get(url_socio, headers=headers, timeout=4, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            h1 = soup.find('h1')
            nombre = h1.text.strip() if h1 else "Empresa AseBio"
            cuerpo = " ".join([p.text.strip() for p in soup.find_all(['p', 'div', 'span', 'li']) if len(p.text.strip()) > 3])
            
            return {
                "Entidad Encontrada": nombre,
                "Ubicación / Sede": "España (AseBio)",
                "Rol / Detalle": cuerpo[:180] + "..." if len(cuerpo) > 180 else "Socio AseBio",
                "Directorio de Origen": "AseBio",
                "Texto Buscable": f"{nombre} {cuerpo} {url_socio}".lower()
            }
    except:
        pass
    return None

def procesar_ficha_openscreen(url_partner, headers):
    try:
        res = requests.get(url_partner, headers=headers, timeout=4, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            h1_h2 = soup.find(['h1', 'h2'])
            nombre = h1_h2.text.strip() if h1_h2 else "Nodo ES-OPENSCREEN"
            cuerpo = " ".join([p.text.strip() for p in soup.find_all(['p', 'div', 'li', 'td']) if len(p.text.strip()) > 3])
            
            return {
                "Entidad Encontrada": nombre,
                "Ubicación / Sede": "Red ES-OPENSCREEN",
                "Rol / Detalle": cuerpo[:180] + "..." if len(cuerpo) > 180 else "Plataforma / Nodo ES-OPENSCREEN",
                "Directorio de Origen": "ES-OPENSCREEN",
                "Texto Buscable": f"{nombre} {cuerpo} {url_partner}".lower()
            }
    except:
        pass
    return None

# =========================================================================
# FUNCIÓN CACHEADA: Indexación total rápida en paralelo
# =========================================================================
@st.cache_data(ttl=3600)
def cargar_y_indexar_total():
    registros = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # -------------------------------------------------------------------------
    # 1. FUENTE: BIOLYNX (Mapa KML)
    # -------------------------------------------------------------------------
    try:
        url_mapa = "https://www.google.com/maps/d/u/0/kml?mid=1hCVAxvUdzUIu6XVaoNjTDvfckdBavpI&forcekml=1"
        res_mapa = requests.get(url_mapa, headers=headers, timeout=10, verify=False)
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            for marcador in soup_mapa.find_all('Placemark'):
                nombre = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                registros.append({
                    "Entidad Encontrada": nombre,
                    "Ubicación / Sede": "España (BioLynx)",
                    "Rol / Detalle": descripcion[:180] + "..." if len(descripcion) > 180 else descripcion,
                    "Directorio de Origen": "BioLynx",
                    "Texto Buscable": f"{nombre} {descripcion}".lower()
                })
    except Exception as e:
        print(f"Error BioLynx: {e}")

    # -------------------------------------------------------------------------
    # 2. FUENTE: ASEBIO (Indexación Profunda en Paralelo)
    # -------------------------------------------------------------------------
    try:
        url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            urls_ab = set()
            for a in soup_ab.find_all('a', href=True):
                href = a['href']
                if '/socios/' in href and len(href) > 8:
                    full_url = href if href.startswith('http') else "https://www.asebio.com" + href
                    urls_ab.add(full_url)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(procesar_ficha_asebio, url, headers) for url in urls_ab]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        registros.append(res)
    except Exception as e:
        print(f"Error AseBio: {e}")

    # -------------------------------------------------------------------------
    # 3. FUENTE: ES-OPENSCREEN (Indexación Profunda de Nodos y Partners)
    # -------------------------------------------------------------------------
    try:
        url_openscreen = "https://www.es-openscreen.com/partner/"
        res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            urls_os = set()
            
            # Buscamos enlaces a socios/nodos específicos de ES-OPENSCREEN
            for a in soup_os.find_all('a', href=True):
                href = a['href']
                if '/partner/' in href or '/nodo/' in href or '/member/' in href:
                    if len(href) > 10 and not href.endswith('/partner/'):
                        full_url = href if href.startswith('http') else "https://www.es-openscreen.com" + href
                        urls_os.add(full_url)
            
            # Si se encuentran fichas internas, las leemos en paralelo
            if urls_os:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(procesar_ficha_openscreen, url, headers) for url in urls_os]
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            registros.append(res)
            
            # Respaldos directos de bloques por si la web es de página única
            for el in soup_os.find_all(['h2', 'h3', 'h4', 'p', 'li']):
                texto = el.text.strip()
                if 10 <= len(texto) <= 250:
                    if not any(k in texto.lower() for k in ['cookie', 'privacy', 'copyright', 'contacto', 'menu']):
                        registros.append({
                            "Entidad Encontrada": texto[:60] + "...",
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": texto,
                            "Directorio de Origen": "ES-OPENSCREEN",
                            "Texto Buscable": texto.lower()
                        })
    except Exception as e:
        print(f"Error ES-OPENSCREEN: {e}")

    df_global = pd.DataFrame(registros)
    if not df_global.empty:
        df_global = df_global.drop_duplicates(subset=["Texto Buscable"])
    return df_global

# =========================================================================
# EJECUCIÓN E INTERFAZ DE BÚSQUEDA
# =========================================================================
with st.spinner("Indexando BioLynx, AseBio y ES-OPENSCREEN en paralelo..."):
    df_master = cargar_y_indexar_total()

# Métricas rápidas de los datos listos
st.success(f"Base de datos global indexada correctamente con **{len(df_master)} registros** entre los 3 directorios.")

buscar = st.text_input("🔍 Introduce un término de búsqueda (ej: Madrid, CSIC, Cáncer, Barcelona, Screening):")

if buscar:
    termino = buscar.strip().lower()
    df_filtrado = df_master[df_master["Texto Buscable"].str.contains(termino, na=False)].copy()
    
    if not df_filtrado.empty:
        st.success(f"¡Se han encontrado **{len(df_filtrado)}** coincidencias totales!")
        
        df_mostrar = df_filtrado[["Entidad Encontrada", "Ubicación / Sede", "Rol / Detalle", "Directorio de Origen"]]
        st.dataframe(df_mostrar, use_container_width=True)
        
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"busqueda_biotech_{buscar}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No se han encontrado resultados para **'{buscar}'**.")
