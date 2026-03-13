from django.contrib import admin
from .models import Reservations, Product, Amounts, Class, Add_Delete, Notification, Reposotory, Workshop, PushToken ,Bill

# Register your models here.
admin.site.register(PushToken)




class Add_DeleteAdmin(admin.ModelAdmin):
    model = Add_Delete
    list_display = ('changer', 'id','change_choices')

admin.site.register(Add_Delete, Add_DeleteAdmin)

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('name', 'id')

admin.site.register(Product, ProductAdmin)

 

class ReposotoryAdmin(admin.ModelAdmin):
    model = Reposotory
    list_display = ('name', 'id')

admin.site.register(Reposotory, ReposotoryAdmin)


class WorkshopAdmin(admin.ModelAdmin):
    model = Workshop
    list_display = ('name', 'id')

admin.site.register(Workshop, WorkshopAdmin)


class AmountsAdmin(admin.ModelAdmin):
    model = Amounts
    list_display = ( 'amount','is_available','product_class','id')

admin.site.register(Amounts, AmountsAdmin)


class ReservationsAdmin(admin.ModelAdmin):
    model = Reservations
    list_display = ( 'amount','reservation_type','product_class','id')
    search_fields = ['workshop__name', 'amount']  # This will search through related Person fields


admin.site.register(Reservations, ReservationsAdmin)

class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ( 'message','createAt','user__username','id')
    search_fields = ['message', 'id', 'user__username']  # This will search through related Person fields


admin.site.register(Notification, NotificationAdmin)

class ClassAdmin(admin.ModelAdmin):
    model = Class
    list_display = ('type', 'id')


admin.site.register(Class, ClassAdmin)


class BillAdmin(admin.ModelAdmin):
    model = Bill
    list_display = ('client_name', 'details', 'id')


admin.site.register(Bill, BillAdmin)

