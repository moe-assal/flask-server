from flask import render_template, request, redirect, url_for, Blueprint, session, flash, abort
from white_party.modules import Users, Law, Proposal, VotePaper, ServerState
from white_party import db
from white_party.Laws.forms import LawForm, EditLawForm, TranslateLawForm
from white_party.Proposals.forms import PostForm
from white_party.global_uttilities import is_moderator, get_status, get_status_arabic

laws = Blueprint('laws', __name__)


@laws.app_context_processor
def inject_data():
    return {'get_status': lambda _law_: get_status(_law_, ServerState.get_state),
            'get_status_arabic': lambda _law_: get_status_arabic(_law_, ServerState.get_state)}


@laws.route('/add_law', methods=['GET', 'POST'])
def add_law():
    """
    - redirects to login page if user not in session
    - redirects to discussion page if  server_state['laws-being-discussed'] is '6'.
    * POST:
        - validates wtf form
        - adds law to database and commit
        - increment server_state['laws-being-discussed']
    """
    server_state = ServerState.get_state()
    if "user" not in session:
        flash('you need to be logged in', 'info')
        return redirect(url_for('users.login'))

    if server_state['laws-being-discussed'] == "6":
        flash('cannot post law. There is six laws being discussed which is the maximum. '
              'Wait until the next week-duel. Don\'t panic!', 'info')
        return redirect(url_for('main.discussion'))

    law_form = LawForm()
    if request.method == 'POST':
        if law_form.validate_on_submit():
            title = law_form.title.data
            info = law_form.law.data
            explanation = law_form.explanation.data

            found_user = Users.query.filter_by(id=session['user']).first()

            _law_ = Law(title, info, explanation, found_user)
            db.session.add(_law_)

            ServerState.increment_laws_being_discussed()
            Users.query.get(session['user']).send_to_followers(action_end_point=request.endpoint)
            db.session.commit()
            return redirect(url_for('laws.law', _id_=str(_law_.id)))
        else:
            return render_template('add_law.html', law_form=law_form)

    else:
        return render_template('add_law.html', law_form=law_form)


@laws.route('/law/<string:_id_>', methods=['GET', 'POST'])
def law(_id_):
    proposal_form = PostForm()
    if "user" in session:
        logged_user = Users.query.filter_by(id=session['user']).first()
    else:
        logged_user = None

    if request.method == 'POST':
        if proposal_form.validate_on_submit():
            if "user" not in session:
                return redirect(url_for('users.login'))

            law_ = Law.query.filter_by(id=_id_).first()
            if not law_.date_posted >= ServerState.get_state()['discussion-start']:
                flash("Cannot add edit-proposal when law isn't under discussion", 'info')
                return redirect(url_for('laws.law', _id_=_id_))

            title = proposal_form.title.data
            info = proposal_form.info.data
            explanation = proposal_form.explanation.data

            prop = Proposal(title, info, explanation, law_, logged_user)
            db.session.add(prop)
            logged_user.send_to_followers(action_end_point=request.endpoint)
            db.session.commit()
            return redirect(url_for('laws.law', _id_=_id_))
        else:
            return "400"
    else:

        _law_ = Law.query.filter_by(id=_id_).first()
        if not _law_:
            return "404"

        proposals_page = request.args.get('proposals_page', 1, type=int)
        proposals_paginate = Proposal.query.filter_by(law_id=_law_.id).order_by(Proposal.date_posted.desc()) \
            .paginate(page=proposals_page, per_page=9)

        return render_template('law.html', law=_law_, proposal_form=proposal_form,
                               proposals_paginate=proposals_paginate, meta_data=_law_.__meta_data__(request.endpoint))


@laws.route('/law/delete', methods=['POST'])
def delete():
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return "403"

    _id_ = request.get_json()['law_id']
    law_ = Law.query.get_or_404(_id_)
    if not law_.date_posted >= ServerState.get_state()['discussion-start']:
        flash('Cannot delete law when not under discussion', 'info')
        return "301"

    Law.remove(law_id=_id_)
    db.session.commit()
    return "200"


@laws.route('/law/edit/<int:_id_>', methods=['POST', 'GET'])
def edit_law(_id_):
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return "403"

    law_ = Law.query.get_or_404(_id_)
    if law_.date_posted < ServerState.get_state()['vote-start']:
        flash("Cannot edit law when not under discussion", 'info')
        return redirect(url_for('laws.law', _id_=_id_))

    edit_law_form = EditLawForm()

    if request.method == 'POST':
        law_.title = edit_law_form.title.data
        law_.explanation = edit_law_form.explanation.data
        law_.info = edit_law_form.law.data
        db.session.commit()
        return redirect(url_for('laws.law', _id_=_id_))
    else:
        edit_law_form.law.data = law_.info
        edit_law_form.title.data = law_.title
        edit_law_form.explanation.data = law_.explanation
        return render_template('edit_law.html', edit_law_form=edit_law_form)


@laws.route('/vote', methods=['GET', 'POST'])
def vote_laws():
    """
    * GET:
        - returns laws between server_state['vote-start'] and server_state['vote-end']
        - vote_papers dictionary is used to render the voting buttons (darkened if clicked before)
    * POST:
        - redirects to login page if user not in session
        - gets vote from json data {
                                    vote: 'revert' || 'upvote' || 'downvote',
                                    law_id: _id_
                                    }
        - maps the vote to 0 if 'downvote' or 1 if 'upvote'
        - reverts the past vote (if exist) of the user in this post
        - creates new VotePaper ad commit it
    """
    logged_user = Users.query.filter_by(id=session['user']).first() if 'user' in session else None

    if request.method == 'POST':
        if logged_user is None:
            flash('you need to be logged in', 'info')
            return url_for('users.login')

        data = request.get_json()
        if data['vote'] not in ['revert', 'upvote', 'downvote']:
            return "400"

        law_found = Law.query.filter_by(id=data['law_id']).first()

        state = ServerState.get_state()
        if not state['vote-start'] <= law_found.date_posted < state['vote-end']:
            flash("Cannot vote for law when it's not under the voting process", 'info')
            return redirect(url_for('laws.vote_laws'))

        old_vote = VotePaper.query.filter_by(law_voted=law_found)
        old_vote = old_vote.filter(VotePaper.voter_id == session['user']).first()

        if old_vote:
            if old_vote.vote == 1:
                law_found.up_votes -= 1
            elif old_vote.vote == 0:
                law_found.down_votes -= 1
            db.session.delete(old_vote)

        db.session.commit()
        if data['vote'] == 'revert':
            return ""

        vote_paper = VotePaper(1) if data['vote'] == 'upvote' else VotePaper(0)
        vote_paper.voter_id = logged_user.id

        law_found.vote_papers.append(vote_paper)

        if vote_paper.vote == 1:
            law_found.up_votes += 1
        elif vote_paper.vote == 0:
            law_found.down_votes += 1

        db.session.commit()
        return ""
    else:
        server_state = ServerState.get_state()

        laws_found = Law.query.filter(Law.date_posted > server_state['vote-start'])\
            .filter(Law.date_posted < server_state['vote-end']).all()

        vote_papers = dict()
        for law_found in laws_found:
            vote_papers[law_found.id] = VotePaper.query.filter_by(law_voted=law_found)\
                .filter_by(user_voted=logged_user).first()

        return render_template('vote_laws.html', laws=laws_found, vote_papers=vote_papers)


@laws.route('/law/<string:_id_>/translate', methods=['GET', 'POST'])
def translate_law(_id_):
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        abort(403)

    law_ = Law.query.get_or_404(_id_)
    translate_law_form = TranslateLawForm()

    if request.method == 'POST':
        law_.title_arabic = translate_law_form.title_arabic.data
        law_.explanation_arabic = translate_law_form.explanation_arabic.data
        law_.info_arabic = translate_law_form.info_arabic.data
        db.session.commit()
        return redirect(url_for('laws.law', _id_=_id_))
    else:
        translate_law_form.info_arabic.data = law_.info_arabic
        translate_law_form.title_arabic.data = law_.title_arabic
        translate_law_form.explanation_arabic.data = law_.explanation_arabic
        return render_template('translate_law.html', translate_law_form=translate_law_form, law=law_)


# arabic interface below

@laws.route('/law/<string:_id_>/ar')
def law_arabic(_id_):
    _law_ = Law.query.filter_by(id=_id_).first()
    if not _law_:
        return "404"

    proposal_page = request.args.get('proposal_page', 1, type=int)
    proposals_paginate = Proposal.query.filter_by(law_id=_law_.id).filter(Proposal.info_arabic.isnot(None))\
        .order_by(Proposal.date_posted.desc()).paginate(page=proposal_page, per_page=9)

    return render_template('ar/law.html', law=_law_, proposals_paginate=proposals_paginate)


@laws.route('/vote/ar', methods=['GET', 'POST'])
def vote_laws_arabic():
    # temporary approach
    logged_user = Users.query.filter_by(id=session['user']).first() if 'user' in session else None

    if request.method == 'POST':
        if logged_user is None:
            flash('you need to be logged in', 'info')
            return url_for('users.login')

        data = request.get_json()
        if data['vote'] not in ['revert', 'upvote', 'downvote']:
            return "400"

        law_found = Law.query.filter_by(id=data['law_id']).first()

        state = ServerState.get_state()
        if not state['vote-start'] <= law_found.date_posted < state['vote-end']:
            flash(u"لا يمكن التصويت على القانون عندما لا يخضع لعملية التصويت", 'info')
            return redirect(url_for('laws.vote_laws_arabic'))

        old_vote = VotePaper.query.filter_by(law_voted=law_found)
        old_vote = old_vote.filter(VotePaper.voter_id == session['user']).first()

        if old_vote:
            if old_vote.vote == 1:
                law_found.up_votes -= 1
            elif old_vote.vote == 0:
                law_found.down_votes -= 1
            db.session.delete(old_vote)

        db.session.commit()
        if data['vote'] == 'revert':
            return ""

        vote_paper = VotePaper(1) if data['vote'] == 'upvote' else VotePaper(0)
        vote_paper.voter_id = logged_user.id

        law_found.vote_papers.append(vote_paper)

        if vote_paper.vote == 1:
            law_found.up_votes += 1
        elif vote_paper.vote == 0:
            law_found.down_votes += 1

        db.session.commit()
        return ""
    else:
        server_state = ServerState.get_state()

        laws_found = Law.query.filter(Law.date_posted > server_state['vote-start']) \
            .filter(Law.date_posted < server_state['vote-end'])\
            .filter(Law.info_arabic.isnot(None)).all()

        vote_papers = dict()
        for law_found in laws_found:
            vote_papers[law_found.id] = VotePaper.query.filter_by(law_voted=law_found) \
                .filter_by(user_voted=logged_user).first()

        return render_template('ar/vote_laws.html', laws=laws_found, vote_papers=vote_papers)
