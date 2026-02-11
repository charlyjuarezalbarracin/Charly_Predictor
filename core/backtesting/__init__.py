"""
Módulo de backtesting y validación
"""

from .backtester import Backtester
from .evaluator import PerformanceEvaluator
from .walk_forward import WalkForwardBacktester

__all__ = ['Backtester', 'PerformanceEvaluator', 'WalkForwardBacktester']
