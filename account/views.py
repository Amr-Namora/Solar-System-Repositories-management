from django.core.serializers import serialize
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth.models import Group
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from sqlparse.engine.grouping import group
from django.db.models import Q

from .models import CustomUser,Store
from .serializers import SingUpSerializerUser, userSerializer, StoresSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
# Create your views here.
from management.models import Reposotory


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
# In your views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    is_manager = user.groups.filter(name='staff').exists()
    is_workshop_manager = user.groups.filter(name='WorkShopManagers').exists()
    
    # Determine role for display
    if is_manager:
        role = 'مشرف'
    elif is_workshop_manager:
        role = 'مشرف الورشة'
    else:
        role = 'بائع'
    
    return Response({
        'username': user.username,
        'is_manager': is_manager,
        'is_workshop_manager': is_workshop_manager,
        'role': role,
        'store_name': user.store.name if user.store else None,
    })
User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class logout_view(APIView):
    permission_classes = [IsAuthenticated]
    print("hhhhhhhhhii   ")
    def post(self, request):
        print("\n\n=== REACHED LOGOUT VIEW ===")  # Add this
        print("Headers:", request.headers)  # Debug headers
        print("Body:", request.data)  # Debug body
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)




User = get_user_model()

class UserSignUpView(APIView):
    def post(self, request):
        role_mapping = {
            'مشرف': 'مشرف',
            'بائع': 'بائع',
            'مشرف ورشة': 'مشرف الورشة',
            'admin': 'مشرف',
            'seller': 'بائع',
            'WorkShopManagers': 'مشرف ورشة',
        }
        user_data = {
            'username': request.data.get('username'),
            'password': request.data.get('password'),
            'confirm_password': request.data.get('confirm_password'),
            'role': request.data.get('role', 'بائع'),
        }
        
        # Get store name from request
        store_name = request.data.get('store_name')
        allowed_repositories_ids = request.data.get('allowed_repositories', [])
        
        # Validate store exists
        try:
            if user_data['role'] == 'مشرف الورشة':
                store = Store.objects.get(name='الورشات')
            elif user_data['role'] in ['مشرف', 'بائع']:
                store = Store.objects.get(name=store_name)
        except Store.DoesNotExist:
            return Response({'error': 'Store does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer = SingUpSerializerUser(data=user_data)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = user_serializer.save()
            user.store = store
            user.save()

            # Add allowed repositories
            if allowed_repositories_ids:
                repositories = Reposotory.objects.filter(id__in=allowed_repositories_ids)
                user.allowed_repositories.set(repositories)

            # Add to staff group if role is مشرف
            if user_data['role'] == 'مشرف':
                staff_group = Group.objects.get(name='staff')
                user.groups.add(staff_group)
                user.save()
            elif user_data['role'] == 'مشرف الورشة':
                WorkShopManagers_group = Group.objects.get(name='WorkShopManagers')
                user.groups.add(WorkShopManagers_group)
                user.save()
                
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'user_id': user.id,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['GET'])
def users(request):

    programmer_group=Group.objects.get(name="programers")
    users=CustomUser.objects.filter(is_active=True).exclude(groups=programmer_group)
    serializer=userSerializer(
        users,
        many=True,
        context={'request': request}
    )
    return Response({
        'users':serializer.data

    })


@api_view(['GET'])
def users_no_boss(request):

    programmer_group=Group.objects.get(name="programers")
    boss_group=Group.objects.get(name="boss")

    users=CustomUser.objects.filter(is_active=True).exclude(Q(groups=programmer_group)|Q(groups=boss_group))
    serializer=userSerializer(
        users,
        many=True,
        context={'request': request}
    )
    return Response({
        'users':serializer.data

    })



@api_view(['GET'])
def users_workshops(request):
    print("hi")
    WorkShopManagers_group=Group.objects.get(name="WorkShopManagers")
    programmer_group=Group.objects.get(name="programers")

    print(WorkShopManagers_group)
    users=CustomUser.objects.filter(is_active=True,groups=WorkShopManagers_group).exclude(groups=programmer_group)
    print(users)

    serializer=userSerializer(
        users,
        many=True,
        context={'request': request}
    )
    return Response({
        'users':serializer.data

    })



class UserDeleteView(APIView):
    # permission_classes = [IsAdminUser]

    def delete(self, request, user_id):
        try:
            user = get_user_model().objects.get(id=user_id)

            # Prevent deleting admin users
            if user.is_superuser:
                return Response({'error': 'لا يمكن حذف مسؤول النظام'}, status=status.HTTP_403_FORBIDDEN)

            user.delete()
            return Response({'message': 'تم حذف المستخدم بنجاح'}, status=status.HTTP_200_OK)

        except get_user_model().DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserToggleStatusView(APIView):
    # permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        try:
            user = get_user_model().objects.get(id=user_id)

            # Prevent deactivating admin users
            if user.is_superuser:
                return Response({'error': 'لا يمكن تعطيل مسؤول النظام'}, status=status.HTTP_403_FORBIDDEN)
            if user == request.user:
                return Response({'error': 'لا يمكن تعطيل حسابك'}, status=status.HTTP_403_FORBIDDEN)

            user.is_active = not user.is_active
            user.save()

            status_message = 'تم تفعيل المستخدم' if user.is_active else 'تم تعطيل المستخدم'
            return Response({
                'message': status_message,
                'is_active': user.is_active
            }, status=status.HTTP_200_OK)

        except get_user_model().DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def stores(request):
    
    stores=Store.objects.filter(is_working='Yes').exclude(name='الورشات')
    serializer=StoresSerializer(stores,many=True)
    return Response({
        'stores': serializer.data

    })

from rest_framework import status

@api_view(['POST'])
def addStores(request):
    data = {
        'location': request.data.get('location'),
        'name': request.data.get('name'),
    }
    try:
        if Store.objects.filter(name=data['name']).exists():
            return Response({'error':'هذا المتجر موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        if Reposotory.objects.filter(name=data['name']).exists():
            return Response({'error':'يوجد مستودع بهذا الاسم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        
        Store.objects.create(
            name=data['name'],
            location=data['location'],
        )
        
        
        Reposotory.objects.create(
            name=data['name'],
            location=data['location'],
        )
    except Exception as e:
        return Response({'error':'data you entered is not enough'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'details': 'your request has been processed successfully!'})


@api_view(['POST'])
def storesToggleStatusView(request):
        print('hi')
        try:
            store_id=request.GET.get('store_id')
            store = Store.objects.get(id=store_id)
            if store.name == 'المرجة' or store.name == 'الرئيسي':
                return Response({'error': 'لا يمكن تعطيل هذا المتجر'}, status=status.HTTP_400_BAD_REQUEST)
            # Prevent deleting admin users
            store.is_working='No'

            Rep=Reposotory.objects.filter(name=store.name).first()

            Rep.is_working='No'
            store.save()
            Rep.save()
            return Response({'message': 'تم تعطيل المتجر بنجاح'}, status=status.HTTP_200_OK)

        except Store.DoesNotExist:
            return Response({'error': 'المتجر غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Add this to your views.py
class UserUpdateView(APIView):
    def put(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)

            # Get the new data from request
            new_username = request.data.get('username')
            new_password = request.data.get('password')
            new_role = request.data.get('role')
            new_store_name = request.data.get('store_name')
            allowed_repositories_ids = request.data.get('allowed_repositories', [])

            # Update username if provided and different
            if new_username and new_username != user.username:
                # Check if username already exists
                if CustomUser.objects.filter(username=new_username).exclude(id=user_id).exists():
                    return Response({'error': 'هذا الاسم محجوز مسبقا'}, status=status.HTTP_400_BAD_REQUEST)
                user.username = new_username

            # Update password if provided
            if new_password:
                user.set_password(new_password)

            # Update store if provided
            if new_store_name:
                try:
                    store = Store.objects.get(name=new_store_name)
                    user.store = store
                except Store.DoesNotExist:
                    return Response({'error': 'المتجر غير موجود'}, status=status.HTTP_400_BAD_REQUEST)

            # Update allowed repositories for sellers
            if new_role == 'بائع':
                if allowed_repositories_ids:
                    repositories = Reposotory.objects.filter(id__in=allowed_repositories_ids)
                    user.allowed_repositories.set(repositories)
                else:
                    user.allowed_repositories.clear()
            else:
                # Clear allowed repositories for non-sellers
                user.allowed_repositories.clear()

            # Update role (group membership)
            if new_role:
                print("old role")
                print(new_role)
                staff_group = Group.objects.get(name='staff')
                workshop_group = Group.objects.get(name='WorkShopManagers')
                boss_group = Group.objects.get(name='boss')

                user.groups.remove(staff_group)
                user.groups.remove(workshop_group)
                user.groups.remove(boss_group)

                if new_role == 'مشرف':
                    user.groups.add(staff_group)
                elif new_role == 'مشرف الورشة':
                    user.groups.add(workshop_group)
                    user.store = Store.objects.get(name='الورشات')
            
            user.save()

            return Response({
                'message': 'تم تحديث بيانات المستخدم بنجاح',
                'user_id': user.id,
            }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def UpdatePassword(request):
        try:
            user = request.user

            # Get the new data from request
            new_password = request.data.get('password')


            # Update username if provided and different


            # Update password if provided
            if new_password:
                user.set_password(new_password)

            # Update store if provided

            user.save()

            return Response({
                'message': 'تم تحديث بيانات المستخدم بنجاح',
            }, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def profile(request):
    return Response({
        'username': request.user.username,
        'is_staff': request.user.is_staff,
        'is_active': request.user.is_active,
        'store': request.user.store.name if request.user.store else None,

    })


