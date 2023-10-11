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

    telegram = StringField('your account in telegram(or other network)/Ваш аккаунт в социальной сети по типу telegram')
    github = StringField('your github/Ваш аккаунт на хостинге основанном на системе Git (ссылка)')
    social = StringField('your social network/Ваш аккаунт в социальной сети (ссылка)')

    about = TextAreaField("About")
    submit = SubmitField('Done')

class ImgUploadForm(FlaskForm):
    image = FileField('choose avatar')
    submit = SubmitField('Done')

class AddJokeForm(FlaskForm):
    about = StringField('joke title/о чём ваш анекдот? (пример - +2-2, вовочка, джин, затрудняюсь ответить)', validators=[DataRequired()])
    text = TextAreaField('write joke/пиши шуточку', validators=[DataRequired()])
    submit = SubmitField('Done/Готово')


class AddServerForm(FlaskForm):
    game = StringField('name of game/Это сервер какой игры? (или сайта, но я вообще под игры делал)', validators=[DataRequired()])
    title = TextAreaField('describe/Ну напиши что нибудь полезное про него')
    protocol = StringField('protocol/Какой протокол сервера? (http/https/ftp/tcp,udp и др если сокет)', validators=[DataRequired()])
    ip = StringField('ip/Введите ip адресс куда стучать', validators=[DataRequired()])
    submit = SubmitField('Done/Готово')

class TerminalForm(FlaskForm):
    terminal = TextAreaField()
    inputfield = StringField('type command')
    submit = SubmitField('Отправить (Enter)')


class AddMusicContext(FlaskForm):
    name = StringField('music name/Имя музыки', validators=[DataRequired()])
    author = StringField('author/Автор музыки')
    submit = SubmitField('Upload audio/Загрузим аудио')


class MusicUploadForm(FlaskForm):
    music = FileField('select file/выбери файл музыки', validators=[DataRequired()])
    submit = SubmitField('Done/Готово')


class ChangeAboutForm(FlaskForm):
    about = TextAreaField('type describtion/Пишите описание')
    submit = SubmitField('Done/Готово')

class AddLinkForm(FlaskForm):

    link = StringField('type link/Введи ссылку', validators=[DataRequired()])

    images = RadioField(
        'Label', choices=svgs.image_choices
    )
    submit = SubmitField('Done/Готово')