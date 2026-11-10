import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
import re
import json
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
    # 3. FUENTE: ES-OPENSCREEN (Extracción de Scripts/Mapa JSON + Nodos Limpios)
    # -------------------------------------------------------------------------
    try:
        url_openscreen = "https://www.es-openscreen.com/partner/?view=map&s="
        res_os = requests.get(url_openscreen, headers=headers, timeout=12, verify=False)
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            
            # 1. Intentar extraer los marcadores JSON inyectados en los scripts del mapa
            nodos_encontrados = False
            scripts = soup_os.find_all('script')
            for script in scripts:
                if script.string and ('marker' in script.string.lower() or 'partner' in script.string.lower()):
                    matches = re.findall(r'\{[^{}]*"title"[^{}]*\}|\{[^{}]*"name"[^{}]*\}', script.string)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            nombre_nodo = data.get('title') or data.get('name')
                            if nombre_nodo and len(nombre_nodo) > 3:
                                registros.append({
                                    "Entidad Encontrada": nombre_nodo.strip(),
                                    "Ubicación / Sede": "Red ES-OPENSCREEN",
                                    "Rol / Detalle": f"Nodo / Plataforma ES-OPENSCREEN - {data.get('address', '')}".strip(),
                                    "Directorio de Origen": "ES-OPENSCREEN",
                                    "Texto Buscable": f"{nombre_nodo} {data.get('address', '')}".lower()
                                })
                                nodos_encontrados = True
                        except:
                            continue

            # 2. Si no viene en JSON de Script, desestructurar tarjetas quitando Menús y Logins
            if not nodos_encontrados:
                for elemento_basura in soup_os(['header', 'footer', 'nav', 'aside', 'form']):
                    elemento_basura.decompose()
                    
                bloques = soup_os.find_all(['article', 'div'], class_=lambda x: x and any(c in str(x).lower() for c in ['post', 'type-partner', 'partner-item', 'location-item', 'map-list']))
                
                if not bloques:
                    main_content = soup_os.find('main') or soup_os.find('div', id='content') or soup_os
                    bloques = main_content.find_all(['h2', 'h3', 'h4'])

                blacklist_estricta = [
                    'inicia sesión', 'usuario', 'contraseña', 'recuérdame', 'observatorio',
                    'quiero participar', 'comité', 'arsenio', 'sofía', 'beatriz', 'raquel',
                    'amelia', 'lourdes', 'emilio', 'jordi', 'archive', 'partners archive'
                ]

                for el in bloques:
                    if el.name in ['h2', 'h3', 'h4']:
                        nombre = el.text.strip()
                        cuerpo = el.parent.text.strip() if el.parent else nombre
                    else:
                        titulo_el = el.find(['h2', 'h3', 'h4', 'strong', 'a'])
                        nombre = titulo_el.text.strip() if titulo_el else ""
                        cuerpo = el.text.strip()

                    for prefijo in ["Coordinador:", "Coordinator:", "Partner:", "Nodo:"]:
                        if nombre.lower().startswith(prefijo.lower()):
                            nombre = nombre[len(prefijo):].strip()

                    if len(nombre) > 4 and not any(b in nombre.lower() for b in blacklist_estricta):
                        detalle = cuerpo.replace(nombre, "").strip()
                        detalle = " ".join(detalle.split())
                        
                        registros.append({
                            "Entidad Encontrada": nombre,
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": detalle[:180] + "..." if len(detalle) > 180 else (detalle or "Nodo ES-OPENSCREEN"),
                            "Directorio de Origen": "ES-OPENSCREEN",
                            "Texto Buscable": f"{nombre} {cuerpo}".lower()
                        })
    except Exception as e:
        print(f"Error ES-OPENSCREEN: {e}")

    df_global = pd.DataFrame(registros)
    if not df_global.empty:
        df_global = df_global.drop_duplicates(subset=["Entidad Encontrada"])
        df_global = df_global.drop_duplicates(subset=["Texto Buscable"])
        
    return df_global

# =========================================================================
# EJECUCIÓN E INTERFAZ DE BÚSQUEDA
# =========================================================================
with st.spinner("Indexando BioLynx, AseBio y ES-OPENSCREEN..."):
    df_master = cargar_y_indexar_total()

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
