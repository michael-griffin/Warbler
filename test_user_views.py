"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        #db.session.flush()
        db.session.commit()

        m1 = Message(text="m1-text", user_id=u1.id)
        m2 = Message(text="test_text2", user_id=u1.id)

        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id
        self.m2_id = m2.id

        like1 = Like.create_like(user_id = self.u2_id, message_id = self.m1_id)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()



class UserAuthViewTestCase(UserBaseViewTestCase):
    """Tests for user authentication routes."""

    def test_show_sign_up(self):
        """Test showing sign up form."""
        with self.client as c:
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sign me up!", html)

    def test_sign_up(self):
        """Tests that users is signed up with valid credentials."""
        with self.client as c:
            resp = c.post('/signup', data={
                'username': 'test_new_user',
                'email': 'test@test.com',
                'password': 'password',
                'image_url': ''
            },
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@test_new_user', html)
            self.assertIn('Log out', html)

            self.assertEqual(len(User.query.all()), 3)


    def test_username_taken(self):
        """Tests error if username is already taken"""
        with self.client as c:
            resp = c.post('/signup', data={
                'username': 'u1',
                'email': 'test@test.com',
                'password': 'password',
                'image_url': ''
            })
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken', html)

    def test_incorrect_password_length(self):
        """Tests error if password is too short"""
        with self.client as c:
            resp = c.post('/signup', data={
                'username': 'test_new_user',
                'email': 'test@test.com',
                'password': '1',
                'image_url': ''
            },
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Field must be between 6 and 50 characters long.', html)

    def test_show_login(self):
        """Test showing login page"""
        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back.", html)

    def test_successful_login(self):
        """Test logging in with valid credentials."""
        with self.client as c:
            resp = c.post('/login', data={
                'username': 'u1',
                'password': 'password'
            },
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, u1!", html)
            self.assertIn("@u1", html)

    def test_unsuccessful_login(self):
        """Test logging in with invalid credentials."""
        with self.client as c:
            resp = c.post('/login', data={
                'username': 'bad_user',
                'password': 'password'
            },
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

            resp = c.post('/login', data={
                'username': 'u1',
                'password': 'bad_password'
            },
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

    def test_logout(self):
        """Test logging out a user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Logout Successful", html)
            self.assertIn("What's Happening?", html)

    def test_bad_logout(self):
        """Test unauthorized logout"""
        with self.client as c:
            resp = c.post('/logout', follow_redirects=True)

            self.assertEqual(resp.status_code, 401)



class UserInfoViewTestCase(UserBaseViewTestCase):
    """Tests for general user routes"""

    def test_show_users_list(self):
        """Test showing list of users to logged in user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u1", html)
            self.assertIn("@u2", html)

    def test_show_users_logged_out(self):
        """Test showing users if logged out"""
        with self.client as c:
            resp = c.get('/users', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_user_profile(self):
        """Test display for profile on logged in user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Profile', html)
            self.assertIn('Delete Profile', html)

    def test_logged_out_profile(self):
        """Test profile redirect when user is logged out"""
        with self.client as c:
            resp = c.get(f'/users/{self.u1_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_users_following(self):
        """Test following list """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.following.append(u2)

            resp = c.get(f'/users/{self.u1_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u2', html)
            self.assertIn('Unfollow', html)


    def test_logged_out_following(self):
        """Test following page redirect when user is logged out"""
        with self.client as c:
            resp = c.get(f'/users/{self.u1_id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)


    def test_users_followers(self):
        """Test followers list """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.followers.append(u2)

            resp = c.get(f'/users/{self.u1_id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u2', html)
            self.assertIn('Follow', html)

    def test_logged_out_followers(self):
        """Test followers page redirect when user is logged out"""
        with self.client as c:
            resp = c.get(f'/users/{self.u1_id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_follow_user(self):
        """Test whether you can start following a user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            u1 = User.query.get(self.u1_id)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(u1.following), 1)
            self.assertIn('@u2', html)
            self.assertIn('Unfollow', html)

    def test_follow_logged_out(self):
        """Test add follower post request when user is logged out"""
        with self.client as c:
            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            u1 = User.query.get(self.u1_id)
            self.assertEqual(len(u1.following), 0)
            self.assertIn("Access unauthorized", html)

    def test_stop_following_user(self):
        """Test whether you can remove follower when logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.following.append(u2)

            self.assertEqual(len(u1.following), 1)
            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(u1.following), 0)
            self.assertNotIn('@u2', html)

    def test_stop_following_logged_out(self):
        """Test unfollow route when logged out."""
        with self.client as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.following.append(u2)

            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(len(u1.following), 1)

    def test_show_user_profile(self):
        """Test showing user profile to logged in user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit your profile", html)
            self.assertIn("u1", html)

    def test_update_user_info(self):
        """Test updating a user's information"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post('/users/profile',
                          data={
                              'username' : 'u1',
                              'email' : 'test.u1@email.com',
                              'password' : 'password',
                              'image_url' : '',
                              'header_image_url' : '',
                              'bio' : 'Test bio info change'
                          },
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test bio info change", html)

            user = User.query.get(self.u1_id)
            self.assertEqual(user.email, 'test.u1@email.com')
            self.assertEqual(user.bio, 'Test bio info change')

    def test_edit_user_name_taken(self):
        """Test handling error when username is already taken"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post('/users/profile',
                          data={
                              'username' : 'u2',
                              'email' : 'u1@email.com',
                              'password' : 'password',
                              'image_url' : '',
                              'header_image_url' : '',
                              'bio' : ''
                          })
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken', html)

    def test_edit_user_route_bad_password(self):
        """Test trying a bad password in user edit form"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post('/users/profile',
                          data={
                              'username' : 'u1',
                              'email' : 'u1@email.com',
                              'password' : 'bad_password',
                              'image_url' : '',
                              'header_image_url' : '',
                              'bio' : ''
                          })
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Incorrect password', html)


    def test_delete_user_success(self):
        """Test deleting a user sucessfully while logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.', html)
            self.assertEqual(len(User.query.all()), 1)
            self.assertEqual(len(Message.query.all()), 0)
            self.assertEqual(len(Like.query.all()), 0)

    def test_delete_user_logged_out(self):
        """Test a failed user delete request (when there is noone logged in)"""
        with self.client as c:
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('New to Warbler?', html)
            self.assertIn('Access unauthorized', html)
            self.assertEqual(len(User.query.all()), 2)
            self.assertEqual(len(Message.query.all()), 2)


