from email.policy import default
from enum import unique

from django.db import models
from django.conf import settings
from django.db.models import PROTECT
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()



class Reposotory(models.Model):
    Yes_No = (
      ('Yes', 'Yes'),
      ('No', 'No')
    )
    name = models.CharField(max_length=30,unique=True, default='')
    location = models.CharField(max_length=30, default='')
    is_working = models.CharField(max_length=5, choices=Yes_No, default='Yes')

    def __str__(self):
       return self.name



class Product(models.Model):
    name=models.CharField(max_length=30,default='')
    description=models.TextField(default='')
    total_available=models.IntegerField(default=0)
    total_on_way=models.IntegerField(default=0)
    total_requested=models.IntegerField(default=0)

    reposotory=models.ForeignKey(Reposotory,on_delete=PROTECT,null=True,blank=False)
    def __str__(self):
        return self.name

class Class(models.Model):
    Yes_No = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    product=models.ForeignKey(Product, null=True, blank=True,related_name='productt',default='',on_delete=models.CASCADE)
    type=models.CharField(max_length=50,default='')
    active = models.CharField(max_length=5, choices=Yes_No, default='Yes')
    def __str__(self):
        return f"type :{self.type} "


class Amounts(models.Model):
    types=(
        ('متاح','متاح'),
        ('قيد الوصول','قيد الوصول'),
        ('محجوز', 'محجوز'),
        ('مخفي', 'مخفي'),
        ('مطلوب للشراء', 'مطلوب للشراء'),

    )
    types_of_work=(
        ('normal','normal'),
        ('workshop','workshop'),
    )
    product_class=models.ForeignKey(Class,related_name='classs',default='',on_delete=models.PROTECT)
    amount=models.IntegerField(default=0)
    is_available=models.CharField(max_length=30,choices=types)
    def __str__(self):
        return f"{self.product_class.product.name}, type :{self.product_class.type} , amount:   {self.amount}"



class Workshop(models.Model):
    Yes_No = (
      ('not started yet','not started yet'),
      ('Yes', 'Yes'),
      ('done', 'done'),
      ('stopped', 'stopped')
    )
    name = models.CharField(max_length=30,unique=True, default='')
    location = models.CharField(max_length=30, default='')
    is_working = models.CharField(max_length=30, choices=Yes_No, default='not started yet')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, related_name='workshop_manager', on_delete=models.PROTECT)

    def __str__(self):
       return self.name



class  Add_Delete(models.Model):
    change_choices = (
        ( 'اضافة كمية', 'اضافة كمية'),
        ( 'اضافة مادة', 'اضافة مادة'),
        ( 'اضافة نوع من مادة', 'اضافة نوع من مادة'),
        ('حجز', 'حجز'),
        ('الغاء حجز', 'الغاء حجز'),
        ('تسليم', 'تسليم'),
        ('ارسال', 'ارسال'),
        ('تعديل', 'تعديل'),
        ('حذف', 'حذف'),
        ('بيع', 'بيع'),
        ('تغيير اسم', 'تغيير اسم'),
        ('مطلوب للشراء','مطلوب للشراء')

    )
    types = (
        ('متاح', 'متاح'),
        ('قيد الوصول', 'قيد الوصول'),
        ('محجوز', 'محجوز'),
        ('مخفي', 'مخفي'),
    )
    changer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='صاحب التغيير',
        related_name='Add_DeleteChanger'
    )
    reader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='قارئ الرسالة',
        related_name='Add_DeleteReader'
    )

    change_type=models.CharField(max_length=30,choices=change_choices)
    type=models.CharField(max_length=50,null=True,blank=True)
    name=models.CharField(max_length=30,null=True,blank=True)
    amount = models.IntegerField(null=True,blank=True)
    details=models.TextField(null=True,blank=True)
    createAt = models.DateTimeField(null=True, auto_now_add=True)

    def __str__(self):
        return f"to : {self.change_type}"



class Notification(models.Model):
    message=models.TextField(default='')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='متلقي الرسالة',
        related_name='Notification'
    )
    createAt = models.DateTimeField(null=True, auto_now_add=True)
    def __str__(self):
        return f"to {self.user} : {self.message}"


class Reservations(models.Model):
    types = (
        ('pending', 'pending'), #حجز
        ('delivered', 'delivered'),#تم الاستلام
        ('sent', 'sent'),#تم الارسال
        ('cancelled', 'cancelled'),#الغاء الحجز
        ('sold', 'sold'),
        ('requested for workshops', 'requested for workshops'),
        ('returned from workshops', 'returned from workshops'),        

    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='صاحب الحجز',
        related_name='reservations'
    )
    newOwner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='صاحب الحجز الجديد',
        related_name='reservations2'
    )
    product_class=models.ForeignKey(Class,related_name='reservations',default='',on_delete=models.PROTECT)
    amount=models.IntegerField(default=0)
    createAt = models.DateTimeField(null=True, auto_now_add=True)
    reservation_type=models.CharField(max_length=50,choices=types,default='')
    workshop=models.ForeignKey(Workshop,related_name='workshop_reservations',default='',on_delete=models.PROTECT,null=True,blank=True)
    used_in_workshop=models.IntegerField(default=0,null=True,blank=True)
    def __str__(self):
        return f"{self.product_class.product.name}, type :{self.product_class.type} , amount:   {self.amount} is reserved"
