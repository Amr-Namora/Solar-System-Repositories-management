from rest_framework import serializers
from .models import Reservations, Product, Amounts, Notification, Class, Add_Delete, Reposotory,Workshop


class ProductSerializer(serializers.ModelSerializer):
    # product = ProductSerializer()
    class Meta:
        model = Product
        fields = "__all__"


class AmountsAsProductSerializer(serializers.ModelSerializer):
    description=serializers.SerializerMethodField()
    name=serializers.SerializerMethodField()
    total_on_way=serializers.SerializerMethodField()
    total_available=serializers.SerializerMethodField()
    class Meta:
        model = Amounts
        fields = ('description','name','total_available','total_on_way','id')
    def get_name(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.name
        else :
            return None
    def get_description(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.description
        else :
            return None
    def get_total_on_way(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.total_on_way
        else :
            return None
    def get_total_available(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.total_available
        else :
            return None


class ClassSerializer(serializers.ModelSerializer):
   class Meta:
        model = Class
        fields = ('id',)


class AmountsSerializer(serializers.ModelSerializer):
    description=serializers.SerializerMethodField()
    name=serializers.SerializerMethodField()
    type=serializers.SerializerMethodField()
    available_amount = serializers.SerializerMethodField()
    class_id=serializers.SerializerMethodField()
    product_id=serializers.SerializerMethodField()
    
    class Meta:
        model = Amounts
        fields = "__all__"
    def get_name(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.name
        else :
            return None
    def get_description(self,obj):
        if obj.product_class.product:
            return obj.product_class.product.description
        else :
            return None
    def get_type(self,obj):
        if obj.product_class:
            return obj.product_class.type
        else :
            return None
    def get_available_amount(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.is_available == 'متاح':
            return obj.amount
        return None

    def get_class_id(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.product_class:
            return obj.product_class.id
        return None

    def get_product_id(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.product_class.product:
            return obj.product_class.product.id
        return None


class AmountsTypeSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    available_amount = serializers.SerializerMethodField()
    is_empyt = serializers.SerializerMethodField()
    is_working=serializers.SerializerMethodField()
    id=serializers.SerializerMethodField()
    #manager_name=serializers.SerializerMethodField()
    class Meta:
        model = Amounts
        fields = ['type', 'available_amount','id','is_empyt','is_working']

    # def get_manager_name(self,obj):
    #     if obj.product_class and obj.product_class.product and obj.product_class.product.reposotory:
    #         if obj.product_class.product.reposotory.manager:
    #             return obj.product_class.product.reposotory.manager.username
    #         else :
    #             return None
    #     return None
    def get_type(self, obj):
        if obj.product_class:
            return obj.product_class.type
        return None
    def get_id(self, obj):
        if obj.product_class:
            return obj.product_class.id
        return None

    def get_available_amount(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.is_available == 'متاح':
            return obj.amount
        return None
    def get_is_empyt(self, obj):

        if obj.product_class :

            return Amounts.objects.filter(product_class=obj.product_class,amount__gt=0).exists()
        return None
    def get_is_working(self, obj):

        if obj.product_class :
            active=obj.product_class.active
            if active == 'Yes':
                return True
            else :
                return False
        return None


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = "__all__"

class Add_DeleteSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    class Meta:
        model = Add_Delete
        fields = "__all__"

    def get_username(self, obj):
        if obj.changer:
            return obj.changer.username
        else:
            return None

class ReservationsSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    newusername = serializers.SerializerMethodField()
    reposotory = serializers.SerializerMethodField()
    workshop_name = serializers.SerializerMethodField()
    workshop_isworking=serializers.SerializerMethodField()
    to_send_to_workshop=serializers.SerializerMethodField()
    to_send=serializers.SerializerMethodField()
    to_not_sending=serializers.SerializerMethodField()
    to_confirm=serializers.SerializerMethodField()
    to_turn=serializers.SerializerMethodField()
    to_cancle_confirm_turning=serializers.SerializerMethodField()
    to_cancle_reserve=serializers.SerializerMethodField()
    class Meta:
        model = Reservations
        fields = ('name' #changer or reader
                  ,'createAt','amount','description','type','username',
                  'reservation_type','id','newusername','reposotory','workshop_name','workshop_isworking'
                    ,'used_in_workshop','to_send_to_workshop',
                    'to_send','to_not_sending','to_confirm','to_turn','to_cancle_confirm_turning','to_cancle_reserve'
                  )

    def get_to_cancle_reserve(self,obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type :
            if obj.workshop:
                return False

            if curr_user.store==obj.user.store and   obj.reservation_type == 'pending':
               return True
        return False

    def get_to_send(self,obj):
        #print('get_to_send')

        #print(obj.amount)
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type and obj.product_class and obj.product_class.product and obj.product_class.product.reposotory :
            # if  obj.workshop:
            #     return False
            #print(1)
            if curr_user.groups.filter(name="staff").exists() and  obj.reservation_type == 'pending':
                #print(2)

                return True
            if  obj.product_class.product.reposotory.name == curr_user.store.name and obj.reservation_type == 'pending':
                #print(3)
                return True
           
        return False

    def get_to_send_to_workshop(self,obj):
        curr_user = self.context.get('request').user
        #print('get_to_send_to_workshop')
        #print(obj.amount) 

        amount_available=Amounts.objects.filter(is_available='متاح',product_class=obj.product_class).first()
        if not (amount_available and amount_available.amount >= obj.amount):
            #print('not enough amount')
            return False
        if not obj.workshop:
            #print('no workshop')
            return False
        if obj.user and obj.user.store  and obj.reservation_type :
            if curr_user.groups.filter(name="staff").exists() and  obj.reservation_type == 'pending':
                #print(4)
                return True

            if  obj.reservation_type == 'requested for workshops':
               #print(5)
               return True

        return False

    def get_to_confirm(self,obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type :
            if obj.newOwner:
                return False
            if  curr_user.store==obj.user.store and (obj.reservation_type == 'sent' or obj.reservation_type == 'returned from workshops') :
               return True
        return False

    def get_to_not_sending(self,obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type and obj.product_class and obj.product_class.product and obj.product_class.product.reposotory :
            if obj.workshop:
                return False

            if curr_user.groups.filter(name="staff").exists() and  obj.reservation_type == 'pending':
                return True
            if  obj.product_class.product.reposotory.name == curr_user.store.name and obj.reservation_type == 'pending':
                return True
        return False

    def get_to_turn(self,obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type :
            if obj.newOwner:
                return False
            if  curr_user.store==obj.user.store and (obj.reservation_type == 'sent' or obj.reservation_type == 'returned from workshops') :
               return True
        return False
    
    def get_to_cancle_confirm_turning(self,obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store  and obj.reservation_type and obj.newOwner :

            if   obj.newOwner.store == curr_user.store and obj.reservation_type == 'sent' :
               return True
        return False


   
    
    def get_name(self, obj):
        if obj.product_class.product:
            return obj.product_class.product.name
        else:
            return None
    def get_workshop_name(self, obj):
        if obj.workshop:
            return obj.workshop.name
        else:
            return None
    def get_workshop_isworking(self, obj):
        if obj.workshop:
            return obj.workshop.is_working
        else:
            return None
    def get_description(self, obj):
        if obj.product_class.product:
            return obj.product_class.product.description
        else:
            return None
    def get_reposotory(self, obj):
        if obj.product_class.product.reposotory:
            return obj.product_class.product.reposotory.name
        else:
            return None

    def get_type(self, obj):
        if obj.product_class:
            return obj.product_class.type
        else:
            return None
    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        else:
            return None
    def get_newusername(self, obj):
        if obj.newOwner:
            return obj.newOwner.username
        else:
            return None




class ReposotorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Reposotory
        fields='__all__'


class WorkshopSerializer(serializers.ModelSerializer):
    manager_name=serializers.SerializerMethodField()
    
    class Meta:
        model=Workshop  
        fields='__all__'        
    def get_manager_name(self,obj):
        if obj.manager:
            return obj.manager.username
        else :
            return None    