import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Score(SqlAlchemyBase, UserMixin):
    __tablename__ = 'snake_scores'
    from sqlalchemy import orm

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))

    user_name = sqlalchemy.Column(sqlalchemy.String, default='incognito')


    score = sqlalchemy.Column(sqlalchemy.Integer, default=0)
