from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("createListing", views.createListing, name="create-listing"),
    path("item/<int:item_id>", views.item, name="item"),
    path("update/<int:item_id>", views.edit, name="update"),
    path("delete/<int:item_id>", views.delete, name="delete"),
    path("watchlist/<int:user_id>", views.watchlist, name="watchlist"),
    path("closed/<int:item_id>", views.closed, name="closed"),
    path("closedItems", views.closeditems, name="closed-items"),
    path("category/<str:category>", views.category, name="category"),
    path("user/<str:name>", views.user, name="user"),
]
