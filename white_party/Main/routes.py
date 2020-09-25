from flask import render_template, request, Blueprint, url_for, redirect, abort, flash, Markup, session
from white_party.modules import Law, ServerState, Users, Notification
from white_party import csrf_token, db
from white_party.Main.forms import NotificationForm
from white_party.global_uttilities import is_moderator

main = Blueprint('main', __name__)


@main.app_context_processor
def inject_server_data():
    return ServerState.get_state()


@main.route('/')
def index():
    """
    retrieves the main page. It also displays the latest laws that finished the voting process.
    """
    server_state = ServerState.get_state()
    laws_found = Law.query.filter(Law.date_posted >= server_state['last-voted-start'])\
        .filter(Law.date_posted <= server_state['last-voted-end']).all()
    return render_template('index.html', laws=laws_found)


@main.route('/developer')
def developer():
    return render_template('developer.html')


@main.route('/fundraiser')
def fundraiser():
    return render_template('fundraiser.html')


@main.route('/search', methods=['GET', 'POST'])
@csrf_token.exempt
def search():
    if request.method == 'POST':
        law_page = request.args.get('law_page', 1, type=int)
        laws_paginate = Law.query.whoosh_search(request.form.get('search-text')).order_by(Law.date_posted.desc()) \
            .paginate(page=law_page, per_page=12)

        return render_template('search.html', laws_paginate=laws_paginate)
    else:
        return render_template('search.html', laws_paginate=None)


@main.route('/discussion', methods=['GET'])
def discussion():
    """
    :return: number of laws being proposed and moved to discussion.
    """
    server_state = ServerState.get_state()
    laws = Law.query.filter(Law.date_posted > server_state['discussion-start'])\
        .filter(Law.date_posted <= server_state['discussion-end']).all()
    return render_template('discussion.html', laws=laws)


@main.route('/archive/<string:week_duel_num>')
def archive(week_duel_num):
    """
    :param week_duel_num: it is a string so that we can interpret negative numbers.
        - if '-1': returns the latest week-duel archive
        - else: return the week-duel number `week_duel_num`
    :return:
        - 404: week_duel_num is not reached yet.
        - redirect to vote: if week_duel_num is the one that's being voted.
    """
    server_state = ServerState.get_state()

    if week_duel_num == "-1":
        week_duel_num = server_state['week-duel'] - 2
        if week_duel_num <= 0:
            return abort(404)
        else:
            return redirect(url_for('main.archive', week_duel_num=week_duel_num))
    else:
        week_duel_num = int(week_duel_num)

    if week_duel_num == server_state['week-duel'] - 1:
        return redirect(url_for('laws.vote_laws'))
    elif week_duel_num == server_state['week-duel']:
        return redirect(url_for('main.discussion'))
    elif week_duel_num > server_state['week-duel']:
        return abort(404)

    # pagination
    has_next = week_duel_num < server_state['week-duel'] - 2
    has_prev = week_duel_num > 1

    start_date, end_date = ServerState.archive_date(week_duel_num)
    print('\nfrom ', start_date.strftime('%Y-%m-%d %H:%M'), '\t to', end_date.strftime('%Y-%m-%d %H:%M'))
    laws_found = Law.query.filter(Law.date_posted >= start_date).filter(Law.date_posted <= end_date).all()

    # if laws_found.__len__() != 6:
    #     abort(500)

    return render_template('law_week.html', laws=laws_found, week_duel=week_duel_num,
                           has_next=has_next, has_prev=has_prev)


@main.route('/add_notification', methods=['GET', 'POST'])
def add_notification():
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return abort(403) if request.method == 'GET' else '403'

    notification_form = NotificationForm()

    if notification_form.validate_on_submit():
        notification = Notification(recipient_id=int(notification_form.recipient_id.data),
                                    message=notification_form.message.data)
        db.session.add(notification)
        db.session.commit()
        return redirect(url_for('main.index'))

    return render_template('add_notification.html', notification_form=notification_form)


# arabic interface


@main.route('/ar')
def index_arabic():
    """
    retrieves the main page. It also displays the latest laws that finished the voting process.
    """
    server_state = ServerState.get_state()
    laws_found = Law.query.filter(Law.date_posted >= server_state['last-voted-start'])\
        .filter(Law.date_posted <= server_state['last-voted-end'])\
        .filter(Law.info_arabic.isnot(None)).all()

    return render_template('ar/index.html', laws=laws_found)


@main.route('/fundraiser/ar')
def fundraiser_arabic():
    return render_template('ar/fundraiser.html')


@main.route('/discussion/ar', methods=['GET'])
def discussion_arabic():
    server_state = ServerState.get_state()
    laws = Law.query.filter(Law.date_posted > server_state['discussion-start'])\
        .filter(Law.date_posted <= server_state['discussion-end'])\
        .filter(Law.info_arabic.isnot(None)).all()
    return render_template('ar/discussion.html', laws=laws)
