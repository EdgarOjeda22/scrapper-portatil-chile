import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def extraer_especificaciones(soup_detalle):
    """Extrae UPC, Modelo, Stock y Specs técnicas directamente del HTML interno de PortatilChile."""
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
        "Imagen": ""
    }
    
    if not soup_detalle:
        return detalles

    texto_completo = soup_detalle.get_text(separator=" ")

    # 1. Extraer UPC / Código EAN
    match_upc = re.search(r'UPC\s*(?:CODIGO|CÓDIGO)?\s*[:\-]?\s*([A-Za-z0-9]+)', texto_completo, re.IGNORECASE)
    if match_upc:
        detalles["UPC_EAN"] = match_upc.group(1).strip()

    # 2. Extraer Referencia / Modelo
    match_ref = re.search(r'Referencia\s*[:\-]?\s*([A-Za-z0-9\-]+)', texto_completo, re.IGNORECASE)
    if match_ref:
        detalles["Modelo_SKU"] = match_ref.group(1).strip()

    # 3. Extraer Stock exacto
    match_stock = re.search(r'(En stock \d+ Artículos|Últimas unidades en stock|En Stock|Agotado)', texto_completo, re.IGNORECASE)
    if match_stock:
        detalles["Stock"] = match_stock.group(1).strip()

    # 4. Extraer Imagen principal de la ficha técnica
    img_tag = soup_detalle.find('img', class_='js-qs-product-cover') or soup_detalle.find('img', itemprop='image')
    if img_tag:
        detalles["Imagen"] = img_tag.get('src') or img_tag.get('data-full-size-image-url') or ""

    # 5. Extraer Ficha Técnica (Procesador, RAM, SSD, etc.)
    lines = [line.strip() for line in texto_completo.split("\n") if line.strip()]
    for i, line in enumerate(lines):
        line_low = line.lower()
        # Búsqueda por par clave-valor en texto o tablas
        if "procesador" in line_low and detalles["Procesador"] == "N/I":
            detalles["Procesador"] = lines[i+1] if i+1 < len(lines) else line
        elif "memoria ram" in line_low and detalles["RAM"] == "N/I":
            detalles["RAM"] = lines[i+1] if i+1 < len(lines) else line
        elif "almacenamiento" in line_low and detalles["Almacenamiento"] == "N/I":
            detalles["Almacenamiento"] = lines[i+1] if i+1 < len(lines) else line
        elif "pantalla" in line_low and detalles["Pantalla"] == "N/I":
            detalles["Pantalla"] = lines[i+1] if i+1 < len(lines) else line
        elif "tarjeta de video" in line_low and detalles["Grafica"] == "N/I":
            detalles["Grafica"] = lines[i+1] if i+1 < len(lines) else line
        elif "sistema operativo" in line_low and detalles["OS"] == "N/I":
            detalles["OS"] = lines[i+1] if i+1 < len(lines) else line

    return detalles

def obtener_catalogo():
    # URL oficial actualizada de PortatilChile
    urls_catalogo = [
        "https://portatilchile.com/3-productos",
        "https://portatilchile.com/4-notebooks"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    productos_lista = []
    
    for base_url in urls_catalogo:
        page = 1
        print(f"--- Escaneando categoría: {base_url} ---")
        
        while True:
            url = f"{base_url}?page={page}"
            print(f"Obteniendo página {page}...")
            resp = requests.get(url, headers=headers)
            
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            articulos = soup.find_all('article', class_='product-miniature')
            
            if not articulos:
                print(f"No hay más productos en {base_url}.")
                break
                
            for art in articulos:
                # Nombre
                title_tag = art.find('h3', class_='product-title') or art.find('a', class_='product-name')
                nombre = title_tag.text.strip().replace(",", " -") if title_tag else "Sin Nombre"
                
                # Enlace
                link_tag = art.find('a', href=True)
                enlace = link_tag['href'] if link_tag else ""
                
                # Precios
                price_tag = art.find('span', class_='price')
                precio_oferta = price_tag.text.strip().replace(",", "") if price_tag else "N/A"
                
                reg_price_tag = art.find('span', class_='regular-price')
                precio_regular = reg_price_tag.text.strip().replace(",", "") if reg_price_tag else precio_oferta

                # Entrar a la ficha individual para obtener UPC, SKU, Stock y Specs
                specs = {}
                if enlace:
                    try:
                        print(f" Extrayendo datos de: {nombre[:35]}...")
                        det_resp = requests.get(enlace, headers=headers, timeout=10)
                        if det_resp.status_code == 200:
                            det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                            specs = extraer_especificaciones(det_soup)
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"Error accediendo a {enlace}: {e}")

                productos_lista.append({
                    "Producto": nombre,
                    "Modelo_SKU": specs.get("Modelo_SKU", "N/I"),
                    "UPC_EAN": specs.get("UPC_EAN", "N/I"),
                    "Precio_Oferta": precio_oferta,
                    "Precio_Regular": precio_regular,
                    "Stock": specs.get("Stock", "Consultar"),
                    "Procesador": specs.get("Procesador", "N/I"),
                    "RAM": specs.get("RAM", "N/I"),
                    "Almacenamiento": specs.get("Almacenamiento", "N/I"),
                    "Pantalla": specs.get("Pantalla", "N/I"),
                    "Grafica": specs.get("Grafica", "N/I"),
                    "OS": specs.get("OS", "N/I"),
                    "Enlace": enlace,
                    "Imagen": specs.get("Imagen", "")
                })
                
            page += 1

    return productos_lista

if __name__ == "__main__":
    datos = obtener_catalogo()
    
    if datos:
        df = pd.DataFrame(datos)
        # Eliminar duplicados si un producto aparece en ambas categorías
        df.drop_duplicates(subset=['Enlace'], keep='first', inplace=True)
        
        # Guardar en CSV limpio
        archivo_salida = 'catalogo_portatil_chile.csv'
        df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
        print(f"\n¡ÉXITO TOTAL! Se guardaron {len(df)} portátiles con UPC, Stock y Specs en '{archivo_salida}'.")
    else:
        print("No se encontraron productos. Revisa la conexión.")
    
