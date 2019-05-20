from flask_security import UserMixin, RoleMixin

from sqlalchemy import (Column, Integer, Table, ForeignKey, Text,
                        Boolean, DateTime, String)
from sqlalchemy.orm import relationship, backref

from .base import Base

# Association table between users and runs.
roles_users = Table(
    'roles_users',
    Base.metadata,
    Column('user_id', Integer(), ForeignKey('user.id')),
    Column('role_id', Integer(), ForeignKey('role.id')))


class User(Base, UserMixin):
    """" User Base class """
    id = Column(Integer, primary_key=True)
    google_id = Column(Text)
    email = Column(String(100), unique=True)
    password = Column(String(255))
    picture = Column(Text)

    name = Column(String(40))
    active = Column(Boolean())  # If set to disabled, cannot access.
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary=roles_users,
                         backref=backref('users'))
    last_activity_at = Column(DateTime())
    last_activity_ip = Column(String(255))

    analyses = relationship('Analysis', backref='user')

    def __repr__(self):
        return '<Bases.User[email=%s]>' % self.email


class Role(Base, RoleMixin):
    """ User roles """
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))
