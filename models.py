from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Cover(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000)
    price = models.IntegerField()
    image = models.ImageField(upload_to='media',default=0)
    
class Cart(models.Model):
    cid = models.ForeignKey(Cover,db_column='cid',on_delete=models.CASCADE)
    uid = models.ForeignKey(User,db_column='uid',on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=200,null=True)
    flat = models.CharField(max_length=300,null=True)
    landmark = models.CharField(max_length=200,null=True)
    city = models.CharField(max_length=200,null=True)
    state = models.CharField(max_length=100,null=True)
    pincode = models.IntegerField(null=True)
    contact = models.BigIntegerField(null=True)
    contactA = models.BigIntegerField(null=True)

class Order(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    cover = models.ForeignKey(Cover,on_delete=models.CASCADE,null=True)
    address = models.ForeignKey(Address,on_delete=models.CASCADE,null=True)
    order_id = models.CharField(max_length=100,null=True)

    

