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
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)
lista_productos = []
pagina = 1

try:
    while True:
        url = f"https://portatilchile.com/4-notebooks?page={pagina}"
        print(f"Navegando a la página {pagina}: {url}")
        driver.get(url)
        time.sleep(3)

        # Scroll automático para obligar a cargar los precios dinámicos
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        items = driver.find_elements(By.CSS_SELECTOR, '.product-miniature, article.product-miniature, .js-product-miniature')
        if not items:
            print("No se encontraron más productos. Finalizando recorrido.")
            break

        encontrados_en_pagina = 0

        for item in items:
            try:
                # 1. Nombre del Producto
                nombre = ""
                for selector in ['.product-title a', '.product-title', 'h2.h3', 'h2', 'h3']:
                    try:
                        elem = item.find_element(By.CSS_SELECTOR, selector)
                        txt = elem.text.strip()
                        if txt:
                            nombre = txt
                            break
                    except:
                        pass

                # 2. Precio Oferta / Actual
                precio_oferta = ""
                for selector in ['.current-price .price', 'span.price', '.product-price-and-shipping .price', '.price', '.product-price']:
                    try:
                        elem = item.find_element(By.CSS_SELECTOR, selector)
                        txt = elem.text.strip()
                        if txt:
                            precio_oferta = txt
                            break
                    except:
                        pass

                if not precio_oferta:
                    precio_oferta = "Consultar"

                # 3. Precio Regular / Normal
                precio_regular = ""
                for selector in ['.regular-price', '.old-price', 'span.regular-price']:
                    try:
                        elem = item.find_element(By.CSS_SELECTOR, selector)
                        txt = elem.text.strip()
                        if txt:
                            precio_regular = txt
                            break
                    except:
                        pass

                if not precio_regular:
                    precio_regular = precio_oferta

                # 4. Enlace del Producto
                enlace = ""
                try:
                    enlace = item.find_element(By.CSS_SELECTOR, 'a.thumbnail-container, a.product-thumbnail, a').get_attribute('href')
                except:
                    pass

                # 5. Imagen
                imagen = ""
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, 'img')
                    imagen = img_elem.get_attribute('data-full-size-image-url') or img_elem.get_attribute('src')
                except:
                    pass

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

        if encontrados_en_pagina == 0 or pagina >= 15:
            break

        pagina += 1

    print(f"\nTOTAL FINAL: {len(lista_productos)} productos extraídos correctamente.")

    df = pd.DataFrame(lista_productos)
    df = df.drop_duplicates(subset=['Producto'])
   df.to_csv('catalogo_portatil_chile.csv', index=False, sep='|', encoding='utf-8-sig')
    print("Archivo 'catalogo_portatil_chile.csv' guardado con éxito.")

except Exception as error:
    print(f"Ocurrió un error inesperado durante el escaneo: {error}")

finally:
    driver.quit()
