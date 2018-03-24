import pytest

@pytest.fixture()
def my_fixture():
	"""
		Example of a fixture
	"""
	print("\nI'm the fixture")

def test_my_fixture(my_fixture): 
	"""
	Example 1: passing fixture name as parameter 
	of the function using the fixture
	"""
	print("I'm the test")

@pytest.mark.usefixtures('my_fixture')
class Test:
	"""
	Example 2: using decorator @pytest.mark.usefixtures
	"""
	def test1(self):
		print("I'm the test 1")

	def test2(self):
		print("I'm the test 2")

