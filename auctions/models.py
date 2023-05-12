from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Item(models.Model):
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=5000)
    photo = models.CharField(max_length=5000)
    time = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price= models.IntegerField()
    status = models.BooleanField()
    category = models.CharField(max_length=64)


class Watchlist(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="watchlist_item")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    watch = models.BooleanField()


class Comments(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    comment= models.CharField(max_length=5000)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} for {self.item}: {self.comment}"


class Bid(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.IntegerField()

    def __str__(self):
        return f"User {self.user} place bid for {self.item} and price is : {self.price}"


