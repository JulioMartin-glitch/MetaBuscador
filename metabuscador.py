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

col1, col2, col3 = st.columns(3)
with col1:
    st.info("📍 **BioLynx**\n\nDirectorio Geográfico & KML")
with col2:
    st.info("🏢 **AseBio**\n\nDirectorio Empresarial & Fichas")
with col3:
    st.info("🔬 **ES-OPENSCREEN**\n\n*(Captura de prueba para refinado)*")

st.divider()

# =========================================================================
# FUNCIONES AUXILIARES DE RASTREO
# =========================================================================
def procesar_ficha_asebio(url_socio, headers):
    try:
        res = requests.get(url_socio, headers=headers, timeout=5, verify=False)
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

# =========================================================================
# FUNCIÓN CACHEADA: Indexación total
# =========================================================================
@st.cache_data(ttl=86400)
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
        res_mapa = requests.get(url_mapa, headers=headers, timeout=12, verify=False)
        if res_mapa.status_code == 200:
            soup_mapa = BeautifulSoup(res_mapa.text, 'xml')
            for marcador in soup_mapa.find_all('Placemark'):
                nombre = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                if nombre:
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
    # 2. FUENTE: ASEBIO (Directorio de Empresas)
    # -------------------------------------------------------------------------
    try:
        url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        res_ab = requests.get(url_asebio, headers=headers, timeout=12, verify=False)
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            urls_ab = set()
            for a in soup_ab.find_all('a', href=True):
                href = a['href']
                if '/socios/' in href and len(href) > 8:
                    full_url = href if href.startswith('http') else "https://www.asebio.com" + href
                    urls_ab.add(full_url)

            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = [executor.submit(procesar_ficha_asebio, url, headers) for url in urls_ab]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        registros.append(res)
    except Exception as e:
        print(f"Error AseBio: {e}")

    # -------------------------------------------------------------------------
    # 3. FUENTE: ES-OPENSCREEN (Selector abierto de respaldo)
    # -------------------------------------------------------------------------
    try:
        url_openscreen = "https://www.es-openscreen.com/partner/"
        res_os = requests.get(url_openscreen, headers=headers, timeout=12, verify=False)
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            
            # Recogemos enlaces relevantes o títulos para garantizar que extraiga contenido
            elementos_capturados = set()
            
            for a in soup_os.find_all('a', href=True):
                texto = a.text.strip()
                href = a['href']
                if len(texto) > 3 and ('partner' in href or 'nodo' in href or 'member' in href):
                    if texto not in elementos_capturados:
                        elementos_capturados.add(texto)
                        registros.append({
                            "Entidad Encontrada": texto,
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": f"Enlace detectado: {href}",
                            "Directorio de Origen": "ES-OPENSCREEN",
                            "Texto Buscable": f"{texto} {href}".lower()
                        })
            
            # Respaldo por encabezados si el filtrado de enlaces aporta pocos
            for h in soup_os.find_all(['h2', 'h3', 'h4']):
                texto = h.text.strip()
                if len(texto) > 4 and texto not in elementos_capturados:
                    elementos_capturados.add(texto)
                    registros.append({
                        "Entidad Encontrada": texto,
                        "Ubicación / Sede": "Red ES-OPENSCREEN",
                        "Rol / Detalle": "Encabezado de red ES-OPENSCREEN",
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
with st.spinner("Indexando directorios (BioLynx, AseBio, ES-OPENSCREEN)..."):
    df_master = cargar_y_indexar_total()

if not df_master.empty:
    n_bio = len(df_master[df_master["Directorio de Origen"] == "BioLynx"])
    n_ase = len(df_master[df_master["Directorio de Origen"] == "AseBio"])
    n_os = len(df_master[df_master["Directorio de Origen"] == "ES-OPENSCREEN"])
    
    st.success(f"Base de datos global indexada con **{len(df_master)} registros totales**.")
    st.caption(f"📊 **Desglose de fuentes:** BioLynx: `{n_bio}` | AseBio: `{n_ase}` | ES-OPENSCREEN: `{n_os}`")

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
