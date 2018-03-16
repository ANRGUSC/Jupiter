# content of ./test_smtpsimple.py
import pytest

@pytest.fixture()
def my_fixture():
    print "\nI'm the fixture"

def test_my_fixture(my_fixture):
    print "I'm the test"


@pytest.mark.usefixtures('my_fixture')
class Test:
    def test1(self):
        print "I'm the test 1"

    def test2(self):
        print "I'm the test 2"

