from . import views
from django.urls import include, path


urlpatterns=[
    path('auth/login/', views.login, name='login'),   
    path('auth/signup/', views.signup, name='signup'),

    path('sell/', views.sell, name='sell'),
    path('SellerList/', views.SellerList, name='SellerList'),

]    
