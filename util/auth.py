from models import Employee
from main import oidc


def is_admin():
    # return True
    username = oidc.user_getfield("email").split("@")[0]
    isAdmin = Employee.query(
        Employee.username == username, Employee.is_admin == True  # noqa E712
    ).get()
    return bool(isAdmin)
