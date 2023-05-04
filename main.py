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
from data.servers import Server
from data.extra_links import Link
from svgs import link_images, image_choices
from pathlib import Path
import subprocess
from flask import Flask, make_response, request, abort
from io import StringIO, BytesIO
from dulwich.pack import PackStreamReader
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



@app.route('/')
@app.route('/main')
def draw_():
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    res = make_response(render_template('main.html', translations=translations, lang=i))
    if not language:
        res.set_cookie("language", 'ru')
    db_sess = db_session.create_session()
    return res

@app.route('/jokes/add_joke', methods=['GET', 'POST'])
@login_required
def add_joke():
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
    return render_template('add_joke.html', form=form)

@app.route('/jokes/add_joke/photo_joke/<int:id>', methods=['GET', 'POST'])
@login_required
def upload_photo_joke(id):

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

    return render_template('upload_photo.html', imgform=imgform, exception='/jokes')


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
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

    return render_template('upload_photo.html', imgform=imgform, exception='/')

USERS_ON_PAGE = 50  # размах!


@app.route('/our_dear_users')
def draw():
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
    return render_template('doska_pocheta.html', blocks=users[::-1], page=page, admins='', page_count = users_count // USERS_ON_PAGE + 1)

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
    return render_template('jokes.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i)

@app.route('/jokes/<string:name>')
def draw_personal_jokes(name):
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
    return render_template('jokes.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id=f"/{id}", one_joke=name, translations=translations, lang=i)

@app.route('/jokes/<int:id>')
def draw_joke(id):
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
    return render_template('jokes.html', jokes=jokes[::-1], page=page, page_count=jokes_count // JOKES_ON_PAGE + 1, by_id=f"/{id}", one_joke=id, translations=translations, lang=i)

@app.route('/our_dear_users/<int:id>')
def draw_user(id=-1):
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    user = load_user(id)
    db_sess = db_session.create_session()
    extra_links = db_sess.query(Link).filter(Link.user_id == id).all()
    now = datetime.datetime.now()
    d, h, m = days_hours_minutes(now - user.created_date)

    return render_template('user_page.html', user=user, dated=d, dateh=h, datem=m, extra_links=extra_links, link_images=link_images, translations=translations, lang=i)

@app.route('/our_dear_users/our_dear_admins')
def draw_admins():
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
    return render_template('doska_pocheta.html', blocks=users[::-1], page=page, admins='/our_dear_admins', page_count = users_count // USERS_ON_PAGE + 1, translations=translations, lang=i)



@app.route('/register', methods=['GET', 'POST'])
def reqister():
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
                                   message="Такой пользователь уже есть", translations=translations, lang=i)
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
    return render_template('register.html', title='Регистрация', form=form, translations=translations, lang=i)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
                               form=form, translations=translations, lang=i)
    return render_template('login.html', title='Авторизация', form=form, translations=translations, lang=i)

@app.route('/music')
def draw_music():
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
    return render_template('music.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i)


@app.route('/music/<string:name>')
def draw_music_byname(name):
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
    return render_template('music.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i)

@app.route('/music/<int:id>')
def draw_music_byid(id):
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
    return render_template('music.html', music=music[::-1], page=page, page_count=music_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i)


@app.route('/music/add_music', methods=['GET', 'POST'])
@login_required
def add_music():
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
    return render_template('add_music.html', form=form, translations=translations, lang=i)

@app.route('/music/add_music/add_file/<int:id>', methods=['GET', 'POST'])
@login_required
def add_music_file(id):
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

    return render_template('upload_music.html', musicform=musicform, translations=translations, lang=i)





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
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='', translations=translations, lang=i)

@app.route('/servers/<string:name>')
def draw_servers_byname(name):
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
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i)

@app.route('/servers/<int:id>')
def draw_servers_byid(id):
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
    return render_template('servers.html', servers=servers[::-1], page=page, page_count=servers_count // JOKES_ON_PAGE + 1, by_id='f/{id}', translations=translations, lang=i)


@app.route('/servers/add_server', methods=['GET', 'POST'])
@login_required
def add_server():
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
    return render_template('add_server.html', form=form, translations=translations, lang=i)


@app.route('/goyda_lent')
def goyda():
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

    return render_template('goyda.html', posts=posts[::-1], translations=translations, lang=i)


@app.route('/change_about', methods=['GET', 'POST'])
@login_required
def change_about():
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    form = ChangeAboutForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.about = form.about.data
        db_sess.commit()
        return redirect(f'/our_dear_users/{current_user.id}')
    return render_template('change_about.html', form=form, exception=f'/our_dear_users/{current_user.id}', translations=translations, lang=i)


@app.route('/add_link', methods=['GET', 'POST'])
@login_required
def add_extra_link():
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
        return redirect(f'/our_dear_users/{current_user.id}', translations=translations, lang=i)

    return render_template('add_link.html', form=form, translations=translations, lang=i)
@app.route('/gitreps')
def draw_reps():
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    path = request.args.get('path', default='')

    r = get_reps(os.path.join(DIR, 'storage'))

    return render_template('gitreps.html', reps=r, translations=translations, lang=i, path=path, ptype='d')

def get_reps(name):
    for i in Path(name).iterdir():
        yield i.name

def gen_get_reps(name):
    a = []
    for i in get_reps(name):
        a.append(i)
    return a

gitauth = HTTPBasicAuth()

git_allowed = {
    'Boyaroslav': 'boyara867'
}

@gitauth.get_password
def get_password(username):
    if username in git_allowed:
        return git_allowed[username]
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


@app.route('/gitreps/<string:name>/git-receive-pack', methods=['POST'])
@gitauth.login_required
def git_receive(name):
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

@app.route('/gitreps/<string:name>/look')
def gitlook(name):
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    return render_template('git_files.html', files=os.popen(f'bash view.bash {name}').read().split(), name=name, translations=translations, lang=i)



@app.route('/docs/why_registration')
def why_registration():
    language = request.cookies.get("language", 'ru')
    i = ['ru', 'en', 'sp'].index(language)
    return render_template('why_registration.html', translations=translations, lang=i)


if __name__ == '__main__':
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')

