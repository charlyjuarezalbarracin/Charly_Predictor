# Carpeta Varios - Herramientas de Scraping

Esta carpeta contiene las herramientas para obtener datos históricos reales del Quini 6.

## Archivos

### Scraper Funcional
- **scraper_quiniya_final.py** - Scraper principal que extrae datos históricos de quiniya.com.ar
  - Obtiene 104+ sorteos reales (Feb 2025 - Feb 2026)
  - Extrae la modalidad "Tradicional" del Quini 6
  - Genera archivo: `data/quini6_historico_quiniya.csv`

### Requisitos
- **requirements_selenium.txt** - Dependencias necesarias para ejecutar el scraper
  - selenium >= 4.15.0
  - webdriver-manager >= 4.0.0

### Archivos de Referencia
- **quiniya_screenshot.png** - Captura de pantalla del sitio quiniya.com.ar/sorteos
- **quiniya_sorteos.html** - HTML completo del sitio (para debugging/análisis)

## Uso

1. Instalar dependencias:
```bash
pip install -r varios/requirements_selenium.txt
```

2. Ejecutar scraper:
```bash
python varios/scraper_quiniya_final.py
```

3. Los datos se guardarán en: `data/quini6_historico_quiniya.csv`

## Notas

- El scraper fue probado exitosamente el 05/02/2026
- Obtiene datos en tiempo real desde https://quiniya.com.ar/sorteos
- El sitio muestra histórico del último año (~104 sorteos)
- Validado con caso de prueba: sorteo 1/2/2026 = [2,4,15,18,31,43]
