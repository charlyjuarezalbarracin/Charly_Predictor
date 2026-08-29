import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.scoring import WeightManager
from core.data.loader import DataLoader


def test_weight_manager_walkforward_optimization():
    loader = DataLoader()
    df = loader.load_csv('data/quini6_historico_test.csv')

    manager = WeightManager()
    result = manager.optimize_walkforward(
        df,
        train_window=120,
        test_window=10,
        step_size=10,
    )

    assert 'best_weights' in result
    assert 'score' in result
    assert 'summary' in result

    best_weights = result['best_weights']
    assert set(best_weights.keys()) == {
        'peso_frecuencia',
        'peso_frecuencia_reciente',
        'peso_ciclo',
        'peso_latencia',
        'peso_tendencia',
    }

    assert abs(sum(best_weights.values()) - 1.0) < 0.05
    assert result['best_weights']['peso_frecuencia'] >= 0.0
    assert result['best_weights']['peso_latencia'] >= 0.0
