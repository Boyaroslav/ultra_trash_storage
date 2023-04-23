import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


#  эта хрень для доп ссылок на сайты 

class Link(SqlAlchemyBase, UserMixin):
    __tablename__ = 'links'
    from sqlalchemy import orm

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    
    user_id = sqlalchemy.Column(sqlalchemy.Integer)

    link = sqlalchemy.Column(sqlalchemy.String)
    #  будет выбор из n картинок для ссылки
    image = sqlalchemy.Column(sqlalchemy.Integer)
