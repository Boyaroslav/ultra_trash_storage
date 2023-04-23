import flask
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired
from flask_login import LoginManager
import svgs

class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    
    telegram = StringField('Ваш аккаунт в социальной сети по типу telegram')
    github = StringField('Ваш аккаунт на хостинге основанном на системе Git (ссылка)')
    social = StringField('Ваш аккаунт в социальной сети (ссылка)')

    about = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')

class ImgUploadForm(FlaskForm):
    image = FileField('выберите аватарку')
    submit = SubmitField('Готово')

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