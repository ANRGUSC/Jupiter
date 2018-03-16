import pytest


@pytest.fixture(scope="class")
def my_fixture(request):
    data = {'x': 1, 'y': 2, 'z': 3}

    def fin():
    	print('Add finalization')

    request.addfinalizer(fin)

    return data

def test_my_fixture(my_fixture):
    assert my_fixture['x'] == 1
