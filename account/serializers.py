from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import CustomUser, Store

User = get_user_model()

#
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     """
#     Custom serializer to allow login with either a username or a phone number.
#     The client still sends 'username' and 'password' in the payload.
#     """
#
#     def validate(self, attrs):
#         identifier = attrs.get("username")  # Can be either username or phone
#         password = attrs.get("password")
#
#         # First try to authenticate by treating the identifier as the username.
#         user = authenticate(request=self.context.get("request"), username=identifier, password=password)
#
#         if user is None:
#             # If the above fails, attempt to fetch the user via the phone field in Person.
#             try:
#                 person = Person.objects.get(phone=identifier)
#                 # Use the username from the associated user object.
#                 user = authenticate(request=self.context.get("request"), username=person.user.username,
#                                     password=password)
#             except Person.DoesNotExist:
#                 user = None
#
#         if user is None:
#             raise serializers.ValidationError("No active account found with the given credentials.",
#                                               code="authorization")
#
#         self.user = user
#         refresh = self.get_token(user)
#
#         data = {
#             "refresh": str(refresh),
#             "access": str(refresh.access_token),
#         }
#
#         return data
#

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to allow login with either a username or a phone number.
    The client still sends 'username' and 'password' in the payload.
    """

    def validate(self, attrs):
        identifier = attrs.get("username")  # Can be either username or phone
        password = attrs.get("password")

        # First try to authenticate by treating the identifier as the username.
        user = authenticate(request=self.context.get("request"), username=identifier, password=password)



        if user is None:
            raise serializers.ValidationError("لا يوجد تطابق بين الاسم وكلمة السر!",
                                              code="authorization")

        self.user = user
        refresh = self.get_token(user)

        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return data


class SingUpSerializerUser(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8)
    class Meta:
        model = User
        # fields = ('username', 'first_name', 'last_name', 'email', 'password', 'confirm_password')
        fields = ('username', 'password', 'confirm_password','store')
        extra_kwargs = {
            # 'first_name': {'required': True, 'allow_blank': False},
            # 'last_name': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
            # 'email': {'required': True, 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False, 'min_length': 8, 'write_only': True},
        }


    def validate(self, data):
        """
        Validate that the password and confirm_password match.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def validate_password(self, value):
        """
        Validate the password using Django's built-in password validation.
        """
        validate_password(value)
        return value

    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        validated_data.pop('confirm_password')  # Remove confirm_password from the data
        user = User.objects.create(
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

#
# class SingUpSerializerPerson(serializers.ModelSerializer):
#     class Meta:
#         model = Person
#         fields = ('phone', 'city',  'name')
#         extra_kwargs = {
#             'city': {'required': True, 'allow_blank': False},
#             'phone': {'required': True, 'allow_blank': False},
#             'name': {'required': True, 'allow_blank': False},
#         }
#



class LogInSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False, 'min_length': 8, 'write_only': True},
        }


class userSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    storeName=serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_active',  'role','storeName'
                      #  'date_joined',
                  ]

    def get_role(self, obj):
        if obj.groups.filter(name='staff').exists():
            return 'مشرف'
        if obj.groups.filter(name='WorkShopManagers').exists():
            return 'مشرف الورشة'    
        return 'بائع'

    def get_storeName(self, obj):
        if obj.store:
            if obj.store.name=='الورشات':
                return None
            return obj.store.name
        else:
            return None

class StoresSerializer(serializers.ModelSerializer):
    class Meta:
        model=Store
        fields='__all__'