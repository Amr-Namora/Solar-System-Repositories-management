from rest_framework import serializers
from .models import Reservations, Product, Amounts, Notification, Class, Add_Delete, Reposotory, Workshop, PushToken, Bill


class ProductSerializer(serializers.ModelSerializer):
    reposotory=serializers.ReadOnlyField(source='reposotory.name', allow_null=True)
    class Meta:
        model = Product
        fields = "__all__"


class AmountsAsProductSerializer(serializers.ModelSerializer):
    description = serializers.ReadOnlyField(source='product_class.product.description', allow_null=True)
    name = serializers.ReadOnlyField(source='product_class.product.name', allow_null=False)
    total_on_way = serializers.ReadOnlyField(source='product_class.product.total_on_way', allow_null=False)
    total_available = serializers.ReadOnlyField(source='product_class.product.total_available', allow_null=False)

    class Meta:
        model = Amounts
        fields = ('description', 'name', 'total_available', 'total_on_way', 'id')


class ClassSerializer(serializers.ModelSerializer):
   class Meta:
        model = Class
        fields = ('id',)


class AmountsSerializer(serializers.ModelSerializer):
    description = serializers.ReadOnlyField(source='product_class.product.description', allow_null=True)
    name = serializers.ReadOnlyField(source='product_class.product.name', allow_null=False)
    type = serializers.ReadOnlyField(source='product_class.type', allow_null=False)
    class_id = serializers.ReadOnlyField(source='product_class.id', allow_null=False)
    product_id = serializers.ReadOnlyField(source='product_class.product.id', allow_null=False)
    
    # Kept as method field because it contains conditional business logic
    available_amount = serializers.SerializerMethodField()

    class Meta:
        model = Amounts
        fields = "__all__"

    def get_available_amount(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.is_available == 'متاح':
            return obj.amount
        return None


class AmountsTypeSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source='product_class.type', allow_null=True)
    id = serializers.ReadOnlyField(source='product_class.id', allow_null=True)
    # is_working = serializers.ReadOnlyField(source='product_class.active', allow_null=True)
    is_empyt = serializers.SerializerMethodField()
    is_working = serializers.SerializerMethodField()

    available_amount = serializers.SerializerMethodField()

    class Meta:
        model = Amounts
        fields = ['type', 'available_amount', 'id', 'is_empyt', 'is_working']

    def get_available_amount(self, obj):
        # Only return amount if this instance is 'متاح'
        if obj.is_available == 'متاح':
            return obj.amount
        return None
    def get_is_empyt(self, obj):
        return self.context.get('is_empyt', False)    
    def get_is_working(self, obj):
        return obj.product_class.active == 'Yes'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ('id','user','token','platform','is_active','created_at')
        read_only_fields = ('id','user','is_active','created_at')


class Add_DeleteSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='changer.username', allow_null=True)

    class Meta:
        model = Add_Delete
        fields = "__all__"


class ReservationsSerializer(serializers.ModelSerializer):
    # 5. Serializer Cleanup: Replace simple methods with ReadOnlyFields 
    name = serializers.ReadOnlyField(source='product_class.product.name')
    description = serializers.ReadOnlyField(source='product_class.product.description')
    type = serializers.ReadOnlyField(source='product_class.type')
    username = serializers.ReadOnlyField(source='user.username')
    newusername = serializers.ReadOnlyField(source='newOwner.username')
    reposotory = serializers.ReadOnlyField(source='product_class.product.reposotory.name')
    workshop_name = serializers.ReadOnlyField(source='workshop.name')
    workshop_isworking = serializers.ReadOnlyField(source='workshop.is_working')

    # Complex logic properties
    to_send_to_workshop = serializers.SerializerMethodField()
    to_send = serializers.SerializerMethodField()
    to_not_sending = serializers.SerializerMethodField()
    to_confirm = serializers.SerializerMethodField()
    to_turn = serializers.SerializerMethodField()
    to_cancle_confirm_turning = serializers.SerializerMethodField()
    to_cancle_reserve = serializers.SerializerMethodField()
    to_edit_amount_in_reservation = serializers.SerializerMethodField()

    class Meta:
        model = Reservations
        fields = (
            'name', 'createAt', 'amount', 'description', 'type', 'username',
            'reservation_type', 'id', 'newusername', 'reposotory', 'workshop_name',
            'workshop_isworking', 'used_in_workshop', 'to_send_to_workshop',
            'to_send', 'to_not_sending', 'to_confirm', 'to_turn',
            'to_cancle_confirm_turning', 'to_cancle_reserve', 'to_edit_amount_in_reservation'
        )

    # Note: All group checks are replaced by self.context.get()
    
    def get_to_edit_amount_in_reservation(self, obj):
        curr_user = self.context.get('request').user
        is_staff = self.context.get('is_staff', False)
        is_store_keeper = self.context.get('is_store_keeper', False)



        if not obj.reservation_type == 'pending':
            return False
        
        if is_staff :
            return True
        
        if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False
                
        # the one who asks for the product in the same repository with the cuurent user 
        # the reciever and the current user in the same reposotory or store
        if obj.user.repository == curr_user.repository:
            return True

        return False

    def get_to_cancle_reserve(self, obj):
        is_store_keeper = self.context.get('is_store_keeper', False)
        is_staff = self.context.get('is_staff', False)
        curr_user = self.context.get('request').user

        if not (obj.reservation_type == 'pending' or obj.reservation_type == 'requested for workshops'):
            return False
        
        if is_staff :
            return True
        
       
        if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False
        # if the user is store keeper and if the cuurent user is in the same store or reposotory of the reservation owner, he can cancle the reservation 
        # the reciever and the current user is the same
        if obj.user.repository == curr_user.repository:
            return True
        
        # the reservation's product was in the and the current user  in the 
        # if currUserStore and obj.product_class and obj.product_class.product and obj.product_class.product.reposotory and obj.product_class.product.reposotory.name == currUserStore:
        #     return True
                
        return False

    def get_to_send(self, obj):
        curr_user = self.context.get('request').user
        is_staff = self.context.get('is_staff', False)
        is_store_keeper = self.context.get('is_store_keeper', False)


        if not obj.reservation_type == 'pending':
            return False
        if obj.workshop:
            return False
        
        if is_staff :
            return True
        

       

        # the reservation's product was in  the current user's repository or store, he can send it 
        if  obj.product_class and obj.product_class.product and obj.product_class.product.reposotory and obj.product_class.product.reposotory == curr_user.repository:
            return True

        return False

    
    def get_to_send_to_workshop(self,obj):
        curr_user = self.context.get('request').user
        is_staff = self.context.get('is_staff', False)
        #print('get_to_send_to_workshop')
        #print(obj.amount)
        if not obj.workshop:           
            return False
        if not (obj.reservation_type == 'requested for workshops' or obj.reservation_type == 'pending'):
            return False
        
        amount_available=Amounts.objects.filter(is_available='متاح',product_class=obj.product_class).first()
        amount_requested=Amounts.objects.filter(is_available='مطلوب للشراء',product_class=obj.product_class).first()

        if not amount_available :   
            return False
        if obj.reservation_type == 'requested for workshops' and amount_requested and amount_requested.amount >0 and amount_available.amount < obj.amount:
            return False

        if is_staff :
            return True
        if obj.user and obj.user.repository   :

            if  obj.product_class and obj.product_class.product and obj.product_class.product.reposotory and obj.product_class.product.reposotory == curr_user.repository:

               #print(5)
               return True
        
        return False
 
    def get_to_confirm(self, obj):
        curr_user = self.context.get('request').user
        is_staff = self.context.get('is_staff', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if obj.newOwner:
                return False
        if not (obj.reservation_type == 'sent'  or obj.reservation_type == 'returned from workshops'):
            return False
        
        if is_staff :
            return True
        
        if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False
       

        #the current user's reposotory or store
        

        if obj.user and obj.user.repository :
            
            if obj.user.repository == curr_user.repository :
               return True
           

        return False

    def get_to_not_sending(self, obj):
        is_store_keeper = self.context.get('is_store_keeper', False)
        is_staff = self.context.get('is_staff', False)
        curr_user = self.context.get('request').user

        if not obj.reservation_type == 'pending':
            return False
        
        if is_staff:
            return True
            
        if  obj.product_class and obj.product_class.product and obj.product_class.product.reposotory and obj.product_class.product.reposotory == curr_user.repository:
            return True    
        return False

    def get_to_turn(self, obj):
        curr_user = self.context.get('request').user
        is_boss = self.context.get('is_boss', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if not obj.reservation_type in ['sent', 'returned from workshops'] or obj.newOwner:
            return False
        
        if is_boss :
            return True

        if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False
                   
        if obj.user and obj.user.repository and curr_user.repository :
            
            if curr_user.repository == obj.user.repository :
               return True
        return False

    def get_to_cancle_confirm_turning(self, obj):
        curr_user = self.context.get('request').user
        is_boss = self.context.get('is_boss', False)

        if not obj.newOwner :
            return False
        if is_boss:
            return True

        if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False  
              
        if obj.user and obj.user.repository :

            

            if obj.newOwner.repository == curr_user.repository :
               return True
        return False


class ReposotorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reposotory
        fields = '__all__'


class WorkshopSerializer(serializers.ModelSerializer):
    manager_name = serializers.ReadOnlyField(source='manager.username', allow_null=True)

    class Meta:
        model = Workshop
        fields = '__all__'


class BillsSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username', allow_null=True)

    class Meta:
        model = Bill
        fields = '__all__'