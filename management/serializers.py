from rest_framework import serializers
from .models import Reservations, Product, Amounts, Notification, Class, Add_Delete, Reposotory, Workshop, PushToken, Bill


class ProductSerializer(serializers.ModelSerializer):
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
    is_working = serializers.ReadOnlyField(source='product_class.active', allow_null=True)
    is_empyt = serializers.SerializerMethodField()
    
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
        is_boss = self.context.get('is_boss', False)
        is_staff = self.context.get('is_staff', False)

        if obj.user and obj.user.store and obj.reservation_type:
            if curr_user.store == obj.user.store and obj.reservation_type == 'pending':
                return True
            if (is_boss or is_staff) and obj.reservation_type == 'pending':
                return True
            if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user and obj.reservation_type == 'pending':
                    return True
        return False

    def get_to_cancle_reserve(self, obj):
        curr_user = self.context.get('request').user
        if obj.user and obj.user.store and obj.reservation_type:
            if obj.workshop:
                return False
            if curr_user.store == obj.user.store and obj.reservation_type == 'pending':
               return True
        return False

    def get_to_send(self, obj):
        curr_user = self.context.get('request').user
        is_staff = self.context.get('is_staff', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if is_staff or is_store_keeper:
            if obj.reservation_type == 'pending' and not obj.workshop:
                return True
            else:
                return False

        if (obj.user and obj.user.store and obj.reservation_type and 
            obj.product_class and obj.product_class.product and obj.product_class.product.reposotory):
            
            if is_staff and obj.reservation_type == 'pending':
                return True
            if obj.product_class.product.reposotory.name == curr_user.store.name and obj.reservation_type == 'pending':
                return True
        return False

    def get_to_send_to_workshop(self, obj):
        is_staff = self.context.get('is_staff', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if not obj.workshop:
            return False

        # Optimized Amount Fetching: Avoids hitting DB inside serializer
        amounts_dict = self.context.get('amounts_dict', {})
        obj_amounts = amounts_dict.get(obj.product_class_id, {})
        amount_available = obj_amounts.get('متاح')
        amount_requested = obj_amounts.get('مطلوب للشراء')

        if not amount_available:
            return False
            
        if amount_requested and amount_requested > 0 and amount_available < obj.amount:
            return False

        if obj.user and obj.user.store and obj.reservation_type:
            if (is_staff or is_store_keeper) and obj.reservation_type == 'pending':
                return True
            if obj.reservation_type == 'requested for workshops':
               return True
               
        return False

    def get_to_confirm(self, obj):
        curr_user = self.context.get('request').user
        is_boss = self.context.get('is_boss', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if obj.user and obj.user.store and obj.reservation_type:
            if obj.newOwner:
                return False
            if obj.reservation_type == 'sent':
                if is_boss or is_store_keeper:
                   return True
                if obj.workshop and obj.workshop.manager:
                    if obj.workshop.manager == curr_user:
                        return True
                    else:
                        return False

            if curr_user.store == obj.user.store and (obj.reservation_type == 'sent' or obj.reservation_type == 'returned from workshops'):
               return True
        return False

    def get_to_not_sending(self, obj):
        is_boss = self.context.get('is_boss', False)
        is_staff = self.context.get('is_staff', False)

        if is_boss or is_staff:
            if obj.reservation_type == 'pending':
                return True
        return False

    def get_to_turn(self, obj):
        curr_user = self.context.get('request').user
        is_boss = self.context.get('is_boss', False)
        is_store_keeper = self.context.get('is_store_keeper', False)

        if is_boss or is_store_keeper:
            if obj.reservation_type in ['sent', 'returned from workshops'] and not obj.newOwner:
                return True
            else:
                return False

        if obj.user and obj.user.store and obj.reservation_type:
            if obj.newOwner:
                return False

            if obj.reservation_type in ['sent', 'returned from workshops']:
                if is_boss:
                   return True
                if obj.workshop and obj.workshop.manager:
                    if obj.workshop.manager == curr_user:
                        return True
                    else:
                        return False
                        
            if curr_user.store == obj.user.store and (obj.reservation_type == 'sent' or obj.reservation_type == 'returned from workshops'):
               return True
        return False

    def get_to_cancle_confirm_turning(self, obj):
        curr_user = self.context.get('request').user
        is_boss = self.context.get('is_boss', False)

        if obj.user and obj.user.store and obj.reservation_type and obj.newOwner:
            if is_boss:
               return True
            if obj.workshop and obj.workshop.manager:
                if obj.workshop.manager == curr_user:
                    return True
                else:
                    return False

            if obj.newOwner.store == curr_user.store and (obj.reservation_type == 'sent' or obj.reservation_type == 'returned from workshops'):
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