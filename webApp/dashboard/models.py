from django.db import models

# Create your models here.
class UserSelfData(models.Model):
	UserName = models.CharField(max_length=50)
	TotalFriends = models.IntegerField()
	Followers = models.IntegerField()
	JoinDate = models.DateField()
	UserID = models.CharField(max_length=50)

class UserFriends(models.Model):
	UserName = models.CharField(max_length=50)
	FriendName = models.CharField(max_length=50)
	MutualFriends = models.IntegerField()
	FriendshipDate = models.DateField()
		