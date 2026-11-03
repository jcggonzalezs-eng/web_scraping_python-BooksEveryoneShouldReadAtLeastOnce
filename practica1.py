#importamos las librerías
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

#indicamos la página de Goodreads para extraer
url: str = "https://www.goodreads.com/list/show/264.Books_That_Everyone_Should_Read_At_Least_Once?ref=ls_pl_car_1"

#añadimos un encabezado para peticiones
headers: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

#creamos las variables
activo: bool = True
autor_fecha:dict[str, str] = {}
libro_autor: list[tuple[str, str]] = []
autores: list[str] = []

#1. EXTRACCIÓN DE LIBROS Y AUTORES

#recorremos las páginas de Goodreads
try:
    with requests.Session() as session:
        session.headers.update(headers)

        while activo:
            #esperamos un segundo antes de realizar otra petición
            time.sleep(0.2)

            #descargamos el contenido
            response = session.get(url, timeout=20)
            response.raise_for_status()

            #analizamos el HTML
            soup = BeautifulSoup(response.text, "html.parser")

            #buscamos los títulos de los libros y los nombres de sus autores
            libros = soup.find_all("a", class_="bookTitle")
            autores_ref = soup.find_all("a", class_="authorName")

            #guardamos cada libro junto con su autor
            libro_autor.extend(
                (l.get_text(strip=True), a.get_text(strip=True))
                for l, a in zip(libros, autores_ref)
            )

            #guardamos los enlaces de los perfiles de los autores
            autores.extend(
                autor.get("href")
                for autor in autores_ref
                if autor.get("href")
            )

            #buscamos el enlace para pasar a la siguiente página
            paginacion = soup.find(class_="pagination")
            prox_pag = paginacion.find("a", rel="next") if paginacion else None

            #si existe otra página, actualizamos la URL si no, terminamos
            if prox_pag:
                url = "https://www.goodreads.com" + prox_pag.get("href")
            else:
                activo = False

except requests.exceptions.RequestException as error:
    print("Error durante la extracción de libros:", error)

finally:
    print("Proceso de extracción de libros finalizado.")


#2. EXTRACCIÓN DE INFORMACIÓN

#eliminamos los enlaces repetidos
autores_unicos: set[str] = set(autores)

#recorremos los perfiles de los autores
try:
    with requests.Session() as session:
        session.headers.update(headers)

        for i, url_aut in enumerate(autores_unicos, start=1):

            #esperamos un segundo antes de consultar otro perfil
            time.sleep(0.2)

            try:
                #completamos la dirección si el enlace es relativo (incompleto)
                if url_aut.startswith("/"):
                    url_aut = "https://www.goodreads.com" + url_aut

                #descargamos el perfil del autor
                response_aut = session.get(url_aut, timeout=20)
                response_aut.raise_for_status()

                #analizamos el HTML del perfil
                soup_aut = BeautifulSoup(response_aut.text, "html.parser")

                #buscamos el nombre y el dato de fecha de nacimiento
                nombre_ref = soup_aut.find(class_="authorName")
                fecha_ref = soup_aut.find(class_="dataItem")

                nombre = nombre_ref.get_text(strip=True) if nombre_ref else "Anonymous"
                fecha_nacimiento = fecha_ref.get_text(strip=True) if fecha_ref else "Unknown"

                #guardamos el nombre del autor
                autor_fecha[nombre] = fecha_nacimiento

            except requests.exceptions.RequestException as error:
                print(f"Error al consultar el perfil: {error}")

            #proceso cada 10 autores
            if i % 10 == 0 or i == len(autores_unicos):
                print(f"Autores procesados: {i}/{len(autores_unicos)}")

finally:
    print("Proceso de extracción de autores finalizado.")


libro_autor_fechaNac = [(libro,autor,autor_fecha.get(autor,'Unknown')) for (libro,autor) in libro_autor]



#3. DATOS EXTRAÍDOS

print("\nRESUMEN DE LA EXTRACCIÓN")
print("Total de libros y autores:", len(libro_autor))
print("Enlaces de autores recopilados:", len(autores))
print("Perfiles únicos de autores:", len(autores_unicos))
print("Autores con información recopilada:", len(autor_fecha))

#4. DATOS GUARDADOS

#Creamos tabla de titulo, autor y fecha de nacimiento.
df_dataset: pd.DataFrame = pd.DataFrame(
    libro_autor_fechaNac,
    columns = ["Titulo", "Autor","Fecha_Nac"]
)

#guardamos en archivo CSV
df_dataset.to_csv("libros_autores_fechas.csv", index = False, encoding = "utf-8-sig")
