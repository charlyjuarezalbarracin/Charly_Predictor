"""
Gestor de pesos configurables
"""

import json
from typing import Dict
from pathlib import Path
from ..config import DEFAULT_WEIGHTS


class WeightManager:
    """
    Gestiona configuraciones de pesos para el sistema de scoring
    Permite guardar y cargar diferentes perfiles de pesos
    """
    
    def __init__(self, config_dir: str = None):
        """
        Args:
            config_dir: Directorio donde guardar configuraciones
        """
        self.config_dir = Path(config_dir) if config_dir else Path('configs')
        self.config_dir.mkdir(exist_ok=True)
        self.current_weights = DEFAULT_WEIGHTS.copy()
        self.profiles = {}
    
    def get_weights(self) -> Dict:
        """Retorna los pesos actuales"""
        return self.current_weights.copy()
    
    def set_weights(self, weights: Dict):
        """
        Establece nuevos pesos
        
        Args:
            weights: Diccionario con pesos
        """
        # Validar que los pesos sumen aproximadamente 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > 0.05:
            print(f"⚠️ Advertencia: Los pesos suman {total:.2f}, se recomienda que sumen 1.0")
        
        self.current_weights = weights.copy()
    
    def save_profile(self, profile_name: str, weights: Dict = None):
        """
        Guarda un perfil de pesos
        
        Args:
            profile_name: Nombre del perfil
            weights: Pesos a guardar (usa los actuales si no se especifica)
        """
        weights_to_save = weights or self.current_weights
        
        filepath = self.config_dir / f"{profile_name}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(weights_to_save, f, indent=2)
        
        self.profiles[profile_name] = weights_to_save.copy()
        
        print(f"✓ Perfil '{profile_name}' guardado en {filepath}")
    
    def load_profile(self, profile_name: str) -> Dict:
        """
        Carga un perfil de pesos
        
        Args:
            profile_name: Nombre del perfil
        
        Returns:
            Diccionario con pesos
        """
        filepath = self.config_dir / f"{profile_name}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"No se encontró el perfil '{profile_name}'")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            weights = json.load(f)
        
        self.current_weights = weights.copy()
        self.profiles[profile_name] = weights.copy()
        
        print(f"✓ Perfil '{profile_name}' cargado")
        
        return weights
    
    def list_profiles(self) -> list:
        """Lista todos los perfiles guardados"""
        profiles = list(self.config_dir.glob("*.json"))
        return [p.stem for p in profiles]
    
    def create_default_profiles(self):
        """Crea algunos perfiles predeterminados útiles"""
        
        # Perfil balanceado (default)
        self.save_profile('balanced', {
            'peso_frecuencia': 0.25,
            'peso_frecuencia_reciente': 0.25,
            'peso_ciclo': 0.20,
            'peso_latencia': 0.15,
            'peso_tendencia': 0.15,
        })
        
        # Perfil enfocado en frecuencia
        self.save_profile('frequency_focused', {
            'peso_frecuencia': 0.50,
            'peso_frecuencia_reciente': 0.30,
            'peso_ciclo': 0.10,
            'peso_latencia': 0.05,
            'peso_tendencia': 0.05,
        })
        
        # Perfil enfocado en tendencias recientes
        self.save_profile('recent_trends', {
            'peso_frecuencia': 0.15,
            'peso_frecuencia_reciente': 0.35,
            'peso_ciclo': 0.15,
            'peso_latencia': 0.20,
            'peso_tendencia': 0.15,
        })
        
        # Perfil conservador (números que no han salido hace tiempo)
        self.save_profile('conservative', {
            'peso_frecuencia': 0.20,
            'peso_frecuencia_reciente': 0.10,
            'peso_ciclo': 0.30,
            'peso_latencia': 0.30,
            'peso_tendencia': 0.10,
        })
        
        print("✓ Perfiles predeterminados creados:")
        print("  - balanced: Equilibrio entre todas las métricas")
        print("  - frequency_focused: Prioriza números más frecuentes")
        print("  - recent_trends: Prioriza tendencias recientes")
        print("  - conservative: Prioriza números con mayor latencia")
    
    def optimize_weights(self, backtesting_results: Dict) -> Dict:
        """
        Optimiza pesos basándose en resultados de backtesting
        (Implementación básica - puede mejorarse con algoritmos genéticos)
        
        Args:
            backtesting_results: Resultados de backtesting con diferentes pesos
        
        Returns:
            Mejores pesos encontrados
        """
        # TODO: Implementar optimización con Grid Search o Algoritmos Genéticos
        # Por ahora retorna los pesos actuales
        print("⚠️ Optimización de pesos aún no implementada")
        return self.current_weights.copy()
