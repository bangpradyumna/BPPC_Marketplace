from google.oauth2 import id_token as googleIdToken
from google.auth.transport import requests as google_requests

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt # For the webapp on inaug day
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Profile
from .utils import generate_random_password, get_jwt_with_user

@csrf_exempt
@api_view(['POST'])
def login(request):
    """
        The auth endpoint services 2 different categories of users:
            Bitsians - Google OAuth 2.0.
            New batch - Simple username/password based login.
        Required keys for this endpoint:
            Mode 1: Simple username/password
                username: str
                password: str
            Mode 2: OAuth 2.0
                id_token: str
    """

    try:
        username = str(request.data["username"])
        password = str(request.data["password"])
        auth_mode = 1
    except KeyError:
        try:
            id_token = str(request.data["id_token"])
            auth_mode = 2
        except KeyError:
            message = "Insufficient authentication parameters."
            payload = {
                "detail": message,
                "display_message": message
            }
            response =  Response(payload, status=400)
            response.delete_cookie('sessionid')
            return response
            

    if auth_mode == 1:
        user = authenticate(username=username, password=password)
        # 'authenticates' returns a user object if the credentials
        # are valid for a backend.
        if user is None:
            message = "Invalid credentials."
            payload = {
                "detail": message,
                "display_message": message
            }
            response =  Response(payload, status=401)
            response.delete_cookie('sessionid')
            return response
            
    elif auth_mode == 2:
        try:
            try:
                idinfo = googleIdToken.verify_oauth2_token(id_token, google_requests.Request())
            except Exception as e:
                message = str(e)
                payload = {
                    "detail": message,
                    "diaplay_message": "Something went wrong. Please try again." 
                }
                response =  Response(payload, status=403)
                response.delete_cookie('sessionid')
                return response

            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                message = "Not a valid Google account."
                payload = {
                    "detail": message,
                    "diaplay_message": message 
                }
                response =  Response(payload, status=403)
                response.delete_cookie('sessionid')
                return response

            email = idinfo["email"]

            try:
                hd = idinfo["hd"] # hd = Hosted Domain
            except KeyError:
                hd = email.split("@")[-1]
            if not hd == "pilani.bits-pilani.ac.in":
                message = "Not a valid BITSian account."
                payload = {
                    "detail": message,
                    "diaplay_message": message 
                }
                response =  Response(payload, status=403)
                response.delete_cookie('sessionid')
                return response

            try:
                user = User.objects.get(email=email)
            
            except User.DoesNotExist:
                # Creating the account for a bitsian.

                name = idinfo['name'].title()
                first_name = name.split(' ', 1)[0]

                try: 
                    last_name = name.split(' ', 1)[1]
                except IndexError:
                    last_name = ''

                short_id = email.split('@')[0]
                
                user = User.objects.create(
                    username=short_id,
                    password=generate_random_password(),
                    email = email,
                    first_name = first_name,
                    last_name = last_name
                )

                profile = Profile()
                profile.user = user
                
                # Extracting year from email, would have to be updated yearly.
                # Or we can just ask the user for his year.
                profile.year = 2020 - int(email[0:4])

            try:
                profile = user.profile
            except:
                profile = Profile()
                profile.user = user
                profile.year = 2020 - int(email[0:4])
                profile.save()

        except KeyError as missing_key:
            message = "Google OAuth configured improperly on the client end. Required key: %s." % missing_key
            response =  Response({
               "detail": message,
               "idinfo": idinfo,
               "display_message": "Something went wrong. Please contact a DVM Official.",
            }, status=400)
            response.delete_cookie('sessionid')
            return response

    if user.profile.new_bitsian:
        new_bitsian = True
        user.profile.new_bitsian = False
    else:
        new_bitsian = False

    payload = {
    "JWT": get_jwt_with_user(user),
    "user_id": user.id,
    "name": user.first_name + ' ' + user.last_name,
    "email": user.email,
    "new_bitsian": new_bitsian,
    }
    if auth_mode == 2:
        payload["bitsian_id"] = profile.bits_id
    else:
        payload["bitsian_id"] = ""


    response =  Response(payload, status=200)
    response.delete_cookie('sessionid')
    return response



