import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'
    from sqlalchemy import orm

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True,  nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    image = sqlalchemy.Column(sqlalchemy.BLOB)

    jokes_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    music_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    servers_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    can_joke = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    can_server = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    can_music = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    telegram_ = sqlalchemy.Column(sqlalchemy.String, default='')
    git_ = sqlalchemy.Column(sqlalchemy.String, default='')
    social_ = sqlalchemy.Column(sqlalchemy.String, default='')

    #snake_max = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    admin = sqlalchemy.Column(sqlalchemy.Boolean, default=False)




    #def __repr__(self):
    #    return f"<Colonist> {self.id} {self.surname} {self.name}"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
