from google.oauth2 import id_token as googleIdToken
from google.auth.transport import requests as google_requests

from django.db import transaction, IntegrityError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt # For the webapp on inaug day
from rest_framework.response import Response
from rest_framework.decorators import api_view

import re

from .models import Profile
from .utils import generate_random_password, get_jwt_with_user, HOSTELS, SINGLE_DEGREE_BRANCHES, DUAL_DEGREE_BRANCHES

CURRENT_YEAR = 2019

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
        else:
            # Create profile if it doesn't exist.
            try: 
                profile = user.profile
            except:
                profile = Profile()
                profile.user = user
                profile.year = 1
                profile.new_bitsian = False
                profile.save()
            
    elif auth_mode == 2:
        try:
            try:
                idinfo = googleIdToken.verify_oauth2_token(id_token, google_requests.Request())
            except Exception as e:
                message = str(e)
                payload = {
                    "detail": message,
                    "display_message": "Something went wrong. Please try again." 
                }
                response =  Response(payload, status=403)
                response.delete_cookie('sessionid')
                return response

            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                message = "Not a valid Google account."
                payload = {
                    "detail": message,
                    "display_message": message 
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
                    "display_message": message 
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
                profile.year = CURRENT_YEAR - int(email[1:5]) + 1 # CURRENT_YEAR variable must be be set on the top of this file. 
                profile.save()

            try:
                profile = user.profile
            except:
                profile = Profile()
                profile.user = user
                profile.year = CURRENT_YEAR - int(email[1:5]) + 1 # CURRENT_YEAR variable must be be set on the top of this file. 
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
        new_bitsian = True # Copying variable for sending api response
        user.profile.new_bitsian = False
        user.profile.save()
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


@csrf_exempt
@api_view(['POST'])
def signup(request):
    try:
        name = str(request.data["name"]) 
        first_name = name.split(' ', 1)[0]
        try: 
            last_name = name.split(' ', 1)[1]
        except IndexError:
            last_name = ''
        
        gender = str(request.data["gender"])
        username = str(request.data["username"])
        password = str(request.data["password"])    
        email = str(request.data["email"]) 
        if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
            message = "Not a valid email."
            detail_message = "Email doesn't comply with regex."
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response

        phone = int(request.data["phone"])
        bits_id = str(request.data["bits_id"]) 
        if int(bits_id[0:4])!=2019:
            message = "Your BITS ID can start only with '2019'"
            detail_message = "The bits_id started with %d instead of '2019'" % int(bits_id[0:4])
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response =  Response(payload, status=400)
            return response
        possible_duplicate_profiles = Profile.objects.filter(bits_id = bits_id)
        if possible_duplicate_profiles.exists():
            message = "This BITS ID already exists"
            detail_message = "bits_id supplied was already found in the database"
            payload = {
                "detail": detail_message ,
                "display_message": message
            }
            response =  Response(payload, status=400)
            return response


        hostel = str(request.data["hostel"])
        if hostel not in HOSTELS:  
            message = "Hostel name is not valid."
            detail_message = "Hostel name supplied wasn't found in the database. Refer API docs for more info."
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response
        
        room_no = int(request.data["room_no"])
        is_dual_degree = bool(request.data["is_dual_degree"])
        if is_dual_degree:
            dual_branch = str(request.data["dual_branch"])
            if dual_branch not in DUAL_DEGREE_BRANCHES:
                message = "Not a valid Dual Degree Branch code."
                detail_message = "Dual Degree Branch supplied wasn't found in the database. Refer API docs for more info."
                payload = {
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response

            if dual_branch != bits_id[4:6]:
                message = "Entered branch doesn't match with the ID."
                detail_message = "Dual Degree Branch supplied was different from the one parsed using BITS ID."
                payload = {
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response
            single_branch = None
        else:
            single_branch = str(request.data["single_branch"])
            if single_branch not in SINGLE_DEGREE_BRANCHES:
                message = "Not a valid Single Degree Branch code."
                detail_message = "Single Degree Branch supplied wasn't found in the database. Refer API docs for more info."
                payload = {
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response
            
            if single_branch != bits_id[4:6]:
                message = "Entered branch doesn't match with the ID."
                detail_message = "Single Degree Branch supplied was different from the one parsed using BITS ID."
                payload = {
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response

            dual_branch = None

        with transaction.atomic(): # Use atomic transactions to create User and Profile instances for each registration.
            user = User.objects.create_user( # TODO: Catch Exceptions due to this command
                        username,
                        email,
                        password
                    )
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            user_profile = Profile.objects.create( # TODO: Catch Exceptions due to this command like user profile for this name etc already exist
                        user = user,
                        gender = gender,
                        bits_id = bits_id,
                        year = 1,
                        is_dual_degree = is_dual_degree,
                        single_branch = single_branch,
                        dual_branch = dual_branch,
                        new_bitsian = None,
                        hostel = hostel,
                        room_no = room_no
                    )
            message = "Successfully registered the user. Please login to proceed!"
            detail_message = "SignUp was completed successfully!"
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=200)
            return response

    except KeyError as missing_key:
            message = "Missing key: %s" % missing_key
            detail_message = "The key: %s is missing in the request. Refer API docs for more info." % missing_key
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response
    except IntegrityError as e: # Shows that a particular field already exists.
            message = "Field specified already exists: %s" % e.__cause__
            detail_message = "%s: This means that one of the fields that you supplied already exists in a database. Refer API docs for more info." % e.__cause__
            payload = {
                "detail": message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response


        
        
        