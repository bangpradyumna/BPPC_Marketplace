from bookmp.views.auth import login, signup
from bookmp.views.trade import buy, sell
from bookmp.views import miscellaneous
from django.urls import include, path

urlpatterns = [

    path('auth/login/', login.login, name='login'),
    path('auth/signup/', signup.signup, name='signup'),
    path('auth/confirm_email/<str:unique_code>',
         miscellaneous.confirm_email, name="confirm_email"),

    path('sell/', sell.sell, name='sell'),

    path('SellerList/', buy.SellerList, name='SellerList'),
    path('SellerDetails/<int:seller_id>/',
         buy.SellerDetails, name='SellerDetails'),
    path('DetailsCollection/', miscellaneous.DetailsCollection,
         name='DetailsCollection'),

]
