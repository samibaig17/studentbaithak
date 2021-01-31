from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail
import math
import json
import os

app = Flask(__name__)

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_username'],
    MAIL_PASSWORD=params['gmail_pswd']

)
mail = Mail(app)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload-location']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

local_server = True

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    """msgid, name, email,  phone,  msg,  date"""
    msgid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(12), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Post(db.Model):
    """postno, title, slug, content, date"""
    postno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=False)


@app.route('/')
def home():

    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['nofpost']))
    #[0:params['nofpost']]
    #Pagination Logic
    #First

    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['nofpost']): (page-1)*int(params['nofpost']) + int(params['nofpost'])]
    #First
    if page == 1:
        prev = '#'
        next = "/?page="+ str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = '#'
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/index')
def indexHome():
    posts = Post.query.filter_by().all()[0:params['nofpost']]
    return render_template('index.html', params=params, posts=posts)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Add Entry to the Database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num=phone, message=message, email=email, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From ' + name,
                          sender=email,
                          recipients=[params['gmail_username']],
                          body=message + "\n" + phone)

    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):

    post = Post.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)


@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'user' in session and session['user'] == params['admin']:
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        #REDIRECT TO LOGIN PANEL
        username = request.form.get('uname')
        pswd = request.form.get('pass')

        if username == params['admin'] and pswd == params['paswd']:
            #Set the session variable
            session['user'] = username
            posts = Post.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():

    if 'user' in session and session['user'] == params['admin']:

        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):

    if 'user' in session and session['user'] == params['admin']:

        if request.method == 'POST':
            new_title = request.form.get('title')
            new_tagline = request.form.get('tagline')
            new_slug = request.form.get('slug')
            new_content = request.form.get('content')
            new_imgfile = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Post(title=new_title, tagline=new_tagline, slug=new_slug, content=new_content, img_file=new_imgfile, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(postno=sno).first()
                post.title = new_title
                post.slug = new_slug
                post.content = new_content
                post.tagline = new_tagline
                post.img_file = new_imgfile
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Post.query.filter_by(postno=sno).first()
        return render_template('edit.html', params=params, post=post)


@app.route("/delete/<string:sno>")
def delete(sno):

    '''
    First We will Check if the USer is logged in or not?
    if user is logged in then we will get the post that we want to delete from database
    then we will run database command to delete that post
    and commit  changes in database
    '''
    if 'user' in session and session['user'] == params['admin']:
        post = Post.query.filter_by(postno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/login')


@app.route("/logout")
def logout():

    session.pop('user')
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
