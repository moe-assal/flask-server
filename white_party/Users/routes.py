from flask import render_template, request, redirect, url_for, Blueprint, flash, session, abort, Markup
from sqlalchemy import or_
from white_party.modules import Users, Law, Proposal, Notification, Volunteer
from white_party import crypt, db
from white_party.Users.forms import SignupForm, LoginForm, EditProfileForm, RequestResetForm, ResetPasswordForm
from white_party.Users.utilities import save_picture, send_reset_email
from white_party.global_uttilities import is_moderator
from datetime import datetime

users = Blueprint('users', __name__)


@users.app_context_processor
def inject_logged_user_data_for_all_templates():
    data = dict()
    if 'user' in session:
        data['logged_user'] = Users.query.filter_by(id=session['user']).first()
        if data['logged_user']:
            data['moderator'] = "yes" if is_moderator(data['logged_user']) else "no"
            data['notifications'] = Notification.query\
                .filter(or_(Notification.recipient == data['logged_user'], Notification.recipient_id == 0))\
                .order_by(Notification.date_posted.desc()).limit(5).all()
            data['new_notifications'] = Notification.query\
                .filter(or_(Notification.recipient == data['logged_user'], Notification.recipient_id == 0))\
                .filter(Notification.date_posted >= data['logged_user'].last_message_read_time).count()
    data.setdefault('moderator', 'no')
    data.setdefault('logged_user', None)
    data.setdefault('notifications', Notification.query
                    .filter_by(recipient_id=0)  # pan-users messages
                    .order_by(Notification.date_posted.desc())
                    .limit(5).all())
    data.setdefault('new_notifications', data['notifications'].__len__())

    # functions
    data['volunteered'] = lambda user: True if Volunteer.query.get(user.id) else False
    return data


@users.before_app_request
def send_legal():
    if 'visited_before' not in session:
        session['visited_before'] = False
    else:
        session['visited_before'] = True
    if not session['visited_before']:
        message = Markup("By continuing you agree to the "
                         "<a href=' " + url_for('static', filename='legal/UserA.pdf') + " '>User Agreement</a> " +
                         "and <a href=' " + url_for('static', filename='legal/PrivacyP.pdf') + " '>Privacy Policy</a>")
        flash(message, 'info')
    return


@users.before_app_request
def check_user():
    logged_user = None
    if 'user' in session:
        logged_user = Users.query.get(session['user'])
    if not logged_user:
        return

    if logged_user.activated == 0:  # deactivated
        if request.endpoint == 'users.banned':  # infinite loop
            return redirect(url_for('users.banned'))
    return


@users.after_app_request
def update_last_seen(response):
    session['visited_before'] = True
    logged_user = Users.query.get(session['user']) if 'user' in session else None
    if not logged_user:
        return response
    if response.status_code in [302, 403, 401] or request.method != 'GET':
        return response
    logged_user.last_message_read_time = datetime.utcnow()
    db.session.commit()

    return response


@users.route('/banned')
def banned():
    return abort(403)


@users.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        if login_form.validate_on_submit():
            found_user = Users.query.filter_by(membership_id=login_form.membership_id.data).first()
            if found_user is None:
                login_form.membership_id.errors = ['User with this ID not found']
                return render_template("login.html", login_form=login_form)

            if not crypt.check_password_hash(found_user.password, login_form.password.data):
                login_form.password.errors = ['password not correct']
                return render_template("login.html", login_form=login_form)

            session.permanent = login_form.remember.data
            session["user"] = found_user.id

            flash('logged in successfully', 'info')
            return redirect(url_for("main.index"))
        else:
            return render_template("login.html", login_form=login_form)
    else:
        if "user" in session:
            flash('already logged in', 'info')
            return redirect(url_for("main.index"))
        return render_template("login.html", login_form=login_form)


@users.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' not in session:
        volunteers = Volunteer.query.filter_by(type='sign_up_collector').all()
        return render_template("enrollment.html", volunteers=volunteers)

    moderator = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(moderator):
        volunteers = Volunteer.query.filter_by(type='sign_up_collector').all()
        return render_template("enrollment.html", volunteers=volunteers)

    signup_form = SignupForm()
    if request.method == "POST":
        if signup_form.validate_on_submit():
            found_user_by_id = Users.query.filter_by(membership_id=signup_form.membership_id.data).first()
            if found_user_by_id:
                signup_form.membership_id.errors = ['user with this Membership ID already exist']
                return render_template("signup.html", signup_form=signup_form)
            found_user_by_name = Users.query.filter_by(user_name=signup_form.username.data).first()
            if found_user_by_name:
                signup_form.username.errors = ['user with this username already exist']
                return render_template("signup.html", signup_form=signup_form)

            session.permanent = signup_form.remember.data
            hashed_password = crypt.generate_password_hash(signup_form.password.data).decode('utf-8')

            user = Users(membership_id=signup_form.membership_id.data,
                         name=signup_form.username.data,
                         password=hashed_password,
                         gender=signup_form.gender.data,
                         email=signup_form.email.data,
                         governorate=signup_form.governorate.data,
                         district=signup_form.district.data,
                         civil_registry_num=signup_form.civil_registry_num.data,
                         national_identity_num=signup_form.national_identity_num.data,
                         birth_date=signup_form.birth_date.data,
                         phone_number=signup_form.phone_number.data)

            db.session.add(user)
            db.session.commit()
            session["user"] = user.id
            flash('Signed Up successfully', 'info')
            return redirect(url_for("main.index"))

        else:
            return render_template("signup.html", signup_form=signup_form)
    else:
        return render_template("signup.html", signup_form=signup_form)


@users.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("users.login"))


@users.route('/profile/<string:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    found_user = Users.query.filter_by(id=user_id).first()
    if found_user is None:
        return render_template('user_not_found.html', img_url='../static/img/bg-iamges.jpg')

    logged_user = Users.query.filter_by(id=session['user']).first() if 'user' in session else None

    if request.method == 'GET':
        # <-- need expert -->
        proposal_page = request.args.get('proposal_page', 1, type=int)
        proposals_paginate = Proposal.query \
            .filter_by(author=found_user) \
            .order_by(Proposal.date_posted.desc()) \
            .paginate(page=proposal_page, per_page=9)

        law_page = request.args.get('law_page', 1, type=int)
        laws_paginate = Law.query \
            .filter_by(author=found_user) \
            .order_by(Law.date_posted.desc()) \
            .paginate(page=law_page, per_page=4)

        # <-- end -->
        if 'user' in session:
            if found_user.id == session['user']:
                return render_template('profile.html', user=found_user, user_profile="true",
                                       proposals_paginate=proposals_paginate,
                                       laws_paginate=laws_paginate,
                                       meta_data=found_user.__meta_data__(request.endpoint))

            if logged_user.is_following(found_user):
                followed = 'true'
            else:
                followed = 'false'
        else:
            followed = None
        print(followed)
        return render_template('profile.html', user=found_user, followed=followed,
                               proposals_paginate=proposals_paginate, laws_paginate=laws_paginate,
                               meta_data=found_user.__meta_data__(request.endpoint))

    else:
        if 'user' in session and found_user.id != session['user']:
            action = request.get_json()['action']
            if action not in ['follow', 'unfollow']:
                return "400"
            follow = 1 if action == 'follow' else 0

            if logged_user.is_following(found_user) and follow == 0:
                logged_user.followed.remove(found_user)
            elif not logged_user.is_following(found_user) and follow == 1:
                logged_user.followed.append(found_user)
            else:
                return "400"

            db.session.commit()
        else:
            return "400"
    return "200"


@users.route('/profile')
def user_profile():
    if 'user' in session:
        return redirect(url_for('users.profile', user_id=session['user']))
    else:
        return redirect(url_for('users.login'))


@users.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if "user" not in session:
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    edit_profile_form = EditProfileForm()

    if request.method == 'POST':
        if edit_profile_form.validate_on_submit():
            logged_user.email = edit_profile_form.email.data
            logged_user.description = edit_profile_form.description.data
            if edit_profile_form.picture.data:
                logged_user.profile_img = save_picture(edit_profile_form.picture.data)
            db.session.commit()
            return redirect(url_for('users.user_profile'))
        return render_template('edit_profile.html', logged_user=logged_user, edit_profile_form=edit_profile_form)

    else:
        edit_profile_form.email.data = logged_user.email
        edit_profile_form.description.data = logged_user.description
        return render_template('edit_profile.html', logged_user=logged_user, edit_profile_form=edit_profile_form)


@users.route('/delete_profile', methods=['POST'])
def delete_profile():
    """
        doesn't allow user to access anything
    """
    if 'user' not in session:
        redirect(url_for('users.login'))
    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return "403"

    user_id = request.get_json()['user_id']
    user = Users.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()
    return "200"


@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if 'user' in session:
        flash('already logged in', 'info')
        return redirect(url_for('main.index'))

    reset_request_form = RequestResetForm()

    if request.method == 'GET':
        return render_template('reset_request.html', reset_request_form=reset_request_form)
    else:
        if reset_request_form.validate_on_submit():
            user = Users.query.filter_by(email=reset_request_form.email.data).first()
            send_reset_email(user)
            flash('check your mail', 'info')
            return redirect(url_for('users.login'))


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if 'user' in session:
        flash('already logged in', 'info')
        return redirect(url_for('main.index'))
    user = Users.verify_reset_token(token)
    if not user:
        flash('invalid or expired token', 'info')
        return redirect(url_for('users.reset_request'))

    reset_password_form = ResetPasswordForm()

    if request.method == 'GET':
        return render_template('reset_password.html', reset_password_form=reset_password_form)

    else:
        hashed_password = crypt.generate_password_hash(reset_password_form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('password changed successfully', 'info')
        return redirect(url_for('users.login'))


@users.route('/add_volunteer', methods=['POST'])
def add_volunteer():
    if 'user' not in session:
        return '403'
    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return '403'

    data = request.get_json()
    user_id = data['user_id']
    volunteer_type = data['type']
    action = data['action']

    if action == "remove":
        db.session.delete(Volunteer.query.get_or_404(user_id))
    elif action == "add":
        user = Users.query.get_or_404(user_id)
        volunteer = Volunteer.query.get(user_id)
        if volunteer:
            return "400"
        volunteer = Volunteer(volunteer_user=user, volunteer_type=volunteer_type)
        db.session.add(volunteer)
    else:
        return "400"

    db.session.commit()
    return "200"


# arabic interface


@users.route('/login/ar', methods=['POST', 'GET'])
def login_arabic():
    login_form = LoginForm()
    if request.method == "POST":
        if login_form.validate_on_submit():
            found_user = Users.query.filter_by(membership_id=login_form.membership_id.data).first()
            if found_user is None:
                login_form.membership_id.errors = [u'المستخدم مع معرف العضوية هذا غير موجود']
                return render_template("ar/login.html", login_form=login_form)

            if not crypt.check_password_hash(found_user.password, login_form.password.data):
                login_form.password.errors = [u'كلمة المرور غير صحيحة']
                return render_template("ar/login.html", login_form=login_form)

            session.permanent = login_form.remember.data
            session["user"] = found_user.id

            flash(u'تم تسجيل الدخول بنجاح', 'info')
            return redirect(url_for("main.index_arabic"))
        else:
            return render_template("ar/login.html", login_form=login_form)
    else:
        if "user" in session:
            flash(u'قمت بتسجيل الدخول بالفعل', 'info')
            return redirect(url_for("main.index_arabic"))
        return render_template("ar/login.html", login_form=login_form)


@users.route('/signup/ar')
def signup_arabic():
    volunteers = Volunteer.query.filter_by(type='sign_up_collector').all()
    return render_template("ar/enrollment.html", volunteers=volunteers)
