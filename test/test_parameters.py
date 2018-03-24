import pytest
@pytest.fixture(params=[
    # Tuples with password string and expected result
    ('password', False),
    ('p@ssword', True),
    ('p@ssw0rd', True)
])

def password(request):
    """Password fixture"""
    return request.param

def password_contains_number(password):
    """Checks if a password contains a number"""
    return any([True for x in range(10) if str(x) in password])

def password_contains_symbol(password):
    """Checks if a password contains a symbol"""
    return any([True for x in '!,@,#,$,%,^,&,*,(,),_,-,+,='.split(',')
            if x in password])

def check_password(password):
    """Check the password"""
    res = password_contains_number(password) and password_contains_symbol(password)
    return res

def test_password_verifier_works(password):
    """Test that the password is verified correctly"""
    (input, result) = password
    print('\n Checking input')
    print(input)

    assert check_password(input) == result
