import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

print("==========================================")
print("INICIANDO NAVEGADOR EN LA NUBE...")
print("==========================================")

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)
lista_productos = []
pagina = 1

try:
    while True:
        url = f"https://portatilchile.com/4-notebooks?page={pagina}"
        print(f"Navegando a la página {pagina}: {url}")
        driver.get(url)
        time.sleep(4)

        items = driver.find_elements(By.CSS_SELECTOR, '.product-miniature, article.product-miniature')
        if not items:
            print("No se encontraron más productos. Finalizando recorrido.")
            break

        encontrados_en_pagina = 0

        for item in items:
            try:
                try:
                    nombre = item.find_element(By.CSS_SELECTOR, '.product-title, h2, h3').text.strip()
                except:
                    nombre = ""

                try:
                    precio_oferta = item.find_element(By.CSS_SELECTOR, '.price, .product-price').text.strip()
                except:
                    precio_oferta = "N/A"

                try:
                    precio_regular = item.find_element(By.CSS_SELECTOR, '.regular-price').text.strip()
                except:
                    precio_regular = precio_oferta

                try:
                    enlace = item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                except:
                    enlace = ""

                try:
                    imagen = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                except:
                    imagen = ""

                if nombre and len(nombre) > 2:
                    lista_productos.append({
                        'Producto': nombre,
                        'Precio Oferta': precio_oferta,
                        'Precio Regular': precio_regular,
                        'Enlace': enlace,
                        'Imagen': imagen
                    })
                    encontrados_en_pagina += 1
            except Exception:
                continue

        print(f" -> Se obtuvieron {encontrados_en_pagina} productos de la página {pagina}.")

        if encontrados_en_pagina == 0:
            break

        pagina += 1

    print(f"\nTOTAL FINAL: {len(lista_productos)} productos extraídos correctamente.")

    df = pd.DataFrame(lista_productos)
    df = df.drop_duplicates(subset=['Producto'])
    df.to_csv('catalogo_portatil_chile.csv', index=False, encoding='utf-8-sig')
    print("Archivo 'catalogo_portatil_chile.csv' guardado con éxito.")

except Exception as error:
    print(f"Ocurrió un error inesperado durante el escaneo: {error}")

finally:
    driver.quit()
