import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def extraer_imagen_real(soup, art):
    """Obtiene la URL real de la imagen (.jpg/.webp) e ignora el relleno SVG de lazy-load."""
    # 1. Intentar buscar en la etiqueta img del catálogo
    img = art.find('img')
    if img:
        for attr in ['data-full-size-image-url', 'data-src', 'data-image-large-src', 'src']:
            val = img.get(attr)
            if val and not val.startswith('data:image'):
                return val

    # 2. Si no se encuentra, buscar en la vista de detalle
    if soup:
        img_detail = soup.find('img', class_='js-qs-product-cover') or soup.find('div', class_='product-cover')
        if img_detail:
            tag = img_detail.find('img') if img_detail.name != 'img' else img_detail
            if tag:
                for attr in ['src', 'data-src', 'data-full-size-image-url']:
                    val = tag.get(attr)
                    if val and not val.startswith('data:image'):
                        return val
    return ""

def obtener_detalles_producto(url, headers):
    """Entra a la página del producto y barre exhaustivamente las especificaciones y el stock."""
    detalles = {
        "Modelo_SKU": "N/I",
        "UPC_EAN": "N/I",
        "Stock": "Consultar",
        "Procesador": "N/I",
        "RAM": "N/I",
        "Almacenamiento": "N/I",
        "Pantalla": "N/I",
        "Grafica": "N/I",
        "OS": "N/I",
        "Imagen_Detalle": ""
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return detalles
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # --- 1. STOCK / DISPONIBILIDAD ---
        stock_elem = (
            soup.find('span', id='product-availability') or 
            soup.find('div', class_='product-quantities') or
            soup.find('span', class_='product-availability') or
            soup.find('p', id='availability_statut')
        )
        if stock_elem:
            texto_stock = stock_elem.text.strip().replace("\n", " ").replace(",", " -")
            detalles["Stock"] = re.sub(r'\s+', ' ', texto_stock)
            
        # --- 2. MODELO / REFERENCIA / SKU / UPC ---
        ref_elem = (
            soup.find('div', class_='product-reference') or 
            soup.find('span', itemprop='sku') or
            soup.find('div', class_='reference')
        )
        if ref_elem:
            detalles["Modelo_SKU"] = ref_elem.text.replace("Referencia:", "").replace("Modelo:", "").replace(",", " -").strip()

        # Búsqueda alternativa para UPC / Código EAN o MPN en meta tags
        meta_upc = soup.find('meta', property='product:upc') or soup.find('meta', property='og:upc') or soup.find('span', itemprop='gtin13')
        if meta_upc:
            detalles["UPC_EAN"] = meta_upc.get('content', meta_upc.text).strip()

        # --- 3. IMAGEN DESDE DETALLE ---
        detalles["Imagen_Detalle"] = extraer_imagen_real(soup, None)

        # --- 4. ESPECIFICACIONES TÉCNICAS (Ficha de datos PrestaShop) ---
        # Forma A: Lista de definición <dl class="data-sheet">
        data_sheets = soup.find_all('dl', class_='data-sheet')
        for sheet in data_sheets:
            dts = sheet.find_all('dt', class_='name')
            dds = sheet.find_all('dd', class_='value')
            for dt, dd in zip(dts, dds):
                clave = dt.text.strip().lower()
                valor = dd.text.strip().replace(",", " -").replace('"', '')
                
                if any(x in clave for x in ["procesador", "cpu"]):
                    detalles["Procesador"] = valor
                elif any(x in clave for x in ["ram", "memoria"]):
                    detalles["RAM"] = valor
                elif any(x in clave for x in ["disco", "ssd", "almacenamiento", "capacidad"]):
                    detalles["Almacenamiento"] = valor
                elif any(x in clave for x in ["pantalla", "display", "resolucion"]):
                    detalles["Pantalla"] = valor
                elif any(x in clave for x in ["gráfica", "grafica", "gpu", "video"]):
                    detalles["Grafica"] = valor
                elif any(x in clave for x in ["sistema", "os", "operativo"]):
                    detalles["OS"] = valor
                elif any(x in clave for x in ["upc", "ean", "código"]):
                    detalles["UPC_EAN"] = valor

        # Forma B: Tablas <table> estándar de especificaciones si no existía <dl>
        if detalles["Procesador"] == "N/I":
            filas_tabla = soup.find_all('tr')
            for fila in filas_tabla:
                tds = fila.find_all(['td', 'th'])
                if len(tds) >= 2:
                    clave = tds[0].text.strip().lower()
                    valor = tds[1].text.strip().replace(",", " -").replace('"', '')
                    if "procesador" in clave: detalles["Procesador"] = valor
                    elif "ram" in clave: detalles["RAM"] = valor
                    elif "ssd" in clave or "disco" in clave: detalles["Almacenamiento"] = valor
                    elif "pantalla" in clave: detalles["Pantalla"] = valor
                    elif "grafica" in clave or "gpu" in clave: detalles["Grafica"] = valor

    except Exception as e:
        print(f"Error parseando detalle {url}: {e}")
        
    return detalles

def obtener_catalogo():
    base_url = "https://portatilchile.com/2-notebooks"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    productos_lista = []
    page = 1
    
    while True:
        url = f"{base_url}?page={page}"
        print(f"Procesando catálogo - Página {page}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articulos = soup.find_all('article', class_='product-miniature')
        
        if not articulos:
            print("No hay más productos. Finalizando recorrido.")
            break
            
        for art in articulos:
            title_tag = art.find('h3', class_='product-title')
            nombre = title_tag.text.strip().replace(",", " -") if title_tag else "Sin nombre"
            
            link_tag = art.find('a', href=True)
            enlace = link_tag['href'] if link_tag else ""
            
            price_tag = art.find('span', class_='price')
            precio_oferta = price_tag.text.strip().replace(",", "") if price_tag else "N/A"
            
            regular_price_tag = art.find('span', class_='regular-price')
            precio_regular = regular_price_tag.text.strip().replace(",", "") if regular_price_tag else precio_oferta
            
            # Intentar obtener imagen desde el catálogo
            imagen_url = extraer_imagen_real(None, art)

            # Entrar obligatoriamente a la ficha individual para obtener SKU, Stock y Ficha Técnica
            detalles = {}
            if enlace:
                print(f" Extrayendo ficha técnica de: {nombre[:40]}...")
                detalles = obtener_detalles_producto(enlace, headers)
                time.sleep(0.3)

            # Priorizar la imagen de la vista individual si la del catálogo era un placeholder SVG
            imagen_final = detalles.get("Imagen_Detalle") if detalles.get("Imagen_Detalle") else imagen_url

            productos_lista.append({
                "Producto": nombre,
                "Modelo_SKU": detalles.get("Modelo_SKU", "N/I"),
                "UPC_EAN": detalles.get("UPC_EAN", "N/I"),
                "Precio_Oferta": precio_oferta,
                "Precio_Regular": precio_regular,
                "Stock": detalles.get("Stock", "Consultar"),
                "Procesador": detalles.get("Procesador", "N/I"),
                "RAM": detalles.get("RAM", "N/I"),
                "Almacenamiento": detalles.get("Almacenamiento", "N/I"),
                "Pantalla": detalles.get("Pantalla", "N/I"),
                "Grafica": detalles.get("Grafica", "N/I"),
                "OS": detalles.get("OS", "N/I"),
                "Enlace": enlace,
                "Imagen": imagen_final
            })
            
        page += 1
        
    return productos_lista

if __name__ == "__main__":
    datos = obtener_catalogo()
    df = pd.DataFrame(datos)
    
    # Exportación estricta libre de caracteres que desorganicen las columnas de Excel
    archivo_salida = 'catalogo_portatil_chile.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"Éxito: Se procesaron {len(df)} portátiles con información técnica completa.")
