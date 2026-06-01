from ament_flake8.main import main_with_errors
import pytest


@pytest.mark.skip(reason='Lint policy will be enabled after shared constants stabilize.')
@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    rc, errors = main_with_errors(argv=[])
    assert rc == 0, 'Found %d code style errors / warnings:\n' % len(errors) + '\n'.join(errors)
