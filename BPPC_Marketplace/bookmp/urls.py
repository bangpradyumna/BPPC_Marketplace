from . import views
from django.urls import include, path


urlpatterns=[
    path('auth/login/', views.login, name='login'),   
    path('auth/signup/', views.signup, name='signup'),   

]    
