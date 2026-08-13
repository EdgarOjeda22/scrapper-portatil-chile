import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def obtener_detalles_producto(url, headers):
    detalles = {
        "Modelo / SKU": "",
        "Stock / Disponibilidad": "",
        "Procesador": "",
        "Memoria RAM": "",
        "Almacenamiento": "",
        "Pantalla": "",
        "Tarjeta Gráfica": "",
        "Sistema Operativo": ""
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return detalles
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Disponibilidad / Stock
        stock_tag = soup.find('span', id='product-availability') or soup.find('div', class_='product-quantities')
        if stock_tag:
            stock_text = stock_tag.text.strip().replace("\n", " ")
            detalles["Stock / Disponibilidad"] = re.sub(r'\s+', ' ', stock_text)
        else:
            detalles["Stock / Disponibilidad"] = "Consultar"
            
        # 2. SKU / Referencia
        sku_tag = soup.find('div', class_='product-reference') or soup.find('span', itemprop='sku')
        if sku_tag:
            detalles["Modelo / SKU"] = sku_tag.text.replace("Referencia:", "").strip()

        # 3. Ficha Técnica
        features = soup.find_all('dl', class_='data-sheet')
        for sheet in features:
            dt_list = sheet.find_all('dt', class_='name')
            dd_list = sheet.find_all('dd', class_='value')
            
            for dt, dd in zip(dt_list, dd_list):
                clave = dt.text.strip().lower()
                valor = dd.text.strip().replace(";", " -").replace('"', '')
                
                if "procesador" in clave:
                    detalles["Procesador"] = valor
                elif "ram" in clave or "memoria" in clave:
                    detalles["Memoria RAM"] = valor
                elif "disco" in clave or "ssd" in clave or "almacenamiento" in clave:
                    detalles["Almacenamiento"] = valor
                elif "pantalla" in clave:
                    detalles["Pantalla"] = valor
                elif "gráfica" in clave or "video" in clave or "gpu" in clave:
                    detalles["Tarjeta Gráfica"] = valor
                elif "sistema" in clave or "os" in clave:
                    detalles["Sistema Operativo"] = valor

    except Exception as e:
        print(f"Error consultando {url}: {e}")
        
    return detalles

def obtener_catalogo_completo():
    base_url = "https://portatilchile.com/2-notebooks"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    productos_lista = []
    page = 1
    
    while True:
        url = f"{base_url}?page={page}"
        print(f"Analizando catálogo página {page}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articulos = soup.find_all('article', class_='product-miniature')
        
        if not articulos:
            break
            
        for art in articulos:
            # Título limpio sin comas molestas que desorganicen las columnas
            title_tag = art.find('h3', class_='product-title')
            nombre = title_tag.text.strip().replace(";", " -") if title_tag else "Sin nombre"
            
            link_tag = art.find('a', href=True)
            enlace = link_tag['href'] if link_tag else ""
            
            price_tag = art.find('span', class_='price')
            precio_oferta = price_tag.text.strip() if price_tag else "N/A"
            
            regular_price_tag = art.find('span', class_='regular-price')
            precio_regular = regular_price_tag.text.strip() if regular_price_tag else precio_oferta
            
            # Captura de Imagen Real
            img_tag = art.find('img')
            imagen_url = ""
            if img_tag:
                imagen_url = (
                    img_tag.get('data-src') or 
                    img_tag.get('data-full-size-image-url') or 
                    img_tag.get('src') or 
                    ""
                )

            # Entrar a la ficha individual del producto
            detalles_tecnicos = {}
            if enlace:
                detalles_tecnicos = obtener_detalles_producto(enlace, headers)
                time.sleep(0.3)

            # Consolidar objeto del producto
            productos_lista.append({
                "Producto": nombre,
                "Modelo / SKU": detalles_tecnicos.get("Modelo / SKU", ""),
                "Precio Oferta": precio_oferta,
                "Precio Regular": precio_regular,
                "Stock": detalles_tecnicos.get("Stock / Disponibilidad", ""),
                "Procesador": detalles_tecnicos.get("Procesador", ""),
                "Memoria RAM": detalles_tecnicos.get("Memoria RAM", ""),
                "Almacenamiento": detalles_tecnicos.get("Almacenamiento", ""),
                "Pantalla": detalles_tecnicos.get("Pantalla", ""),
                "Tarjeta Gráfica": detalles_tecnicos.get("Tarjeta Gráfica", ""),
                "Sistema Operativo": detalles_tecnicos.get("Sistema Operativo", ""),
                "Enlace": enlace,
                "Imagen": imagen_url
            })
            
        page += 1
        
    return productos_lista

if __name__ == "__main__":
    datos = obtener_catalogo_completo()
    df = pd.DataFrame(datos)
    
    # Exportación con delimitador seguro ';' para Google Sheets
    archivo_salida = 'catalogo_portatil_chile.csv'
    df.to_csv(archivo_salida, index=False, sep=';', encoding='utf-8-sig')
    print(f"Scraping finalizado. {len(df)} productos guardados en {archivo_salida}.")
