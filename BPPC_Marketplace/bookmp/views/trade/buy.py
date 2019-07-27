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

CURRENT_YEAR = 2019


@csrf_exempt
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def SellerList(request):

    user = request.user

    try:
        profile = user.profile
        year = profile.year
        single_branch = profile.single_branch
        dual_branch = profile.dual_branch

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

    # No check for is_dual_degree as the values will match nonetheless (None).
    seniors_same_branch = Seller.objects.filter(profile__year=year+1,
                                                profile__single_branch=single_branch,
                                                profile__dual_branch=dual_branch,
                                                is_listed=True)

    # Number of books in the seller's year and branch(es).
    book_count_total = BookClass.objects.filter(course__branch__in=[single_branch, dual_branch],
                                                course__year=year).count()

    payload = {}
    payload['sellers'] = []
    for seller in seniors_same_branch:
        seller_dict = {}
        seller_dict['id'] = seller.id

        name = seller.profile.user.first_name + ' ' + seller.profile.user.last_name
        seller_dict['name'] = name

        seller_dict['tags'] = seller.tags.split('~')
        seller_dict['price'] = seller.price

        book_count = BookInstance.objects.filter(seller=seller).count()
        seller_dict['no_of_books'] = str(
            book_count) + '/' + str(book_count_total)

        payload['sellers'].append(seller_dict)

    # Add seniors of different branch if the buyer is a 1st yearite.
    if profile.year == 1:
        seniors_different_branch = Seller.objects.filter(is_listed=True,
                                                         profile__year=year+1).exclude(profile__single_branch=single_branch,
                                                                                       profile__dual_branch=dual_branch)
        for seller in seniors_different_branch:
            seller_dict = {}
            seller_dict['id'] = seller.id

            name = seller.profile.user.first_name + ' ' + seller.profile.user.last_name
            seller_dict['name'] = name

            seller_dict['tags'] = seller.tags.split('~')
            seller_dict['price'] = seller.price

            book_count = BookInstance.objects.filter(seller=seller).count()
            seller_dict['no_of_books'] = str(
                book_count) + '/' + str(book_count_total)

            payload['sellers'].append(seller_dict)

    response = Response(payload, status=200)
    response.delete_cookie('sessionid')
    return response


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET'])
def SellerDetails(request, seller_id):
    try:
        seller = Seller.objects.get(id=seller_id)
    except:
        message = "Invalid Seller ID."
        detail_message = "Seller with this ID does not exist."
        payload = {
            "detail": detail_message,
            "display_message": message
        }
        response = Response(payload, status=400)
        response.delete_cookie('sessionid')
        return response

    if not seller.is_listed:
        message = "This seller is currently not available."
        detail_message = "Seller is currently un-listed."
        payload = {
            "detail": detail_message,
            "display_message": message
        }
        response = Response(payload, status=400)
        response.delete_cookie('sessionid')
        return response

    payload = {
        "description": seller.description,
        "details": seller.details,
        "tags": seller.tags.split('~')
    }

    books = BookInstance.objects.filter(seller=seller)
    # List of books.
    payload['books'] = []
    for book in books:
        payload['books'].append(book.book_class.name)

    # Adding the image urls.
    images = Image.objects.get(seller=seller)
    payload['images'] = []
    for image in images:
        payload['images'].append(image.img.url)

    response = Response(payload, status=200)
    response.delete_cookie('sessionid')
    return response
