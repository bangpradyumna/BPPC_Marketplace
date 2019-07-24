from google.oauth2 import id_token as googleIdToken
from google.auth.transport import requests as google_requests

from django.db import transaction, IntegrityError
from django.contrib.auth import authenticate
from django.shortcuts import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt # For the webapp on inaug day
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from BPPC_Marketplace import keyconfig


import re

from .models import (
    Profile,
    Seller,
    Image,
    Course,
    BookClass,
    BookInstance,
)

from .utils import (
    generate_random_password,
    get_jwt_with_user,
    HOSTELS,
    SINGLE_DEGREE_BRANCHES,
    DUAL_DEGREE_BRANCHES,
    BOYS_HOSTEL,
    GIRLS_HOSTEL,
)

from .email import send_confirmation_mail

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
    "bitsian_id": user.profile.bits_id,
    }


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
        if gender not in ['M','F']:
            message = "Not a valid gender ID"
            detail_message = "Gender entered is invalid."
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
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
        
        if not re.match(r'^2019[AB]\dPS\d\d\d\d[PT]$', bits_id):
            message = "Not a valid ID"
            detail_message = "ID doesn't comply with regex."
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
        
        if gender == 'M':
            if hostel in GIRLS_HOSTEL:
                message = "We wish boys were allowed in Meera but they aren't :("
                detail_message = "Hostel selected is not available for the entered gender."
                payload = {
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response
        else :
            if hostel in BOYS_HOSTEL:
                message = "We wish girls were allowed in Boys Hostels but they aren't :("
                detail_message = "Hostel selected is not available for the entered gender."
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
            unique_code = generate_random_password()  # Should change the name of this function I think.
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
                        room_no = room_no,
                        is_email_confirmed=False,
                        unique_code = unique_code
                    )
            try:
                confirmation_url = keyconfig.SERVER_ADDRESS + 'api/auth/confirm_email/' + str(unique_code)  # currently, SERVER_ADDRESS = localhost:8080
                send_confirmation_mail(email, confirmation_url)
                message = "Successfully registered the user. Please login to proceed!"
                detail_message = "SignUp was completed successfully!"
            except:
                message = "Error! Could not register the user"
                detail_message = "What the fuck, sendgrid?"
                user_profile.delete()  # Rolling back changes. Could've sent the email before these changes were
                user.delete()          # made, but then I can't unsend the email if the object creation fails.
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
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response


@transaction.atomic
@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def sell(request):
        
    user = request.user
    try:
        profile = user.profile
    except User.profile.RelatedObjectDoesNotExist:
        message = "Profile does not exist."
        detail_message = "Profile object for this user does not exist."
        payload = {
            "detail": detail_message,
            "display_message": message 
        }
        response =  Response(payload, status=400)
        return response

    if request.method == 'POST':
        
        seller, created = Seller.objects.get_or_create(profile=profile)
        
        if created:
            seller.profile = profile
        
        try:
            seller.details = request.data['details']
            seller.description = request.data['description']
            seller.price = int(request.data['price'])

            for tag in request.data['tags']:
                try:
                    tags = tags + '~' + str(tag)
                except:
                    tags = str(tag)

            seller.tags = tags # A single string of tags, separated by '~'.       
            seller.save()

            for Id in request.data['book_ids']:
                try:
                    book_class = BookClass.objects.get(id=int(Id))
                except BookClass.DoesNotExist:
                    message = "Not a valid book."
                    detail_message = "BookClass with id " + Id + " not found in database."
                    payload = {
                        "detail": detail_message,
                        "display_message": message 
                    }
                    response =  Response(payload, status=400)
                    return response
                
                try:
                    BookInstance.objects.get(seller=seller, book_class=book_class)
                except:
                    new_book_instance = BookInstance()
                    new_book_instance.book_class = book_class
                    new_book_instance.seller = seller
                    new_book_instance.save()
    
                    with transaction.atomic(): # Delete old images to avoid duplicates.
                        
                        images = Image.objects.filter(seller=seller)
                        for image in images:
                            image.delete()
                            # The actual image file is deleted using signals.
                            # SEE: models.auto_delete_file_on_delete()

                        for filename, file in request.FILES.items():
                            # Adding the new images.
                            image_object = Image()
                            image_object.seller = seller
                            img = request.FILES[filename]
                            image_object.img = img
                            image_object.save()
                            
                    
            message = "Submitted successfully!"
            detail_message = "Success."
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
                    "detail": detail_message,
                    "display_message": message 
                }
                response =  Response(payload, status=400)
                return response

    elif request.method == 'GET':

        if profile.year == 1:
            message = "2019 batch is not allowed to access the sell page."
            detail_message = "The 'year' field for this user is set to 1."
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response

        try:
            seller = profile.seller
            payload = {
                "details":seller.details,
                "description":seller.description,
                "price":str(seller.price),
            }
            
            # Adding the list of tags.
            payload['tags'] = seller.tags.split('~')

            # Adding the image urls.
            images = Image.objects.get(seller=seller)
            payload['images'] = []
            for image in images:
                img_dict = {}
                img_dict['url'] = image.img.url
                payload['images'].append(img_dict)

        except:
            payload = {
                "details":"",
                "description":"",
                "tags":"",
                "price":"",
                "images":[]  
            }

        try:
            branches = [profile.single_branch]
            if profile.is_dual_degree:
                branches.append(profile.dual_branch)
        except:
            message = "Invalid branch details"
            detail_message = "This user has invalid branch details."
            payload = {
                "detail": detail_message,
                "display_message": message 
            }
            response =  Response(payload, status=400)
            return response
        
        if profile.year == 2:
            courses = Course.objects.filter(year=profile.year-1)
        elif profile.year > 2:    
            courses = Course.objects.filter(year=profile.year-1, branch__in=branches)
        
        payload['books'] = [] # A list of books, inside every course_dict.
                        
        for course in courses:

            books = course.books.all()
            
            for book in books:
                book_dict = {} # Similar to courses, each book is a dict.
                book_dict['name'] = book.name
                book_dict['id'] = book.id
                book_dict['category'] = course.name
                payload['books'].append(book_dict)

        try:
            selected_books = BookInstance.objects.filter(seller=seller)
            payload['selected_books'] = []

            for book in selected_books:
                book_dict = {}
                book_dict['id'] = str(book.book_class.id)
                payload['selected_books'].append(book_dict)
        except:
            payload['selected_books'] = []
    
        response =  Response(payload, status=200)
        return response
    

def confirm_email(request, unique_code):
    target_user = Profile.objects.get(unique_code=unique_code)  
    target_user.is_email_confirmed = True
    target_user.unique_code = "confirm"   # Just reducing the chances of a unique_code collision even more
    target_user.save()
    return HttpResponse("Email verification successful") # Replace with a nice template or something later.
