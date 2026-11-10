import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meta-Buscador Biotech Global", layout="wide")
st.title("🧬 Meta-Buscador Biotech Global (Indexado Total)")
st.markdown("Búsqueda avanzada en profundidad en BioLynx, AseBio y ES-OPENSCREEN.")

# =========================================================================
# FUNCIÓN CACHEADA: Indexación profunda en las 3 fuentes
# =========================================================================
@st.cache_data(ttl=3600)
def cargar_y_indexar_total():
    registros = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # -------------------------------------------------------------------------
    # 1. FUENTE: MAPA BIOLYNX (KML Geográfico)
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
                    "Rol / Detalle": descripcion[:150] + "..." if len(descripcion) > 150 else descripcion,
                    "Directorio de Origen": "BioLynx (Mapa)",
                    "Texto Buscable": f"{nombre} {descripcion}".lower()
                })
    except Exception as e:
        print(f"Error BioLynx: {e}")

    # -------------------------------------------------------------------------
    # 2. FUENTE: ASEBIO (Fichas Internas de Socios)
    # -------------------------------------------------------------------------
    try:
        url_asebio = "https://www.asebio.com/socios/directorio-empresas-biotecnologia"
        res_ab = requests.get(url_asebio, headers=headers, timeout=10, verify=False)
        
        if res_ab.status_code == 200:
            soup_ab = BeautifulSoup(res_ab.text, 'html.parser')
            enlaces_socios = soup_ab.find_all('a', href=True)
            
            urls_socios = set()
            for a in enlaces_socios:
                href = a['href']
                if '/socios/' in href and len(href) > 8:
                    if href.startswith('http'):
                        urls_socios.add(href)
                    else:
                        urls_socios.add("https://www.asebio.com" + href)

            for url_socio in list(urls_socios):
                try:
                    res_socio = requests.get(url_socio, headers=headers, timeout=5, verify=False)
                    if res_socio.status_code == 200:
                        soup_socio = BeautifulSoup(res_socio.text, 'html.parser')
                        h1 = soup_socio.find('h1')
                        nombre_socio = h1.text.strip() if h1 else "Empresa AseBio"
                        cuerpo_texto = " ".join([p.text.strip() for p in soup_socio.find_all(['p', 'div', 'span', 'li']) if len(p.text.strip()) > 3])
                        
                        registros.append({
                            "Entidad Encontrada": nombre_socio,
                            "Ubicación / Sede": "España (AseBio Ficha)",
                            "Rol / Detalle": cuerpo_texto[:150] + "..." if len(cuerpo_texto) > 150 else "Socio AseBio",
                            "Directorio de Origen": "AseBio",
                            "Texto Buscable": f"{nombre_socio} {cuerpo_texto} {url_socio}".lower()
                        })
                except:
                    continue
    except Exception as e:
        print(f"Error AseBio: {e}")

    # -------------------------------------------------------------------------
    # 3. FUENTE: ES-OPENSCREEN (Rastreo Profundo de Bloques y Partners)
    # -------------------------------------------------------------------------
    try:
        url_openscreen = "https://www.es-openscreen.com/partner/"
        res_os = requests.get(url_openscreen, headers=headers, timeout=10, verify=False)
        
        if res_os.status_code == 200:
            soup_os = BeautifulSoup(res_os.text, 'html.parser')
            
            # Recorremos bloques amplios de texto (párrafos, títulos, celdas de tablas y listas)
            elementos_os = soup_os.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'div'])
            
            for el in elementos_os:
                texto_bloque = el.text.strip()
                # Filtramos para descartar menús, avisos de cookies y textos vacíos o gigantes
                if 5 <= len(texto_bloque) <= 200:
                    if not any(p in texto_bloque.lower() for p in ['cookie', 'aviso', 'home', 'contacto', 'menu', 'privacy', 'copyright']):
                        registros.append({
                            "Entidad Encontrada": texto_bloque[:60] + "..." if len(texto_bloque) > 60 else texto_bloque,
                            "Ubicación / Sede": "Red ES-OPENSCREEN",
                            "Rol / Detalle": "Mención / Nodo en Observatorio",
                            "Directorio de Origen": "ES-OPENSCREEN",
                            "Texto Buscable": texto_bloque.lower()
                        })
    except Exception as e:
        print(f"Error ES-OpenScreen: {e}")

    df_global = pd.DataFrame(registros)
    if not df_global.empty:
        df_global = df_global.drop_duplicates(subset=["Texto Buscable"])
    return df_global

# =========================================================================
# INTERFAZ DE USUARIO EN STREAMLIT
# =========================================================================

with st.spinner("Indexando todas las fuentes en profundidad (esto puede tardar unos segundos la primera vez)..."):
    df_master = cargar_y_indexar_total()

st.success(f"Base de datos global indexada con **{len(df_master)} registros** totales listos para buscar.")

buscar = st.text_input("Introduce cualquier término (ej: Madrid, Barcelona, CSIC, Farmacos, Biotech):")

if buscar:
    termino = buscar.strip().lower()
    st.info(f"Buscando en todos los campos y fuentes para: **'{buscar}'**...")
    
    # Búsqueda global cruzada
    df_filtrado = df_master[df_master["Texto Buscable"].str.contains(termino, na=False)].copy()
    
    if not df_filtrado.empty:
        st.success(f"¡Se han encontrado {len(df_filtrado)} coincidencias en total!")
        
        df_mostrar = df_filtrado[["Entidad Encontrada", "Ubicación / Sede", "Rol / Detalle", "Directorio de Origen"]]
        st.dataframe(df_mostrar, use_container_width=True)
        
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"biotech_resultados_{buscar}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en las fuentes indexadas.")
