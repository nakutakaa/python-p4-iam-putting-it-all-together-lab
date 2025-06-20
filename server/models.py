# from sqlalchemy.orm import validates
# from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy_serializer import SerializerMixin

# from config import db, bcrypt

# class User(db.Model, SerializerMixin):
#     __tablename__ = 'users'

#     pass

# class Recipe(db.Model, SerializerMixin):
#     __tablename__ = 'recipes'
    
#     pass
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    # I'm defining the columns for the User model here.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    # I'm defining the relationship with the Recipe model.
    # A user can have many recipes.
    recipes = db.relationship('Recipe', backref='user', lazy=True, cascade='all, delete-orphan')

    # I'm defining serialization rules to exclude the password hash from API responses.
    serialize_rules = ('-_password_hash',)

    # I'm using hybrid_property for the password to handle hashing and checking.
    @hybrid_property
    def password_hash(self):
        # I'm raising an AttributeError if someone tries to access the password_hash directly.
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        # I'm hashing the provided password using bcrypt.
        self._password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')

    # I'm creating a method to authenticate the user's password.
    def authenticate(self, password):
        # I'm checking if the provided password matches the stored hash.
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    # I'm adding a validation for the username.
    @validates('username')
    def validate_username(self, key, username):
        # I'm ensuring the username is present and unique.
        if not username:
            raise ValueError('Username must be provided')
        # I'm checking if a user with the same username already exists.
        if User.query.filter_by(username=username).first():
            raise ValueError('Username must be unique')
        return username

    def __repr__(self):
        return f'<User {self.username}>'

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    # I'm defining the columns for the Recipe model here.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)

    # I'm defining the foreign key to link recipes to users.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # I'm defining serialization rules for the Recipe model.
    # I'm including the user's username for easy access.
    serialize_rules = ('-user.recipes',)

    # I'm adding validations for the title and instructions.
    @validates('title')
    def validate_title(self, key, title):
        # I'm ensuring the title is present.
        if not title:
            raise ValueError('Recipe must have a title')
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        # I'm ensuring the instructions are present and at least 50 characters long.
        if not instructions:
            raise ValueError('Recipe must have instructions')
        if len(instructions) < 50:
            raise ValueError('Instructions must be at least 50 characters long')
        return instructions

    def __repr__(self):
        return f'<Recipe {self.title}>'