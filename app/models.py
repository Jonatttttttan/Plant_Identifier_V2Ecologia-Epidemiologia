from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password, tipo_acesso):
        self.id = id
        self.username = username
        self.password = password
        self.tipo_acesso = tipo_acesso