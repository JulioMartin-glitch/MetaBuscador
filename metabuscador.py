import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Desactivamos advertencias de seguridad en la pantalla
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Buscador BioLynx", layout="wide")
st.title("🧬 Buscador en Vivo: Mapa BioLynx Drug Discovery")
st.markdown("Consulta en tiempo real utilizando la URL directa de Google My Maps.")

# Caja de búsqueda vacía
buscar = st.text_input("Introduce un término para buscar en el mapa (ej: Madrid, Barcelona, Biotech):")

if buscar:
    st.info(f"Conectando en vivo con el mapa de BioLynx para buscar: '{buscar}'...")
    termino = buscar.lower()
    resultados_finales = []

    try:
        # URL TÉCNICA CORRECTA: Forzamos la descarga del archivo de datos KML abierto de Google
        url_kml_real = "https://google.com"
        
        # Enviamos una petición normal de internet
        respuesta = requests.get(url_kml_real, timeout=15, verify=False)
        
        if respuesta.status_code == 200:
            # Google My Maps devuelve un archivo XML estructurado
            soup = BeautifulSoup(respuesta.text, 'xml')
            # Cada empresa guardada en el mapa está bajo la etiqueta 'Placemark'
            marcadores = soup.find_all('Placemark')
            
            for marcador in marcadores:
                nombre_empresa = marcador.find('name').text.strip() if marcador.find('name') else ""
                descripcion = marcador.find('description').text.strip() if marcador.find('description') else ""
                
                # Filtramos en vivo: si el término está en el nombre o en la descripción de la empresa
                if termino in nombre_empresa.lower() or termino in descripcion.lower():
                    resultados_finales.append({
                        "Empresa Encontrada": nombre_empresa,
                        "Detalles / Enfoque": descripcion[:150] + "..." if descripcion else "Mapeado en Drug Discovery",
                        "Origen": "BioLynx (Google My Maps)"
                    })
                    
    except Exception as e:
        st.error(f"Error técnico de conexión: {e}")

    # Mostrar la tabla en tu pantalla
    if resultados_finales:
        st.success(f"¡Éxito! Hemos encontrado {len(resultados_finales)} empresas registradas en el mapa.")
        df = pd.DataFrame(resultados_finales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"No se ha encontrado ninguna coincidencia para '{buscar}' en el mapa online.")
