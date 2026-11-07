"""Module that provides the functionality to read data for the Mexican "chispazo" sweepstakes."""

import os
import sys
import platform
import time
from tkinter import messagebox
import tkinter as tk
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

# VARIABLES
# URL de la página a abrir
URL = "https://www.loterianacional.gob.mx/Home/Historicos?ARHP=UgBlAHYAYQBuAGMAaABhAA=="

# Revanchita https://www.loterianacional.gob.mx/Home/Historicos?ARHP=UgBlAHYAYQBuAGMAaABpAHQAYQA=

# Ruta del archivo CSV
CSV = "Revancha.csv"

# Ruta de descarga
DOWNLOAD_PATH = os.getcwd()


def main():
    """Método principal"""

    try:
        # METODOS
        # Cargar los resultados del CSV
        if os.path.isfile(CSV):
            resultados, resultados_df = cargar_resultados_csv(CSV)
        else:
            print("Archivo de datos no encontrado. Descargando ...")
            descargar_csv()
            main()

        # Calcula frecuencia de cada número
        frecuencia_numeros = calcular_frecuencia_numeros(resultados)

        while True:
            opcion = menu_opc()

            if opcion == "1":
                revisar_combinacion_existente(resultados, resultados_df)
            elif opcion == "2":
                generar_combinaciones_probables(resultados, frecuencia_numeros)
            elif opcion == "3":
                calcular_probabilidades_combinaciones(resultados, frecuencia_numeros)
            elif opcion == "4":
                print("Actualizando registros.")
                descargar_csv()
            elif opcion == "5":
                combinacion_mas_repetida(resultados_df)
            elif opcion == "6":
                print("¡Hasta luego!")
                break
            else:
                title = "ERROR"
                msg = f"{opcion} no es una opción valida.\nPor favor, elije una opción válida.\n"
                print(msg)
                mostrar_messagebox(title, msg)
                limpiar_consola()

    finally:
        print("\nEjecución finalizada.")


#         Web         #
def open_web(_url):
    """Método que abre el navegador y va a la página indicada"""

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecuta el navegador oculto
    chrome_options.add_argument("--log-level=3")  # Evita logs innecesarios
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": DOWNLOAD_PATH,  # Establece ruta de descarga
            "download.prompt_for_download": False,  # Desactiva el diálogo de descarga
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    driver = webdriver.Chrome(options=chrome_options)

    driver.maximize_window()
    driver.get(_url)

    return driver


def descargar_csv():
    """Método que descarga el archivo con los resultados historicos del sorteo CHISPAZO"""

    try:
        # Se abre el navegador y carga la URL
        with open_web(URL) as driver:
            # Simulación de una descarga de 2 segundos
            for _ in tqdm(range(2), desc="Descargando información"):
                time.sleep(1)
            driver.close()
    except WebDriverException as e:
        mostrar_messagebox("ERROR", f"Error al intentar abrir la web: {e}")

    # Verificar si el archivo ha sido descargado
    if os.path.exists(CSV):
        mostrar_messagebox("EXITO", "Archivo descargado con éxito.")
        limpiar_consola()
    else:
        mostrar_messagebox("ERROR", "Archivo no descargado, intentando nuevamente")
        limpiar_consola()


#                     #


#        Optimización        #
def obtener_combinacion_usuario():
    """Obtiene la combinación ingresada por el usuario."""
    combinacion = []
    for i in range(6):
        while True:
            try:
                numero = int(input(f"Ingrese el número {i+1}: "))
                if 1 <= numero <= 56:
                    if numero not in combinacion:
                        combinacion.append(numero)
                        break
                    else:
                        mostrar_messagebox(
                            "ADVERTENCIA",
                            f"El número {numero} no puede repetirse. Intenta con otro número.",
                        )
                else:
                    mostrar_messagebox(
                        "ADVERTENCIA", "El número debe ser entre 1 y 56."
                    )
            except ValueError:
                mostrar_messagebox("ADVERTENCIA", "Por favor, ingresa un número.")

    return combinacion


def revisar_combinacion_existente(res, res_df):
    """Revisa si una combinación existe en los resultados."""
    title = "Upss!"
    msg = "Oh no!, la combinación ya salió sorteada.\n\n"

    comb_usuario = obtener_combinacion_usuario()
    comb_usuario.sort()
    if comb_usuario in res:
        for _, row in res_df[
            res_df.apply(
                lambda x: (x["R1"], x["R2"], x["R3"], x["R4"], x["R5"], x["R6"])
                == tuple(comb_usuario),
                axis=1,
            )
        ].iterrows():
            # ,3,5,9,13,27, - 4
            msg += (
                f"CONCURSO: {row['CONCURSO']} - "
                f"[{', '.join([str(value) for column, value in row.items() if column.startswith('R')])}] - "
                f"FECHA: {row['FECHA']}\n"
            )
        mostrar_messagebox(title, msg)
        limpiar_consola()
    else:
        title = "¡¡ ESTAS DE SUERTE !!"
        msg = f"¡¡ ESTAS DE SUERTE !!\nLa combinación {comb_usuario} nunca ha salido sorteada."

        mostrar_messagebox(title, msg)
        limpiar_consola()


def generar_combinaciones_probables(res, frec_num):
    """Genera las combinaciones más probables."""
    combinaciones_probables = obtener_combinaciones_probables(frec_num)
    probabilidades_combinaciones = [
        calcular_probabilidades_combinaciones(res, combinacion, frec_num)
        for combinacion in combinaciones_probables
    ]
    imprimir_combinaciones_probables(
        combinaciones_probables, probabilidades_combinaciones
    )


#                            #


#        Logica Principal        #
def menu_opc():
    """Método que contiene el menú de opciones"""
    mostrar_banner()
    print("Seleccione una opción:")
    print("1- Revisar si una combinación existe.")
    print("2- Generar las combinaciones más probables.")
    print("3- Calcular la probabilidad de una combinación ingresada.")
    print("4- Descargar resultados del sorteo. (Actualiza datos del sorteo)")
    print("5- Mostrar la combinación mas repetida.")
    print("6- Salir.")
    opc = input("\nIngresa el número de la opción: ")

    return opc


def cargar_resultados_csv(csv):
    """Carga los resultados del archivo CSV con barra de progreso."""

    tqdm.pandas(desc="Leyendo DATOS")

    # Se lee CSV
    df = pd.read_csv(csv)

    # Se crea un DataFrame sin columnas 'NPRODUCTO' y 'BOLSA'
    df_mod = df.drop(["NPRODUCTO", "BOLSA"], axis=1)

    # Se aplica operación para visualizar el progreso
    df_mod.progress_apply(lambda x: x, axis=1)

    resultados = df_mod.iloc[:, 1:7].values.tolist()

    return resultados, df_mod


def calcular_frecuencia_numeros(resul):
    """Calcula la frecuencia de cada número."""
    frecuencia_numeros = {}
    for resultado in resul:
        for numero in resultado:
            if numero in frecuencia_numeros:
                frecuencia_numeros[numero] += 1
            else:
                frecuencia_numeros[numero] = 1
    return frecuencia_numeros


def obtener_combinaciones_probables(frec_nums):
    """Obtiene las 5 combinaciones probables basadas en los números más frecuentes."""
    numeros_ordenados = sorted(frec_nums, key=frec_nums.get, reverse=True)
    combinaciones_probables = [sorted(numeros_ordenados[:6])]
    for i in range(1, 6):
        combinaciones_probables.append(sorted(numeros_ordenados[i : i + 6]))
    return combinaciones_probables


def verificar_existencia_combinaciones(results, comb_probables):
    """Verifica si las combinaciones probables existen en el archivo CSV."""
    combinaciones_validas = []
    for combinacion in comb_probables:
        combinacion_existe = False
        for resultado in results:
            if all(numero in resultado for numero in combinacion):
                combinacion_existe = True
                break
        if not combinacion_existe:
            combinaciones_validas.append(combinacion)
    return combinaciones_validas


def calcular_probabilidades_combinaciones(resul, frec_numeros):
    """Calcula la probabilidad de la combinación ingresada por el usuario."""
    comb_usuario = obtener_combinacion_usuario()
    comb_usuario.sort()
    total_resultados = len(resul)
    probabilidad_combinacion = 1
    for numero in comb_usuario:
        probabilidad_combinacion *= frec_numeros[numero] / total_resultados

    title = "Probabilidad de combinación ingresada"
    msg = f"La probabilidad de la combinación {comb_usuario} es: {probabilidad_combinacion}%"

    print(msg)
    mostrar_messagebox(title, msg)
    limpiar_consola()


def imprimir_combinaciones_probables(comb_probables, prob_combinaciones):
    """Imprime las 5 combinaciones probables restantes con sus probabilidades."""
    title = "Combinaciones probables de ganar"
    msg = "Las 5 combinaciones probables de ganar (sin que hayan salido antes):\n\n"

    print(
        "\nLas 5 combinaciones probables de ganar (sin que hayan salido anteriormente):"
    )
    for i, combinacion in enumerate(comb_probables[:5]):
        print(
            f"Combinación {i+1}: {combinacion} - Probabilidad: {prob_combinaciones[i]} %"
        )
        msg += f"Comb. {i+1}: {combinacion} - Probabilidad: {prob_combinaciones[i]:.10f}%\n\n"
    mostrar_messagebox(title, msg)
    limpiar_consola()


def combinacion_mas_repetida(res_df):
    """Encuentra las 5 combinaciones más repetidas en los resultados."""
    title = "Combinaciones mas repetidas"
    msg = "Las 5 combinaciones con mas repeticiones en la historia son:\n"

    combinaciones = res_df.iloc[:, 1:7].apply(tuple, axis=1)
    combinaciones_repetidas = combinaciones.value_counts().head(5)
    combinaciones_repetidas = combinaciones_repetidas.reset_index()
    combinaciones_repetidas.columns = ["Combinación", "Repeticiones"]

    print("Las 5 combinaciones con mas repeticiones en la historia son:")

    for _, row in combinaciones_repetidas.iterrows():
        combinacion_str = "[" + ", ".join(map(str, row["Combinación"])) + "]"
        print(f"{combinacion_str} - con {row['Repeticiones']} repeticiones.")

        msg += f"{combinacion_str} - con {row['Repeticiones']} repeticiones.\n"

    mostrar_messagebox(title, msg)
    limpiar_consola()


#                                #


#       Extras       #
def limpiar_consola():
    """Limpia la consola según el sistema operativo."""
    sistema = platform.system()
    if sistema == "Windows":
        os.system("cls")  # Comando para limpiar consola en Windows
    else:
        os.system("clear")  # Comando para limpiar consola en Unix/Linux/MacOS


def mostrar_messagebox(titulo, mensaje):
    """Método que muestra un mensaje al usuario"""

    # Crea la ventana principal
    root = tk.Tk()

    # Coloca la ventana principal como superior
    root.attributes("-topmost", True)
    root.withdraw()

    # Muestra un cuadro de diálogo con el mensaje
    messagebox.showinfo(titulo, mensaje)

    # Cierra la ventana principal
    root.destroy()


def mostrar_banner():
    "Imprime un banner gráfico en la consola."
    banner = """
    ########  ######## ##     ##    ###    ##    ##  ######  ##     ##    ###    
    ##     ## ##       ##     ##   ## ##   ###   ## ##    ## ##     ##   ## ##   
    ##     ## ##       ##     ##  ##   ##  ####  ## ##       ##     ##  ##   ##  
    ########  ######   ##     ## ##     ## ## ## ## ##       ######### ##     ## 
    ##   ##   ##        ##   ##  ######### ##  #### ##       ##     ## ######### 
    ##    ##  ##         ## ##   ##     ## ##   ### ##    ## ##     ## ##     ## 
    ##     ## ########    ###    ##     ## ##    ##  ######  ##     ## ##     ## 
    """
    print(banner)


#                    #

if __name__ == "__main__":
    main()
else:
    print("Uso incorrecto.")
