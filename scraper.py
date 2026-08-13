import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def extraer_imagen_real(img_tag):
    """Extrae la URL real de la imagen ignorando el relleno SVG."""
    if not img_tag:
        return ""
    
    # Lista de atributos donde Prestashop/PortatilChile guarda la foto real
    atributos = ['data-full-size-image-url', 'data-src', 'data-image-large-src', 'src']
    
    for attr in atributos:
        url = img_tag.get(attr)
        if url and not url.startswith('data:image'):
            return url
            
    # Si viene en srcset
    srcset = img_tag.get('srcset')
    if srcset:
        partes = [p.strip().split(' ')[0] for p in srcset.split(',')]
        for p in partes:
            if p and not p.startswith('data:image'):
                return p
                
    return ""

def obtener_detalles_producto(url, headers):
    detalles = {
        "Modelo_SKU": "",
        "Stock": "",
        "Procesador": "",
        "RAM": "",
        "Almacenamiento": "",
        "Pantalla": "",
        "Grafica": "",
        "OS": ""
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return detalles
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Stock
        stock_tag = soup.find('span', id='product-availability') or soup.find('div', class_='product-quantities')
        if stock_tag:
            txt = stock_tag.text.strip().replace("\n", " ").replace(",", " ")
            detalles["Stock"] = re.sub(r'\s+', ' ', txt)
        else:
            detalles["Stock"] = "Consultar"
            
        # 2. SKU
        sku_tag = soup.find('div', class_='product-reference') or soup.find('span', itemprop='sku')
        if sku_tag:
            detalles["Modelo_SKU"] = sku_tag.text.replace("Referencia:", "").replace(",", " ").strip()

        # 3. Especificaciones
        features = soup.find_all('dl', class_='data-sheet')
        for sheet in features:
            dt_list = sheet.find_all('dt', class_='name')
            dd_list = sheet.find_all('dd', class_='value')
            
            for dt, dd in zip(dt_list, dd_list):
                clave = dt.text.strip().lower()
                valor = dd.text.strip().replace(",", " -").replace('"', '')
                
                if "procesador" in clave:
                    detalles["Procesador"] = valor
                elif "ram" in clave or "memoria" in clave:
                    detalles["RAM"] = valor
                elif "disco" in clave or "ssd" in clave or "almacenamiento" in clave:
                    detalles["Almacenamiento"] = valor
                elif "pantalla" in clave:
                    detalles["Pantalla"] = valor
                elif "gráfica" in clave or "video" in clave or "gpu" in clave:
                    detalles["Grafica"] = valor
                elif "sistema" in clave or "os" in clave:
                    detalles["OS"] = valor

    except Exception as e:
        print(f"Error en {url}: {e}")
        
    return detalles

def obtener_catalogo():
    base_url = "https://portatilchile.com/2-notebooks"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    productos_lista = []
    page = 1
    
    while True:
        url = f"{base_url}?page={page}"
        print(f"Scrapeando página {page}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articulos = soup.find_all('article', class_='product-miniature')
        
        if not articulos:
            break
            
        for art in articulos:
            title_tag = art.find('h3', class_='product-title')
            # Reemplazamos comas en el título por guiones para no romper las columnas del CSV
            nombre = title_tag.text.strip().replace(",", " -") if title_tag else "Sin nombre"
            
            link_tag = art.find('a', href=True)
            enlace = link_tag['href'] if link_tag else ""
            
            price_tag = art.find('span', class_='price')
            precio_oferta = price_tag.text.strip().replace(",", "") if price_tag else "N/A"
            
            regular_price_tag = art.find('span', class_='regular-price')
            precio_regular = regular_price_tag.text.strip().replace(",", "") if regular_price_tag else precio_oferta
            
            # Captura de Imagen REAL
            img_tag = art.find('img')
            imagen_url = extraer_imagen_real(img_tag)

            # Extraer especificaciones entrando al producto
            detalles = {}
            if enlace:
                detalles = obtener_detalles_producto(enlace, headers)
                time.sleep(0.2)

            productos_lista.append({
                "Producto": nombre,
                "Modelo_SKU": detalles.get("Modelo_SKU", ""),
                "Precio_Oferta": precio_oferta,
                "Precio_Regular": precio_regular,
                "Stock": detalles.get("Stock", ""),
                "Procesador": detalles.get("Procesador", ""),
                "RAM": detalles.get("RAM", ""),
                "Almacenamiento": detalles.get("Almacenamiento", ""),
                "Pantalla": detalles.get("Pantalla", ""),
                "Grafica": detalles.get("Grafica", ""),
                "OS": detalles.get("OS", ""),
                "Enlace": enlace,
                "Imagen": imagen_url
            })
            
        page += 1
        
    return productos_lista

if __name__ == "__main__":
    datos = obtener_catalogo()
    df = pd.DataFrame(datos)
    
    # Exportación en CSV estándar con comas puras
    archivo_salida = 'catalogo_portatil_chile.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"Proceso completado. {len(df)} productos guardados.")
