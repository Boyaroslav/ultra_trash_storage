from flask import *
from flask_login import LoginManager, logout_user, login_required, current_user, login_user
from forms import *
import json
import datetime
import dateutil
import os
from data import db_session
from data import __all_models
from data.users import User
from data.jokes import Joke
from data.music import Music
from data.score import Score
from data.servers import Server
from data.extra_links import Link
from svgs import link_images, image_choices
from pathlib import Path
import subprocess
from flask import Flask, make_response, request, abort
from io import StringIO, BytesIO
import subprocess, os.path

from flask_httpauth import HTTPBasicAuth

from languages import translations

DIR = '/home/boyaroslav/ultra_trash_storage'

db_session.global_init("db/blogs.db")

defaultimg = open("static/img/default.png", 'rb').read()
storagepath = Path(__file__[:__file__.rfind('/')] + '/storage')
print(storagepath)

def days_hours_minutes(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)


GOYDA_COUNT = 10

app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = "ilovebulochka"
app.config['UPLOAD_FOLDER'] = "static/img/"


'''внимание, сейчас эпично'''
JOKES_ON_PAGE = 10


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

def load_user_by_name(name):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(name)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

n = 0

@app.route('/change_language/<string:lang>')
def change_language(lang):
    if lang in ['ru', 'en', 'sp']:
        i = ['ru', 'en', 'sp'].index(lang)
        page = request.args.get('page', default='/')
        res = make_response(redirect(page))
        res.set_cookie('language', lang)
        return res

@app.route('/change_cs')
def change_cs():
    cs = request.cookies.get('design', 'main.css')
    if cs == 'main.css':
        cs = 'main3.css'
    elif cs == 'main3.css':
        cs = 'main.css'
    res = make_response(redirect('/'))
    res.set_cookie('design', cs)
    return res



@app.route('/')
@app.route('/main')
def draw_():
    language = request.cookies.get("language", 'ru')
    cs = request.cookies.get("design", "main.css")
    i = ['ru', 'en', 'sp'].index(language)
    res = make_response(render_template('main.html', translations=translations, lang=i, cs=cs))
    if not language:
        res.set_cookie("language", 'ru')
    if not cs:
        res.set_cookie("design", "main.css")
    db_sess = db_session.create_session()
    return res

@app.route('/jokes/add_joke', methods=['GET', 'POST'])
@login_required
def add_joke():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    ilp = ['ru', 'en', 'sp'].index(language)
    form = AddJokeForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.jokes_count = user.jokes_count + 1

        joke = Joke(
            about = form.about.data,
            text = form.text.data,
            user_id = user.id,
            user_name = current_user.name
        )

        db_sess.add(joke)
        db_sess.commit()
        return redirect(f'/jokes/add_joke/photo_joke/{joke.id}')
    return render_template('add_joke.html', form=form, translations=translations, lang=ilp, cs=cs)

@app.route('/jokes/add_joke/photo_joke/<int:id>', methods=['GET', 'POST'])
@login_required
def upload_photo_joke(id):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    ilp = ['ru', 'en', 'sp'].index(language)
    imgform = ImgUploadForm()
    if imgform.validate_on_submit():
        db_sess = db_session.create_session()
        joke = db_sess.query(Joke).filter(Joke.id == id).first()
        if current_user.id != joke.user_id:
            print("попался голубчик")
            return redirect('/jokes')
        joke.image = imgform.image.data.stream.read()
        db_sess.commit()
        return redirect('/jokes')   #  {{imgform.submit(type="submit", class="btn btn-primary")}}

    return render_template('upload_photo.html', imgform=imgform, exception='/jokes', translations=translations, lang=ilp, cs=cs)


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    cs = request.cookies.get('design', 'main.css')
    imgform = ImgUploadForm()
    if imgform.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        try:
            user.image = imgform.image.data.stream.read()
        except:
            pass
        db_sess.commit()
        return redirect('/')   #  {{imgform.submit(type="submit", class="btn btn-primary")}}

    return render_template('upload_photo.html', imgform=imgform, exception='/', cs=cs)

USERS_ON_PAGE = 50  # размах!


@app.route('/our_dear_users')
def draw():
    cs = request.cookies.get('design', 'main.css')
    #global n
    #user = User(name = "User" + str(n), email = "bobara")
    #db_sess.add(user)
    #db_sess.commit()

    #s = []
    #for user in db_sess.query(User).all():
    #    s.append([user.name, user.id])

    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    user = db_sess.query(User).all()
    users_count = db_sess.query(User).count()
    start = users_count - page * USERS_ON_PAGE
    end = users_count - (page + 1) * USERS_ON_PAGE
    if end < 0:
        end = 0
    users = db_sess.query(User).slice(end,start)
    return render_template('doska_pocheta.html', blocks=users[::-1], page=page, admins='', page_count = users_count // USERS_ON_PAGE + 1, cs=cs)

@app.route("/show_image/<int:id>")
def show_image(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if user.image == None:
        ret = make_response(defaultimg)
    else:
        ret = make_response(user.image)
    ret.headers.set('Content-Type', 'image/png')
    return ret

@app.route('/show_svgs/<int:index>')
def show_svgs(index):
    ret = make_response(link_images[index])
    ret.headers.set('Content-Type', 'image/svg+xml')
    return ret

@app.route("/play_music/<int:id>")
def play_music(id):
    db_sess = db_session.create_session()
    music = db_sess.query(Music).filter(Music.id == id).first()

    ret = make_response(music.music)
    ret.headers.set('Content-type', 'audio/mpeg')
    return ret


@app.route("/show_image/jokes/<int:id>")
def show_joke_image(id):
    db_sess = db_session.create_session()
    user = db_sess.query(Joke).filter(Joke.id == id).first()
    if user.image == None:
        ret = make_response(defaultimg)
    else:
        ret = make_response(user.image)
    ret.headers.set('Content-Type', 'image/png')
    return ret

@app.route('/jokes')
def draw_jokes():
    cs = request.cookies.get('design', 'main.css')
    page = request.args.get('page', default=0, type=int)
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    db_sess = db_session.create_session()
    jokes = db_sess.query(Joke).all()
    jokes_count = db_sess.query(Joke).count()
    start = jokes_count - page * JOKES_ON_PAGE
    end = jokes_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Joke).slice(end,start)
    return render_template('jokes.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i, cs=cs)

@app.route('/jokes/<string:name>')
def draw_personal_jokes(name):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    jokes = db_sess.query(Joke).filter(Joke.user_name == name).all()
    jokes_count = db_sess.query(Joke).filter(Joke.user_name == name).count()
    start = jokes_count - page * JOKES_ON_PAGE
    end = jokes_count - (page + 1) * JOKES_ON_PAGE
    if end > jokes_count:
        end = jokes_count
    jokes = db_sess.query(Joke).filter(Joke.user_name == name).slice(end, start)
    return render_template('jokes.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id=f"/{id}", one_joke=name, translations=translations, lang=i, cs=cs)

@app.route('/jokes/<int:id>')
def draw_joke(id):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    jokes = db_sess.query(Joke).filter(Joke.id == id).all()
    jokes_count = db_sess.query(Joke).filter(Joke.id == id).count()
    start = jokes_count - page * JOKES_ON_PAGE
    end = jokes_count - (page + 1) * JOKES_ON_PAGE
    if end > jokes_count:
        end = jokes_count
    jokes = db_sess.query(Joke).filter(Joke.id == id).slice(end, start)
    return render_template('joke_page.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id=f"/{id}", one_joke=id, translations=translations, lang=i, cs=cs)

@app.route('/our_dear_users/<int:id>')
@app.route('/user/<int:id>')
def draw_user(id=-1):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    user = load_user(id)
    db_sess = db_session.create_session()
    extra_links = db_sess.query(Link).filter(Link.user_id == id).all()
    now = datetime.datetime.now()
    d, h, m = days_hours_minutes(now - user.created_date)

    return render_template('user_page.html', user=user, dated=d, dateh=h, datem=m, extra_links=extra_links, link_images=link_images, translations=translations, lang=i, cs=cs)

@app.route('/our_dear_users/<string:name>')
@app.route('/user/<string:name>')
def draw_user1(name='boyaroslav'):
    db_sess = db_session.create_session()
    usid = db_sess.query(User).filter(User.name == name).first()
    return draw_user(usid.id)

@app.route('/our_dear_users/our_dear_admins')
def draw_admins():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.admin == 1).all()
    users_count = db_sess.query(User).filter(User.admin == 1).count()
    start = users_count - page * USERS_ON_PAGE
    end = users_count - (page + 1) * USERS_ON_PAGE
    if end < 0:
        end = 0
    users = db_sess.query(User).filter(User.admin == 1).slice(end,start)
    return render_template('doska_pocheta.html', blocks=users[::-1], page=page, admins='/our_dear_admins', page_count = users_count // USERS_ON_PAGE + 1, translations=translations, lang=i, cs=cs)



@app.route('/register', methods=['GET', 'POST'])
def reqister():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = RegisterForm()
    imgform = ImgUploadForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают", translations=translations, lang=i)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть", translations=translations, lang=i, cs=cs)
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            telegram_=form.telegram.data,
            git_=form.github.data,
            social_=form.social.data
        )

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, False)
        return redirect('/upload_photo')
    return render_template('register.html', title='Регистрация', form=form, translations=translations, lang=i, cs=cs)


@app.route('/login', methods=['GET', 'POST'])
def login():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form, translations=translations, lang=i, cs=cs)
    return render_template('login.html', title='Авторизация', form=form, translations=translations, lang=i, cs=cs)

@app.route('/music')
def draw_music():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    music = db_sess.query(Music).all()
    music_count = db_sess.query(Music).count()  #  не смущайтесь, это надо
    start = music_count - page * JOKES_ON_PAGE
    end = music_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Music).slice(end,start)
    return render_template('music.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i, cs=cs)


@app.route('/music/<string:name>')
def draw_music_byname(name):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    music = db_sess.query(Music).filter(Music.user_name == name).all()
    music_count = db_sess.query(Music).filter(Music.user_name == name).count()  #  не смущайтесь, это надо
    start = music_count - page * JOKES_ON_PAGE
    end = music_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Music).slice(end,start)
    return render_template('music.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i, cs=cs)

@app.route('/music/<int:id>')
def draw_music_byid(id):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    music = db_sess.query(Music).filter(Music.id == id).all()
    music_count = db_sess.query(Music).filter(Music.id == id).count()  #  не смущайтесь, это надо
    start = music_count - page * JOKES_ON_PAGE
    end = music_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Music).slice(end,start)
    return render_template('music_page.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i, cs=cs)


@app.route('/music/add_music', methods=['GET', 'POST'])
@login_required
def add_music():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = AddMusicContext()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.music_count = user.music_count + 1

        music = Music(
            name = form.name.data,
            author = form.author.data,
            user_id = user.id,
            user_name = current_user.name
        )

        db_sess.add(music)
        db_sess.commit()
        return redirect(f'/music/add_music/add_file/{music.id}')
    return render_template('add_music.html', form=form, translations=translations, lang=i, cs=cs)

@app.route('/music/add_music/add_file/<int:id>', methods=['GET', 'POST'])
@login_required
def add_music_file(id):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    musicform = MusicUploadForm()
    if musicform.validate_on_submit():
        db_sess = db_session.create_session()
        music = db_sess.query(Music).filter(Music.id == id).first()
        if current_user.id != music.user_id:
            print("попался голубчик")
            return redirect('/music')
        music.music = musicform.music.data.stream.read()
        db_sess.commit()
        return redirect('/music')   #  {{imgform.submit(type="submit", class="btn btn-primary")}}

    return render_template('upload_music.html', musicform=musicform, translations=translations, lang=i, cs=cs)





@app.route('/jokes/delete/<int:id>')
@login_required
def delete_joke(id):
    if current_user.admin == 1:
        db_sess = db_session.create_session()
        joke = db_sess.query(Joke).filter(Joke.id == id)
        user = db_sess.query(User).filter(User.id == joke.first().user_id).first()
        user.jokes_count = user.jokes_count - 1
        joke.delete()
        db_sess.commit()
        return redirect('/jokes')


@app.route('/music/delete/<int:id>')
@login_required
def delete_music(id):
    if current_user.admin == 1:
        db_sess = db_session.create_session()
        music = db_sess.query(Music).filter(Music.id == id)
        user = db_sess.query(User).filter(User.id == music.first().user_id).first()
        user.music_count = user.music_count - 1
        music.delete()
        db_sess.commit()
        return redirect('/music')

@app.route('/servers/delete/<int:id>')
@login_required
def delete_server(id):
    if current_user.admin == 1:
        db_sess = db_session.create_session()
        server = db_sess.query(Server).filter(Server.id == id)
        user = db_sess.query(User).filter(User.id == server.first().user_id).first()
        user.servers_count = user.servers_count - 1
        server.delete()
        db_sess.commit()
        return redirect('/servers')


@app.route('/administrate/can_joke/<int:id>')
@login_required
def adm_joke(id):
    if current_user.admin == 0:
        redirect('/')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    user.can_joke = not user.can_joke
    db_sess.commit()
    return redirect(f'/our_dear_users/{id}')


@app.route('/administrate/can_music/<int:id>')
@login_required
def adm_music(id):
    if current_user.admin == 0:
        redirect('/')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    user.can_music = not user.can_music
    db_sess.commit()
    return redirect(f'/our_dear_users/{id}')

@app.route('/administrate/can_server/<int:id>')
@login_required
def adm_server(id):
    if current_user.admin == 0:
        redirect('/')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    user.can_server = not user.can_server
    db_sess.commit()
    return redirect(f'/our_dear_users/{id}')

@app.route('/administrate/make_admin/<int:id>')
@login_required
def adm_make_admin(id):
    if current_user.admin == 0:
        redirect('/')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    user.admin = 1
    db_sess.commit()
    return redirect(f'/our_dear_users/{id}')

@app.route('/administrate/delete_account._./<int:id>')
@login_required
def adm_delete_account(id):
    if current_user.admin == 1:
        db_sess = db_session.create_session()
        print('ГОЙДА',db_sess.query(User).filter(User.id == id).first().admin)
        if db_sess.query(User).filter(User.id == id).first().admin == 0:

            db_sess.query(Joke).filter(Joke.user_id == id).delete()
            db_sess.query(Music).filter(Music.user_id == id).delete()
            db_sess.query(Server).filter(Server.user_id == id).delete()
            db_sess.query(User).filter(User.id == id).delete()
            db_sess.query(Link).filter(Link.user_id == id).delete()
            db_sess.commit()
            return redirect('/our_dear_users')

        return redirect(f'/our_dear_users/{id}')
    elif current_user.id == id:
        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.id == id).first().admin == 0:
            logout_user()
            db_sess.query(Joke).filter(Joke.user_id == id).delete()
            db_sess.query(Music).filter(Music.user_id == id).delete()
            db_sess.query(Server).filter(Server.user_id == id).delete()
            db_sess.query(User).filter(User.id == id).delete()
            db_sess.query(Link).filter(Link.user_id == id).delete()
            db_sess.commit()
            return redirect('/')

        return redirect(f'/our_dear_users/{id}')

@app.route('/servers')
def draw_servers():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    servers = db_sess.query(Server).all()
    servers_count = db_sess.query(Server).count()
    start = servers_count - page * JOKES_ON_PAGE
    end = servers_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    servers = db_sess.query(Server).slice(end,start)
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i, cs=cs)

@app.route('/servers/<string:name>')
def draw_servers_byname(name):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    servers = db_sess.query(Server).filter(Server.user_name == name).all()
    servers_count = db_sess.query(Server).filter(Server.user_name == name).count()  #  не смущайтесь, это надо
    start = servers_count - page * JOKES_ON_PAGE
    end = servers_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Music).slice(end,start)
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i, cs=cs)

@app.route('/servers/<int:id>')
def draw_servers_byid(id):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    page = request.args.get('page', default=0, type=int)
    db_sess = db_session.create_session()
    servers = db_sess.query(Server).filter(Server.id == id).all()
    servers_count = db_sess.query(Server).filter(Server.id == id).count()  #  не смущайтесь, это надо
    start = servers_count - page * JOKES_ON_PAGE
    end = servers_count - (page + 1) * JOKES_ON_PAGE
    if end < 0:
        end = 0

    jokes = db_sess.query(Music).slice(end,start)
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i, cs=cs)


@app.route('/servers/add_server', methods=['GET', 'POST'])
@login_required
def add_server():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = AddServerForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.servers_count = user.servers_count + 1

        server = Server(
            game = form.game.data,
            protocol = form.protocol.data,
            title = form.title.data,
            ip = form.ip.data,
            user_id = user.id,
            user_name = current_user.name
        )

        db_sess.add(server)
        db_sess.commit()
        return redirect('/servers')
    return render_template('add_server.html', form=form, translations=translations, lang=i,cs=cs)


@app.route('/goyda_lent')
def goyda():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    posts = []
    db_sess = db_session.create_session()
    #  jokes

    jokes_count = db_sess.query(Joke).count()

    posts += db_sess.query(Joke).order_by(-Joke.id).slice(0, 10)
    #  music

    music_count = db_sess.query(Music).count()

    posts += db_sess.query(Music).order_by(-Music.id).slice(0, 10)

    #  servers

    servers_count = db_sess.query(Server).count()

    posts += db_sess.query(Server).order_by(-Server.id).slice(0, 10)

    posts = sorted(posts, key=lambda j: j.created_date)

    return render_template('goyda.html', posts=posts[::-1], translations=translations, lang=i, cs=cs)


@app.route('/change_about', methods=['GET', 'POST'])
@login_required
def change_about():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = ChangeAboutForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.about = form.about.data
        db_sess.commit()
        return redirect(f'/our_dear_users/{current_user.id}')
    return render_template('change_about.html', form=form, exception=f'/our_dear_users/{current_user.id}', translations=translations, lang=i, cs=cs)


@app.route('/add_link', methods=['GET', 'POST'])
@login_required
def add_extra_link():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = AddLinkForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        link = Link(
            link = form.link.data,
            image = form.images.data,
            user_id = user.id
        )

        db_sess.add(link)
        db_sess.commit()
        return redirect(f'/our_dear_users/{current_user.id}', translations=translations, lang=i, cs=cs)

    return render_template('add_link.html', form=form, translations=translations, lang=i, cs=cs)

def get_author(name):
    ans = open(f"storage/{name}/bpauthor").read()
    return ans

def get_describtion(name):
    return open(f"storage/{name}/bpdescribe").read()

@app.route('/gitreps')
def draw_reps():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    path = request.args.get('path', default='')

    r = get_reps(os.path.join(DIR, 'storage'))

    return render_template('gitreps.html', reps=r, translations=translations, lang=i, path=path, ptype='d', cs=cs)

def get_reps(name):
    for i in Path(name).iterdir():
        yield [get_author(i.name), i.name, get_describtion(i.name)]

def gen_get_reps(name):
    a = []
    for i in get_reps(name):
        a.append(i)
    return a

gitauth = HTTPBasicAuth()
@gitauth.verify_password
def verify_password(username, password):
    if username and password:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == username).first()
        if user == None: return None
        if user.check_password(password):
            return 1
    return None


@app.route('/gitreps/<string:name>/info/refs')
@gitauth.login_required
def inforefs(name):
    service = request.args.get('service')
    if service[:4] != 'git-':
        abort(500)
    print(os.path.join(DIR, 'storage', name))
    p = subprocess.Popen([service, '--stateless-rpc', '--advertise-refs', os.path.join('storage', name)], stdout=subprocess.PIPE)
    packet = '# service=%s\n' % service
    length = len(packet) + 4
    _hex = '0123456789abcdef'
    prefix = ''
    prefix += _hex[length >> 12 & 0xf]
    prefix += _hex[length >> 8  & 0xf]
    prefix += _hex[length >> 4 & 0xf]
    prefix += _hex[length & 0xf]
    data = prefix + packet + '0000'
    data += p.stdout.read().decode()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-%s-advertisement' % service
    p.wait()
    return res

@app.route('/gitreps/create', methods=['GET', 'POST'])
@login_required
def git_create_repo():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    ilp = ['ru', 'en', 'sp'].index(language)
    form = AddJokeForm()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if form.validate_on_submit():

        about = form.about.data,
        text = form.text.data,


        if about[0] not in os.listdir('storage'):
            ans = os.popen(f'bash init_repo.bash {about[0]} {user.name} "{text[0]}"').read()

        return redirect(f'/gitreps')
    return render_template('git_create_repo.html', form=form, translations=translations, lang=ilp, cs=cs)

def lower(s):
    return s.lower()

@app.route('/gitreps/<string:name>/git-receive-pack', methods=['POST'])
@gitauth.login_required
def git_receive(name):
    user = gitauth.username()
    if user not in list(map(lower, os.popen(f'bash get_auth.bash {name}').read().split('\n'))):
        return "fuck you", 417
    repoPath = os.path.join(DIR, 'storage', name)
    p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', repoPath], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(request.data)
    p.stdin.flush()
    data_out = p.stdout.read()
    res = make_response(data_out)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-receive-pack-result'
    p.wait()
    return res


@app.route('/gitreps/<string:name>/git-upload-pack', methods=['POST'])
@gitauth.login_required
def git_upload_pack(name):
    repoPath = os.path.join(DIR, 'storage', name)
    if 'Content-Encoding' in request.headers:
        # gzip
        app.logger.debug('Content-Encoding: ' + request.headers['Content-Encoding'])
        reqData = gzip.decompress(request.data)
    else:
        reqData = request.data
    p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', repoPath], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(reqData)
    p.stdin.flush()
    data = p.stdout.read()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-upload-pack-result'
    p.wait()
    return res


from io import BytesIO
@app.route('/archive/<string:name>')
def make_zip(name):
    path = os.path.join(DIR, 'storage', name)
    outputpath = os.path.join(DIR, 'cache', name)
    os.system(f'bash archive.bash {name}')
    o = open(f'cache/{name}.zip', 'rb').read()
    os.system(f"rm -rf cache/{name}.zip")
    r = make_response(BytesIO(o))
    r.headers['Content-Type'] = 'application/zip'


    return r

@app.route('/gitreps/<string:name>')
def gitlook(name):
    cs = request.cookies.get('design', 'main.css')
    ans = ''

    language = request.cookies.get("language", 'ru')
    inb = ['ru', 'en', 'sp'].index(language)
    if os.path.exists(f'storage/{name}'):
        files_ = os.popen(f'bash view.bash {name}').read().split()
        if 'README.md' in files_:
            vb = os.popen(f'bash viewb.bash {name}').read().replace('\t', ' ').split('\n')
            for i in vb:
                j = i.split(' ')
                if j[-1].lower() == 'readme.md':
                    ans = j[2]
                    ans = os.popen(f'bash viewf.bash {name} {ans}').read().replace('\t', '    ')
                    break

        return render_template('git_files.html', folder=None ,files=files_, name=name, translations=translations, lang=inb, text=ans, cs=cs)
    return render_template('git_files.html', folder=None, files=[], name=name, translations=translations, lang=inb, cs=cs)

def all_folder(folder, files):
    ans = []
    l = len(folder)
    for i in files:
        if i[:l] == folder:
            if '/' not in i[l+1:]:
                ans.append(i[l+1:])
            else:
                le = i[l+1:].find('/')+1
                ans.append(i[l+1:l+le])
    return list(set(ans))

@app.route('/gitreps/<string:name>/<path:folder>')
def gitlookf(name, folder):
    cs = request.cookies.get('design', 'main.css')
    ans = ''

    language = request.cookies.get("language", 'ru')
    inb = ['ru', 'en', 'sp'].index(language)
    if os.path.exists(f'storage/{name}'):
        files_ = all_folder(folder, os.popen(f'bash viewnbf.bash {name}').read().split())
        if 'README.md' in files_:
            vb = os.popen(f'bash viewb.bash {name}').read().replace('\t', ' ').split('\n')
            for i in vb:
                j = i.split(' ')
                if j[-1].lower() == 'readme.md':
                    ans = j[2]
                    ans = os.popen(f'bash viewf.bash {name} {ans}').read().replace('\t', '    ')
                    break

        return render_template('git_files.html', folder=folder, files=files_, name=name, translations=translations, lang=inb, text=ans, cs=cs)
    return render_template('git_files.html', folder=folder, files=[], name=name, translations=translations, lang=inb, cs=cs)

def is_folder(folder, files):
    l = len(folder)
    for i in files:
        if files[:l] == folder:
            return 1
    return 0


@app.route('/gitreps/<string:name>/<path:file>/look')
def view_file(name, file):
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    lan = ['ru', 'en', 'sp'].index(language)
    ans = ''
    if os.path.exists(f'storage/{name}'):
        r = os.popen(f'bash viewbf.bash {name}').read().replace('\t', ' ').split('\n')
        for i in r:
            j = i.split(' ')
            if j[-1] == file:
                ans = j[2]
                break
        if ans:
            return render_template('git_view.html', text=os.popen(f'bash viewf.bash {name} {ans}').read().replace('\t', '    '), name=name, translations=translations, lang=lan, cs=cs)

        else:

            return redirect(f'/gitreps/{name}/{file}')


    return 'no'




@app.route('/docs/why_registration')
def why_registration():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    return render_template('why_registration.html', translations=translations, lang=i, cs=cs)

phy = [
    'Сила - количественная мера сил друг на друга',
    'Сила определяет ускорение тела, но не его скорость',
    'Траектория - кривая по которой движется тело',
    'Перемещение - вектор из начального положения в конечное',
    'Vсред по перемещению = вектор из начального положения в конечное / время',
    'Инерция - Свойство тела оставаться в некоторых, называемых инерциальными, системах отсчёта в состоянии покоя или равномерного прямолинейного движения',
    'Масса-это количество материи в физическом теле. Это также мера инерции тела',
    'Инертность - это свойство тел по разному изменять свою скорость при действии на него одной и той же силы.',
    'иннертность - способность тела сохранять свою скорость при действии внешней F',
    'Импульс силы - F * дельта t - время действия силы на силу',
    'Мощность - быстрота совершения работы',
    'Потенциальные силы - Работа сил не зависит от траектории',
    'Амплитуда колебиания - максимальное смещение относительно состояния покоя',
    'Центральный удар - Скорости направлены по линии, соединяющей центры масс тел'
    'Масса - мера инертности.',
    'Угловая скорость (W - омега) - скорость смены угла при движении по окружности',
    'Закон изменения механическрй энергии в исо - изменение механической E в исо - сумма A внутренних сил трения и внешних сил на тело',
    'Закон сохранения механической E - полная механическая E в замкнутой системе тел остается неизменной',
    'Энергия - Скалярная физическая величина, являющаяся единой мерой различных форм движения и взаимодействия материи, мерой силы перехода движения материи из одних форм в другие для приведения её в состояние покоя. Введение понятия энергии удобно тем, что в случае, если физическая система является замкнутой, то её энергия сохраняется в этой системе на протяжении времени, в течение которого система будет являться замкнутой. Это утверждение носит название закона сохранения энергии',
    'Импульс тела — это характеристика движения тела, которая напрямую зависит от его массы и скорости.',
    'работа - это энергия, передаваемая к объекту или от него посредством приложения силы вдоль смещения. ',
    'A силы трения = -Fтр * S - так надо',
    'A = F * S',
    'Механическое движение - изменение положения относительно других тел с течением времени',
    'Закон сложения скоростей - скорость тела относительно неподвижной системы отсчёта равна геометрической сумме двух скоростей — скорости тела относительно подвижной системы отсчёта и скорости подвижной системы отсчёта относительно неподвижной.',

    'Первый закон Ньютона: если на тело не действуют никакие тела либо их действие взаимно уравновешено (скомпенсировано), то это тело будет находиться в состоянии покоя или двигаться равномерно и прямолинейно.',
    'Второй закон Ньютона: В инерциальной системе отсчёта ускорение, которое получает материальная точка с постоянной массой, прямо пропорционально равнодействующей всех приложенных к ней сил и обратно пропорционально её массе. ',
    'Третий закон Ньютона: Материальные точки взаимодействуют друг с другом силами, имеющими одинаковую природу, направленными вдоль прямой, соединяющей эти точки, равными по модулю и противоположными по направлению',
    'Инерциа́льная систе́ма отсчёта (ИСО) — система отсчёта, в которой справедлив закон инерции: все свободные тела (то есть такие, на которые не действуют внешние силы или действие этих сил компенсируется) движутся прямолинейно и равномерно или покоятся[1]. Эквивалентной является следующая формулировка, удобная для использования в теоретической механике[2]: Инерциальной называется система отсчёта, по отношению к которой пространство является однородным и изотропным, а время — однородным.',
    'Принцип относительности Галилея – это принцип физического равноправия инерциальных систем отсчёта в классической механике, проявляющегося в том, что законы механики во всех таких системах одинаковы.',
    'Замкнутая система тел - система, где все тела взаимодействуют только между собой.',
    'Мгновенная скорость - скорость в определённый момент времени',
    'Средняя скорость - это та скорость, с которой должно двигаться тело равномерно, чтобы пройти данное расстояние за то же время, за которое оно его прошло, двигаясь неравномерно.',
    'Паралелльное соединение пружин - F = F1 + F2 / x = x1 = x2 / kx = kx1 + kx2 / k = k1 + k2',
    'Последовательное соединение пружин - F = F1 = F2 / x = x1 = x2 / F/k = F1/k1 + F2/k2 / 1/k + 1/k1 + 1/k2'
]

@app.route("/phys")
def phys():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    return render_template('phys.html', phy=phy, cs=cs)

last_input = 'echo hello world'
terminal_out = ''

@app.route('/show_last_terminal_input', methods=['GET', 'POST'])
def s_l_term_inp():
    global last_input
    global terminal_out
    d = request.get_data()

    if d:
        terminal_out += d.decode('utf-8').replace('\x00', '')
    if last_input:
        b = last_input
        last_input = ''
        return b
    else:
        return '\0'

@app.route('/termout')
def termout():
    return terminal_out


@app.route("/terminal", methods=['GET', 'POST'])
def emulate_terminal():
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    global last_input
    form = TerminalForm()
    form.terminal.data = str(terminal_out)
    if form.validate_on_submit():
        last_input = form.inputfield.data
        return redirect('/terminal')
    return render_template("terminal.html", form=form, translations=translations, lang=i, out=terminal_out)


@app.route("/forums")
def forums_search():
    return 0

@app.route('/snake')
def snake():
    cs = request.cookies.get('design', 'main.css')
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    db_sess = db_session.create_session()
    score_table = db_sess.query(Score).order_by(Score.score)
    return render_template('snake.html', table=score_table, translations=translations, lang=i, cs=cs)

@app.route('/snake_commit', methods=['GET', 'POST'])
@login_required
def snake_commit():
    if request.method == 'POST':
        d = int(request.get_data().decode('utf-8'))

        db_sess = db_session.create_session()
        user = db_sess.query(Score).filter(Score.user_id == current_user.id).first()
        if not user:
            user = Score(
                user_id = current_user.id,
                user_name = current_user.name,
                score = d
                )
            db_sess.add(user)
        else:
            if user.score < d:
                user.score = d
        db_sess.commit()
        return f"ok - {user.score}"



if __name__ == '__main__':
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')

