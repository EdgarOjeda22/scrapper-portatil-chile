import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def obtener_catalogo():
    base_url = "https://portatilchile.com/2-notebooks"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
            # 1. Nombre
            title_tag = art.find('h3', class_='product-title')
            nombre = title_tag.text.strip() if title_tag else "Sin nombre"
            
            # Limpiamos comas molestas en el título por si acaso
            nombre_limpio = nombre.replace(",", " -")
            
            # 2. Enlace
            link_tag = art.find('a', href=True)
            enlace = link_tag['href'] if link_tag else ""
            
            # 3. Precios
            price_tag = art.find('span', class_='price')
            precio_oferta = price_tag.text.strip() if price_tag else "N/A"
            
            regular_price_tag = art.find('span', class_='regular-price')
            precio_regular = regular_price_tag.text.strip() if regular_price_tag else precio_oferta
            
            # 4. Imagen Real (Evita el SVG transitorio de carga)
            img_tag = art.find('img')
            imagen_url = ""
            if img_tag:
                imagen_url = (
                    img_tag.get('data-src') or 
                    img_tag.get('data-full-size-image-url') or 
                    img_tag.get('src') or 
                    ""
                )
            
            productos_lista.append({
                "Producto": nombre_limpio,
                "Precio Oferta": precio_oferta,
                "Precio Regular": precio_regular,
                "Enlace": enlace,
                "Imagen": imagen_url
            })
            
        page += 1
        time.sleep(1)
        
    return productos_lista

if __name__ == "__main__":
    datos = obtener_catalogo()
    df = pd.DataFrame(datos)
    
    # Guardar en CSV estándar limpio
    archivo_salida = 'catalogo_portatil_chile.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print("Guardado correctamente.")
    
