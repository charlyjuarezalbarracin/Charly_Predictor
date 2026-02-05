"""
Utilidades para generar datos de muestra
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


def generate_sample_data(num_sorteos: int = 200, 
                        start_date: str = "2023-01-01",
                        frequency_days: int = 3) -> List[Dict]:
    """
    Genera datos de muestra realistas para el Quini 6
    
    Args:
        num_sorteos: Cantidad de sorteos a generar
        start_date: Fecha inicial
        frequency_days: Días entre sorteos
    
    Returns:
        Lista de sorteos con formato estándar
    """
    sorteos = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Parámetros para generar datos realistas
    # Algunos números serán más frecuentes que otros (simulando tendencias reales)
    frequent_numbers = random.sample(range(0, 46), 15)  # 15 números "calientes"
    
    for i in range(num_sorteos):
        # Generar 6 números únicos
        numeros = set()
        
        # 4 números con sesgo hacia números frecuentes
        for _ in range(4):
            if random.random() < 0.6:  # 60% probabilidad de número "caliente"
                num = random.choice(frequent_numbers)
            else:
                num = random.randint(0, 45)
            numeros.add(num)
        
        # Completar con números aleatorios puros
        while len(numeros) < 6:
            numeros.add(random.randint(0, 45))
        
        sorteo = {
            'sorteo_id': i + 1,
            'fecha': current_date.strftime("%Y-%m-%d"),
            'numeros': sorted(list(numeros))
        }
        
        sorteos.append(sorteo)
        
        # Avanzar fecha
        current_date += timedelta(days=frequency_days)
    
    return sorteos


def generate_csv_sample(filepath: str = "data/quini6_historico.csv", 
                       num_sorteos: int = 200):
    """
    Genera un archivo CSV de muestra
    
    Args:
        filepath: Ruta donde guardar el CSV
        num_sorteos: Cantidad de sorteos
    """
    import os
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    sorteos = generate_sample_data(num_sorteos)
    
    # Convertir a formato CSV
    rows = []
    for sorteo in sorteos:
        row = {
            'sorteo_id': sorteo['sorteo_id'],
            'fecha': sorteo['fecha'],
            'num1': sorteo['numeros'][0],
            'num2': sorteo['numeros'][1],
            'num3': sorteo['numeros'][2],
            'num4': sorteo['numeros'][3],
            'num5': sorteo['numeros'][4],
            'num6': sorteo['numeros'][5],
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    
    print(f"✓ Archivo CSV generado: {filepath}")
    print(f"  {len(df)} sorteos creados")


def generate_json_sample(filepath: str = "data/quini6_historico.json",
                        num_sorteos: int = 200):
    """
    Genera un archivo JSON de muestra
    
    Args:
        filepath: Ruta donde guardar el JSON
        num_sorteos: Cantidad de sorteos
    """
    import os
    import json
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    sorteos = generate_sample_data(num_sorteos)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sorteos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Archivo JSON generado: {filepath}")
    print(f"  {len(sorteos)} sorteos creados")


if __name__ == "__main__":
    # Generar archivos de ejemplo
    print("Generando datos de muestra...\n")
    generate_csv_sample()
    generate_json_sample()
    print("\n✓ Datos de muestra generados exitosamente")
