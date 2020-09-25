from flask import render_template, request, redirect, url_for, Blueprint, session, flash, abort
from white_party.modules import Users, Comment, Proposal, ServerState
from white_party.Proposals.forms import CommentForm, UpdateEditProposal, TranslateEditProposal
from white_party import db
from white_party.global_uttilities import is_moderator

proposals = Blueprint('proposals', __name__)


@proposals.route('/law/<string:law_id>/edit_proposal/<string:proposal_id>', methods=['GET', 'POST'])
def edit_proposal(law_id, proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    comment_form = CommentForm()
    if 'user' in session:
        logged_user = Users.query.filter_by(id=session['user']).first()
    else:
        logged_user = None

    if request.method == "POST":
        if 'user' not in session:
            redirect(url_for('users.login'))

        if proposal.posted_at.date_posted < ServerState.get_state()['archive-end']:
            flash('Cannot write Comment when Proposal is archived', 'info')
            return redirect(url_for('proposals.edit_proposal', law_id=law_id, proposal_id=proposal_id))

        if comment_form.validate_on_submit():
            content = comment_form.comment.data

            if content[0] == '@':

                parent_id, content = content.split(' ', 1)
                parent_id = parent_id[1:]
                parent_comment = Comment.query.filter_by(id=parent_id).first()
                if parent_comment is not None:
                    if parent_comment.posted_at == proposal:
                        comment = Comment(content, proposal, logged_user, parent_comment)
                        db.session.add(comment)
                        db.session.commit()
                    else:
                        return "500"
                else:
                    return "500"
            else:
                logged_user = Users.query.filter_by(id=session['user']).first()
                comment = Comment(content, proposal, logged_user)
                db.session.add(comment)
                db.session.commit()

            return redirect(url_for('proposals.edit_proposal', law_id=law_id, proposal_id=proposal_id))
        else:
            return "400"
    else:
        # TODO: Add ajax GET requests to retrieve more replies instead of showing all replies for a comment
        comment_page = request.args.get('comment_page', 1, type=int)
        comments_paginate = Comment.query.filter_by(proposal_id=proposal.id)\
            .filter_by(parent_id=0).order_by(Comment.date_posted.desc()).paginate(page=comment_page, per_page=20)
        # parent_id set to 0 to exclude replies
        return render_template('edit_proposal.html', edit_proposal=proposal, comment_form=comment_form,
                               comments_paginate=comments_paginate, meta_data=proposal.__meta_data__(request.endpoint))


@proposals.route('/like_comment', methods=['POST'])
def comment_like():
    """
    like a comment located in a proposal page.
    :return:
    """
    if 'user' not in session:
        flash('you need to be logged in', 'info')
        redirect(url_for('users.login'))

    comment_id = request.get_json()['comment_id']
    comment = Comment.query.filter_by(id=comment_id).first()
    logged_user = Users.query.filter_by(id=session['user']).first()

    if logged_user in comment.users_likes:
        comment.users_likes.remove(logged_user)
        comment.likes -= 1
    else:
        comment.users_likes.append(logged_user)
        comment.likes += 1

    db.session.commit()
    return ""


@proposals.route('/proposal_vote', methods=['POST'])
def vote():
    """
    up-vote a proposal displayed in a law page.
    :return:
    """
    if 'user' not in session:
        flash("need to be logged in", 'info')
        return url_for('users.login')

    proposal_id = request.get_json()['proposal_id']

    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if proposal.posted_at.date_posted < ServerState.get_state()['archive-end']:
        flash("Cannot vote on Proposal when it's archived", 'info')
        return ""

    user = Users.query.filter_by(id=session['user']).first()

    if user in proposal.voters:
        proposal.voters.remove(user)
        proposal.up_votes -= 1
        db.session.commit()
        return ""
    else:
        proposal.up_votes += 1
        proposal.voters.append(user)
        db.session.commit()
        return ""


@proposals.route('/law/<string:law_id>/edit_proposal/<string:proposal_id>/edit', methods=['GET', 'POST'])
def update_edit_proposal(law_id, proposal_id):
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        abort(403)

    proposal = Proposal.query.get_or_404(proposal_id)
    if not proposal.posted_at.date_posted >= ServerState.get_state()['discussion-start']:
        flash("Cannot update edit-proposal when law isn't under discussion", 'info')
        return redirect(url_for('laws.law', _id_=proposal.posted_at.id))

    update_edit_proposal_form = UpdateEditProposal()

    if request.method == 'POST':
        proposal.title = update_edit_proposal_form.title.data
        proposal.explanation = update_edit_proposal_form.explanation.data
        proposal.info = update_edit_proposal_form.info.data
        db.session.commit()
        return redirect(url_for('proposals.edit_proposal', law_id=law_id, proposal_id=proposal_id))
    else:
        update_edit_proposal_form.info.data = proposal.info
        update_edit_proposal_form.title.data = proposal.title
        update_edit_proposal_form.explanation.data = proposal.explanation
        return render_template('update_edit_proposal.html', update_edit_proposal_form=update_edit_proposal_form)


@proposals.route('/edit_proposal/delete', methods=['POST'])
def delete():
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        return "403"

    proposal_id = request.get_json()['proposal_id']
    Proposal.remove(proposal_id=proposal_id)
    db.session.commit()
    return "200"


@proposals.route('/law/<string:law_id>/edit_proposal/<string:proposal_id>/translate', methods=['GET', 'POST'])
def translate_edit_proposal(law_id, proposal_id):
    if 'user' not in session:
        flash('you need to be logged in')
        return redirect(url_for('users.login'))

    logged_user = Users.query.filter_by(id=session['user']).first()
    if not is_moderator(logged_user):
        abort(403)

    proposal = Proposal.query.get_or_404(proposal_id)
    translate_edit_proposal_form = TranslateEditProposal()

    if request.method == 'POST':
        proposal.title_arabic = translate_edit_proposal_form.title_arabic.data
        proposal.explanation_arabic = translate_edit_proposal_form.explanation_arabic.data
        proposal.info_arabic = translate_edit_proposal_form.info_arabic.data
        db.session.commit()
        return redirect(url_for('proposals.edit_proposal', law_id=law_id, proposal_id=proposal_id))
    else:
        translate_edit_proposal_form.info_arabic.data = proposal.info_arabic
        translate_edit_proposal_form.title_arabic.data = proposal.title_arabic
        translate_edit_proposal_form.explanation_arabic.data = proposal.explanation_arabic
        return render_template('translate_edit_proposal.html',
                               translate_edit_proposal_form=translate_edit_proposal_form, edit_proposal=proposal)


# arabic interface
@proposals.route('/law/<string:law_id>/edit_proposal/<string:proposal_id>/ar', methods=['GET', 'POST'])
def edit_proposal_arabic(law_id, proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    comment_form = CommentForm()
    if 'user' in session:
        logged_user = Users.query.filter_by(id=session['user']).first()
    else:
        logged_user = None

    if request.method == "POST":
        if 'user' not in session:
            redirect(url_for('users.login'))
        if comment_form.validate_on_submit():
            content = comment_form.comment.data

            if content[0] == '@':

                parent_id, content = content.split(' ', 1)
                parent_id = parent_id[1:]
                parent_comment = Comment.query.filter_by(id=parent_id).first()
                if parent_comment is not None:
                    if parent_comment.posted_at == proposal:
                        comment = Comment(content, proposal, logged_user, parent_comment)
                        db.session.add(comment)
                        db.session.commit()
                    else:
                        return "500"
                else:
                    return "500"
            else:
                logged_user = Users.query.filter_by(id=session['user']).first()
                comment = Comment(content, proposal, logged_user)
                db.session.add(comment)
                db.session.commit()

            return redirect(url_for('proposals.edit_proposal_arabic', law_id=law_id, proposal_id=proposal_id))
        else:
            return "400"
    else:
        # TODO: Add ajax GET requests to retrieve more replies instead of showing all replies for a comment
        comment_page = request.args.get('comment_page', 1, type=int)
        comments_paginate = Comment.query.filter_by(proposal_id=proposal.id)\
            .filter_by(parent_id=0).order_by(Comment.date_posted.desc()).paginate(page=comment_page, per_page=20)
        # parent_id set to 0 to exclude replies
        return render_template('ar/edit_proposal.html', edit_proposal=proposal, comment_form=comment_form,
                               comments_paginate=comments_paginate)
