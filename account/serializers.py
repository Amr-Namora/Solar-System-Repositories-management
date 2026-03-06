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


from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.conf import settings

import re

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    app_version = serializers.CharField(required=False, allow_blank=True)

    def is_outdated(self, client_version, required_version):
        print(f"Checking app version... Client: {client_version} | Required: {required_version}")
        if not client_version:
            return True
        
        try:
            # 1. Clean the strings (removes spaces, letters, etc. Keeps only numbers and dots)
            c_clean = re.sub(r'[^\d.]', '', str(client_version))
            r_clean = re.sub(r'[^\d.]', '', str(required_version))

            # 2. Convert to lists of integers
            c_parts = [int(v) for v in c_clean.split('.') if v]
            r_parts = [int(v) for v in r_clean.split('.') if v]

            # 3. Pad with zeros so they are the same length (e.g. 1.2 vs 1.2.0)
            length = max(len(c_parts), len(r_parts))
            c_parts.extend([0] * (length - len(c_parts)))
            r_parts.extend([0] * (length - len(r_parts)))
            
            # 4. Compare
            is_old = c_parts < r_parts
            
            print(f"--- VERSION CHECK ---")
            print(f"Client: {c_parts} | Required: {r_parts}")
            print(f"Is App Outdated?: {is_old}")
            print(f"---------------------")
            
            return is_old

        except Exception as e:
            print(f"Version check error: {e}")
            return False # Return False if parsing fails so we don't accidentally lock users out

    def validate(self, attrs):
        app_version = attrs.get("app_version", "0.0.0")
        required_version = getattr(settings, 'MINIMUM_APP_VERSION', '1.0.0')
        
        # 1. Check version
        if self.is_outdated(app_version, required_version):
            print("Action: Rejecting login, app is outdated.")
            raise serializers.ValidationError({
                "error_type": "update_required",
                "detail": "يوجد إصدار جديد من التطبيق. يرجى التحديث للمتابعة.",
                "download_link": getattr(settings, 'APP_DOWNLOAD_LINK', '')
            })

        # 2. Authenticate
        identifier = attrs.get("username")
        password = attrs.get("password")
        
        print(f"Action: Version is good. Attempting to log in user: {identifier}")

        user = authenticate(request=self.context.get("request"), username=identifier, password=password)

        if user is None:
            print("Action: Login failed! Wrong username or password.")
            raise serializers.ValidationError({"detail": "لا يوجد تطابق بين الاسم وكلمة السر!"}, code="authorization")

        print("Action: Login Success!")
        self.user = user
        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

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
    repositoryName=serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_active',  'role','storeName','repositoryName']
                      #  'date_joined',
                  

    def get_role(self, obj):
        if obj.groups.filter(name='staff').exists():
            return 'مشرف'
        if obj.groups.filter(name='WorkShopManagers').exists():
            return 'مشرف الورشة'  
        if obj.groups.filter(name='StoreKeeper').exists():
            return 'امين مستودع'
        return 'بائع'

    def get_storeName(self, obj):
        if obj.store:
            if obj.store.name=='الورشات':
                return None
            return obj.store.name
        else:
            return None

    def get_repositoryName(self, obj):
        if obj.repository :
            if obj.repository.name=='المستودعات':
                return None
            return obj.repository.name
        else:
            return None

class StoresSerializer(serializers.ModelSerializer):
    class Meta:
        model=Store
        fields='__all__'