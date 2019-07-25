from . import views
from django.urls import include, path


urlpatterns=[
    
    path('auth/login/', views.login, name='login'),   
    path('auth/signup/', views.signup, name='signup'),
    path('auth/confirm_email/<str:unique_code>', views.confirm_email, name="confirm_email"),

    path('sell/', views.sell, name='sell'),
    path('SellerList/', views.SellerList, name='SellerList'),
    path('SellerDetails/<int:seller_id>/', views.SellerDetails, name='SellerDetails'),

]    
