"""Counterexamples for the identical ROS 1/ROS 2 health-status criteria."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATHS = [ROOT / 'src/sa-bsn/target_system/components/component/test/health_status_oracle.py']

@pytest.mark.parametrize('path', PATHS, ids=['bsn2'])
@pytest.mark.parametrize('readings,states,positive,accepted', [
    ([37], [15, 45], True, True),
    ([37], [], False, True),
    ([], [15, 45], True, False),
    ([], [], False, False),
    ([37], [], True, False),
    ([37], [15], False, False),
    ([37], [15, 15], True, False),
    ([37], ['15', '15.0'], True, False),
    ([37], [-1, 15], True, False),
    ([37], [15, 101], True, False),
    ([37], [15, float('nan')], True, False),
    ([float('nan')], [15, 45], True, False),
    ([37], ['invalid'], True, False),
])
def test_observation(path, readings, states, positive, accepted):
    spec = importlib.util.spec_from_file_location('health_oracle', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if accepted:
        module.assert_health_observation(readings, states, positive)
    else:
        with pytest.raises(AssertionError):
            module.assert_health_observation(readings, states, positive)
