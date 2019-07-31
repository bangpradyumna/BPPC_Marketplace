import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as googleIdToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from BPPC_Marketplace import keyconfig

from bookmp.models import BookClass, BookInstance, Course, Image, Profile, Seller
from bookmp.email import send_confirmation_mail
from bookmp.utils import (BOYS_HOSTEL, DUAL_DEGREE_BRANCHES, GIRLS_HOSTEL, HOSTELS,
                          SINGLE_DEGREE_BRANCHES, generate_random_password,
                          get_jwt_with_user)

CURRENT_YEAR = 2019


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
        if gender not in ['M', 'F']:
            message = "Not a valid gender ID"
            detail_message = "Gender entered is invalid."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

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
            response = Response(payload, status=400)
            return response

        phone = int(request.data["phone"])
        if not len(request.data["phone"]) == 10:
            message = "Invalid phone number."
            detail_message = "Phone number should be of length 10."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        bits_id = str(request.data["bits_id"])
        if int(bits_id[0:4]) != 2019:
            message = "Your BITS ID can start only with '2019'"
            detail_message = "The bits_id started with %d instead of '2019'" % int(
                bits_id[0:4])
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        if not re.match(r'^2019[AB]\dPS\d\d\d\d[PT]$', bits_id):
            message = "Not a valid ID"
            detail_message = "ID doesn't comply with regex."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        possible_duplicate_profiles = Profile.objects.filter(bits_id=bits_id)
        if possible_duplicate_profiles.exists():
            message = "This BITS ID already exists"
            detail_message = "bits_id supplied was already found in the database"
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        hostel = str(request.data["hostel"])
        if hostel not in HOSTELS:
            message = "Hostel name is not valid."
            detail_message = "Hostel name supplied wasn't found in the database. Refer API docs for more info."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        if gender == 'M':
            if hostel in GIRLS_HOSTEL:
                message = "We wish boys were allowed in Meera but they aren't :("
                detail_message = "Hostel selected is not available for the entered gender."
                payload = {
                    "detail": detail_message,
                    "display_message": message
                }
                response = Response(payload, status=400)
                return response
        else:
            if hostel in BOYS_HOSTEL:
                message = "We wish girls were allowed in Boys Hostels but they aren't :("
                detail_message = "Hostel selected is not available for the entered gender."
                payload = {
                    "detail": detail_message,
                    "display_message": message
                }
                response = Response(payload, status=400)
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
                response = Response(payload, status=400)
                return response

            if dual_branch != bits_id[4:6]:
                message = "Entered branch doesn't match with the ID."
                detail_message = "Dual Degree Branch supplied was different from the one parsed using BITS ID."
                payload = {
                    "detail": detail_message,
                    "display_message": message
                }
                response = Response(payload, status=400)
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
                response = Response(payload, status=400)
                return response

            if single_branch != bits_id[4:6]:
                message = "Entered branch doesn't match with the ID."
                detail_message = "Single Degree Branch supplied was different from the one parsed using BITS ID."
                payload = {
                    "detail": detail_message,
                    "display_message": message
                }
                response = Response(payload, status=400)
                return response
            dual_branch = None

        # Use atomic transactions to create User and Profile instances for each registration.
        with transaction.atomic():
            user = User.objects.create_user(  # TODO: Catch Exceptions due to this command
                username,
                email,
                password
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            unique_code = generate_random_password()
            user_profile = Profile.objects.create(  # TODO: Catch Exceptions due to this command like user profile for this name etc already exist
                user=user,
                gender=gender,
                bits_id=bits_id,
                year=1,
                is_dual_degree=is_dual_degree,
                single_branch=single_branch,
                dual_branch=dual_branch,
                new_bitsian=None,
                hostel=hostel,
                room_no=room_no,
                is_email_confirmed=False,
                unique_code=unique_code,
                phone = phone
            )
            signup_completion_status = 200
            try:
                confirmation_url = keyconfig.SERVER_ADDRESS + '/api/auth/confirm_email/' + \
                    str(unique_code)
                send_confirmation_mail(email, confirmation_url)
                message = "We've sent a verification link to your email: %s, Please click on it to complete the registration. NOTE: Please check your spam folder if you haven't recieved it." % email
                detail_message = "SignUp was completed successfully, Email verification is pending!"

            except:
                message = "Error! Could not register the user. Problem with sending email."
                detail_message = "Email verification could not be sent to the email: %s" % email
                # Rolling back changes. Could've sent the email before these changes were
                # made, but then I can't unsend the email if the object creation fails.
                user.delete()
                signup_completion_status = 400
                try:
                    user_profile.delete()
                except Profile.DoesNotExist:
                    pass

            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=signup_completion_status)
            return response

    except KeyError as missing_key:
        message = "Missing key: %s" % missing_key
        detail_message = "The key: %s is missing in the request. Refer API docs for more info." % missing_key
        payload = {
            "detail": detail_message,
            "display_message": message
        }
        response = Response(payload, status=400)
        return response
    except IntegrityError as e:  # Shows that a particular field already exists.
        message = "Field specified already exists: %s" % e.__cause__
        detail_message = "%s: This means that one of the fields that you supplied already exists in a database. Refer API docs for more info." % e.__cause__
        payload = {
            "detail": detail_message,
            "display_message": message
        }
        response = Response(payload, status=400)
        return response
