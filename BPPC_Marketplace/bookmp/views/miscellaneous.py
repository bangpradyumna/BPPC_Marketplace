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

from bookmp.models import BookClass, BookInstance, Course, Image, Profile, Seller
from bookmp.utils import (BOYS_HOSTEL, DUAL_DEGREE_BRANCHES, GIRLS_HOSTEL, HOSTELS,
                          SINGLE_DEGREE_BRANCHES, generate_random_password,
                          get_jwt_with_user)


@csrf_exempt
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def DetailsCollection(request):
    """
    To get additional details from Bitsians after
    they login using Google.
    """
    user = request.user

    try:
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

        phone = int(request.data["phone"])
        bits_id = str(request.data["bits_id"])
        if int(bits_id[0:4]) == 2019:
            message = "Your BITS ID cannot start with '2019'"
            detail_message = "The bits_id started with '2019'"
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            return response

        if not re.match(r'^20\d\d[AB]\dPS\d\d\d\d[PT]$', bits_id):
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

        with transaction.atomic():

            profile = user.profile
            profile.gender = gender
            profile.bits_id = bits_id
            profile.is_dual_degree = is_dual_degree
            profile.single_branch = single_branch
            profile.dual_branch = dual_branch
            profile.new_bitsian = False
            profile.hostel = hostel
            profile.room_no = room_no
            profile.save()

            message = "Details submitted succesfully!"
            detail_message = "Details submitted succesfully!"
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=200)
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


def confirm_email(request, unique_code):
    target_user = Profile.objects.get(unique_code=unique_code)
    target_user.is_email_confirmed = True
    # Just reducing the chances of a unique_code collision even more
    target_user.unique_code = "confirm"
    target_user.save()
    # Replace with a nice template or something later.
    return HttpResponse('Email verification successful. Please go here to login: <a href="https://market.bits-dvm.org/login">https://market.bits-dvm.org/login</a>')
