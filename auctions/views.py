from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, OperationalError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms
from .models import *
from datetime import datetime
from django.contrib import messages


class NewListingItem(forms.Form):

    title = forms.CharField(label="Title", widget=forms.TextInput(attrs={'style': "width:100%;"}), required=True)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'style': "width:100%;"}), required=True)
    url = forms.URLField(label="Photo URL(optional)", widget=forms.TextInput(attrs={'style': "width:100%;"}), required=False)
    # Getting all categories
    categories = [("pistols", "PISTOLS"), ("submachine", "SUBMACHINE GUNS"), ("rifles", "RIFLES"), ("sniper", "SNIPER")]
    category = forms.CharField(label="Select the category", widget=forms.Select(choices=categories), required=True)
    price = forms.IntegerField(label="Start price", required=True, widget=forms.TextInput(), min_value=0)


class CommentForm(forms.Form):
    comment = forms.CharField(label="Write a comment", widget=forms.Textarea(attrs={'style': "width:100%;"}), required=True, max_length=5000)


def index(request):
    return render(request, "auctions/index.html", {
        "items": Item.objects.filter(status = True)
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def createListing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    else:
        if request.method == "POST":
            form = NewListingItem(request.POST)
            if form.is_valid():
                # Current time
                now = datetime.now()
                time = now.strftime("%d/%m/%Y %H:%M:%S")
                # Adding new item in listing
                new_item = Item(title=form.cleaned_data["title"], description=form.cleaned_data["description"], photo=form.cleaned_data["url"], time=time, user=request.user, price=form.cleaned_data["price"], status=True, category=form.cleaned_data["category"])
                new_item.save()
                return render(request, "auctions/index.html", {
                    "items": Item.objects.all()
                })
            else:
                return render(request, "auctions/create-listing.html", {
                "form": NewListingItem(request.POST),
                "add": True
            })
        
        else:
            return render(request, "auctions/create-listing.html", {
                "form": NewListingItem(),
                "add": True
            })


def item(request, item_id):
    item = Item.objects.get(pk=item_id)

    if not request.user.is_authenticated:
        return render (request, "auctions/item.html", {
        "item": item,
        "bid": False,
        "edit_and_delete": False,
        "watchlist": False
    })

    else:
        if request.user == item.user:
            bid_input = False
            edit_and_delete = True
            watchlist = False
            close_item = True
        else:
            bid_input = True
            edit_and_delete = False
            watchlist = True
            close_item = False
        if request.method == "POST":

            # BID POST
            if "bid_value" in request.POST:
                current_user = request.user

                try: 
                    check_watchlist = Watchlist.objects.get(item=Item.objects.get(pk=item_id), user=User(pk=current_user.id))
                    if check_watchlist:
                        watch = False
                    else:
                        watch = True
                except Watchlist.DoesNotExist:
                    watch = True

                try:
                    is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    number_of_bids = is_there_any_bid.count()
                except Bid.DoesNotExist:
                    number_of_bids = 0

                is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                if is_there_any_bid:
                    number_of_bids = is_there_any_bid.count()
                    last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    last_object_price =last_object.last().price
                    # Value of the last price
                    if last_object_price < int(request.POST["price"]):
                        new_bid = Bid(item=Item(pk=item_id), user=User(pk=current_user.id), price=request.POST["price"])
                        new_bid.save()
                        bid_message = True
                        bid_alert = None
                        n = 1
                    else:
                        bid_alert = True
                        bid_message = None
                        n = 0

                    last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    last_object_price =last_object.last().price

                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        if request.user == last_object.last().user:
                            bid_user_current = True
                    except AttributeError:
                        bid_user_current = False
                    
                    try:
                        comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
                    except Comments.DoesNotExist:
                        comments = None

                    return render (request, "auctions/item.html", {
                        "item": item,
                        "bid": bid_input,
                        "edit_and_delete": edit_and_delete,
                        "watchlist": watchlist,
                        "watch": watch,
                        "bid_message": bid_message,
                        "number_of_bids": number_of_bids + n,
                        "bid_alert": bid_alert,
                        "last_price": last_object_price,
                        "bid_user_current": bid_user_current,
                        "comment_form": CommentForm(),
                        "all_comments": comments,
                        "comment_alert": False,
                        "close": close_item,
                        })
                else:
                    if item.price < int(request.POST["price"]):
                        new_bid = Bid(item=Item(pk=item_id), user=User(pk=current_user.id), price=request.POST["price"])
                        new_bid.save()
                        bid_message = True
                        bid_alert = None
                        n = 1
                    else:
                        bid_alert = True
                        bid_message = None
                        n = 0

                    last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    last_object_price =last_object.last().price

                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        if request.user == last_object.last().user:
                            bid_user_current = True
                    except AttributeError:
                        bid_user_current = False
                    
                    try:
                        comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
                    except Comments.DoesNotExist:
                        comments = None

                    return render (request, "auctions/item.html", {
                        "item": item,
                        "bid": bid_input,
                        "edit_and_delete": edit_and_delete,
                        "watchlist": watchlist,
                        "watch": watch,
                        "bid_message": bid_message,
                        "number_of_bids": number_of_bids + n ,
                        "bid_alert": bid_alert,
                        "last_price": last_object_price,
                        "comment_form": CommentForm(),
                        "all_comments": comments,
                        "comment_alert": False,
                        "close": close_item,
                        })

                
            # WATHCLIST POST
            if "watchlist" in request.POST:
                if request.POST["watch"] == '1':
                    try:
                        is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        number_of_bids = is_there_any_bid.count()
                    except Bid.DoesNotExist:
                        number_of_bids = 0
                    
                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        last_object_price =last_object.last().price
                    except AttributeError:
                        last_object_price = None
                    
                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        if request.user == last_object.last().user:
                            bid_user_current = True
                        else:
                            bid_user_current = False
                    except AttributeError:
                        bid_user_current = False
                    
                    try:
                        comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
                    except Comments.DoesNotExist:
                        comments = None

                    current_user = request.user
                    add_to_watchlist = Watchlist(item=Item(pk=item_id), user=User(pk=current_user.id), watch=True)
                    add_to_watchlist.save()
                    return render (request, "auctions/item.html", {
                    "item": item,
                    "bid": bid_input,
                    "edit_and_delete": edit_and_delete,
                    "watchlist": watchlist,
                    "watch": False,
                    "number_of_bids": number_of_bids,
                    "last_price": last_object_price,
                    "bid_user_current": bid_user_current,
                    "comment_form": CommentForm(),
                    "all_comments": comments,
                    "comment_alert": False,
                    "close": close_item,
                })
                else:
                    try:
                        is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        number_of_bids = is_there_any_bid.count()
                    except Bid.DoesNotExist:
                        number_of_bids = 0

                    try:
                        is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        number_of_bids = is_there_any_bid.count()

                    except Bid.DoesNotExist:
                        number_of_bids = 0

                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        last_object_price =last_object.last().price
                    except AttributeError:
                        last_object_price = None

                    try:
                        last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                        if request.user == last_object.last().user:
                            bid_user_current = True
                        else:
                            bid_user_current = False
                    except AttributeError:
                        bid_user_current = False

                    try:
                        comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
                    except Comments.DoesNotExist:
                        comments = None


                    current_user = request.user
                    remove_watchlist = Watchlist.objects.filter(item=Item.objects.get(pk=item_id), user=User(pk=current_user.id))
                    remove_watchlist.delete()
                    return render (request, "auctions/item.html", {
                    "item": item,
                    "bid": bid_input,
                    "edit_and_delete": edit_and_delete,
                    "watchlist": True,
                    "watch": True,
                    "number_of_bids": number_of_bids,
                    "last_price": last_object_price,
                    "bid_user_current": bid_user_current,
                    "comment_form": CommentForm(),
                    "all_comments": comments,
                    "comment_alert": False,
                    "close": close_item,
                })


            # COMMENT POST
            if "comment" in request.POST: 
                form = CommentForm(request.POST)
                if form.is_valid():
                    current_user = request.user
                    comment = form.cleaned_data["comment"]
                    new_comment = Comments(item=Item.objects.get(pk=item_id), user=User.objects.get(pk = current_user.id), comment = comment)
                    new_comment.save()
                    comment_alert = False
                else:
                    comment_alert = True

                try: 
                    check_watchlist = Watchlist.objects.filter(item=Item.objects.get(pk=item_id), user=User(pk=current_user.id))
                    if check_watchlist:
                        watch = False
                    else:
                        watch = True

                except Watchlist.DoesNotExist:
                    watch = True
                
                try:
                    is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    number_of_bids = is_there_any_bid.count()

                except Bid.DoesNotExist:
                    number_of_bids = 0
                    last_object_price = None

                try: 
                    last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    last_object_price =last_object.last().price
                
                except AttributeError:
                    last_object_price = item.price
                
                try:
                    last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                    if request.user == last_object.last().user:
                        bid_user_current = True
                    else:
                        bid_user_current = False
                except AttributeError:
                    bid_user_current = False
                
                try:
                    comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
                except Comments.DoesNotExist:
                    comments = None

                return render (request, "auctions/item.html", {
                                "item": item,
                                "bid": bid_input,
                                "edit_and_delete": edit_and_delete,
                                "watchlist": watchlist,
                                "watch": watch,
                                "number_of_bids": number_of_bids,
                                "last_price": last_object_price,
                                "bid_user_current": bid_user_current,
                                "comment_form": CommentForm(),
                                "all_comments": comments,
                                "comment_alert": comment_alert,
                                "close": close_item,
                            })
                


        else:
            current_user = request.user

            try: 

                check_watchlist = Watchlist.objects.filter(item=Item.objects.get(pk=item_id), user=User(pk=current_user.id))
                if check_watchlist:
                    watch = False
                else:
                    watch = True

            except Watchlist.DoesNotExist:
                watch = True
            
            try:
                is_there_any_bid = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                number_of_bids = is_there_any_bid.count()

            except Bid.DoesNotExist:
                number_of_bids = 0
                last_object_price = None

            try: 
                last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                last_object_price =last_object.last().price
            
            except AttributeError:
                last_object_price = item.price
            
            try:
                last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
                if request.user == last_object.last().user:
                    bid_user_current = True
                else:
                    bid_user_current = False
            except AttributeError:
                bid_user_current = False
            
            try:
                comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
            except Comments.DoesNotExist:
                comments = None

            return render (request, "auctions/item.html", {
                            "item": item,
                            "bid": bid_input,
                            "edit_and_delete": edit_and_delete,
                            "watchlist": watchlist,
                            "watch": watch,
                            "number_of_bids": number_of_bids,
                            "last_price": last_object_price,
                            "bid_user_current": bid_user_current,
                            "comment_form": CommentForm(),
                            "all_comments": comments,
                            "comment_alert": False,
                            "close": close_item,
                        })


def edit(request, item_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    else:
        item = Item.objects.get(pk=item_id)
        if request.method == "POST":
            form = NewListingItem(request.POST)
            if form.is_valid():
                item.title = form.cleaned_data["title"]
                item.description = form.cleaned_data["description"]
                item.photo = form.cleaned_data["url"]
                now = datetime.now()
                time = now.strftime("%d/%m/%Y %H:%M:%S")
                item.time = time
                item.price = form.cleaned_data["price"]
                item.category = form.cleaned_data["category"]
                item.save()
                return render(request, "auctions/index.html", {
                    "items": Item.objects.all()
                })
            else:
                return render (request, "auctions/update.html", {
                    "form": NewListingItem(request.POST),

                })
            
        else:
            # Getting data for item with "item_id" from DB 
            item = Item.objects.get(pk=item_id)
            # Initial values from DB
            values = {
                "title": item.title,
                "description": item.description,
                "url": item.photo,
                "price": item.price,
                "category": item.category,
            }
            return render(request, "auctions/update.html",{
                "form": NewListingItem(initial=values),
                "id": item.pk
                
            })


def delete(request, item_id):
    item_delete = Item.objects.get(pk=item_id).delete()
    return HttpResponseRedirect(reverse("index"))


def watchlist(request, user_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    else:
        current_user = request.user
        watchlist = Watchlist.objects.filter(user=User(pk=current_user.id))
        watchlist_list=[]
        # Getting data from DB for current user and watchlist items
        for n in range(0, len(watchlist)):
            watchlist_list.append({
                "title": watchlist[n].item.title,
                "price": watchlist[n].item.price,
                "time": watchlist[n].item.time,
                "id": watchlist[n].item.pk,
                "photo": watchlist[n].item.photo,

            })
        # Passing the variable for watchlist.html (checking is there any item in watchlist_list)
        if len(watchlist_list) == 0:
            empty = True
        else:
            empty = False

        return render(request, "auctions/watchlist.html",{
            "items": watchlist_list,
            "no_item": empty
        })


def closed(request, item_id):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")
    else:
        item = Item.objects.get(pk=item_id)
        item.status = False
        item.save()
        item = Item.objects.get(pk=item_id)
        try:
            comments = Comments.objects.filter(item=Item.objects.get(pk=item_id))
        except Comments.DoesNotExist:
            comments = None

        try: 
            last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
            last_object_price =last_object.last().price
            
                    
        except AttributeError:
            last_object_price = item.price
        try: 
            last_object = Bid.objects.filter(item=Item.objects.get(pk=item_id))
            winner = last_object.last().user
            closed_message = True
        except AttributeError:
            winner = "There is no any bids on this item."
            closed_message = False

        return render(request, "auctions/closed-item.html", {
            "item": item,
            "all_comments": comments,
            "last_price": last_object_price,
            "winner": winner,
            "message": closed_message,

        })
        

def closeditems(request):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")
    else:

        return render(request, "auctions/closed-items.html", {
            "items": Item.objects.filter(status = False),

        })


def category(request, category):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")
    else:
        return render(request, "auctions/category.html", {
            "items": Item.objects.filter(category = category)
        })


def user(request, name):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")
    else:
        user = User.objects.get(username = name)
        return render(request, "auctions/user.html", {
        "items": Item.objects.filter(user = user.pk),
        "item_user": user,
        "email": user.email
    })