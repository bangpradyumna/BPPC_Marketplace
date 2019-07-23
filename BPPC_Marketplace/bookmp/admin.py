from django.contrib import admin

from .models import Profile, BookInstance, BookClass, Course, Image, Seller


# Register your models here.
admin.site.register(Profile)
admin.site.register(BookInstance)
admin.site.register(BookClass)
admin.site.register(Course)
admin.site.register(Image)
admin.site.register(Seller)
