from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from white_party import db, app
from flask import url_for
from datetime import datetime, timedelta


comment_likes_table = db.Table('comment_likes_table',
                               db.Column('comment_id', db.Integer, db.ForeignKey('comment.id')),
                               db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
                               )


proposals_up_voting_table = db.Table('proposals_up_voting_table',
                                     db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')),
                                     db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
                                     )


follow_ship_table = db.Table('follow_ship_table',
                             db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
                             db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
                             )


class Users(db.Model):
    """
    Table columns:
        - id: primary key
        - membership id: unique id given for every member
        - description: About me section in user profile
        - password: *****
        - gender: 1 is man. 0 is woman.
        - profile_img: FILENAME of profile image in 'static/profile_img/*********-`original_name`'
        - email: g@example.com
        - date joined: Note that this is automated once `Users` instance is created
        - activated: 1 if activated, 0 if deactivated.

        - laws_: All the laws posted by the user with backref of `author` in `Law` instances.
        - comments: All the comments posted by the user with backref of `author` in `Comment` instances.
        - proposals: All the proposals posted by the user with backref of `author` in `Proposal` instances.

        - followed: All users the user followed. backref `followers` for `Users` Instances. Many-to-Many relationship
                    using association table `follow_ship_table`

        - proposals_voted_for: ---. backref `voters`. Many-to-Many relationship with Association table
                               `proposals_up_voting_table`
        - comments_liked: ---. backref `users_likes`. Many-to-Many relationship with Association table
                          `comment_likes_table`.
        - laws_voted_in: ---. no backref (Association Object). Many-to-Many relationship using ASSOCIATION OBJECT
                         `VotePaper`.
    """
    __tablename__ = 'users'
    __searchable__ = ['membership_id', 'user_name']
    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(500), nullable=False, default='user likes to stay anonymous')
    user_name = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.Integer, nullable=False)
    profile_img = db.Column(db.String(40))
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activated = db.Column(db.Integer, nullable=False, default=1)

    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(80), nullable=False)

    # location and national identity
    governorate = db.Column(db.String(15), nullable=False)
    district = db.Column(db.String(30), nullable=False)
    civil_registry_num = db.Column(db.String(10), nullable=False)
    national_identity_num = db.Column(db.String(12), nullable=False)
    birth_date = db.Column(db.DateTime, nullable=False)

    laws_ = db.relationship('Law', backref='author')
    proposals = db.relationship('Proposal', backref='author')
    comments = db.relationship('Comment', backref='author')

    messages_sent = db.relationship('Notification',
                                    foreign_keys='Notification.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Notification',
                                        foreign_keys='Notification.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime, default=datetime.utcnow)

    volunteer = db.relationship('Volunteer', backref='user', lazy='dynamic')

    followed = db.relationship(
        'Users', secondary=follow_ship_table,
        primaryjoin=(follow_ship_table.c.follower_id == id),
        secondaryjoin=(follow_ship_table.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    proposals_voted_for = db.relationship('Proposal', secondary=proposals_up_voting_table,
                                          backref=db.backref('voters', lazy='dynamic'))
    comments_liked = db.relationship('Comment', secondary=comment_likes_table,
                                     backref=db.backref('users_likes', lazy='dynamic'))
    laws_voted_in = db.relationship('VotePaper')

    def __init__(self, membership_id, name, password, email, gender,
                 governorate, district, civil_registry_num, national_identity_num, birth_date, phone_number):
        self.user_name = name
        self.gender = 1 if gender == 'male' else 0
        self.password = password
        self.membership_id = membership_id
        self.email = email
        self.profile_img = gender + '.jpg'
        self.governorate = governorate
        self.district = district
        self.civil_registry_num = civil_registry_num
        self.national_identity_num = national_identity_num
        self.birth_date = birth_date
        self.phone_number = phone_number

    def __repr__(self):
        return 'user ' + self.user_name

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        found_user = self.followed.filter_by(id=user.id).all()
        return True if found_user else False

    def profile_image_url(self):
        return url_for('static', filename='profile-image/' + self.profile_img)

    def get_gender(self):
        return 'male' if self.gender == 1 else 'female'

    def get_reset_token(self, expire_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expire_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    def user_location(self):
        return self.governorate + ", " + self.district

    def user_age(self):
        return int((datetime.utcnow() - self.birth_date).total_seconds() / 31536000)

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

    def __meta_data__(self, endpoint):
        if endpoint in ['users.user_profile', 'users.profile']:
            data = [
                {
                    'name': 'title',
                    'content': 'user profile - ' + self.user_name
                },
                {
                    'name': 'description',
                    'content': 'About - ' + self.description[:155] + '...'
                },
                {
                    'name': 'og:description',
                    'content': 'Me - ' + self.description[:155] + '...'
                },
                {
                    'name': 'og:title',
                    'content': 'user profile - ' + self.user_name
                }
            ]
            return data
        return None

    def send_to_followers(self, action_end_point=None, message=None):
        # message is unescaped
        if message and not action_end_point:
            pass
        elif action_end_point == 'laws.law':  # added edit proposal
            message = "Added a new edit-proposal."
        elif action_end_point == 'laws.add_law':
            message = "Added a new law."
        else:
            message = "Has new activity."

        for follower in self.followers:
            notification = Notification(sender_id=self.id, recipient_id=follower.id, message=message)
            db.session.add(notification)


class Law(db.Model):

    """
    Table columns:
        - id: primary key
        - title: ---.
        - info: law's main information that is displayed under title.
        - explanation: ---.
        - date posted: Note that this is automated once `Law` instance is created

        - author_id: one(Users)-to-Many(Laws) relationship with `Users`.
        - edit_proposals: All edit_proposals associated with this law. backref `posted_at`.

        - vote_papers: no backref (Association Object). Many-to-Many relationship using ASSOCIATION OBJECT
                       `VotePaper`.
        - up_votes: ---.
        - down_votes: ---.

        - title_arabic: Translation
        - info_arabic: Translation
        - explanation_arabic: Translation
    """

    __tablename__ = 'law'
    __bind_key__ = 'laws'
    __searchable__ = ['id', 'title', 'info']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False, default='title')
    info = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    edit_proposals = db.relationship('Proposal', backref='posted_at')

    vote_papers = db.relationship('VotePaper')
    up_votes = db.Column(db.Integer, nullable=False, default=0)
    down_votes = db.Column(db.Integer, nullable=False, default=0)

    title_arabic = db.Column(db.Text, nullable=True)
    info_arabic = db.Column(db.Text, nullable=True)
    explanation_arabic = db.Column(db.Text, nullable=True)

    def __init__(self, title, info, explanation, author):
        self.title = title
        self.info = info
        self.explanation = explanation
        self.author = author

    def __repr__(self):
        return 'law ' + str(self.id)

    def __meta_data__(self, endpoint):
        if endpoint == 'laws.law':
            data = [
                {
                    'name': 'title',
                    'content': 'law - ' + self.title
                },
                {
                    'name': 'description',
                    'content': self.info[:155] + '...'
                },
                {
                    'name': 'og:description',
                    'content': self.info[:155] + '...'
                },
                {
                    'name': 'og:title',
                    'content': self.title
                }
            ]
            return data
        return None

    @staticmethod
    def remove(law=None, law_id=None):
        if law_id:
            law = Law.query.get(law_id)
        if not law:
            return

        for proposal in law.edit_proposals:
            Proposal.remove(proposal=proposal)

        for vote_paper in law.vote_papers:
            VotePaper.remove(vote_paper=vote_paper)

        db.session.delete(law)


class Proposal(db.Model):

    """
    Table columns:
        - id: primary key
        - title: ---.
        - info: proposal's main information that is displayed under title.
        - explanation: ---.
        - date posted: Note that this is automated once `Proposal` instance is created

        - author_id: one(user)-to-Many(proposals) relationship with `Users`.
        - law_id: one(law)-to-Many(proposals) relationship with `Law`.
        - comments: All comments associated with this law. backref `posted_at`.

        - up_votes: ---.

        - title_arabic: Translation
        - info_arabic: Translation
        - explanation_arabic: Translation
    """
    __tablename__ = 'proposal'
    __bind_key__ = 'proposals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default='title')
    info = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    law_id = db.Column(db.Integer, db.ForeignKey('law.id'))
    comments = db.relationship('Comment', backref='posted_at')

    up_votes = db.Column(db.Integer, nullable=False, default=0)

    title_arabic = db.Column(db.Text, nullable=True)
    info_arabic = db.Column(db.Text, nullable=True)
    explanation_arabic = db.Column(db.Text, nullable=True)

    def __init__(self, title, info, explanation, law_, author):
        self.title = title
        self.info = info
        self.explanation = explanation
        self.posted_at = law_
        self.author = author

    def __repr__(self):
        return 'proposal ' + str(self.id)

    def __meta_data__(self, endpoint):
        data = [
            {
                'name': 'title',
                'content': 'proposal - ' + self.title
            },
            {
                'name': 'description',
                'content': self.info[:155] + '...'
            },
            {
                'name': 'og:description',
                'content': self.info[:155] + '...'
            },
            {
                'name': 'og:title',
                'content': self.title
            }
        ]
        return data

    @staticmethod
    def remove(proposal=None, proposal_id=None):
        if proposal_id:
            proposal = Proposal.query.get(proposal)
        if not proposal:
            return

        for comment in proposal.comments:
            Comment.remove(comment=comment)

        for user in proposal.voters:
            proposal.voters.remove(user)

        db.session.delete(proposal)


class Comment(db.Model):

    """
        Table columns:
            - id: primary key
            - content: The comment displayed
            - date posted: Note that this is automated once `Comment` instance is created

            - likes: ---.

            - author_id: one(user)-to-Many(comments) relationship with `Users`.
            - proposal_id: one(proposal)-to-Many(comments) relationship with `Proposal`.
            - comments: All comments associated with this law. backref `posted_at`.

            - parent id: One(parent comment)-to-Many(replies). defaults to `0` if comment is a parent and not a reply.
            - parent: Relationship with `Comment`. backref `children`.
        """

    __tablename__ = 'comment'
    __bind_key__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    likes = db.Column(db.Integer, nullable=False, default=0)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))

    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False, default=0)
    parent = db.relationship('Comment', remote_side=[id], backref='children')

    def __init__(self, content, proposal, author, parent_comment=None):
        self.content = content
        self.posted_at = proposal
        self.author = author
        self.parent = parent_comment

    def __repr__(self):
        return 'comment ' + str(self.id)

    @staticmethod
    def remove(comment=None, comment_id=None):
        if comment_id:
            comment = Comment.query.get(comment_id)
        if not comment:
            return

        if comment.parent_id != 0:  # child (reply)
            db.session.remove(comment)
        else:
            for reply in comment.children:
                Comment.remove(comment=reply)
            db.session.remove(comment)

        return


class VotePaper(db.Model):

    """
        voter_id: `Users` instance id (primary key)
        law_voted_id: `Law` instance id (primary key)
        vote: TODO: document
        law_voted: the relationship with `Law` table above. Backref `vote_papers`
        user_voted: the relationship with `Users` table above. Backref `laws_voted_in`
    """
    __tablename__ = 'vote_paper'
    __bind_key__ = 'law_votes_cast'
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    law_voted_id = db.Column(db.Integer, db.ForeignKey('law.id'), primary_key=True)
    vote = db.Column(db.Integer)

    law_voted = db.relationship("Law", back_populates="vote_papers")
    user_voted = db.relationship("Users", back_populates="laws_voted_in")

    def __init__(self, vote):
        self.vote = vote

    @staticmethod
    def remove(vote_paper=None, voter_id=None, law_voted_id=None):
        if voter_id and law_voted_id:
            vote_paper = VotePaper.query.filter(VotePaper.voter_id == voter_id)\
                .filter(VotePaper.law_voted_id == law_voted_id).first()
        if not vote_paper:
            return

        db.session.delete(vote_paper)


class Notification(db.Model):
    __bind_key__ = 'notification_db'
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), default=0)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), default=0)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, message, sender_id=0, recipient_id=0):
        self.recipient_id = recipient_id
        self.message = message
        self.sender_id = sender_id


class Volunteer(db.Model):
    """
    - type: - sign_up_collector
    """
    __bind_key__ = 'volunteer_db'
    __tablename__ = 'volunteer'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, primary_key=True)
    type = db.Column(db.Text, nullable=False)
    date_volunteered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, volunteer_type, volunteer_user):
        self.user = volunteer_user
        self.type = volunteer_type


class ConfigurationDB(db.Model):

    """
    configuration data is saved here.
    ** week_duel >= 1
    """
    __bind_key__ = 'configuration_db'
    id = db.Column(db.Integer, primary_key=True)
    launch_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    week_duel = db.Column(db.Integer, nullable=False, default=1)
    laws_being_discussed = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self):
        pass

    def get_state(self):
        base_date = self.launch_date + timedelta(days=14 * self.week_duel)
        state = {
            'base-date': base_date,
            'week-duel': self.week_duel,
            'laws-being-discussed': self.laws_being_discussed,
            'launch-date': self.launch_date,
            'discussion-start': base_date,
            'discussion-end': base_date + timedelta(days=14),
            'vote-start': base_date - timedelta(days=14),
            'vote-end': base_date,
            'last-voted-start': base_date - timedelta(days=28),
            'last-voted-end': base_date - timedelta(days=14),
            'archive-end':  base_date - timedelta(days=28)
        }

        return state

    def increment_week_duel(self):
        self.week_duel += 1
        self.laws_being_discussed = 0
        db.session.commit()

    def increment_laws_being_discussed(self):
        if self.laws_being_discussed < 6:
            self.laws_being_discussed += 1
            db.session.commmit()
            return True
        else:
            return False


class ServerState:
    """
    High Level interface with `ConfigurationDB` table.
    Any operations with `ConfigurationDB` must be done here.
    """
    @staticmethod
    def get_state():
        return ConfigurationDB.query.get(1).get_state()

    @staticmethod
    def archive_date(week_duel_num: int):
        state = ServerState.get_state()
        start = state['launch-date'] + timedelta(days=14 * week_duel_num)
        end = start + timedelta(days=14)
        return start, end

    @staticmethod
    def increment_laws_being_discussed():
        config = ConfigurationDB.query.get(1)
        if config.laws_being_discussed < 6:
            config.laws_being_discussed += 1
            return True
        else:
            return False

    @staticmethod
    def increment_week_duel():
        config = ConfigurationDB.query.get(1)
        config.week_duel += 1
        config.laws_being_discussed = 0
