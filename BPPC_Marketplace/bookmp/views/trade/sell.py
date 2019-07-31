import re
import os

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as googleIdToken
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from bookmp.models import BookClass, BookInstance, Course, Image, Profile, Seller
from bookmp.utils import (BOYS_HOSTEL, DUAL_DEGREE_BRANCHES, GIRLS_HOSTEL, HOSTELS,
                          SINGLE_DEGREE_BRANCHES, generate_random_password,
                          get_jwt_with_user)

from bookmp.decorators import disallow_unconfirmed_email_users

CURRENT_YEAR = 2019
DOMAIN_NAME = 'https://market.bits-dvm.org'

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
@disallow_unconfirmed_email_users
@parser_classes([JSONParser, FormParser, MultiPartParser]) # For image uploads.
@transaction.atomic
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
        response = Response(payload, status=400)
        response.delete_cookie('sessionid')
        return response

    if profile.year == 1:
        message = "2019 batch is not allowed to access the sell page."
        detail_message = "The 'year' field for this user is set to 1."
        payload = {
            "detail": detail_message,
            "display_message": message
        }
        response = Response(payload, status=400)
        response.delete_cookie('sessionid')
        return response

    if request.method == 'POST':

        seller, created = Seller.objects.get_or_create(profile=profile)

        if created:
            seller.profile = profile

        try:
            seller.details = request.data['details']
            seller.description = request.data['description']
            seller.price = int(request.data['price'])

            if not request.data['tags']: 
                # If there is no tag.
                tags = ''
            else:    
                for tag in request.data['tags']:
                    try:
                        tags = tags + '~' + str(tag)
                    except:
                        tags = str(tag)

            seller.tags = tags  # A single string of tags, separated by '~'.
            seller.save()

            # Previously selected books.
            old_books = BookInstance.objects.filter(seller=seller)

            # From the old books, remove the ones not selected anymore.
            for book in old_books:
                if not str(book.book_class.id) in request.data['book_ids']:
                    book.delete() 

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
                    response = Response(payload, status=400)
                    response.delete_cookie('sessionid')
                    return response

                try:
                    BookInstance.objects.get(
                        seller=seller, book_class=book_class)
                except:
                    new_book_instance = BookInstance()
                    new_book_instance.book_class = book_class
                    new_book_instance.seller = seller
                    new_book_instance.save()

            with transaction.atomic():  # Delete images that the user removed.
                
                deleted_ids=[]
                for Id in request.data['deleted_image_ids']:
                    deleted_ids.append(int(Id))

                images = Image.objects.filter(id__in=deleted_ids)
                for image in images:
                    image.delete()
                    # The actual image file is deleted using signals.
                    # SEE: models.auto_delete_file_on_delete()

                # for filename, file in request.FILES.items():
                #     # Adding the new images.
                #     image_object = Image()
                #     image_object.seller = seller
                #     img = request.FILES[filename]
                #     image_object.img = img
                #     image_object.save()

                # Adding the new images.  
                request_string = 'images-1'
                current_image = request.FILES.get(request_string)
                print(request.FILES)
                image_object = Image()
                image_object.seller = seller
                image_object.img = current_image
                image_object.save()

                # for image in request.data['images']:
                #     image_object = Image()
                #     image_object.seller = seller
                #     image_object.img = image
                #     image_object.save()

            message = "Submitted successfully!"
            detail_message = "Success."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=200)
            response.delete_cookie('sessionid')
            return response

        except KeyError as missing_key:
            message = "Missing key: %s" % missing_key
            detail_message = "The key: %s is missing in the request. Refer API docs for more info." % missing_key
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            response.delete_cookie('sessionid')
            return response

        except IntegrityError as e:  # Shows that a particular field already exists.
            message = "Field specified already exists: %s" % e.__cause__
            detail_message = "%s: This means that one of the fields that you supplied already exists in a database. Refer API docs for more info." % e.__cause__
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            response.delete_cookie('sessionid')
            return response

    elif request.method == 'GET':

        try:
            seller = profile.seller
            payload = {
                "details": seller.details,
                "description": seller.description,
                "price": str(seller.price),
            }

            # Adding the list of tags.
            if seller.tags == '':
                payload['tags'] = []
            else:    
                payload['tags'] = seller.tags.split('~')

            # Adding the image urls.
            images = Image.objects.filter(seller=seller)
            payload['images'] = []
            for image in images:
                img_dict = {}
                img_dict['url'] = DOMAIN_NAME + image.img.url
                img_dict['name'] = os.path.basename(image.img.name) # Name of the file
                img_dict['id'] = image.id
                payload['images'].append(img_dict)


        except Seller.DoesNotExist:
            payload = {
                "details": "",
                "description": "",
                "tags": [],
                "price": "",
                "images": []
            }

        try:
            year = profile.year
            
            # Three types of courses: 
            # 1 - Courses for all branches.
            # 2 - Courses for single branches(B.E.)
            # 3 - Courses for dual branches(M.Sc.) 
            
            course_types = []
            
            # Add courses that are for all branches.
            all_branch_courses = Course.objects.filter(year=year-1, branch='ALL')
            course_types.append(all_branch_courses)

            # Add courses for dual branches.
            if profile.is_dual_degree:
                dual_courses = Course.objects.filter(year=year-1, branch=profile.dual_branch)
                course_types.append(dual_courses)
                
                # Add single branch courses for dualites.
                # 'year-2' because dualites have single degree courses a year late.
                if not profile.single_branch is None:
                    single_courses = Course.objects.filter(year=year-2, branch=profile.single_branch)
                    course_types.append(single_courses)
            
            # Add courses for non-dualites.
            else:
                if not profile.single_branch is None:
                    single_courses = Course.objects.filter(year=year-1, branch=profile.single_branch)
                    course_types.append(single_courses)
                else:
                    message = "Error: No branch specified."
                    detail_message = "This niether has a single_branch nor any dual_branch."
                    payload = {
                        "detail": detail_message,
                        "display_message": message
                    }
                    response = Response(payload, status=400)
                    response.delete_cookie('sessionid')
                    return response


        except:
            message = "Error in fetching courses for you."
            detail_message = "An error occured while fetching courses for this user."
            payload = {
                "detail": detail_message,
                "display_message": message
            }
            response = Response(payload, status=400)
            response.delete_cookie('sessionid')
            return response

        payload['books'] = []  # A list of books, inside every course_dict.

        for course_type in course_types:
            
            for course in course_type:

                books = course.books.all()

                for book in books:
                    book_dict = {}  # Each book is a dict.
                    book_dict['title'] = book.name
                    book_dict['id'] = book.id
                    book_dict['category'] = course.name
                    payload['books'].append(book_dict)

        try:
            selected_books = BookInstance.objects.filter(seller=seller)
            payload['selected_books'] = []

            for book in selected_books:
                book_dict = {}
                book_dict['id'] = str(book.book_class.id)
                book_dict['title'] = book.book_class.name
                book_dict['category'] = book.book_class.course.name
                payload['selected_books'].append(book_dict)
        except:
            payload['selected_books'] = []

        response = Response(payload, status=200)
        response.delete_cookie('sessionid')
        return response
