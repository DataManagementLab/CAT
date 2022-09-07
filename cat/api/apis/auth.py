from flask import request, jsonify
from flask_restplus import Resource, Namespace, fields
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_refresh_token_required, \
    set_access_cookies, set_refresh_cookies
import os

api = Namespace('auth', description='Authentication operations.')

login_data = api.model('Login_data', {
    'passphrase': fields.String('Passphrase', required=True),
})


@api.route('/login')
class Login(Resource):
    @api.doc('access_token')
    @api.expect(login_data)
    def post(self):
        data = request.json
        if data['passphrase'] == os.environ['JWT_PASSPHRASE']:
            access_token = create_access_token(identity='client')
            refresh_token = create_refresh_token(identity='client')
            response = jsonify({'authenticated': True})
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response
        api.abort(401, 'Invalid passphrase')


@jwt_refresh_token_required
@api.route('/refresh')
class Refresh(Resource):
    @api.doc('refresh_token')
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        response = jsonify({'authenticated': True})
        set_access_cookies(response, access_token)
        return response
