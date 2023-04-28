import flask
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired
from flask_login import LoginManager
import svgs

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Passowrd', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Done')


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Retry password', validators=[DataRequired()])
    name = StringField('username', validators=[DataRequired()])
    
    telegram = StringField('Ваш аккаунт в социальной сети по типу telegram')
    github = StringField('Ваш аккаунт на хостинге основанном на системе Git (ссылка)')
    social = StringField('Ваш аккаунт в социальной сети (ссылка)')

    about = TextAreaField("About")
    submit = SubmitField('Done')

class ImgUploadForm(FlaskForm):
    image = FileField('choose avatar')
    submit = SubmitField('Done')

class AddJokeForm(FlaskForm):
    about = StringField('о чём ваш анекдот? (пример - +2-2, вовочка, джин, затрудняюсь ответить)', validators=[DataRequired()])
    text = TextAreaField('пиши шуточку', validators=[DataRequired()])
    submit = SubmitField('Готово')


class AddServerForm(FlaskForm):
    game = StringField('Это сервер какой игры? (или сайта, но я вообще под игры делал)', validators=[DataRequired()])
    title = TextAreaField('Ну напиши что нибудь полезное про него')
    protocol = StringField('Какой протокол сервера? (http/https/ftp/tcp,udp и др если сокет)', validators=[DataRequired()])
    ip = StringField('Введите ip адресс куда стучать', validators=[DataRequired()])
    submit = SubmitField('Готово')


class AddMusicContext(FlaskForm):
    name = StringField('Имя музыки', validators=[DataRequired()])
    author = StringField('Автор музыки')
    submit = SubmitField('Загрузим аудио')


class MusicUploadForm(FlaskForm):
    music = FileField('выбери файл музыки', validators=[DataRequired()])
    submit = SubmitField('Готово')


class ChangeAboutForm(FlaskForm):
    about = TextAreaField('Пишите описание')
    submit = SubmitField('Готово')

class AddLinkForm(FlaskForm):

    link = StringField('Введи ссылку', validators=[DataRequired()])

    images = RadioField(
        'Label', choices=svgs.image_choices
    )
    submit = SubmitField('Готово')