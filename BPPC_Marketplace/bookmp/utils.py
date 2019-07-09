import random
import string

from rest_framework_jwt.settings import api_settings



def generate_random_password():
    PASS_CHARS = string.ascii_letters + string.digits
    for i in '0oO1QlLiI':
        PASS_CHARS = PASS_CHARS.replace(i,'')
    return "".join(random.choice(PASS_CHARS) for _ in range(0, 10))

def get_jwt_with_user(auth_user):
	"""
		Use the GetBlimp djangorestframework-jwt library to generate a JWT.
		For more read: http://getblimp.github.io/django-rest-framework-jwt/
		Source: https://github.com/GetBlimp/django-rest-framework-jwt
	"""
	jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
	jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
	payload = jwt_payload_handler(auth_user)
	token = jwt_encode_handler(payload)
	return token

