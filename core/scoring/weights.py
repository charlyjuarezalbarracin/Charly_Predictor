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
    
    def optimize_walkforward(
        self,
        data,
        train_window: int = 200,
        test_window: int = 10,
        step_size: int = 10,
        use_ideas: bool = False,
        use_idea1: bool = False,
        use_idea2: bool = False,
        use_idea3: bool = False,
        idea3_ventana: int = 16,
        idea3_umbral: float = 0.12,
        candidate_steps: tuple = (-0.10, 0.0, 0.10),
        max_candidates: int = 243,
    ) -> Dict:
        """
        Optimiza los pesos usando validación walk-forward sobre datos históricos.

        La idea es evaluar un conjunto de perfiles cercanos al actual, medir su
        rendimiento simulatedo en el pasado y devolver el mejor conjunto de pesos.
        """
        from ..backtesting.walk_forward import WalkForwardBacktester

        if data is None or len(data) < train_window + test_window:
            raise ValueError(
                f"Se necesitan al menos {train_window + test_window} sorteos para optimizar. "
                f"Disponibles: {len(data) if data is not None else 0}."
            )

        base = self.current_weights.copy()
        keys = [
            'peso_frecuencia',
            'peso_frecuencia_reciente',
            'peso_ciclo',
            'peso_latencia',
            'peso_tendencia',
        ]

        candidates = []
        seen = set()

        for delta_f in candidate_steps:
            for delta_r in candidate_steps:
                for delta_c in candidate_steps:
                    for delta_l in candidate_steps:
                        delta_t = -(delta_f + delta_r + delta_c + delta_l)
                        proposal = {
                            'peso_frecuencia': base.get('peso_frecuencia', 0.0) + delta_f,
                            'peso_frecuencia_reciente': base.get('peso_frecuencia_reciente', 0.0) + delta_r,
                            'peso_ciclo': base.get('peso_ciclo', 0.0) + delta_c,
                            'peso_latencia': base.get('peso_latencia', 0.0) + delta_l,
                            'peso_tendencia': base.get('peso_tendencia', 0.0) + delta_t,
                        }

                        if min(proposal.values()) < 0.0:
                            continue
                        total = sum(proposal.values())
                        if total <= 0:
                            continue
                        normalized = {k: max(0.0, v / total) for k, v in proposal.items()}
                        if any(v < 0.02 for v in normalized.values()):
                            continue

                        signature = tuple(round(normalized[k], 4) for k in keys)
                        if signature in seen:
                            continue
                        seen.add(signature)
                        candidates.append(normalized)

                        if len(candidates) >= max_candidates:
                            break
                    if len(candidates) >= max_candidates:
                        break
                if len(candidates) >= max_candidates:
                    break
            if len(candidates) >= max_candidates:
                break

        if not candidates:
            raise ValueError("No se pudo generar un conjunto válido de pesos para optimizar.")

        best_candidate = None
        best_summary = None
        best_score = float('-inf')
        best_result = None

        for candidate in candidates:
            backtester = WalkForwardBacktester(
                train_window=train_window,
                test_window=test_window,
                step_size=step_size,
                use_ideas=use_ideas,
                use_idea1=use_idea1 if use_ideas else False,
                use_idea2=use_idea2 if use_ideas else False,
                use_idea3=use_idea3 if use_ideas else False,
                idea3_ventana=idea3_ventana,
                idea3_umbral=idea3_umbral,
            )

            try:
                results = backtester.run_walk_forward(data, candidate)
            except Exception:
                continue

            summary = results.get('summary', {})
            if not summary:
                continue

            accuracy = float(summary.get('accuracy_promedio', 0.0))
            stability = float(backtester.get_stability_score())
            std_dev = float(summary.get('accuracy_std', 0.0))
            eval_score = accuracy + stability - (std_dev * 1.5)

            if eval_score > best_score:
                best_score = eval_score
                best_candidate = candidate.copy()
                best_summary = summary.copy()
                best_result = results

        if best_candidate is None:
            raise ValueError("No hubo un perfil de pesos que pudiera validarse correctamente en walk-forward.")

        self.current_weights = best_candidate.copy()
        return {
            'best_weights': self.current_weights.copy(),
            'score': best_score,
            'summary': best_summary,
            'results': best_result,
            'candidates_evaluated': len(candidates),
        }

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
