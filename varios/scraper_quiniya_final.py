"""
Scraper final para QuiniYa.com.ar - Extracción masiva de datos históricos
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import csv
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup


def _normalizar_premio_texto(premio_texto):
    """Convierte un texto de premio a solo dígitos enteros."""
    if premio_texto is None:
        return None
    premio = str(premio_texto).strip()
    if not premio:
        return None
    premio = premio.replace('$', '').replace('.', '').split(',')[0].strip()
    premio = re.sub(r'[^\d]', '', premio)
    return premio or None


def _normalizar_ganadores_texto(ganadores_texto):
    """Normaliza el texto de ganadores para mantener el criterio existente."""
    if ganadores_texto is None:
        return None
    ganadores = str(ganadores_texto).strip()
    if not ganadores:
        return None
    return ganadores


def _mapear_modalidad_desde_titulo(titulo):
    """Mapea el título del bloque HTML a la modalidad interna."""
    titulo = (titulo or '').strip().lower()
    if 'tradicional' in titulo and 'primer' in titulo:
        return 'Tradicional'
    if 'segunda' in titulo:
        return 'Segunda'
    if 'revancha' in titulo:
        return 'Revancha'
    if 'siempre sale' in titulo:
        return 'SiempreSale'
    return None


def _extraer_pozos_desde_soup(soup):
    """Extrae pozos desde el HTML nuevo de QuiniYa."""
    pozos = {
        'Tradicional': {'premio': None, 'ganadores': None},
        'Segunda': {'premio': None, 'ganadores': None},
        'Revancha': {'premio': None, 'ganadores': None},
        'SiempreSale': {'premio': None, 'ganadores': None}
    }

    main = soup.select_one('main#main-content') or soup
    bloques = main.select('div.shadow')

    print(f"Bloques de sorteo encontrados: {len(bloques)}")

    for idx, bloque in enumerate(bloques):
        try:
            titulo_elem = bloque.select_one('h2')
            titulo = titulo_elem.get_text(' ', strip=True) if titulo_elem else ''
            modalidad_key = _mapear_modalidad_desde_titulo(titulo)
            if not modalidad_key:
                continue

            tabla = bloque.select_one('table')
            if not tabla:
                continue

            filas = tabla.select('tbody tr') or tabla.select('tr')
            if not filas:
                continue

            print(f"  Bloque {idx + 1}: {modalidad_key} detectado")

            for fila_idx, fila in enumerate(filas):
                celdas = fila.find_all(['th', 'td'])
                if len(celdas) < 3:
                    continue

                aciertos = celdas[0].get_text(' ', strip=True)
                ganadores = _normalizar_ganadores_texto(celdas[1].get_text(' ', strip=True))
                premio = _normalizar_premio_texto(celdas[2].get_text(' ', strip=True))

                if not premio:
                    continue

                if modalidad_key in ('Tradicional', 'Segunda', 'Revancha'):
                    if aciertos == '6' and pozos[modalidad_key]['premio'] is None:
                        pozos[modalidad_key] = {'premio': premio, 'ganadores': ganadores}
                        print(f"  {modalidad_key}: ${premio} - {ganadores}")
                        break
                elif modalidad_key == 'SiempreSale':
                    if pozos['SiempreSale']['premio'] is None:
                        pozos['SiempreSale'] = {'premio': premio, 'ganadores': ganadores}
                        print(f"  Siempre Sale: ${premio} - {ganadores} ({aciertos} aciertos)")
                        break

        except Exception:
            continue

    return pozos


def _extraer_historico_desde_soup(soup):
    """Extrae todos los sorteos históricos desde la tabla nueva de /sorteos."""
    sorteos = []

    main = soup.select_one('main#main-content') or soup
    tabla = main.select_one('div.qy-table-scroll table') or main.select_one('table.table')
    if not tabla:
        return sorteos

    filas = tabla.select('tbody tr') or tabla.select('tr')
    if not filas:
        return sorteos

    # Si existe thead, la primera fila de tr no debe saltarse porque usamos tbody;
    # si no hay tbody, descartamos cabecera por contenido.
    for fila in filas:
        celdas = fila.find_all(['th', 'td'])
        if len(celdas) < 6:
            continue

        fecha_str = celdas[0].get_text(' ', strip=True)
        fecha = parse_fecha_quiniya(fecha_str)
        if not fecha:
            continue

        series = {
            'Tradicional': celdas[1].get_text(' ', strip=True),
            'Segunda': celdas[2].get_text(' ', strip=True),
            'Revancha': celdas[3].get_text(' ', strip=True),
            'SiempreSale': celdas[4].get_text(' ', strip=True),
        }

        for modalidad, numeros_str in series.items():
            numeros = [int(n) for n in re.findall(r'\d{1,2}', numeros_str)]
            if len(numeros) != 6:
                continue

            sorteos.append({
                'fecha': fecha,
                'fecha_original': fecha_str,
                'modalidad': modalidad,
                'numeros': numeros,
            })

    return sorteos

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.page_load_strategy = 'eager'  # No esperar a que carguen todos los recursos
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.set_page_load_timeout(30)  # Timeout de 30 segundos para carga de página
    driver.implicitly_wait(10)  # Espera implícita de 10 segundos para elementos
    
    return driver

def parse_fecha_quiniya(fecha_str):
    """
    Convierte fecha de QuiniYa a formato YYYY-MM-DD
    Ejemplos: "4/2/2026" => "2026-02-04", "28/1/2026" => "2026-01-28"
    """
    try:
        # Parsear d/m/yyyy o dd/mm/yyyy
        partes = fecha_str.split('/')
        dia = int(partes[0])
        mes = int(partes[1])
        anio = int(partes[2])
        
        return f"{anio:04d}-{mes:02d}-{dia:02d}"
    except:
        return None

def extraer_tabla_principal(driver):
    """
    Extrae todos los sorteos de la tabla principal en /sorteos
    """
    print("\n" + "="*80)
    print("EXTRAYENDO TABLA PRINCIPAL")
    print("="*80)
    
    sorteos = []
    
    try:
        url = "https://quiniya.com.ar/sorteos"
        print(f"\nAccediendo a: {url}")
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        sorteos = _extraer_historico_desde_soup(soup)

        print(f"Filas encontradas: {len(sorteos) // 4 if sorteos else 0}")
        
        print(f"✓ Extraídos {len(sorteos)} sorteos de la tabla")
        
        if sorteos:
            print(f"  Rango: {sorteos[-1]['fecha']} a {sorteos[0]['fecha']}")
        
    except Exception as e:
        print(f"✗ Error extrayendo tabla: {e}")
    
    return sorteos

def extraer_sorteo_individual(driver, sorteo_id):
    """
    Intenta extraer un sorteo individual desde /sorteos/{sorteo_id}
    """
    try:
        url = f"https://quiniya.com.ar/sorteos/{sorteo_id}"
        driver.get(url)
        time.sleep(1)
        
        # Verificar si la página existe (no es 404 o error)
        if "404" in driver.title.lower() or "error" in driver.page_source.lower()[:500]:
            return None
        
        # Buscar fecha
        # Patrón típico: "📅 9/2/2025 #3242"
        html = driver.page_source
        match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', html)
        
        if not match_fecha:
            return None
        
        fecha_str = match_fecha.group(1)
        fecha = parse_fecha_quiniya(fecha_str)
        
        # Buscar números de las 4 modalidades
        patrones = {
            'Tradicional': r'Tradicional[^0-9]*([0-9\s]{17,})',
            'Segunda': r'Segunda[^0-9]*([0-9\s]{17,})',
            'Revancha': r'Revancha[^0-9]*([0-9\s]{17,})',
            'SiempreSale': r'Siempre\s*Sale[^0-9]*([0-9\s]{17,})'
        }
        
        sorteos = []
        for modalidad, patron in patrones.items():
            match_modalidad = re.search(patron, html, re.IGNORECASE)
            if not match_modalidad:
                continue
            
            numeros_text = match_modalidad.group(1).strip()
            numeros = [int(n) for n in re.findall(r'\b([0-4][0-9])\b', numeros_text)]
            
            if len(numeros) == 6:
                sorteos.append({
                    'sorteo_id': sorteo_id,
                    'fecha': fecha,
                    'fecha_original': fecha_str,
                    'modalidad': modalidad,
                    'numeros': numeros
                })
        
        return sorteos if sorteos else None
        
    except Exception as e:
        return None

def obtener_sorteos_antiguos(driver, sorteo_inicio, cantidad=50):
    """
    Intenta obtener sorteos más antiguos navegando hacia atrás
    desde sorteo_inicio - 1, sorteo_inicio - 2, etc.
    """
    print("\n" + "="*80)
    print(f"BUSCANDO SORTEOS ANTIGUOS (desde {sorteo_inicio - 1} hacia atrás)")
    print("="*80)
    
    sorteos = []
    sorteo_actual = sorteo_inicio - 1
    intentos_fallidos = 0
    max_fallos = 5  # Detener después de 5 fallos consecutivos
    sorteos_encontrados = 0
    
    while sorteos_encontrados < cantidad and intentos_fallidos < max_fallos:
        print(f"\rProbando sorteo #{sorteo_actual}...", end='', flush=True)
        
        sorteo_data = extraer_sorteo_individual(driver, sorteo_actual)
        
        if sorteo_data:
            sorteos.extend(sorteo_data)
            sorteos_encontrados += 1
            intentos_fallidos = 0
            modalidades = [s['modalidad'] for s in sorteo_data]
            print(f"\r✓ Sorteo #{sorteo_actual}: {sorteo_data[0]['fecha']} - {', '.join(modalidades)}")
        else:
            intentos_fallidos += 1
        
        sorteo_actual -= 1
        time.sleep(0.5)  # Pausa corta para no saturar
    
    print(f"\n\n✓ Obtenidos {sorteos_encontrados} sorteos antiguos adicionales")
    return sorteos

def guardar_csv(sorteos, archivo='data/quini6_historico.csv'):
    """
    Guarda todos los sorteos en CSV
    """
    if not sorteos:
        print("\n✗ No hay sorteos para guardar")
        return
    
    # Ordenar por fecha (más antiguos primero)
    sorteos_ordenados = sorted(sorteos, key=lambda x: x['fecha'])
    
    print(f"\n" + "="*80)
    print("GUARDANDO DATOS")
    print("="*80)
    print(f"\nArchivo: {archivo}")
    print(f"Total sorteos: {len(sorteos_ordenados)}")
    print(f"Rango: {sorteos_ordenados[0]['fecha']} a {sorteos_ordenados[-1]['fecha']}")
    
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sorteo_id', 'fecha', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6'])
        
        for i, sorteo in enumerate(sorteos_ordenados):
            # ID es el índice consecutivo o el sorteo_id si existe
            sid = sorteo.get('sorteo_id', i + 1)
            fila = [sid, sorteo['fecha']] + sorteo['numeros']
            writer.writerow(fila)
    
    print(f"✓ Datos guardados exitosamente")
    
    # Validar caso conocido
    caso_test = [2, 4, 15, 18, 31, 43]
    for sorteo in sorteos_ordenados:
        if sorted(sorteo['numeros']) == caso_test:
            print(f"\n✓ VALIDACIÓN: Encontrado caso de prueba")
            print(f"  Fecha: {sorteo['fecha']}")
            print(f"  Números: {sorteo['numeros']}")
            break

def _leer_existentes_csv(archivo):
    existentes = set()
    max_id = 0
    path = Path(archivo)
    if not path.exists():
        return existentes, max_id
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = row.get('fecha')
            if not fecha:
                continue
            try:
                numeros = [int(row[f'num{i}']) for i in range(1, 7)]
            except Exception:
                continue
            
            existentes.add((fecha, tuple(numeros)))
            try:
                max_id = max(max_id, int(row.get('sorteo_id', 0)))
            except Exception:
                continue
    
    return existentes, max_id

def actualizar_historico_csv(archivo='data/quini6_historico.csv'):
    """
    Actualiza el CSV de Quini6 desde QuiniYa.com.ar agregando solo sorteos faltantes.
    SOLO puede escribir en CSVs cuyo nombre contenga 'quini' para evitar cruce con Loto.
    """
    archivo_norm = str(archivo).replace('\\', '/').lower()
    if 'quini' not in archivo_norm:
        raise ValueError(
            f"Ruta destino inválida para scraper de Quini6: '{archivo}'.\n"
            f"Este scraper extrae datos de QuiniYa.com.ar (Quini 6) y solo puede "
            f"escribir en el CSV de Quini 6 (la ruta debe contener 'quini')."
        )
    driver = configurar_driver()
    
    try:
        existentes, max_id = _leer_existentes_csv(archivo)
        sorteos_tabla = extraer_tabla_principal(driver)
        
        nuevos = []
        for sorteo in sorteos_tabla:
            key = (sorteo['fecha'], tuple(sorteo['numeros']))
            if key not in existentes:
                nuevos.append(sorteo)
        
        if not nuevos:
            print("\n✓ No hay sorteos nuevos para agregar")
            return 0
        
        nuevos_ordenados = sorted(nuevos, key=lambda x: x['fecha'])
        path = Path(archivo)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = path.exists()
        with open(path, 'a' if file_exists else 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['sorteo_id', 'fecha', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6'])
            
            for i, sorteo in enumerate(nuevos_ordenados, start=max_id + 1):
                fila = [i, sorteo['fecha']] + sorteo['numeros']
                writer.writerow(fila)
        
        print(f"\n✓ Agregados {len(nuevos_ordenados)} sorteos nuevos")
        return len(nuevos_ordenados)
    
    finally:
        driver.quit()

def obtener_pozos_rapido():
    """
    Versión OPTIMIZADA: Obtiene pozos usando requests + BeautifulSoup (10-20x más rápido que Selenium)
    Retorna: dict con pozos de Tradicional, Segunda, Revancha y Siempre Sale
    """
    try:
        url = "https://quiniya.com.ar/sorteos/ultimo"
        print(f"\nAccediendo a: {url}")
        
        # Request HTTP simple (sin navegador)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("Página cargada, parseando HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')

        pozos = _extraer_pozos_desde_soup(soup)
        
        # Verificar cuántos pozos se obtuvieron
        pozos_count = sum(1 for v in pozos.values() if v and v.get('premio'))
        print(f"\n✓ Pozos obtenidos: {pozos_count}/4")
        
        if pozos_count < 4:
            print("⚠ No se obtuvieron todos los pozos con requests, intentando con Selenium...")
            return None  # Trigger fallback a Selenium
        
        return pozos
    
    except Exception as e:
        print(f"✗ Error con método rápido: {e}")
        return None

def obtener_pozos_ultimo_sorteo():
    """
    Obtiene los pozos actuales del último sorteo desde /sorteos/ultimo
    NOTA: Primero intenta con requests (rápido), si falla usa Selenium (lento pero robusto)
    Retorna: dict con pozos de Tradicional, Segunda, Revancha y Siempre Sale
    """
    # INTENTO 1: Método rápido con requests + BeautifulSoup
    pozos = obtener_pozos_rapido()
    if pozos:
        return pozos
    
    # INTENTO 2: Fallback a Selenium (más lento pero más robusto)
    print("\n⚙ Usando método alternativo con Selenium...")
    driver = None
    
    try:
        driver = configurar_driver()
        url = "https://quiniya.com.ar/sorteos/ultimo"
        print(f"\nAccediendo a: {url}")
        
        try:
            driver.get(url)
            print("Página cargada, esperando elementos...")
            time.sleep(2)
            print("Buscando bloques de sorteo...")
        except Exception as e:
            print(f"✗ Error al cargar la página: {e}")
            return None
        
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            main = soup.select_one('main#main-content') or soup
            bloques = main.select('div.shadow')
            print(f"Bloques de sorteo encontrados: {len(bloques)}")
            pozos = _extraer_pozos_desde_soup(soup)
        except Exception as e:
            print(f"  Error parseando HTML con Selenium: {e}")
            return None
        
        print(f"\n✓ Pozos obtenidos:")
        for modalidad, data in pozos.items():
            if data and data.get('premio'):
                print(f"  {modalidad}: ${data['premio']} - {data.get('ganadores', 'N/A')}")
        
        return pozos
    
    except Exception as e:
        print(f"✗ Error obteniendo pozos: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def main():
    print("="*80)
    print("SCRAPER QUINIYA.COM.AR - EXTRACCIÓN MASIVA DE DATOS HISTÓRICOS")
    print("="*80)
    
    driver = configurar_driver()
    todos_sorteos = []
    
    try:
        # 1. Extraer tabla principal (104 sorteos aprox)
        sorteos_tabla = extraer_tabla_principal(driver)
        todos_sorteos.extend(sorteos_tabla)
        
        # 2. Identificar el sorteo más antiguo de la tabla
        if sorteos_tabla:
            sorteos_ordenados = sorted(sorteos_tabla, key=lambda x: x['fecha'])
            
            # Extraer ID del sorteo más antiguo (aproximadamente 3242)
            # Asumiendo que el sorteo más reciente es ~3345
            sorteo_mas_reciente = 3345
            sorteo_mas_antiguo_tabla = sorteo_mas_reciente - len(sorteos_tabla) + 1
            
            print(f"\nSorteo más antiguo en tabla: ~#{sorteo_mas_antiguo_tabla}")
            
            # 3. Intentar obtener más sorteos antiguos
            print("\n¿Intentar obtener sorteos más antiguos? (navegación individual)")
            print("Esto puede tomar varios minutos...")
            
            respuesta = input("\nCantidad de sorteos adicionales a buscar (0 para saltar, 50-200 recomendado): ").strip()
            
            try:
                cantidad = int(respuesta)
                if cantidad > 0:
                    sorteos_antiguos = obtener_sorteos_antiguos(driver, sorteo_mas_antiguo_tabla, cantidad)
                    todos_sorteos.extend(sorteos_antiguos)
            except:
                print("Saltando búsqueda de sorteos antiguos...")
        
        # 4. Guardar todos los datos
        if todos_sorteos:
            guardar_csv(todos_sorteos)
            
            print("\n" + "="*80)
            print("SCRAPING COMPLETADO")
            print("="*80)
            print(f"\nTotal sorteos obtenidos: {len(todos_sorteos)}")
            print(f"Archivo: data/quini6_historico.csv")
            print("\nPróximos pasos:")
            print("1. Ejecutar test_accuracy.py con estos datos")
            print("2. Ajustar parámetros según resultados")
        else:
            print("\n✗ No se obtuvieron sorteos")
        
    except Exception as e:
        print(f"\n✗ Error general: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
