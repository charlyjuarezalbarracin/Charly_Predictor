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

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

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
        
        # Encontrar la tabla
        tabla = driver.find_element(By.CSS_SELECTOR, 'table.table')
        filas = tabla.find_elements(By.TAG_NAME, 'tr')[1:]  # Saltar header
        
        print(f"Filas encontradas: {len(filas)}")
        
        for fila in filas:
            try:
                celdas = fila.find_elements(By.TAG_NAME, 'td')
                
                if len(celdas) >= 5:
                    fecha_str = celdas[0].text.strip()
                    fecha = parse_fecha_quiniya(fecha_str)
                    
                    series = {
                        'Tradicional': celdas[1].text.strip(),
                        'Segunda': celdas[2].text.strip(),
                        'Revancha': celdas[3].text.strip(),
                        'SiempreSale': celdas[4].text.strip()
                    }
                    
                    for modalidad, numeros_str in series.items():
                        numeros = [int(n) for n in numeros_str.split()]
                        if fecha and len(numeros) == 6:
                            sorteos.append({
                                'fecha': fecha,
                                'fecha_original': fecha_str,
                                'modalidad': modalidad,
                                'numeros': numeros
                            })
            except Exception:
                continue
        
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
    Actualiza el CSV agregando solo sorteos faltantes (sin pisar datos)
    """
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

def obtener_pozos_ultimo_sorteo():
    """
    Obtiene los pozos actuales del último sorteo desde /sorteos/ultimo
    Retorna: dict con pozos de Tradicional, Segunda, Revancha y Siempre Sale
    """
    driver = configurar_driver()
    
    try:
        url = "https://quiniya.com.ar/sorteos/ultimo"
        print(f"\nAccediendo a: {url}")
        driver.get(url)
        time.sleep(4)
        
        pozos = {
            'Tradicional': {'premio': None, 'ganadores': None},
            'Segunda': {'premio': None, 'ganadores': None},
            'Revancha': {'premio': None, 'ganadores': None},
            'SiempreSale': {'premio': None, 'ganadores': None}
        }
        
        # Obtener todo el HTML de la página
        page_html = driver.page_source
        
        # Buscar todas las secciones con encabezados
        sections = driver.find_elements(By.TAG_NAME, 'section')
        
        for section in sections:
            try:
                section_text = section.text.lower()
                
                # Buscar tabla dentro de esta sección
                try:
                    tabla = section.find_element(By.TAG_NAME, 'table')
                except:
                    continue
                
                filas = tabla.find_elements(By.TAG_NAME, 'tr')
                
                # Determinar tipo de modalidad basado en el texto de la sección
                es_tradicional = 'tradicional' in section_text and 'primer sorteo' in section_text
                es_segunda = 'la segunda' in section_text or ('segunda' in section_text and 'tradicional' not in section_text)
                es_revancha = 'revancha' in section_text
                es_siempre_sale = 'siempre sale' in section_text
                
                for fila in filas:
                    try:
                        celdas = fila.find_elements(By.TAG_NAME, 'td')
                        if len(celdas) >= 3:
                            aciertos = celdas[0].text.strip()
                            col2_texto = celdas[1].text.strip()
                            col2_lower = col2_texto.lower()
                            premio_texto = celdas[2].text.strip()
                            
                            # Limpiar el número (quitar puntos de miles)
                            premio = premio_texto.replace('.', '').replace('$', '').strip()
                            
                            # Tradicional: 6 aciertos con "Pozo Vacante"
                            if es_tradicional and aciertos == '6' and 'pozo vacante' in col2_lower and pozos['Tradicional']['premio'] is None:
                                pozos['Tradicional'] = {'premio': premio, 'ganadores': col2_texto}
                                print(f"  Tradicional: ${premio} - {col2_texto}")
                            
                            # Segunda: 6 aciertos con "Pozo Vacante"
                            elif es_segunda and aciertos == '6' and 'pozo vacante' in col2_lower and pozos['Segunda']['premio'] is None:
                                pozos['Segunda'] = {'premio': premio, 'ganadores': col2_texto}
                                print(f"  Segunda: ${premio} - {col2_texto}")
                            
                            # Revancha: 6 aciertos (primer valor)
                            elif es_revancha and aciertos == '6' and pozos['Revancha']['premio'] is None:
                                pozos['Revancha'] = {'premio': premio, 'ganadores': col2_texto}
                                print(f"  Revancha: ${premio} - {col2_texto}")
                            
                            # Siempre Sale: 5 aciertos
                            elif es_siempre_sale and aciertos == '5' and pozos['SiempreSale']['premio'] is None:
                                pozos['SiempreSale'] = {'premio': premio, 'ganadores': col2_texto}
                                print(f"  Siempre Sale: ${premio} - {col2_texto}")
                    
                    except Exception:
                        continue
            
            except Exception:
                continue
        
        # Si no se encontraron con sections, intentar búsqueda directa
        if not any(p.get('premio') for p in pozos.values()):
            try:
                tablas = driver.find_elements(By.CSS_SELECTOR, 'table.table')
                
                for i, tabla in enumerate(tablas):
                    # Buscar el encabezado más cercano antes de esta tabla
                    try:
                        # Obtener elemento padre y buscar h2/h3 hermanos
                        parent = tabla.find_element(By.XPATH, '..')
                        titulo_elem = None
                        
                        try:
                            titulo_elem = parent.find_element(By.XPATH, './preceding-sibling::*[self::h2 or self::h3][1]')
                        except:
                            try:
                                titulo_elem = parent.find_element(By.XPATH, './/h2 | .//h3')
                            except:
                                pass
                        
                        titulo = titulo_elem.text.lower() if titulo_elem else ''
                        
                        # También revisar el HTML alrededor
                        tabla_html = tabla.get_attribute('outerHTML').lower()
                        
                        filas = tabla.find_elements(By.TAG_NAME, 'tr')
                        
                        for fila in filas:
                            try:
                                celdas = fila.find_elements(By.TAG_NAME, 'td')
                                if len(celdas) >= 3:
                                    aciertos = celdas[0].text.strip()
                                    col2_texto = celdas[1].text.strip()
                                    col2_lower = col2_texto.lower()
                                    premio_texto = celdas[2].text.strip()
                                    
                                    premio = premio_texto.replace('.', '').replace('$', '').strip()
                                    
                                    # Identificar según título y contenido
                                    if aciertos == '6' and 'pozo vacante' in col2_lower:
                                        if 'tradicional' in titulo and pozos['Tradicional']['premio'] is None:
                                            pozos['Tradicional'] = {'premio': premio, 'ganadores': col2_texto}
                                            print(f"  Tradicional: ${premio} - {col2_texto}")
                                        elif 'segunda' in titulo and pozos['Segunda']['premio'] is None:
                                            pozos['Segunda'] = {'premio': premio, 'ganadores': col2_texto}
                                            print(f"  Segunda: ${premio} - {col2_texto}")
                                    elif aciertos == '6' and 'revancha' in titulo and pozos['Revancha']['premio'] is None:
                                        pozos['Revancha'] = {'premio': premio, 'ganadores': col2_texto}
                                        print(f"  Revancha: ${premio} - {col2_texto}")
                                    elif aciertos == '5' and 'siempre sale' in titulo and pozos['SiempreSale']['premio'] is None:
                                        pozos['SiempreSale'] = {'premio': premio, 'ganadores': col2_texto}
                                        print(f"  Siempre Sale: ${premio} - {col2_texto}")
                            
                            except Exception:
                                continue
                    
                    except Exception:
                        continue
            
            except Exception as e:
                print(f"  Error en búsqueda alternativa: {e}")
        
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
        driver.quit()

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
