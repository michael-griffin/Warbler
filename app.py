import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized


from forms import UserAddForm, LoginForm, MessageForm, EditProfileForm, BlankForm
from models import db, connect_db, User, Message, Like, DEFAULT_HEADER_IMAGE_URL, DEFAULT_IMAGE_URL

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
#toolbar = DebugToolbarExtension(app)

connect_db(app)



# def get_csrf_form():
#     if 'csrf_form' not in g:
#         g.csrf_form = BlankForm()

# @app.teardown_appcontext
# def teardown_db(exception):
#     csrf_form = g.pop('csrf_form', None)

    # if csrf_form is not None:
    #     csrf_form.close()

# get_csrf_form()

##############################################################################
# User signup/login/logout

# g.csrf_form = get_csrf_form()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


@app.before_request
def add_csrf():
    g.csrf_form = BlankForm()



def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]



@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    if g.user:
        return redirect('/')

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        raise Unauthorized()

    do_logout() #this erases user from session
    flash(message='Logout Successful', category="success")
    return redirect('/')




##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """
    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, form=form)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    messages = (Message
                .query
                .filter_by(user_id=user.id)
                .order_by(Message.timestamp.desc())
                .all())

    return render_template('users/show.html', user=user, form=form, messages=messages)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, form=form)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, form=form)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")



@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = EditProfileForm(obj=g.user)

    if form.validate_on_submit():
        try:
            if User.authenticate(g.user.username, form.password.data):
                user = g.user
                user.username = form.username.data
                user.email = form.email.data
                user.image_url = form.image_url.data or DEFAULT_IMAGE_URL
                user.header_image_url = form.header_image_url.data or DEFAULT_HEADER_IMAGE_URL
                user.bio = form.bio.data

                db.session.commit()
                return redirect(f'/users/{g.user.id}')

            else:
                form.password.errors = ['Incorrect password']
                return render_template('users/edit.html', user=g.user, form=form)

        except IntegrityError:
            db.session.rollback()
            form.username.errors = ['Username already taken']

    return render_template('users/edit.html', user=g.user, form=form)


@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    Like.query.filter_by(user_id=g.user.id).delete()

    #for each message in user's messages, we have message.likes, and delete
    for message in g.user.messages:
        Like.query.filter_by(message_id = message.id).delete()

    Message.query.filter_by(user_id=g.user.id).delete()

    db.session.delete(g.user)
    db.session.commit()
    do_logout()
    return redirect("/signup")




##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)

    like = Like.query.get((message_id, g.user.id))

    return render_template('messages/show.html', like=like, message=msg, form=form)



@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    if msg.user_id == g.user.id:

        Like.query.filter_by(message_id = msg.id).delete()

        db.session.delete(msg)
        db.session.commit()
        flash('message deleted', "success")

    return redirect(f"/users/{g.user.id}")




##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        following_ids = [u.id for u in g.user.following]
        messages = (Message
                    .query
                    .filter((Message.user_id==g.user.id) |
                            (Message.user_id.in_(following_ids)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())


        form = g.csrf_form

        liked_message_ids = [ message.id for message in g.user.liked_messages]

        return render_template('home.html',
                               liked_message_ids = liked_message_ids,
                               user=g.user,
                               messages=messages, form=form)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response

@app.errorhandler(404)
def page_not_found(e):
    form = g.csrf_form

    return render_template('404.html', form=form)


##############################################################################
# Like routes:


@app.post('/messages/<int:msg_id>/toggle-like')
def toggle_like(msg_id):
    """Toggle a like for current message"""

    #CSRF validation is surprisingly tricky. This works for now.
    if not g.user:# or not g.csrf_form.validate_on_submit():
        # flash("Access unauthorized.", "danger")
        return jsonify({"status": "Unauthorized"}) #redirect('/')


    like = Like.query.get((msg_id, g.user.id))

    if like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like.create_like(user_id = g.user.id, message_id= msg_id)
        db.session.commit()


    return jsonify({'status': 'ok'})
    # return redirect(f'/messages/{msg_id}')


# @app.post('/messages/<int:msg_id>/toggle-like')
# def api_test(msg_id):


@app.get('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show list of liked warbles of this user."""

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    liked_message_ids = [m.id for m in user.liked_messages]

    return render_template('users/likes.html',
                           user=user,
                           form=form,
                           liked_message_ids=liked_message_ids,
                           messages=user.liked_messages)