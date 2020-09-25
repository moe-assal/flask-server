from white_party.modules import *


def create_database():
    """
    :notes:
        'database' FOLDER must be created manually
    :return:
    """
    db.create_all()
    return


def initialize_configuration():
    old_config = ConfigurationDB.query.first()
    if old_config:
        db.session.delete(old_config)
        db.session.commit()

    c = ConfigurationDB()

    # custom config
    c.week_duel = 0
    c.launch_date = datetime(year=2020, month=9, day=25, hour=12, minute=0, second=0, microsecond=0)
    c.laws_being_discussed = 0

    db.session.add(c)
    db.session.commit()
