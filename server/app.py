#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio,
            )
            user.password_hash = password

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            user_data = {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }
            return make_response(user_data, 201)

        except ValueError as e:
            db.session.rollback()
            return make_response({'errors': [str(e)]}, 422)
        except IntegrityError:
            db.session.rollback()
            return make_response({'errors': ['Username already exists or other data integrity issue.']}, 422)
        except Exception as e:
            db.session.rollback()
            return make_response({'errors': [f'An unexpected error occurred: {str(e)}']}, 500)


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if user:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
                return make_response(user_data, 200)
            else:
                session.pop('user_id', None)
                return make_response({'message': 'User not found, please log in again.'}, 401)
        else:
            return make_response({'message': 'Not authorized'}, 401)


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            user_data = {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }
            return make_response(user_data, 200)
        else:
            return make_response({'message': 'Invalid username or password'}, 401)

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id', None)
            return make_response({}, 204)
        else:
            return make_response({'message': 'Not authorized'}, 401)

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            recipes = Recipe.query.all()
            # MODIFIED LINE: Include 'user' in the serialization rules.
            # We explicitly tell it to include the 'user' relationship,
            # and then exclude the 'recipes' from the user to prevent circular reference.
            recipes_data = [recipe.to_dict(rules=('-user.recipes', 'user')) for recipe in recipes]
            return make_response(recipes_data, 200)
        else:
            return make_response({'message': 'Not authorized to view recipes'}, 401)

    def post(self):
        user_id = session.get('user_id')

        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if not user:
                session.pop('user_id', None)
                return make_response({'message': 'User not found, please log in again.'}, 401)

            data = request.get_json()
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            try:
                recipe = Recipe(
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete,
                    user_id=user.id
                )

                db.session.add(recipe)
                db.session.commit()

                # MODIFIED LINE: Ensure the newly created recipe also returns its user data
                return make_response(recipe.to_dict(rules=('-user.recipes', 'user')), 201)

            except ValueError as e:
                db.session.rollback()
                return make_response({'errors': [str(e)]}, 422)
            except Exception as e:
                db.session.rollback()
                return make_response({'errors': [f'An unexpected error occurred: {str(e)}']}, 500)
        else:
            return make_response({'message': 'Not authorized to create recipes'}, 401)


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)