from itertools import product
from urllib import request
from django.contrib.auth.models import Group
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView
from rest_framework import status
from .models import Product, Amounts, Notification, Class, Add_Delete, Reservations, Reposotory, PushToken
from .serializers import AmountsTypeSerializer, ReservationsSerializer, ClassSerializer, ProductSerializer, \
    AmountsSerializer, ReservationsSerializerForBillAndWorkshop ,\
    NotificationSerializer, Add_DeleteSerializer, AmountsAsProductSerializer, ReposotorySerializer ,BillsSerializer
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.decorators import  permission_classes

from django.http import HttpRequest
from django.utils import timezone
from datetime import timedelta
from rest_framework.status import HTTP_200_OK
from django.db.models import Q, Min
from .models import Product, Amounts
from .serializers import AmountsAsProductSerializer
from .filters import Add_Delete_filter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Add_Delete,Workshop,Bill
from .serializers import Add_DeleteSerializer,WorkshopSerializer
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers

from .filters import home_filter
import django_filters


from datetime import timedelta
from django.utils import timezone
from collections import Counter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from .filters import Add_Delete_filter
from .serializers import Add_DeleteSerializer

User = get_user_model()


@api_view(['GET'])
def is_staff(request):


    is_manager = request.user.groups.filter(name="staff").exists()

    return Response({
        'is_manager': is_manager,
    }, status=HTTP_200_OK)



from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.decorators import api_view
from django.db.models import Q

@api_view(['GET'])
def home(request):
    # 1. Get pagination parameters
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    
    reposotory_name = request.GET.get('reposotory_name')
    is_manager = request.user.groups.filter(name="staff").exists() 
    is_store_keeper = request.user.groups.filter(name="StoreKeeper").exists()

    # 2. Base Queryset Logic
    if reposotory_name:
        reposotory = Reposotory.objects.filter(name=reposotory_name).first()
        if is_manager or is_store_keeper:
            base_qs = Product.objects.filter(reposotory=reposotory)
        else:
            base_qs = Product.objects.filter(
                reposotory=reposotory,
                classes__amounts__amount__gt=0,
                classes__amounts__is_available__in=['قيد الوصول', 'متاح']
            ).distinct()
    else:
        if is_manager or is_store_keeper:
            base_qs = Product.objects.all().exclude(reposotory__name='الورشات')
        else:
            allowed_repos = request.user.allowed_repositories.all()
            base_qs = Product.objects.filter(
                classes__amounts__amount__gt=0,
                classes__amounts__is_available__in=['قيد الوصول', 'متاح'],
                reposotory__in=allowed_repos
            ).exclude(Q(reposotory__name=request.user.repository.name) | Q(reposotory__name='الورشات')).distinct()

    # 3. Apply your existing filter
    filtered_qs = home_filter(request.GET, queryset=base_qs).qs

    # 4. Serialize
    serializer = ProductSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data  

    # 5. Deduplicate by (name, description)
    unique = []
    seen = set()
    for item in raw:
        key = (item.get('name'), item.get('description'))
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # 6. Apply Pagination to the deduplicated list
    paginator = Paginator(unique, limit)
    try:
        paginated_items = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = []

    user = request.user
    repository_name = None
    if hasattr(user, 'repository') and user.repository and hasattr(user.repository, 'name'):
        repository_name = user.repository.name

    # 7. Return paginated deduplicated list
    return Response({
        'serialize': paginated_items.object_list if hasattr(paginated_items, 'object_list') else [],
        'is_manager': is_manager,
        'store': repository_name,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    }, status=HTTP_200_OK)


@api_view(['GET'])
def home_for_reposotory_workshop(request):

    reposotory_id=request.GET.get('reposotory_id')    
    base_qs= Product.objects.filter(
            classes__amounts__is_available ='متاح',reposotory__id=reposotory_id
        )
    filtered_qs = home_filter(request.GET, queryset=base_qs).qs

    # 4. serialize
    serializer = ProductSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data  # this is a list of {'name':…, 'description':…}

    # 5. dedupe by (name, description)
    unique = []
    seen = set()
    for item in raw:
        key = (item.get('name'), item.get('description'))
        if key not in seen:
            seen.add(key)
            unique.append(item)

    user=request.user
   

    
    # print(user.store_na)
    # 6. return deduped list
    return Response({

        'serialize': unique,
    }, status=HTTP_200_OK)


@api_view(['GET'])
def myStore(request):
    reposotory_name=Reposotory.objects.get(name=request.user.store.name)
    # 1. compute totals from Product
    

   
    base_qs= Product.objects.filter(reposotory__name=reposotory_name,).distinct()

    # 3. apply your existing filter
    filtered_qs = home_filter(request.GET, queryset=base_qs).qs

    # 4. serialize
    serializer = ProductSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data  # this is a list of {'name':…, 'description':…}

    # 5. dedupe by (name, description)
    unique = []
    seen = set()
    for item in raw:
        key = (item.get('name'), item.get('description'))
        if key not in seen:
            seen.add(key)
            unique.append(item)

    user=request.user
    reposotory=user.repository
    repository_name = None

    if reposotory and reposotory.name:
        repository_name=reposotory.name
    # print(user.repository_name)
    # 6. return deduped list
    return Response({

        'serialize': unique,
        'store':repository_name
    }, status=HTTP_200_OK)


@api_view(['GET'])
def homeRead(request):
    # 1. compute totals from Product

    is_manager = request.user.groups.filter(name="staff").exists()
    if is_manager:
        base_qs = Product.objects.all().exclude(reposotory__name='الورشات')
        # base_qs = Product.objects.all()
    else:
        base_qs= Product.objects.filter(
            classes__amounts__amount__gt=0,
            classes__amounts__is_available__in=['قيد الوصول', 'متاح']
        ).exclude(reposotory__name='الورشات').distinct()

    # 3. apply your existing filter
    filtered_qs = home_filter(request.GET, queryset=base_qs).qs

    # 4. serialize
    serializer = ProductSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data  # this is a list of {'name':…, 'description':…}

    # 5. dedupe by (name, description)
    unique = []
    seen = set()
    for item in raw:
        key = (item.get('name'), item.get('description'))
        if key not in seen:
            seen.add(key)
            unique.append(item)

    user=request.user
    reposotory=user.repository
    repository_name = None

    if reposotory and reposotory.name:
        repository_name=reposotory.name
    # print(user.repository_name)
    # 6. return deduped list
    return Response({

        'serialize': unique,
        'is_manager': is_manager,
        'store':repository_name
    }, status=HTTP_200_OK)


@api_view(['GET'])
def product_types(request):
    print('here product_types')

    product_id = request.GET.get('product_id')
    print("hereeee ",product_id)
    is_boss = request.user.groups.filter(name="boss").exists()
    is_manager = request.user.groups.filter(name="staff").exists()

    product=Product.objects.get(id=product_id)
    print('here product_types:',product.name)

    if not product:
        return Response({'error':'there is no such a product'})
    if   request.user.groups.filter(name="WorkShopManagers").exists():
        details = Amounts.objects.filter(
            product_class__product=product,

        )
    
    else:
        rep = product.reposotory.name
        print("rep ",rep)
        my_rep = request.user.repository.name
        print("my_rep ",my_rep)
        print( my_rep == rep)
        if is_manager or my_rep == rep:       
            details = Amounts.objects.filter(
                product_class__product=product,

            )
        else:
            details = Amounts.objects.filter(
                Q(is_available='قيد الوصول') | Q(is_available='متاح'),
                product_class__product=product,
                amount__gt=0
            )

    is_empty=details.filter(amount__gt=0).exists()
        
    # Amounts.objects.filter(product_class=obj.product_class, amount__gt=0).exists()    

    serialize = AmountsTypeSerializer(details, many=True, context={'request': request ,'is_empty':is_empty})
    print('here product_types serialize:',serialize.data)
    # Collect unique types and their 'متاح' amount
    unique_data = {}
    for item in serialize.data:
        type_name = item['type']
        if type_name not in unique_data:
            unique_data[type_name] = {
                'type': type_name,
                'available_amount': item['available_amount'],
                'id':item['id'],
                'is_empyt':item['is_empyt'],
                'is_working':item['is_working']
            }
        elif item['available_amount'] is not None:
            # Update if this is the 'متاح' entry
            unique_data[type_name]['available_amount'] = item['available_amount']


    return Response({
        'is_boss': is_boss,
        'serialize': list(unique_data.values()),
        'is_manager': is_manager
    }, status=HTTP_200_OK)




@api_view(['POST'])
def edit_product_name(request):
    data = {
        'new_name': request.data.get('new_name'),
        'product_id': request.data.get('product_id'),

    }
    print('hhhhhhhhere')
    print(data['new_name'])
    print(data['product_id'])
    print('hhhhhhhhere')
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    obj=Product.objects.get(id=data['product_id'])
    print(obj)
    oldname=obj.name
    obj.name=data['new_name']
    obj.save() 

    print(11)
    print(obj)
    try:

        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        
        Add_Delete.objects.create(
            changer=user,
            change_type='تغيير اسم',
            name=obj.name,
            type=data['new_name'],
            reader=user,
            details=f"من {oldname} الى {obj.name}"

        )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")
    
    Notification.objects.create(
        user=user,
        message =f' لقد تم تغيير اسم {oldname}  الى {obj.name} '
        )
    #users=CustomUser.objects.all()
    #for user in users :

    return Response({
        'details':'done!'
    }, status=HTTP_200_OK)




@api_view(['GET'])
def product_details(request):
    user_data = {
        'class_id': request.GET.get('class_id'),

    }
    print('here product_details')
    print(user_data['class_id'])

    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    #product_class=Class.objects.filter(type=user_data['product_class'],product__name=user_data['product_name'])
    #print(product_clasws)


    if user_data['class_id']:
        class_obj=Class.objects.get(id=user_data['class_id'])
        print('here product_details ',class_obj)
        rep=class_obj.product.reposotory.name
        my_rep=request.user.repository.name
        if is_manager or my_rep==rep:
            details = Amounts.objects.filter(product_class=class_obj )
        else:
            details=Amounts.objects.filter(Q(is_available='قيد الوصول') | Q(is_available='متاح'),
            amount__gt= 0 ,product_class=class_obj )
    else:
        return Response({'error':'لم تقم بادخال نوع المادة'})
    serialize = AmountsSerializer(
        details,
        many=True,
        context={'request': request}
    )

    return Response({
        'serialize': serialize.data,
        'is_manager':is_manager
    }, status=HTTP_200_OK)


@api_view(['POST'])
def class_type_name(request):
    data = {
        'new_type': request.data.get('new_type'),
        'class_id': request.data.get('class_id'),

    }
    print('hhhhhhhhere')
    print(data['new_type'])
    print(data['class_id'])
    print('hhhhhhhhere')
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    obj=Class.objects.get(id=data['class_id'])
    print(obj)
    oldType=obj.type
    obj.type=data['new_type']
    obj.save()
    print(11)
    try:

        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        for staff_member in staff_users:
            if request.user != staff_member:
                Add_Delete.objects.create(
                    changer=user,
                    change_type='تغيير اسم',
                    name=obj.product.name,
                    type=data['new_type'],
                    reader=staff_member,
                    details=f' لقد تم تغيير اسم {oldType} من {obj.product.name} الى {obj.type} '

                )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")
    Notification.objects.create(
        user=user,
        message =f' لقد تم تغيير اسم {oldType} من {obj.product.name} الى {obj.type} '
        )
    #users=CustomUser.objects.all()
    #for user in users :

    return Response({
        'details':'done!'
    }, status=HTTP_200_OK)


@api_view(['POST'])
def class_type_delete(request):
    data = {
        'class_id': request.data.get('class_id'),

    }
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    print("hi")

    print(data)

    obj_class= Class.objects.get(id=data['class_id'])
    print(obj_class)
    amounts=Amounts.objects.filter(product_class=obj_class,amount__gt=0).first()
    if amounts:
        return Response({'error':f' يوجد كميات من النوع {amounts.is_available} من هذه المادة, لذا لا يمكنك حذفها'},status=status.HTTP_400_BAD_REQUEST)
    obj_class.active='No'
    obj_class.save()
    try:

        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        for staff_member in staff_users:
                Add_Delete.objects.create(
                    changer=user,
                    change_type='الغاء تفعيل',
                    name=obj_class.product.name,
                    type=obj_class.type,
                    reader=staff_member,

                )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")

    Notification.objects.create(
        user=user,
        message=f"قام {user} بالغاء تفعيل المادة {obj_class.type}"

    )

    print('done')
    return Response({
        'details':'done!'
    }, status=HTTP_200_OK)



@api_view(['POST'])
def class_type_undelete(request):
    data = {
        'class_id': request.data.get('class_id'),

    }
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    print("hi")

    print(data)

    obj_class= Class.objects.get(id=data['class_id'])
    obj_class.active='Yes'
    obj_class.save()
    try:

        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        for staff_member in staff_users:
                Add_Delete.objects.create(
                    changer=user,
                    change_type='تفعيل',
                    name=obj_class.product.name,
                    type=obj_class.type,
                    reader=staff_member,

                )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")

    Notification.objects.create(
        user=user,
        message=f"قام {user} بتفعيل المادة {obj_class.type}"

    )

    print('done')
    return Response({
        'details':'done!'
    }, status=HTTP_200_OK)



@api_view(['POST'])
def register_push_token(request):
    """Register or update a push token for the authenticated user.
    Expects JSON: {"push_token": "ExponentPushToken[...]", "platform": "android"}
    """
    token = request.data.get('push_token')
    platform = request.data.get('platform', '')
    if not token:
        return Response({'detail': 'push_token is required'}, status=HTTP_400_BAD_REQUEST)

    obj, created = PushToken.objects.update_or_create(
        token=token,
        defaults={'user': request.user if request.user and request.user.is_authenticated else None, 'platform': platform, 'is_active': True}
    )
    return Response({'detail': 'registered'}, status=HTTP_200_OK)


@api_view(['POST'])
def unregister_push_token(request):
    """Unregister a push token (delete or deactivate). Expects {"push_token": "..."}"""
    token = request.data.get('push_token')
    if not token:
        return Response({'detail': 'push_token is required'}, status=HTTP_400_BAD_REQUEST)

    PushToken.objects.filter(token=token).delete()
    return Response({'detail': 'unregistered'}, status=HTTP_200_OK)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def history_changes(request):
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()

    # الحصول على رقم الصفحة والحد الأقصى
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)

    # Step 1: Base queryset
    base_queryset = Add_Delete.objects.filter(reader=user)

    # Step 2: Apply filters using GET parameters
    queryset = base_queryset

    # Get the created_range parameter if it exists
    created_range = request.GET.get('created_range', '')
    if created_range:
        # Handle single date (day filter)
        if ',' not in created_range:
            if created_range == 'today': # إصلاح حالة كلمة today التي يرسلها التطبيق
                target_date = datetime.now().date()
                queryset = queryset.filter(createAt__date=target_date)
            else:
                try:
                    target_date = datetime.strptime(created_range, '%Y-%m-%d').date()
                    queryset = queryset.filter(createAt__date=target_date)
                except ValueError:
                    pass  # Ignore invalid date format

        # Handle date range (week/month/custom)
        else:
            try:
                start_str, end_str = created_range.split(',')
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
                # Add one day to end_date to include the entire end day
                end_date += timedelta(days=1)
                queryset = queryset.filter(createAt__range=(start_date, end_date))
            except (ValueError, IndexError):
                pass  # Ignore invalid date formats

    # Apply other filters from Add_Delete_filter and order it for consistent pagination
    filtered_queryset = Add_Delete_filter(request.GET, queryset=queryset).qs.order_by('-createAt')

    # Apply Pagination
    paginator = Paginator(filtered_queryset, limit)
    try:
        paginated_history = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_history = paginator.page(1)
    except EmptyPage:
        paginated_history = []

    # Step 3: Serialize the filtered data
    serializer = Add_DeleteSerializer(paginated_history, many=True)

    return Response({
        'history': serializer.data,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count,
        'is_manager': is_manager,
    })


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
# لا تنسى الاستيرادات الخاصة بك

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def newreservation(request):
    user = request.user
    
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
    except ValueError:
        page = 1
        limit = 20

    data = {
        'reposotory_id': request.GET.get('reposotory_id'),
        'workshop_id': request.GET.get('workshop_id'),
    }
    
    # Get status filter from frontend
    status_filter = request.GET.get('status')

    user_groups = set(user.groups.values_list('name', flat=True))
    is_store_keeper = "StoreKeeper" in user_groups
    is_workshop_manager = "WorkShopManagers" in user_groups
    is_staff = "staff" in user_groups
    is_boss = "boss" in user_groups
    username = user.username

    # 1. Base Query
    if is_workshop_manager:
        details = Reservations.objects.filter(
            Q(user=user) | Q(newOwner=user) | Q(workshop__manager=user)
        ).exclude(Q(workshop__is_working='done')|Q(workshop__is_working='stopped')).order_by('-finalActionTime')    
    elif is_staff:
        details = Reservations.objects.all().exclude(
            Q(workshop__is_working='done')|Q(workshop__is_working='stopped')
        ).order_by('-finalActionTime')
    else:
        details = Reservations.objects.filter(
            Q(product_class__product__reposotory__name=user.repository.name) |
            Q(user__repository=user.repository)|
            Q(newOwner__repository=user.repository)
        ).exclude(Q(workshop__is_working='done')|Q(workshop__is_working='stopped')).order_by('-finalActionTime')
        
    # 2. Apply Repository / Workshop Filters
    if data.get('reposotory_id'):
        rep = Reposotory.objects.get(id=data['reposotory_id'])   
        details = details.filter(user__repository__name=rep.name)

    if data.get('workshop_id'):
        details = details.filter(Q(workshop__id=data['workshop_id'])|Q(newWorkshop__id=data['workshop_id']))
    details = details.filter(is_deleted=False)
    # details = details.filter(is_deleted=False).order_by('-finalActionTime')
    details = details.select_related(
        'user', 'user__store', 'user__repository', 'newOwner', 'newOwner__store', 
        'workshop', 'workshop__manager', 'product_class', 'product_class__product', 
        'product_class__product__reposotory',
    )

    response_data = {
        'page': page,
        'limit': limit,
    }

    # 3. Calculate Counts BEFORE filtering by status (so stats stay visible/accurate)
    if page == 1:
        now = timezone.now()
        five_days_ago = now - timedelta(days=5)
        counts = details.aggregate(
            cancelled_last_5_days=Count('id', filter=Q(reservation_type='cancelled', finalActionTime__gte=five_days_ago)&Q(newOwner__isnull=True)),
            delivered_last_5_days=Count('id', filter=Q(reservation_type='delivered', finalActionTime__gte=five_days_ago)&Q(newOwner__isnull=True)),
            pending_total=Count('id', filter=Q(reservation_type='pending')&Q(newOwner__isnull=True)),
            sent_total=Count('id', filter=Q(reservation_type='sent')&Q(newOwner__isnull=True)),
            returned_from_workshops_total=Count('id', filter=Q(reservation_type='returned from workshops')&Q(newOwner__isnull=True)),
            requested_total=Count('id', filter=Q(reservation_type='requested for workshops')&Q(newOwner__isnull=True)),
            # NEW: Add transfer count in backend so it represents ALL pages
            transfer_total=Count('id', filter=Q(newOwner__isnull=False)),
        )
        total_count = details.count()
        
        response_data.update({
            'count': total_count,
            'is_manager': is_staff,
            'is_workshop_manager': is_workshop_manager,
            'is_store_keeper': is_store_keeper,
            'username': username,
            'counts': counts
        })

    # 4. Apply Status Filter from Frontend Stats Card
    if status_filter:
        
        if status_filter == 'transfer':
            details = details.filter(newOwner__isnull=False)            
        else:
            details = details.filter(reservation_type=status_filter,newOwner__isnull=True)

    # 5. Apply Pagination
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_details = details[start_index:end_index]

    # Extract Amounts
    product_class_ids = {item.product_class_id for item in paginated_details if item.product_class_id}
    amounts_qs = Amounts.objects.filter(product_class_id__in=product_class_ids)
    amounts_dict = {}
    for amt in amounts_qs:
        pc_id = amt.product_class_id
        if pc_id not in amounts_dict:
            amounts_dict[pc_id] = {}
        amounts_dict[pc_id][amt.is_available] = amt.amount
        
    context = {
        'request': request,
        'is_staff': is_staff,
        'is_store_keeper': is_store_keeper,
        'is_workshop_manager': is_workshop_manager,
        'is_boss': is_boss,
        'details': paginated_details,
        'amounts_dict': amounts_dict,
    }

    serializer = ReservationsSerializer(paginated_details, many=True, context=context)
    response_data['details'] = serializer.data
    
    return Response(response_data)


@api_view(['GET'])
def settings(request):
    total = Class.objects.all().count()
    reserved = Amounts.objects.filter(is_available='محجوز').count()
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(hours=2)
    is_manager = request.user.groups.filter(name="manager").exists()

    filtered_history = Add_Delete.objects.filter(createAt__gte=yesterday_start)
    materials = Product.objects.all().count()
    non_approved_qs = Amounts.objects.filter(is_available='محجوز')

    serializer = Add_DeleteSerializer(filtered_history, many=True)
    is_boss = request.user.groups.filter(name="boss").exists()

    return Response({
        'is_manager': is_manager,
        'is_boss': is_boss,

        'history': serializer.data,
        'reserved': reserved,
        'total': total,
        'materials': materials,
        # send a number, not a QuerySet
        'non_approved_reservations': non_approved_qs.count(),
    }, status=HTTP_200_OK)


@api_view(['POST'])
def add_product(request):
    data = {
        'name': request.data.get('name') ,
        'description': request.data.get('description') ,
        'reposotory': request.data.get('reposotory') ,
    }
    is_manager = request.user.groups.filter(name="staff").exists()
    if Product.objects.filter(name=data['name'], reposotory__name=data['reposotory']).exists():
        return Response({'error':'هذا الصنف موجود بالفعل'},status=HTTP_400_BAD_REQUEST)

    if not data['name']:  # Validate input to avoid NULL errors
        return Response({"error": "name field is required"})

    if is_manager and not data['reposotory']:  # Validate input to avoid NULL errors
        return Response({"error":"قم باختيار المستودع اولا"})
    elif not data['reposotory']:
        print('here add_product',request.user.repository.name)
        reposotory=Reposotory.objects.filter(name=request.user.repository.name).first()
    else :
        reposotory=Reposotory.objects.get(name=data['reposotory'])

    if Product.objects.filter(reposotory=reposotory,name=data['name']).exists():
        return Response({'error':'هذا الصنف موجود بالفعل'})
    product_object = Product.objects.create(
        name=data['name'],
        description=data['description'],
        reposotory=reposotory
    )

    user = request.user
    default_user = User.objects.filter(groups__name="staff").first()

    try:

        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        for staff_member in staff_users:
            print(user.username if user else "Anonymous")
            Add_Delete.objects.create(
                changer=user ,
                change_type='اضافة مادة',
                name=data['name'],
                reader=staff_member,
                details=f'الى المستودع {product_object.reposotory}'
            )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")

    Notification.objects.create(
        user=user,
        message=f'قام {user} باضافة المادة {product_object.name} الى المستودع {product_object.reposotory}'

    )


    return Response({
        'done!'
    }, status=HTTP_201_CREATED)

@api_view(['POST'])
def edit_amount_Amount(request):
    #editing amounts in the reposotory by the staff 

    data = {
        'amount_id': request.data.get('amount_id') ,
        'new_amount': request.data.get('new_amount') ,
    }
    is_manager = request.user.groups.filter(name="staff").exists()
    if not is_manager:
        return Response({'error':'غير مسموح لك بتعديل الكمية'},status=status.HTTP_403_FORBIDDEN)
    if not data['amount_id'] or not data['new_amount']:
        return Response({'error':'amount_id and new_amount are required'},status=status.HTTP_400_BAD_REQUEST)   
    try:
        amount_obj = Amounts.objects.get(id=data['amount_id'])
    except Amounts.DoesNotExist:
        return Response({'error':'Amount not found'},status=status.HTTP_404_NOT_FOUND)
    old_amount = amount_obj.amount
    amount_obj.amount = data['new_amount']
    amount_obj.save()
    product_obj = amount_obj.product_class.product
    amount_changed = int(data['new_amount']) - old_amount
    if amount_obj.is_available == 'متاح':
        product_obj.total_available += amount_changed
        product_obj.save()
    elif amount_obj.is_available == 'قيد الوصول':
        product_obj.total_on_way += amount_changed
        product_obj.save()
    user = request.user
    
    
    Add_Delete.objects.create(
                changer=user ,
                change_type='تعديل كمية',
                name=product_obj.name,
                type=amount_obj.product_class.type,
                reader=user,
                details=f'تم تعديل الكمية من {old_amount} الى {amount_obj.amount} في حالة {amount_obj.is_available} في المستودع {product_obj.reposotory}'
            )
    Notification.objects.create(
        user=user,
        message=f'قام {user} بتعديل الكمية في المادة {product_obj.name} في المستودع {product_obj.reposotory}'
    )
    return Response({
        'done!' 
    }, status=HTTP_200_OK)



@api_view(['POST'])
def add_class(request=None, custom_data=None,user=None):
    if user and user.is_authenticated:
        authenticated_user = user
    elif request and request.user.is_authenticated:
        authenticated_user = request.user
    else:
        authenticated_user = None

    data = custom_data or {
        'type': request.data.get('type') if request else None,
        # 'description': request.data.get('description') if request else None,
        'product_id': request.data.get('product_id') if request else None,
        'amount': request.data.get('amount') if request else None,
        'is_available': request.data.get('is_available') if request else None,
        'class_id': request.data.get('class_id') if request else None,
    }

    print('here add_class data ')
    print(data)
    if not data['amount']:
        data['amount']=0
    # Ensure we have a valid user
    if not data['type'] :
        if not data['class_id']:
            return Response({'error': 'Type field is required'}, status=HTTP_400_BAD_REQUEST)
        class_obj=Class.objects.get(id=data['class_id'])
        data['type']=class_obj.type
    user = authenticated_user 
    print(user)
    print(1)
    if not Product.objects.filter(id=data['product_id']).exists():
        return Response({'error': 'There is no such Product'}, status=HTTP_400_BAD_REQUEST)
    product = Product.objects.filter(id=data['product_id']).first()
    print(2)

    if not Class.objects.filter(product=product,type=data['type']).exists():
        Class.objects.create(
            product=product,
            type=data['type']
        )
        default_user = User.objects.filter(groups__name="staff").first()
        print(3)
        try:

            staff_group = Group.objects.get(name="staff")
            staff_users = User.objects.filter(groups=staff_group)
            print(4)

            for staff_member in staff_users:
                print(user if user else "Anonymous")
                Add_Delete.objects.create(
                    changer=user ,
                    change_type='اضافة نوع من مادة',
                    name=product.name,
                    type=data['type'],
                    reader=staff_member,

                    )
        except Group.DoesNotExist:
            print("Warning: Staff group does not exist")
    print(1.2)

    print(1)
    Class_object = Class.objects.get(type=data['type'], product=product)
    print(1.5)
    print(Class_object)
    Class_object.active='Yes'
    Class_object.save()
    if Amounts.objects.filter(product_class=Class_object, is_available=data['is_available']).exists():
        print(2)
        amount_obj = Amounts.objects.filter(product_class=Class_object, is_available=data['is_available']).first()
        amount_obj.amount += int(data['amount'])
        amount_obj.save()
    else:
        print(3)
        Amounts.objects.create(
            amount=data['amount'],
            is_available=data['is_available'],
            product_class=Class_object
        )

    # Send notification and record transaction
    default_user = User.objects.filter(groups__name="staff").first()
    if data['is_available']=='متاح':
        product.total_available += int(data['amount'])
        product.save()
    if data['is_available']=='قيد الوصول':
        product.total_on_way += int(data['amount'])
        product.save()

    try:
      if not custom_data:
        staff_group = Group.objects.get(name="staff")
        staff_users = User.objects.filter(groups=staff_group)
        for staff_member in staff_users:
            print(user  if user else "Anonymous")
            Add_Delete.objects.create(
                changer=user   ,
                change_type='اضافة كمية',
                name=product.name,
                amount=data['amount'],
                type=data['type'],
                reader=staff_member,
                details=data['is_available']
            )
    except Group.DoesNotExist:
        print("Warning: Staff group does not exist")
    
    return Response({'done!'}, status=HTTP_201_CREATED)


def add_class_fun(mytype,product_id,amount,is_available,class_id,user):
    
    try:
        data =  {
            'type': mytype if mytype else None,
            # 'description': request.data.get('description') if request else None,
            'product_id': product_id if product_id else None,
            'amount': amount if amount else None,
            'is_available': is_available if is_available else None,
            'class_id': class_id if class_id else None,
        }
        print('here add_class_fun ')
        print(data)
        if not data['amount']:
            data['amount']=0
        # Ensure we have a valid user
        if not data['type'] :
            if not data['class_id']:
                return Response({'error': 'Type field is required'}, status=HTTP_400_BAD_REQUEST)
            class_obj=Class.objects.get(id=data['class_id'])
            data['type']=class_obj.type
        print(user)
        print(1)
        if not Product.objects.filter(id=data['product_id']).exists():
            return Response({'error': 'There is no such Product'}, status=HTTP_400_BAD_REQUEST)
        product = Product.objects.filter(id=data['product_id']).first()
        print(2)

        if not Class.objects.filter(product=product,type=data['type']).exists():
            Class.objects.create(
                product=product,
                type=data['type']
            )
            default_user = User.objects.filter(groups__name="staff").first()

        print(1.2)

        print(1)
        Class_object = Class.objects.get(type=data['type'], product=product)
        print(1.5)
        print(Class_object)
        Class_object.active='Yes'
        Class_object.save()
        if Amounts.objects.filter(product_class=Class_object, is_available=data['is_available']).exists():
            print(2)
            amount_obj = Amounts.objects.filter(product_class=Class_object, is_available=data['is_available']).first()
            amount_obj.amount += int(data['amount'])
            amount_obj.save()
        else:
            print(3)
            Amounts.objects.create(
                amount=data['amount'],
                is_available=data['is_available'],
                product_class=Class_object
            )

        # Send notification and record transaction
        default_user = User.objects.filter(groups__name="staff").first()
        if data['is_available']=='متاح':
            product.total_available += int(data['amount'])
            product.save()
        if data['is_available']=='قيد الوصول':
            product.total_on_way += int(data['amount'])
            product.save()

        
        return "done"
    except Exception as e:
        print("Error in add_class_fun:", str(e))
        return str(e)


@api_view(['POST'])
def changetype(request):
    data = {
        'amount_id': request.data.get('amount_id'),

        'amount': request.data.get('amount'),
        'new_mode_is_available': request.data.get('new_mode_is_available'),
    }
    print("h i")
    print(data['amount_id'])
    print(data['amount'])
    print(data['new_mode_is_available'])

    amount = Amounts.objects.get(id=data['amount_id'])
    print(0)
    print("h i")

    class_obj =amount.product_class
    print(class_obj)

    if amount:
        if amount.amount >= int(data['amount']):
            user = request.user
            default_user = User.objects.filter(groups__name="staff").first()

            # try:

            #     staff_group = Group.objects.get(name="staff")
            #     staff_users = User.objects.filter(groups=staff_group)
            #     for staff_member in staff_users:
            #        if request.user != staff_member:
            #         print('hiiiiiiiiii')
            #         print(user)
            #         Add_Delete.objects.create(
            #             changer=user ,
            #             change_type='تعديل',
            #             name=class_obj.product.name,
            #             amount=data['amount'],
            #             type=class_obj.type,
            #             reader=staff_member,
            #             details= f"من {} الى {amount.is_available}"
            #         )
            # except Group.DoesNotExist:
            #     print("Warning: Staff group does not exist")


            product=class_obj.product

            if amount.is_available == 'متاح':
                product.total_available -= int(data['amount'])
                print('متاح')
                product.save()
            if amount.is_available == 'قيد الوصول':
                product.total_on_way -= int(data['amount'])
                print('قيد الوصول')
                product.save()

            

            data['is_available'] = data['new_mode_is_available']
            amount.amount -= int(data['amount'])
            amount.save()
            data['type']=class_obj.type
            data['product_id']=class_obj.product.id
            django_request = HttpRequest()
            django_request.method = 'POST'
            django_request.POST = data
            print("here before")
            print(data['is_available'])

            return add_class(django_request, custom_data=data, user=request.user)
        elif amount.amount < int(data['amount']):
            return Response({"error": "ليس لديك ما يكفي من المواد"}, status=HTTP_404_NOT_FOUND)

    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)



@api_view(['POST'])
def reserve(request=None, custom_data=None, user=None):
    if user and user.is_authenticated:
        authenticated_user = user
    elif request and request.user.is_authenticated:
        authenticated_user = request.user
    else:
        authenticated_user = None


    data = custom_data or {
        'amount_id': request.data.get('amount_id') ,
        'amount': request.data.get('amount') ,
        'is_available': None,
    }
    print('afdassddsad')
    print(data['amount'])
    print(data['amount_id'])
    amount = Amounts.objects.get(
       id=data['amount_id']
    )
    class_obj = amount.product_class
    name=class_obj.product.name
    type=class_obj.type
    print(1)
    print(data)
    print(amount)
    amountt=data['amount']

    if amount:
        if amount.amount >= int(data['amount']):
            user =authenticated_user
            print("user.username")

            # print(user)
            # default_user = User.objects.filter(groups__name="staff").first()

            # try:

            #     staff_group = Group.objects.get(name="staff")
            #     staff_users = User.objects.filter(groups=staff_group)
            #     for staff_member in staff_users:
            #        if user != staff_member:

            #         Add_Delete.objects.create(
            #             changer=user ,
            #             change_type='حجز',
            #             name=name,
            #             amount=data['amount'],
            #             type=type,
            #             reader=staff_member,

            #         )
            # except Group.DoesNotExist:
            #     print("Warning: Staff group does not exist")
            product = class_obj.product

            product.total_available -= int(data['amount'])
            product.save()


            # Add_Delete.objects.create(
            #     changer=user ,
            #     change_type='حجز',
            #     name=name,
            #     amount=data['amount'],
            #     type=type,
            #     reader=user ,
            # )

            Reservations.objects.create(
                amount=data['amount'],
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=Workshop.objects.get(id=data['workshop_id']) if 'workshop_id' in data else None

            )

            data['is_available'] ='محجوز'
            amount.amount -= int(data['amount'])
            amount.save()
            data['product_id']=class_obj.product.id
            data['type']=type

            django_request = HttpRequest()
            django_request.method = 'POST'
            django_request.POST = data
            print('try')
            # Notification.objects.create(
            #     user=user,
            #     message=f' لقد قام {request.user.username} بحجز {amountt} قطعة من المنتج {amount.product_class.type} '
            # )
            return add_class(django_request, custom_data=data, user=request.user)
        elif amount.amount < int(data['amount']):
            return Response({"error": "You have asked for more than what you have"}, status=HTTP_404_NOT_FOUND)

    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)


def reserve_fun(amount_id,amount,user):
   

    data =  {
        'amount_id': amount_id ,
        'amount': amount ,
        'is_available': None,
    }
    print(data['amount'])
    print(data['amount_id'])
    amount = Amounts.objects.get(
       id=data['amount_id']
    )
    class_obj = amount.product_class
    name=class_obj.product.name
    type=class_obj.type
    print(1)
    print(data)
    print(amount)
    amountt=data['amount']

    if amount:
        if amount.amount >= int(data['amount']):
            print("user.username")

            print(user)
            default_user = User.objects.filter(groups__name="staff").first()

            product = class_obj.product

            product.total_available -= int(data['amount'])
            product.save()


           

            Reservations.objects.create(
                amount=data['amount'],
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=Workshop.objects.get(id=data['workshop_id']) if 'workshop_id' in data else None

            )

            data['is_available'] ='محجوز'
            amount.amount -= int(data['amount'])
            amount.save()
            data['product_id']=class_obj.product.id
            data['type']=type

            django_request = HttpRequest()
            django_request.method = 'POST'
            django_request.POST = data
            print('try')
            # add_class_fun(mytype,product_id,amount,is_available,class_id,user)
            return add_class_fun(None,class_obj.product.id,int(data['amount']),'محجوز',class_obj.id,user)
        elif amount.amount < int(data['amount']):
            return Response({"error": "You have asked for more than what you have"}, status=HTTP_404_NOT_FOUND)

    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)



@api_view(['POST'])
def cancle_reservation(request):
    data = {

        'Reservation_id': request.data.get('Reservation_id'),

    }
    reservation=Reservations.objects.get(id=data['Reservation_id'])
    res_owner=reservation.user
    class_obj = reservation.product_class
    data['type']=class_obj.type
    data['name']=class_obj.product.name
    data['amount']=reservation.amount
    data['product_id']=class_obj.product.id
    print(reservation)
    print(class_obj)
    amount = Amounts.objects.filter(
        is_available='محجوز',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    user = request.user
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)



    amountt=data['amount']

    x=cancle_reservation_fun(reservation.id,request.user)
    if x == 'done':
        user = request.user
        # default_user = User.objects.filter(groups__name="staff").first()
        # 
        # try:

        #     staff_group = Group.objects.get(name="staff")
        #     staff_users = User.objects.filter(groups=staff_group)
        #     for staff_member in staff_users:
        #       if request.user != staff_member:

        #         Add_Delete.objects.create(
        #             changer=user ,
        #             change_type='الغاء حجز',
        #             name=data['name'],
        #             amount=data['amount'],
        #             type=data['type'],
        #             reader=staff_member,

        #         )
                
        # except Group.DoesNotExist:
        #     print("Warning: Staff group does not exist")
        Add_Delete.objects.create(
            changer=res_owner ,
            change_type='الغاء حجز',
            name=data['name'],
            amount=data['amount'],
            type=data['type'],
            reader=user ,
        )
        Notification.objects.create(
            user=res_owner,
            message=f' لقد قام {user} بالغاء حجز {res_owner} بكمية {amountt} قطعة من المنتج {amount.product_class.type}'
        )
        
        data['is_available'] = 'متاح'
      
        prodict_obj=class_obj.product
        
        django_request = HttpRequest()
        django_request.method = 'POST'
        django_request.POST = data
        print('try')
        
        return Response({"message": "تم الغاء الحجز بنجاح"}, status=HTTP_200_OK)
    else:
        return Response({"error": x}, status=HTTP_404_NOT_FOUND)



def cancle_reservation_fun(Reservation_id,user):
    data = {

        'Reservation_id': Reservation_id

    }
    print("here cancle_reservation_fun")
    reservation=Reservations.objects.get(id=Reservation_id)
    res_owner=reservation.user
    class_obj = reservation.product_class
    data['type']=class_obj.type
    data['name']=class_obj.product.name
    data['amount']=reservation.amount
    data['product_id']=class_obj.product.id
    print(reservation)
    print(class_obj)
    amount = Amounts.objects.filter(
        is_available='محجوز',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)



    amountt=data['amount']

    print(user)
    print(class_obj)
    print(data['amount'])
    print(1)
    print(amount)
    if reservation:
        
        default_user = User.objects.filter(groups__name="staff").first()

        
       
        reservation.reservation_type='cancelled'
        reservation.save()
        data['is_available'] = 'متاح'
        amount.amount -= int(data['amount'])
        amount.save()
        prodict_obj=class_obj.product
        reservation.finalActionTime=timezone.now()
        reservation.save()
        print('add_class_fun ...')
        return add_class_fun(None,data['product_id'],data['amount'],data['is_available'],class_obj.id,user)
    elif amount.amount < int(data['amount']):
        return  "some thing goes wrong"

    return "No matching reservation found"


@api_view(['POST'])
def confirm_reservation(request):
    data = {

        'Reservation_id': request.data.get('Reservation_id'),
        # 'username': request.data.get('username'),

    }
    print("here confirm_reservation", data)
    reservation = Reservations.objects.get(id=data['Reservation_id'])
    if reservation.workshop:
        res_own=reservation.workshop.manager
    else:
        res_own=reservation.user
    
    class_obj = reservation.product_class
    data['type'] = class_obj.type
    data['name'] = class_obj.product.name
    data['amount'] = reservation.amount
    data['product_id'] = class_obj.product.id
    amountt=data['amount']


    amount = Amounts.objects.filter(
        is_available='محجوز',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    # user=User.objects.get(username=data['username'])
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)




    if reservation :
        user = request.user
        default_user = User.objects.filter(groups__name="staff").first()

        # try:

        #     staff_group = Group.objects.get(name="staff")
        #     staff_users = User.objects.filter(groups=staff_group)
        #     for staff_member in staff_users:
        #       if request.user != staff_member:

        #         Add_Delete.objects.create(
        #             changer=user  ,
        #             change_type='تسليم',
        #             name=data['name'],
        #             amount=data['amount'],
        #             type=data['type'],
        #             reader=staff_member,
        #         )
        # except Group.DoesNotExist:
        #     print("Warning: Staff group does not exist")
        # Add_Delete.objects.create(
        #     changer=user ,
        #     change_type='تسليم',
        #     name=data['name'],
        #     amount=data['amount'],
        #     type=data['type'],
        #     reader=user ,
        # )
        # Notification.objects.create(
        #     user=res_own,
        #     message=f' لقد تم تاكيد حجز {res_own.username} بكمية {amountt} قطعة من المنتج {amount.product_class.type}  '
        # )
        old_rep_obj=reservation.product_class.product.reposotory
        new_rep_obj=Reposotory.objects.get(name=res_own.store.name)

        if not Product.objects.filter(name=data['name'],reposotory=new_rep_obj).exists():
            pro_obj=Product.objects.create(name=data['name'], reposotory=new_rep_obj)
        else:
            pro_obj=Product.objects.filter(name=data['name'],reposotory=new_rep_obj).first()
        
        
        print('pro_obj')
        print(pro_obj)
        data['product_id']=pro_obj.id
        data['is_available']='متاح'
        data['user']='متاح'
        django_request = HttpRequest()
        django_request.method = 'POST'
        django_request.POST = data
        print('try')
        print('try2')
        if reservation.workshop:
            other_reservation=Reservations.objects.filter(
                        product_class=class_obj,
                        reservation_type='delivered',
                        workshop=reservation.workshop,
                        used_in_workshop=-1

                        ).exclude(id=data['Reservation_id']).first()
            print('other_reservation',other_reservation.id if other_reservation else None)
            if reservation.reservation_type=='sent' and other_reservation:
                    print('here if')
                   
                    reservation.amount+=other_reservation.amount
                    reservation.save()
                    other_reservation.delete()
        
        reservation.reservation_type='delivered'
        reservation.EndAt=timezone.now()
        reservation.finalActionTime=timezone.now()

        reservation.save()
        return add_class(django_request, custom_data=data, user=request.user)


    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)



@api_view(['POST'])
def send_reservation(request):
    data = {

        'Reservation_id': request.data.get('Reservation_id'),
        'username': request.data.get('username'),

    }
    try:
        print("here send_reservation", data) 
        reservation = Reservations.objects.get(id=data['Reservation_id'])
        res_own=reservation.user
        print("1 ") 

        class_obj = reservation.product_class
        data['type'] = class_obj.type
        data['name'] = class_obj.product.name
        data['amount'] = reservation.amount
        data['product_id'] = class_obj.product.id
        amountt=data['amount']
        print("2 ") 

        amount = Amounts.objects.filter(
            is_available='محجوز',
            # product_class__product__name=data['name'],
            # product_class__type=data['type']
            product_class=class_obj,
        ).first()
        user=User.objects.get(username=data['username'])
        # In your view, before you call `.first()`:
        # print("Params:", qs.query.params)
        print("3 ") 

        if reservation :
            if Reservations.objects.filter(
                    product_class=class_obj,
                    product_class__type=data['type'],
                    reservation_type='requested for workshops'
                    ).exists() and reservation.reservation_type!='requested for workshops' and reservation.workshop==None:
                        return Response({'error': 'هناك حجز مطلوب لصالح ورشة لهذه المادة. قم بمعالجة ذلك الحجز اولا.'},
                                    status=HTTP_400_BAD_REQUEST)
            user = request.user
            # default_user = User.objects.filter(groups__name="staff").first()
            # try:
            #     print("4 ") 

            #     staff_group = Group.objects.get(name="staff")
            #     staff_users = User.objects.filter(groups=staff_group)
            #     for staff_member in staff_users:
            #       if request.user != staff_member:
            #         Add_Delete.objects.create(
            #             changer=user ,
            #             change_type='تسليم',
            #             name=data['name'],
            #             amount=data['amount'],
            #             type=data['type'],
            #             reader=staff_member,
            #         )
            # except Group.DoesNotExist:
            #     print("Warning: Staff group does not exist")
            # Add_Delete.objects.create(
            #     changer=user ,
            #     change_type='ارسال',
            #     name=data['name'],
            #     amount=data['amount'],
            #     type=data['type'],
            #     reader=user ,
            # )
            # print("5 ") 

            # Notification.objects.create(
            #     user=res_own,
            #     message=f' لقد تم ارسال حجزك بكمية {amountt} قطعة من المنتج {amount.product_class.type}  '
            # )
            # Notification.objects.create(
            #     user=request.user,
            #     message=f' لقد قام {request.user.username}  بارسال حجز بكمية {amountt} قطعة من المنتج {amount.product_class.type}  '
            # )
            reservation.reservation_type='sent'
            print('reservation.workshop')
            print(reservation.workshop)
            print(reservation.workshop==None)
            if reservation.workshop!=None :
                print('YES')
                reservation.workshop.is_working='Yes'
                reservation.workshop.save()
            reservation.save()
            amount.amount -= int(data['amount'])
            amount.save()
            reservation.finalActionTime=timezone.now()
            reservation.save()

            return Response({"done": "you have confirmed the reservation "}, status=HTTP_200_OK)
        return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Error in send_reservation:", str(e))
        return Response({"error": "An error occurred while processing the request."}, status=HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_requested_reservation(request):
    data = {

        'Reservation_id': request.data.get('Reservation_id'),
        'username': request.data.get('username'),

    }
    print("here send_requested_reservation", data) 
    reservation = Reservations.objects.get(id=data['Reservation_id'])
    res_own=reservation.user
    print("1 ") 

    class_obj = reservation.product_class
    product_obj=class_obj.product
    data['type'] = class_obj.type
    data['name'] = class_obj.product.name
    data['amount'] = reservation.amount
    data['product_id'] = class_obj.product.id
    amountt=data['amount']
    print("2 ") 

    amount = Amounts.objects.filter(
        is_available='مطلوب للشراء',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    amount_available=Amounts.objects.filter( is_available='متاح',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj).first()
    if amount_available.amount < int(data['amount']):
        return Response({'error': 'ليس لديك ما يكفي من المواد المتاحة لتلبية هذا الطلب.'},
                                status=HTTP_400_BAD_REQUEST)
    user=User.objects.get(username=data['username'])
    # In your view, before you call `.first()`:
    # print("Params:", qs.query.params)
    print("3 ") 

    if reservation :
        user = request.user
        # default_user = User.objects.filter(groups__name="staff").first()
        # try:
        #     print("4 ") 

        #     staff_group = Group.objects.get(name="staff")
        #     staff_users = User.objects.filter(groups=staff_group)
        #     for staff_member in staff_users:
        #       if request.user != staff_member:
        #         Add_Delete.objects.create(
        #             changer=user ,
        #             change_type='تسليم',
        #             name=data['name'],
        #             amount=data['amount'],
        #             type=data['type'],
        #             reader=staff_member,
        #         )
        # except Group.DoesNotExist:
        #     print("Warning: Staff group does not exist")
        # Add_Delete.objects.create(
        #     changer=user ,
        #     change_type='ارسال',
        #     name=data['name'],
        #     amount=data['amount'],
        #     type=data['type'],
        #     reader=user ,
        # )
        # print("5 ") 

        # Notification.objects.create(
        #     user=res_own,
        #     message=f' لقد تم ارسال حجزك بكمية {amountt} قطعة من المنتج {amount.product_class.type}  '
        # )
        # Notification.objects.create(
        #     user=request.user,
        #     message=f' لقد قام {request.user.username}  بارسال حجز بكمية {amountt} قطعة من المنتج {amount.product_class.type}  '
        # )
        reservation.reservation_type='sent'
        print('reservation.workshop')
        print(reservation.workshop)
        print(reservation.workshop==None)
        if reservation.workshop!=None :
            print('YES')
            reservation.workshop.is_working='Yes'
            reservation.workshop.save()
        reservation.save()
        amount.amount -= int(data['amount'])
        amount.save()
        amount_available.amount -= int(data['amount'])
        amount_available.save()
        product_obj.total_available -= int(data['amount'])
        product_obj.total_requested -= int(data['amount'])
        product_obj.save()
        reservation.finalActionTime=timezone.now()
        reservation.save()
        return Response({"done": "you have confirmed the reservation "}, status=HTTP_200_OK)
    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)



@api_view(['POST'])
def confirm_requested_reservation(request):
    # استلام ما تبقى من ورشة عندما تم اعادة ما تبقى من ورشة الى مستودع
    data = {

        'Reservation_id': request.data.get('Reservation_id'),
        # 'username': request.data.get('username'),

    }
    print("here ", data)
    reservation = Reservations.objects.get(id=data['Reservation_id'])
    res_own=reservation.user
    class_obj = reservation.product_class
    data['type'] = class_obj.type
    data['name'] = class_obj.product.name
    data['amount'] = reservation.amount
    data['product_id'] = class_obj.product.id
    amountt=data['amount']


    
    # user=User.objects.get(username=data['username'])
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)




    if reservation :
        user = request.user
        default_user = User.objects.filter(groups__name="staff").first()

        # try:

        #     staff_group = Group.objects.get(name="staff")
        #     staff_users = User.objects.filter(groups=staff_group)
        #     for staff_member in staff_users:
        #       if request.user != staff_member:

        #         Add_Delete.objects.create(
        #             changer=user  ,
        #             change_type='تسليم',
        #             name=data['name'],
        #             amount=data['amount'],
        #             type=data['type'],
        #             reader=staff_member,

        #         )
        # except Group.DoesNotExist:
        #     print("Warning: Staff group does not exist")
        # Add_Delete.objects.create(
        #     changer=user ,
        #     change_type='تسليم',
        #     name=data['name'],
        #     amount=data['amount'],
        #     type=data['type'],
        #     reader=user ,
        # )
        # Notification.objects.create(
        #     user=res_own,
        #     message=f' لقد تم اعادة ما تبقى من الورشة بكمية {amountt} قطعة من المنتج {class_obj.type}  '
        # )
        old_rep_obj=reservation.product_class.product.reposotory
        new_rep_obj=Reposotory.objects.get(name=user.repository.name)

        if not Product.objects.filter(name=data['name'],reposotory=new_rep_obj).exists():
            pro_obj=Product.objects.create(name=data['name'], reposotory=new_rep_obj)
        else:
            pro_obj=Product.objects.filter(name=data['name'],reposotory=new_rep_obj).first()
        reservation.reservation_type='delivered'
        reservation.workshop=None
        reservation.EndAt=timezone.now()
        reservation.save()
        
        print('pro_obj')
        print(pro_obj)
        data['product_id']=pro_obj.id
        data['is_available']='متاح'
        data['user']='متاح'
        django_request = HttpRequest()
        django_request.method = 'POST'
        django_request.POST = data
        print('try')
        print('try2')
        reservation.finalActionTime=timezone.now()
        reservation.save()
        return add_class(django_request, custom_data=data, user=request.user)


    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)


@api_view(['POST'])
def cancle_requested_reservation(request):
    data = {

        'Reservation_id': request.data.get('Reservation_id'),

    }
    reservation=Reservations.objects.get(id=data['Reservation_id'])
    res_owner=reservation.user
    class_obj = reservation.product_class
    data['type']=class_obj.type
    data['name']=class_obj.product.name
    data['amount']=reservation.amount
    data['product_id']=class_obj.product.id
    print(reservation)
    print(class_obj)
    amount = Amounts.objects.filter(
        is_available='مطلوب للشراء',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    user = request.user
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)



    amountt=data['amount']

    x=cancle_requested_reservation_fun(reservation.id,request.user)
    if x == 'done':
        user = request.user
        default_user = User.objects.filter(groups__name="staff").first()

        try:

            staff_group = Group.objects.get(name="staff")
            staff_users = User.objects.filter(groups=staff_group)
            for staff_member in staff_users:
              if request.user != staff_member:

                Add_Delete.objects.create(
                    changer=user ,
                    change_type='الغاء حجز',
                    name=data['name'],
                    amount=data['amount'],
                    type=data['type'],
                    reader=staff_member,

                )
                
        except Group.DoesNotExist:
            print("Warning: Staff group does not exist")
        Add_Delete.objects.create(
            changer=res_owner ,
            change_type='الغاء حجز',
            name=data['name'],
            amount=data['amount'],
            type=data['type'],
            reader=user ,
        )
        Notification.objects.create(
            user=res_owner,
            message=f' لقد قام {user} الغاء حجز {res_owner} بكمية {amountt} قطعة من المنتج {amount.product_class.type} '
        )
        
        

        return Response({"message": "تم الغاء الحجز بنجاح"}, status=HTTP_200_OK)
    else:
        return Response({"error": x}, status=HTTP_404_NOT_FOUND)



def cancle_requested_reservation_fun(Reservation_id,user):
    data = {

        'Reservation_id': Reservation_id

    }
    print("here cancle_requested_reservation_fun")
    reservation=Reservations.objects.get(id=Reservation_id)
    res_owner=reservation.user
    class_obj = reservation.product_class
    data['type']=class_obj.type
    data['name']=class_obj.product.name
    data['amount']=reservation.amount
    data['product_id']=class_obj.product.id
    print(reservation)
    print(class_obj)
    amount = Amounts.objects.filter(
        is_available='مطلوب للشراء',
        # product_class__product__name=data['name'],
        # product_class__type=data['type']
        product_class=class_obj,
    ).first()
    
    # In your view, before you call `.first()`:

    # print("Params:", qs.query.params)



    amountt=data['amount']

    print(user)
    print(class_obj)
    print(data['amount'])
    print(1)
    print(amount)
    if reservation:
        
        default_user = User.objects.filter(groups__name="staff").first()

        
       
        reservation.reservation_type='cancelled'
        reservation.save()
        data['is_available'] = 'متاح'
        print('amount after : ',amount.amount)
        amount.amount -= int(data['amount'])
        amount.save()
        print('amount before : ',amount.amount)
        product_obj=class_obj.product

        print('total_requested after : ',product_obj.total_requested )

        product_obj.total_requested -= int(data['amount'])
        product_obj.save()
        print('total_requested before : ',product_obj.total_requested )
        reservation.finalActionTime=timezone.now()
        reservation.reservation_type='cancelled'
        reservation.save()
        return 'done'
    return "No matching reservation found"



@api_view(['GET'])
def search_materials(request):
    # Apply the same base filtering as the home view
    is_manager = request.user.groups.filter(name="staff").exists()
    if is_manager:
        base_qs = Amounts.objects.filter(amount__gt=0).exclude(product_class__product__reposotory__name='الورشات')
    else:
        base_qs = Amounts.objects.filter(
            Q(amount__gt=0) & (Q(is_available='قيد الوصول') | Q(is_available='متاح'))
        ).exclude(product_class__product__reposotory__name='الورشات')

    # Create a custom filter set for search
    class SearchFilter(django_filters.FilterSet):
        query = django_filters.CharFilter(method='custom_query_filter', label='Search Query')
        category = django_filters.CharFilter(field_name='product_class__product__name', lookup_expr='icontains')
        status = django_filters.CharFilter(field_name='is_available', lookup_expr='iexact')

        class Meta:
            model = Amounts
            fields = []

        def custom_query_filter(self, queryset, name, value):
            return queryset.filter(
                Q(product_class__product__name__icontains=value) |
                Q(product_class__product__description__icontains=value) |
                Q(product_class__type__icontains=value)
            )

    # Apply search filters
    search_filter = SearchFilter(request.GET, queryset=base_qs)
    filtered_qs = search_filter.qs

    # Serialize results
    serializer = AmountsSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data

    # Dedupe by (name, description)


    return Response(raw, status=HTTP_200_OK)



@api_view(['GET'])
def reposotory(request):
    is_manager = request.user.groups.filter(name="staff").exists()
    is_store_keeper = request.user.groups.filter(name="StoreKeeper").exists()
    user =request.user

    if is_manager or is_store_keeper:
        repositories=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
    
    elif   request.user.groups.filter(name="WorkShopManagers").exists():
        # repositories=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
        repositories = user.allowed_repositories.filter(is_working='Yes').exclude(name='الورشات')

    elif  Reposotory.objects.filter(is_working='Yes',name=request.user.repository.name).exists():
        repositories = user.allowed_repositories.filter(is_working='Yes').exclude(Q(name=request.user.repository.name)|Q(name='الورشات'))
    else:
        repositories = user.allowed_repositories.filter(is_working='Yes').exclude(name='الورشات')

    serializer=ReposotorySerializer(repositories,many=True)
    print('herrrrrrr reposotory')
    print(repositories.count())
    return Response({
        'reposotories': serializer.data

    })



@api_view(['GET'])
def reposotory_for_showing(request):
    is_manager = request.user.groups.filter(name="staff").exists()
    is_store_keeper = request.user.groups.filter(name="StoreKeeper").exists()
    user =request.user

    
    if   request.user.groups.filter(name="WorkShopManagers").exists():
        # repositories=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
        repositories = user.allowed_repositories.filter(is_working='Yes').exclude(name='الورشات')

    else :
        repositories=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
    
    
    serializer=ReposotorySerializer(repositories,many=True)
    
    
    return Response({
        'reposotories': serializer.data

    })



@api_view(['POST'])
def addReposotory(request):
    data = {
        'location': request.data.get('location'),
        'name': request.data.get('name'),
    }
    try:
        if Reposotory.objects.filter(name=data['name']).exists():
            return Response({'error':'هذا المستودع موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        
        Reposotory.objects.create(
            name=data['name'],
            location=data['location'],
        )
    except Exception as e:
        return Response({'error':'data you entered is not enough'})

    return Response({'details:': 'your request has been proceed succefully!'})


@api_view(['POST'])
def reposotoryToggleStatusView(request):
        try:
            reposotory_id=request.GET.get('reposotory_id')
            reposotory = Reposotory.objects.get(id=reposotory_id)
            if reposotory.name == 'الرئيسي' or reposotory.name == 'المرجة':
                return Response({'error': 'لا يمكن تعطيل هذا المستودع'}, status=status.HTTP_400_BAD_REQUEST)
            # Prevent deleting admin users
            reposotory.is_working='No'
            reposotory.save()
            users = User.objects.all()
            for curuser in users:
                Notification.objects.create(
                    user=curuser,
                    message=f' لقد تم تعطيل المستودع {reposotory.name} '
                )
            return Response({'message': 'تم تعطيل المستودع بنجاح'}, status=status.HTTP_200_OK)
        except Reposotory.DoesNotExist:
            return Response({'error': 'المستودع غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )


@api_view(['POST'])
def turnResevation(request):
    data={
        'reservation_id':request.data.get('reservation_id'),
         'new_username':request.data.get('new_username'),
         'new_workshop_name':request.data.get('new_workshop_name'),
    }

    print('turnResevation')
    print('data:', data)
    print(data['reservation_id'])
    print(data['new_username'])
    if  data['reservation_id']:
        
        reservauion=Reservations.objects.get(id=data['reservation_id'])
    else:
        return Response ({'error':'you did not enter the informations properly'})
    if data['new_workshop_name']:
        print('new_workshop_name:', data['new_workshop_name'])
        if reservauion.workshop and reservauion.workshop.name:
            if  data['new_workshop_name'] == reservauion.workshop.name:
                print('same workshop,the error has been araised')
                return Response ({'error':'هذا الحجز موجود بالفعل في هذه الورشة'},status=status.HTTP_400_BAD_REQUEST)
    
    if data['new_username'] and reservauion.workshop==None:
        user=User.objects.get(username=data['new_username'])
        if  user.repository == reservauion.user.repository:
            return Response ({'error':'الحجز موجود بالفعل في متجر هذا المستخدم'},status=status.HTTP_400_BAD_REQUEST)        
        
    if data['new_workshop_name']:
        new_workshop=Workshop.objects.get(name=data['new_workshop_name'])
        reservauion.newWorkshop=new_workshop
        if reservauion.reservation_type=='returned from workshops':
            reservauion.reservation_type='sent'
        new_user=new_workshop.manager
        new_workshop.is_working='Yes'
        new_workshop.save()
        reservauion.save()
    elif data['new_username']:
        new_user=User.objects.get(username=data['new_username'])
    else :
        return Response ({'error':'you did not enter the informations properly'})

     

    reservauion.newOwner=new_user
    reservauion.save()
    Notification.objects.create(
        user=request.user,
        message=f' لقد قام {request.user.username}  بتحويل حجزك من المنتج {reservauion.product_class.type} الى {new_user.username} '
    )
    Notification.objects.create(
        user=new_user,
        message=f' لقد قام {request.user.username} بتحويل حجزه اليك من المنتج {reservauion.product_class.type}  '
    )
    reservauion.finalActionTime=timezone.now()
    reservauion.save()
    return Response({'details': 'the proceed went successfully'})


@api_view(['POST'])
def confirmTurnResevation(request):
    data = {
        'Reservation_id': request.data.get('Reservation_id'),
    }
    print('here')
    print(data['Reservation_id'])
    reservauion = Reservations.objects.get(id=data['Reservation_id'])

    if reservauion :
        if reservauion.newWorkshop:
            old_user=reservauion.user
            reservauion.user = reservauion.newOwner
            reservauion.newOwner = None
            reservauion.workshop=reservauion.newWorkshop
            reservauion.newWorkshop=None
            reservauion.save()
        else :
            old_user=reservauion.user
            reservauion.user = reservauion.newOwner
            reservauion.newOwner = None
            reservauion.workshop=None
            reservauion.newWorkshop=None

            reservauion.save()    

        Notification.objects.create(
            user=old_user,
            message=f' لقد قام {request.user.username} بتاكيد تحويل حجزك اليه من المنتج {reservauion.product_class.type}  '
        )
        Notification.objects.create(
            user=request.user,
            message=f' لقد قام {request.user.username}  بتاكيد استلام تحويل حجز {old_user.username} من المنتج {reservauion.product_class.type} اليك '
        )
        reservauion.finalActionTime=timezone.now()
        reservauion.save()
    else:
        return Response({'error': 'you did not enter the informations properly'})
    return Response({'details': 'the proceed went successfully'})


@api_view(['POST'])
def cancelTurnResevation(request):
    data = {
        'Reservation_id': request.data.get('Reservation_id'),
    }
    reservauion = Reservations.objects.get(id=data['Reservation_id'])
    if reservauion :
        old_user=reservauion.user
        reservauion.newOwner = None
        reservauion.newWorkshop = None
        reservauion.finalActionTime=timezone.now()
        reservauion.save()
            
        Notification.objects.create(
            user=old_user,
            message=f' لقد قام {request.user.username} بالغاء تحويل حجزك اليه من المنتج {reservauion.product_class.type}  '
        )
        Notification.objects.create(
            user=request.user,
            message=f' لقد قام {request.user.username}  بالغاء تحويل حجز {old_user.username} من المنتج {reservauion.product_class.type} اليك '
        )
    else:
        return Response({'error': 'you did not enter the informations properly'})
    return Response({'details': 'the proceed went successfully'})

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
# (Make sure Workshop and WorkshopSerializer are also imported)

@api_view(['GET'])
def workshops(request):
    # 1. Get page and limit from the request url (default to page 1, limit 10)
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)

    is_manager = request.user.groups.filter(name="staff").exists()
    
    if is_manager:
        workshops_qs = Workshop.objects.all().exclude(Q(is_working='stopped')|Q(is_working='done')).order_by('-id')
    else:
        workshops_qs = Workshop.objects.filter(
            Q(is_working='Yes')|Q(is_working='not started yet'),
            Q(manager=request.user)|Q(manager=None)
        ).exclude(is_working='stopped').order_by('-id')

    # 2. Apply Pagination
    paginator = Paginator(workshops_qs, limit)
    
    try:
        paginated_workshops = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated_workshops = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver empty list instead of an error.
        paginated_workshops = []

    # 3. Serialize only the paginated data
    serializer = WorkshopSerializer(paginated_workshops, many=True)
    
    return Response({
        'workshops': serializer.data,
        # Optional: Sending metadata helps if you ever want to upgrade your frontend logic
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    })


@api_view(['GET'])
def ended_workshops(request):
    print(timezone.now())
    # 1. Get page and limit from the request url (default to page 1, limit 10)
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)

    is_manager = request.user.groups.filter(name="staff").exists()
    
    if is_manager:
        workshops_qs = Workshop.objects.filter(is_working='done').exclude(is_working='stopped').order_by('-EndAt')
    else:
        workshops_qs = Workshop.objects.filter(is_working='done', manager=request.user).exclude(is_working='stopped').order_by('-EndAt')

    # 2. Apply Pagination
    paginator = Paginator(workshops_qs, limit)
    
    try:
        paginated_workshops = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_workshops = paginator.page(1)
    except EmptyPage:
        paginated_workshops = []

    # 3. Serialize only the paginated data
    serializer = WorkshopSerializer(paginated_workshops, many=True)
    
    return Response({
        'workshops': serializer.data,
        # Optional metadata
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    })


@api_view(['GET'])
def workshops_has_manager(request):
    
    workshops=Workshop.objects.filter(Q(is_working='Yes')|Q(is_working='not started yet'),manager__isnull=False).order_by('createAt')

    serializer=WorkshopSerializer(workshops,many=True)
    return Response({
        'workshops': serializer.data

    })


@api_view(['GET'])
def turn_Reservation_to_workshops(request):
   
    workshops=Workshop.objects.all().exclude(Q(is_working='stopped')|Q(is_working='done'))
   
    serializer=WorkshopSerializer(workshops,many=True)
    return Response({
        'workshops': serializer.data

    })




@api_view(['POST'])
def addWorkshop(request):
    data = {
        'location': request.data.get('location'),
        'name': request.data.get('name'),
    }
    try:
        if Workshop.objects.filter(name=data['name']).exists():
            return Response({'error':'هذه الورشة موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        Workshop.objects.create(
            name=data['name'],
            location=data['location'],
        )
    except Exception as e:
        return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)

    return Response({'details:': 'your request has been proceed succefully!'})


@api_view(['POST'])
def WorkshopToggleStatusView(request):
        try:
            workshop_id=request.GET.get('workshop_id')
            workshop = Workshop.objects.get(id=workshop_id)

            # Prevent deleting admin users
            workshop.is_working='stopped'
            workshop.save()
            reservations=Reservations.objects.filter(workshop=workshop)
            users = User.objects.all()
            Notification.objects.create(
                    user=request.user,
                    message=f' لقد قام {request.user.username}  بتعطيل الورشة {workshop.name} '
                )
            return Response({'message': 'تم تعطيل الورشة بنجاح'}, status=status.HTTP_200_OK)
        except Reposotory.DoesNotExist:
            return Response({'error': 'الورشة غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )




@api_view(['POST'])
def addClassToWorkshop(request):
    data = {
        'workshop_id':request.data.get('workshop_id'),
        'class_id': request.data.get('class_id'),
        'amount': request.data.get('amount'),
        'reposotory_id': request.data.get('reposotory_id'),
    }
    try:
        print('addClassToWorkshop')
        print('data',data)
        reposotory=Reposotory.objects.get(id=data['reposotory_id'])
        print('reposotory',reposotory)
        workshop_obj=Workshop.objects.get(id=data['workshop_id'])
        print('workshop_obj',workshop_obj)
        class_obj=Class.objects.get(id=data['class_id'])
        print('class_obj',class_obj)
        name=class_obj.product.name
        type=class_obj.type
        if data['amount'] is None:
            return Response({'error':'data you entered is not enough'})
        if class_obj.product.reposotory !=reposotory:
            print('class_obj.product.reposotory',class_obj.product.reposotory)
            return Response ({'error':'المنتج الذي طلبته موجود في المستودع الاخر'},status=HTTP_404_NOT_FOUND)
       
        amount=int(data['amount'])
    except Exception as e:
        return Response({'error':'data you entered is not enough'})
    try:    

        amounts=Amounts.objects.filter(product_class=class_obj)
        amount_obj=amounts.filter(is_available='متاح').first()

        print('amount_obj',amount_obj)
        print(data['amount'])
        
        
        if amount_obj.amount >= int(data['amount']):
            user =request.user
            print("user.username")
            print(user)
            default_user = User.objects.filter(groups__name="staff").first()
            try:
                staff_group = Group.objects.get(name="staff")
                staff_users = User.objects.filter(groups=staff_group)
                for staff_member in staff_users:
                   if user != staff_member:
                    Add_Delete.objects.create(
                        changer=user ,
                        change_type='حجز',
                        name=name,
                        amount=data['amount'],
                        type=type,
                        reader=staff_member,
                    )
            except Group.DoesNotExist:
                print("Warning: Staff group does not exist")
            print(1)

            product = class_obj.product
            product.total_available -= amount
            product.save()
            Add_Delete.objects.create(
                changer=user ,
                change_type='حجز',
                name=name,
                amount=data['amount'],
                type=type,
                reader=user ,
            )
            print(2)
            Reservations.objects.create(
                amount=data['amount'],
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=workshop_obj
            )
            print(3)
            data['is_available'] ='محجوز'
            amount_obj.amount -= amount
            amount_obj.save()
            data['product_id']=class_obj.product.id
            data['type']=type
            print('try2')
            print(data['type'])
            workshop_obj.is_working='Yes'
            workshop_obj.save()
            django_request = HttpRequest()
            django_request.method = 'POST'
            django_request.POST = data
            print('try')
            Notification.objects.create(
                user=user,
                message=f' لقد قام {request.user.username}  بحجز {amount} قطعة من المنتج {amount_obj.product_class.type} '
            )
            print('done!')
            return add_class(django_request, custom_data=data, user=request.user)
        elif amount_obj.amount < int(data['amount']):
            
            user =request.user
            print("user.username")
            print(user)
            default_user = User.objects.filter(groups__name="staff").first()
            try:
                staff_group = Group.objects.get(name="staff")
                staff_users = User.objects.filter(groups=staff_group)
                for staff_member in staff_users:
                   if user != staff_member:
                    Add_Delete.objects.create(
                        changer=user ,
                        change_type='حجز',
                        name=name,
                        amount=amount_obj.amount,
                        type=type,
                        reader=staff_member,
                    )
                    Add_Delete.objects.create(
                        changer=user ,
                        change_type='مطلوب للشراء',
                        name=name,
                        amount=data['amount']-amount_obj.amount,
                        type=type,
                        reader=staff_member,
                    )
            except Group.DoesNotExist:
                print("Warning: Staff group does not exist")
            product = class_obj.product
            product.total_available -= amount_obj.amount
            product.save()
            Add_Delete.objects.create(
                changer=user ,
                change_type='حجز',
                name=name,
                amount=amount_obj.amount,
                type=type,
                reader=user ,
            )
            Add_Delete.objects.create(
                        changer=user ,
                        change_type='مطلوب للشراء',
                        name=name,
                        amount=int(data['amount'])-amount_obj.amount,
                        type=type,
                        reader=user,
                    )
            if amount_obj.amount>0 :    
                Reservations.objects.create(
                amount=amount_obj.amount,
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=workshop_obj
                )
            Reservations.objects.create(
                amount=int(data['amount'])-amount_obj.amount,
                product_class=class_obj,
                user=user,
                reservation_type='requested for workshops',
                workshop=workshop_obj
            )
           
            data['product_id']=class_obj.product.id
            data['type']=type
           
            print('try1')
            print(class_obj)
            Notification.objects.create(
                user=user,
                message=f' لقد قام {request.user.username}  بحجز {amount_obj.amount} قطعة وطلب لشراء {amount-amount_obj.amount} من المنتج {amount_obj.product_class.type} '
            )
            print("asked amount ",amount-amount_obj.amount)
            print("reserved amount ",amount_obj.amount)

            amount_reserved_obj= amounts.filter( is_available='محجوز').first()
            if amount_reserved_obj:
                print('محجوز',2)
                amount_reserved_obj.amount += amount_obj.amount
                amount_reserved_obj.save()
            else:
                print('محجوز',3)
                Amounts.objects.create(
                    amount=amount_obj.amount,
                    is_available='محجوز',
                    product_class=class_obj
                )

            amount_requested_obj=amounts.filter( is_available='مطلوب للشراء').first()
            if amount_requested_obj:
                print('مطلوب للشراء',2)
                amount_requested_obj.amount +=int(data['amount'])-amount_obj.amount
                amount_requested_obj.save()
            else:
                print('مطلوب للشراء',3)
                
                Amounts.objects.create(
                    amount=int(data['amount'])-amount_obj.amount,
                    is_available='مطلوب للشراء',
                    product_class=class_obj
                )
            print('here it comes')    
            workshop_obj.is_working='Yes'
            workshop_obj.save()
            class_obj.product.total_requested += int(data['amount'])-amount_obj.amount
            class_obj.product.save()
            print( amount_obj.amount)
            amount_obj.amount=0
            amount_obj.save()
            

            return Response({'details:':'done!'},status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def addClassToWorkshop_fun(workshop_id,class_id,amount,reposotory_id,user):
    data = {
        'workshop_id':workshop_id,
        'class_id': class_id,
        'amount': amount,
        'reposotory_id': reposotory_id,
    }
    try:
        print('addClassToWorkshop')
        print('data',data)
        reposotory=Reposotory.objects.get(id=data['reposotory_id'])
        print('reposotory',reposotory)
        workshop_obj=Workshop.objects.get(id=data['workshop_id'])
        print('workshop_obj',workshop_obj)
        class_obj=Class.objects.get(id=data['class_id'])
        print('class_obj',class_obj)
        name=class_obj.product.name
        type=class_obj.type
        if data['amount'] is None:
            return Response({'error':'data you entered is not enough'})
        if class_obj.product.reposotory !=reposotory:
            return Response ({'error':'المنتج الذي طلبته موجود في المستودع الاخر'},status=HTTP_404_NOT_FOUND)
       
        amount=int(data['amount'])
    except Exception as e:
        return Response({'error':'data you entered is not enough'})
    try:    
        amounts=Amounts.objects.filter(product_class=class_obj)
        amount_obj=amounts.filter(is_available='متاح').first()

        print('amount_obj',amount_obj)
        print(data['amount'])
        
        
        if amount_obj.amount >= int(data['amount']):
            print("user.username")
            print(user)
            default_user = User.objects.filter(groups__name="staff").first()
            print(1)

            product = class_obj.product
            product.total_available -= amount
            product.save()
            
            print(2)
            Reservations.objects.create(
                amount=data['amount'],
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=workshop_obj
            )
            print(3)
            data['is_available'] ='محجوز'
            amount_obj.amount -= amount
            amount_obj.save()
            data['product_id']=class_obj.product.id
            data['type']=type
            print('try2')
            print(data['type'])
            workshop_obj.is_working='Yes'
            workshop_obj.save()
            print('try')
            Notification.objects.create(
                user=user,
                message=f' لقد قام {user.username}  بحجز {amount} قطعة من المنتج {amount_obj.product_class.type} '
            )
            print('done!')
            return add_class_fun('',class_obj.product.id,int(data['amount']),'محجوز',class_obj.id,user)
        elif amount_obj.amount < int(data['amount']):
            
            print("user.username")
            print(user)
            default_user = User.objects.filter(groups__name="staff").first()
            product = class_obj.product
            product.total_available -= amount_obj.amount
            product.save()
            
           
            if amount_obj.amount>0 :    
                Reservations.objects.create(
                amount=amount_obj.amount,
                product_class=class_obj,
                user=user,
                reservation_type='pending',
                workshop=workshop_obj
                )
            Reservations.objects.create(
                amount=int(data['amount'])-amount_obj.amount,
                product_class=class_obj,
                user=user,
                reservation_type='requested for workshops',
                workshop=workshop_obj
            )
           
            data['product_id']=class_obj.product.id
            data['type']=type
           
            print('try1')
            print(class_obj)
            
            print("asked amount ",amount-amount_obj.amount)
            print("reserved amount ",amount_obj.amount)
            amount_reserved_obj= amounts.filter( is_available='محجوز').first()
            if amount_reserved_obj:
                print('محجوز',2)
                amount_reserved_obj.amount += amount_obj.amount
                amount_reserved_obj.save()
            else:
                print('محجوز',3)
                Amounts.objects.create(
                    amount=amount_obj.amount,
                    is_available='محجوز',
                    product_class=class_obj
                )
            amount_requested_obj=amounts.filter( is_available='مطلوب للشراء').first()
            if amount_requested_obj :
                print('مطلوب للشراء',2)
                amount_requested_obj.amount +=int(data['amount'])-amount_obj.amount
                amount_requested_obj.save()
            else:
                print('مطلوب للشراء',3)
                
                Amounts.objects.create(
                    amount=int(data['amount'])-amount_obj.amount,
                    is_available='مطلوب للشراء',
                    product_class=class_obj
                )

            workshop_obj.is_working='Yes'
            workshop_obj.save()
            class_obj.product.total_requested += int(data['amount'])-amount_obj.amount
            class_obj.product.save()
            print( amount_obj.amount)
            amount_obj.amount=0
            amount_obj.save()
            return 'done'
    except Exception as e:
        return str(e)
  

@api_view(['POST'])
def Assign_manager_Workshop(request):
    data = {
        'workshop_id':request.data.get('workshop_id'),
        'username': request.data.get('username'),

    }
    try:
        workshop_obj=Workshop.objects.get(id=data['workshop_id'])
        user=User.objects.get(username=data['username'])
        workshop_obj.manager=user
        workshop_obj.save()
        Notification.objects.create(
                user=user,
                message=f' لقد تم تعيينك كمدير للورشة {workshop_obj.name}  '
            )
        Notification.objects.create(
                user=request.user,
                message=f' قمت بتعيين {user.username} كمدير لورشة {workshop_obj.name}  '
            )    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

    return Response({'details:': 'your request has been proceed succefully!'})


@api_view(['POST'])
def Workshop_details(request):
    data = {
        'workshop_id':request.data.get('workshop_id'),

    }
    try:
        print('hiiii')
        workshop_obj=Workshop.objects.get(id=data['workshop_id'])
        print('workshop_obj',workshop_obj)
        reservations=Reservations.objects.filter(Q(workshop=workshop_obj)|Q(newWorkshop=workshop_obj),is_deleted=False).exclude(reservation_type='returned from workshops').order_by('-finalActionTime')
        
        serializer=ReservationsSerializerForBillAndWorkshop(reservations,many=True,context={'request': request})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
    print('serializer.data',serializer.data)
    return Response({
        'reservations': serializer.data,
        'username':request.user.username

    })



@api_view(['GET'])
def reposotories_for_workshop(request):

    is_manager = request.user.groups.filter(name="staff").exists()
    is_workshop_manager = request.user.groups.filter(name="WorkShopManagers").exists()
    if is_manager :
        reposotories_for_workshop=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
    elif is_workshop_manager:
        reposotories_for_workshop=request.user.allowed_repositories.filter(is_working='Yes').exclude(name='الورشات')
    else:
        return Response({'error':'you are not allowed to see the repositories for workshops'}, status=status.HTTP_403_FORBIDDEN )
    serializer=ReposotorySerializer(reposotories_for_workshop,many=True)

    return Response({
        'reposotories': serializer.data

    })


@api_view(['POST'])    
def end_workshop(request):

    data = {
        'workshop_id':request.data.get('workshop_id'),

    }
    try:

        workshop_obj=Workshop.objects.get(id=data['workshop_id'])
        reservations_pending=Reservations.objects.filter(workshop=workshop_obj,reservation_type='pending').exists()
        reservations_sent=Reservations.objects.filter(workshop=workshop_obj,reservation_type='sent').exists()
        if reservations_pending or reservations_sent :
            return Response({'error':'لا يمكنك انهاء الورشة , قم بالغاء الحجوزات او استلامها اولا  '}, status=status.HTTP_400_BAD_REQUEST )   
        reservations=Reservations.objects.filter(workshop=workshop_obj).exists()
        if not reservations:
            return Response({'error':'لا يمكنك انهاء الورشة , لا يوجد بها اي حجز  '}, status=status.HTTP_400_BAD_REQUEST )
        workshop_obj.is_working='done'
        workshop_obj.EndAt=timezone.now()
        workshop_obj.save()
        users = User.objects.all()
        for curuser in users:
            Notification.objects.create(
                user=curuser,
                message=f' لقد تم انهاء الورشة {workshop_obj.name} '
            )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

    return Response({'details:': 'your request has been proceed succefully!'})


@api_view(['POST'])    
def unused_amount(request):

    data = {
        'reservation_id': request.data.get('reservation_id'),
        'amount': request.data.get('amount'),
        'reposotory_id': request.data.get('reposotory_id'),
        'workshop_id': request.data.get('workshop_id'),
        }
    try:
        print('data',data)
        reservation=Reservations.objects.get(id=data['reservation_id'])
        if data['reposotory_id'] :
            reposotorie=Reposotory.objects.get(id=data['reposotory_id'])
        else :
            reposotorie=None
        
        if data['workshop_id'] :
            workshop=Workshop.objects.get(id=data['workshop_id'])
            if workshop == reservation.workshop:
                return Response({'error':'الورشة التي ادخلتها هي نفس الورشة الموجودة في الحجز '}, status=status.HTTP_400_BAD_REQUEST )
        else: 
            workshop=None

            

        if int(data['amount'])> reservation.amount:
            return Response({'error':'الكمية التي ادخلتها اكبر من الكمية المستخدمة في الورشة '}, status=status.HTTP_400_BAD_REQUEST )
        reservation.used_in_workshop=int(data['amount'])
        reservation.save()
        if data['reposotory_id'] :
            Notification.objects.create(
                user=request.user,
                message=f' لقد قام {request.user.username}  بارجاع {reservation.amount-data["amount"]} قطعة من المنتج {reservation.product_class.type} الى المستودع {reposotorie.name}  '
            )
        elif data['workshop_id'] and not data['reposotory_id'] :
            Notification.objects.create(
                user=request.user,
                message=f' لقد قام {request.user.username}  بارجاع {reservation.amount-data["amount"]} قطعة من المنتج {reservation.product_class.type} الى  الورشة {workshop.name}  '
            )

        if data['reposotory_id'] :
            users=User.objects.filter(store__name=reposotorie.name)  
            for curuser in users:
                Notification.objects.create(
                user=curuser,
                message=f' لقد تم ارجاع {reservation.amount-data["amount"]} قطعة من المنتج {reservation.product_class.type} من الورشة {reservation.workshop.name} الى مستودعك  '
                ) 

        else :
            #was turned to workshop :
            user=workshop.manager
            Notification.objects.create(
                user=user,
                message=f' لقد تم ارجاع {reservation.amount-data["amount"]} قطعة من المنتج {reservation.product_class.type} من الورشة {reservation.workshop.name} الى ورشتك  '
            ) 

            
       
        

        if data['reposotory_id'] :
            # Get active users in this repository, then exclude programmers
            user_obj = User.objects.filter(
                repository=reposotorie, 
                is_active=True
            ).exclude(groups__name='programers').first()
            
            if user_obj:
                rep_user = user_obj
                print('rep_user', rep_user)
            else:
                # Get active bosses, then exclude programmers
                rep_user = User.objects.filter(
                    groups__name='boss', 
                    is_active=True
                ).exclude(groups__name='programers').first()

            Add_Delete.objects.create(
                changer=request.user ,
                change_type='ارسال',
                name=reservation.product_class.product.name,
                amount=reservation.amount-int(data['amount']),
                type=reservation.product_class.type,
                reader=rep_user ,
                details=f'كمية زائدة عن ورشة {reservation.workshop.name} تم ارسالها الى المستودع  {reposotorie.name}'
            ) 


        elif data['workshop_id'] and not data['reposotory_id'] and workshop.manager :
            rep_user=workshop.manager
            
            Add_Delete.objects.create(
                changer=request.user ,
                change_type='ارسال',
                name=reservation.product_class.product.name,
                amount=reservation.amount-int(data['amount']),
                type=reservation.product_class.type,
                reader=rep_user ,
                details=f'كمية زائدة عن ورشة {reservation.workshop.name} تم ارسالها الى الورشة  {workshop.name}'
            )   
            

            
            

     
        if data['reposotory_id'] :
            Reservations.objects.create(
                amount=reservation.amount - int(data['amount']),
                product_class=reservation.product_class,
                user=rep_user,
                reservation_type='returned from workshops',
            )
        elif data['workshop_id'] and not data['reposotory_id'] :
            Reservations.objects.create(
                amount=reservation.amount - int(data['amount']),
                product_class=reservation.product_class,
                user=rep_user,
                reservation_type='sent',
                workshop=workshop
            )    


        if data['reposotory_id'] :
            other_reservation=Reservations.objects.filter(
                        product_class=reservation.product_class,
                        reservation_type='delivered',
                        workshop=reservation.workshop,
                        used_in_workshop__gte=0

                        ).exclude(id=data['reservation_id']).first()
            
            if  other_reservation:
                    print('here if')
                    print('other_reservation',other_reservation if other_reservation else None)
                    
                    reservation.amount+=other_reservation.amount
                    reservation.used_in_workshop+=other_reservation.used_in_workshop
                    reservation.save()
                    other_reservation.delete()
        elif data['workshop_id'] and not data['reposotory_id'] :
            other_reservation=Reservations.objects.filter(
                        product_class=reservation.product_class,
                        reservation_type='delivered',
                        workshop=workshop,
                        used_in_workshop__gte=0

                        ).exclude(id=data['reservation_id']).first()
            if  other_reservation:
                    print('here if')
                    print('other_reservation',other_reservation if other_reservation else None)
                    
                    reservation.amount+=other_reservation.amount
                    reservation.used_in_workshop+=other_reservation.used_in_workshop
                    reservation.save()
                    other_reservation.delete()

        return Response({'details:': 'your request has been proceed succefully!'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )




@api_view(['GET'])
def user_allowed_repositories(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        repositories = user.allowed_repositories.all()
        serializer = ReposotorySerializer(repositories, many=True)
        return Response({
            'allowed_repositories': [repo.id for repo in repositories]
        })
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)       


@api_view(['POST'])
def edit_amount_in_reservation(request):
    data={
        'reservation_id':request.data.get('reservation_id'),
        'new_amount':request.data.get('new_amount'), 
        } 
    
    try:

        print('data',data)
        reservation=Reservations.objects.get(id=data['reservation_id']) 
        new_amount=data['new_amount']
        
        # return Response({'details:': 'your request has been proceed succefully!'}) 
    except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
    if new_amount > reservation.amount:
        amount_to_add = new_amount - reservation.amount
        if reservation.workshop :
            try:
                class_obj=reservation.product_class
                product=class_obj.product
                available_amount=Amounts.objects.filter(product_class=class_obj,is_available='متاح').first()    
                reserved_amount=Amounts.objects.filter(product_class=class_obj,is_available='محجوز').first()   
                print('here x',)
                if reservation.reservation_type=='pending':
                    x=cancle_reservation_fun(reservation.id,request.user)
                else :
                    x=cancle_requested_reservation_fun(reservation.id,request.user)    
                if x=='done' :
                    y=addClassToWorkshop_fun(reservation.workshop.id ,class_obj.id,new_amount,reservation.product_class.product.reposotory.id,request.user)                # add_class_fun(mytype,product_id,amount,is_available,class_id,user)
                    if y=='done' :
                        Reservations.objects.get(id=reservation.id).delete() 
      
                        Notification.objects.create(
                            user=request.user,
                            message=f' لقد قام {request.user.username}  بزيادة كمية الحجز من المنتج {reservation.product_class.type} الى {new_amount}  '
                        )
                        return Response({'details:': 'your request has been proceed succefully!'}) 
                    else :
                        print('error in addClassToWorkshop_fun ',y)
                        return Response({'error': y}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
                else :
                    print('error in cancle_reservation_fun ',x)
                    return Response({'error': x}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

                
            except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        else :

            class_obj=reservation.product_class
            product=class_obj.product
            available_amount=Amounts.objects.filter(product_class=class_obj,is_available='متاح').first()    
            reserved_amount=Amounts.objects.filter(product_class=class_obj,is_available='محجوز').first()   
            if amount_to_add > available_amount.amount:
                return Response({'error': 'لا يوجد لديك ما يكفي من المواد في المستودع'}, status=status.HTTP_400_BAD_REQUEST) 
            else:
                try:
                    
                    print('here x',)
                    x=cancle_reservation_fun(reservation.id,request.user)
                    if x=='done' :
                        y=reserve_fun(available_amount.id,new_amount,request.user)                # add_class_fun(mytype,product_id,amount,is_available,class_id,user)
                        if y=='done' :
                            Reservations.objects.get(id=reservation.id).delete() 

                            Notification.objects.create(
                                user=request.user,
                                message=f' لقد قام {request.user.username}  بزيادة كمية الحجز من المنتج {reservation.product_class.type} الى {new_amount}  '
                            )
                            return Response({'details:': 'your request has been proceed succefully!'}) 
                        else :
                            print('error in addClassToWorkshop_fun ',y)
                            return Response({'error': y}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
                    else :
                        print('error in cancle_reservation_fun ',x)
                        return Response({'error': x}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

                
                except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        

    elif  new_amount == reservation.amount:
        return Response({'error': 'لقد ادخلت نفس الكمية'}, status=status.HTTP_400_BAD_REQUEST) 

    else:    
        amount_to_remove = reservation.amount - new_amount

        # try:
            # class_obj=reservation.product_class
            # product=class_obj.product
            # available_amount=Amounts.objects.filter(product_class=class_obj,is_available='متاح').first()    
            # reserved_amount=Amounts.objects.filter(product_class=class_obj,is_available='محجوز').first()        

            # product.total_available += amount_to_remove
            # product.save()

            # reserved_amount.amount -= amount_to_remove
            # reserved_amount.save()
            # available_amount.amount += amount_to_remove
            # available_amount.save()
            # reservation.amount=new_amount
            # reservation.save()
        if reservation.workshop :
            try:
                class_obj=reservation.product_class
                product=class_obj.product
                available_amount=Amounts.objects.filter(product_class=class_obj,is_available='متاح').first()    
                reserved_amount=Amounts.objects.filter(product_class=class_obj,is_available='محجوز').first()   
                print('here x',)
                if reservation.reservation_type=='pending':
                    x=cancle_reservation_fun(reservation.id,request.user)
                else :
                    x=cancle_requested_reservation_fun(reservation.id,request.user)
                if x=='done' :
                    y=addClassToWorkshop_fun(reservation.workshop.id ,class_obj.id,new_amount,reservation.product_class.product.reposotory.id,request.user)                # add_class_fun(mytype,product_id,amount,is_available,class_id,user)
                    if y=='done' :
                        Reservations.objects.get(id=reservation.id).delete() 
      
                        Notification.objects.create(
                            user=request.user,
                            message=f' لقد قام {request.user.username}  بانقاص كمية الحجز من المنتج {reservation.product_class.type} الى {new_amount}  '
                        )
                        return Response({'details:': 'your request has been proceed succefully!'}) 
                    else :
                        print('error in addClassToWorkshop_fun ',y)
                        return Response({'error': y}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
                else :
                    print('error in cancle_reservation_fun ',x)
                    return Response({'error': x}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

                
            except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        else :

            class_obj=reservation.product_class
            product=class_obj.product
            available_amount=Amounts.objects.filter(product_class=class_obj,is_available='متاح').first()    
            resrved_amount=Amounts.objects.filter(product_class=class_obj,is_available='محجوز').first()   
            try:
                
                print('here x',)
                x=cancle_reservation_fun(reservation.id,request.user)
                if x=='done' :
                    y=reserve_fun(available_amount.id,new_amount,request.user)                # add_class_fun(mytype,product_id,amount,is_available,class_id,user)
                    if y=='done' :
                        Reservations.objects.get(id=reservation.id).delete() 
                        Notification.objects.create(
                            user=request.user,
                            message=f' لقد قام {request.user.username}  بانقاص كمية الحجز من المنتج {reservation.product_class.type} الى {new_amount}  '
                        )
                        return Response({'details:': 'your request has been proceed succefully!'}) 
                    else :
                        print('error in addClassToWorkshop_fun ',y)
                        return Response({'error': y}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
                else :
                    print('error in cancle_reservation_fun ',x)
                    return Response({'error': x}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
            
            except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        
        
    
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q

@api_view(['GET'])
def bills(request):
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    is_manager = request.user.groups.filter(name="staff").exists()
    user=request.user
    is_staff=User.objects.filter(groups__name="staff")

    if is_manager:
        bills_qs = Bill.objects.all().exclude(Q(is_working='stopped')|Q(is_working='done')).order_by('-createAt')
    else:
        bills_qs = Bill.objects.filter(
            Q(is_working='Yes')|Q(is_working='not started yet'),
            Q(Reposotory=user.repository)|Q(allowed_users=user)
        ).exclude(is_working='stopped',seller__groups__name="staff").order_by('-createAt')

    # Apply Pagination
    paginator = Paginator(bills_qs, limit)
    try:
        paginated_bills = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_bills = paginator.page(1)
    except EmptyPage:
        paginated_bills = []
    context = {
        'request':request,

        'is_staff': is_staff,
    }

    serializer = BillsSerializer(paginated_bills, many=True,context=context)
    return Response({
        'bills': serializer.data,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    })


@api_view(['GET'])
def ended_bills(request):
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    is_manager = request.user.groups.filter(name="staff").exists()
    user=request.user
    is_staff=User.objects.filter(groups__name="staff")
    if is_manager:
        bills_qs = Bill.objects.filter(is_working='done').order_by('-EndAt')
    else:
        bills_qs = Bill.objects.filter(Q(Reposotory=user.repository)|Q(allowed_users=user), is_working='done').exclude(seller__groups__name="staff").order_by('-EndAt')

    # Apply Pagination
    paginator = Paginator(bills_qs, limit)
    try:
        paginated_bills = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_bills = paginator.page(1)
    except EmptyPage:
        paginated_bills = []

    context = {
        'request':request,
        'is_staff': is_staff,
    }
    serializer = BillsSerializer(paginated_bills, many=True,context=context)
    return Response({
        'ended_bills': serializer.data,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    })


@api_view(['GET'])
def notification(request):
    page_number = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    user = request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    
    notifications_qs = Notification.objects.filter(user=user).order_by('-createAt')
    
    # Apply Pagination
    paginator = Paginator(notifications_qs, limit)
    try:
        paginated_notifications = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_notifications = paginator.page(1)
    except EmptyPage:
        paginated_notifications = []
    
    serializer = NotificationSerializer(
        paginated_notifications, many=True, context={'request': request}
    )
    
    return Response({
        'notifications': serializer.data,
        'is_manager': is_manager,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'total_items': paginator.count
    })


@api_view(['POST'])
def sell(request):
    data =  {
        'amount_id': request.data.get('amount_id') ,
        'amount': request.data.get('amount') ,
        'is_available': None,
        'bill_id':request.data.get('bill_id') 
    }
    user=request.user
    print('selling data',data)
    print(data['amount'])
    print(data['amount_id'])
    amount = Amounts.objects.get(
       id=data['amount_id']
    )
    bill_obj = Bill.objects.get(id=data['bill_id'])
    class_obj = amount.product_class
    name=class_obj.product.name
    type=class_obj.type
    print(1)
    print(data)
    print(amount)
    amountt=data['amount']

    if amount:
        if amount.amount >= int(data['amount']):
            user = request.user
            product = class_obj.product

            product.total_available -= int(data['amount'])
            product.save()

            data['is_available'] ='محجوز'
            amount.amount -= int(data['amount'])
            amount.save()
            Reservations.objects.create(
                user=request.user,
                product_class=class_obj,
                amount=data['amount'],
                reservation_type='sold',
                bill=bill_obj
            )
            Notification.objects.create(
                user=request.user,
                message=f' لقد قام {request.user.username}  باضافة كمية {amountt} قطعة من المنتج {amount.product_class.type} الى فاتورة {bill_obj.client_name}  '
            )
            return Response({"details:": "done!"}, status=HTTP_200_OK)
        elif amount.amount < int(data['amount']):
            return Response({"error": "You have asked for more than what you have"}, status=HTTP_404_NOT_FOUND)

    return Response({"error": "No matching reservation found"}, status=HTTP_404_NOT_FOUND)



@api_view(['GET'])
def bill_details(request):
    data = {
        'bill_id':request.GET.get('bill_id'),

    }
    try:
        print('hiiii , bill_details')
        print('bill_id',data['bill_id'])
        bill_obj=Bill.objects.get(id=data['bill_id'])
        reservations=Reservations.objects.filter(bill=bill_obj,is_deleted=False).order_by('finalActionTime')
        serializer=ReservationsSerializerForBillAndWorkshop(reservations,many=True,context={'request': request})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )
    return Response({
        'reservations': serializer.data

    })



@api_view(['POST'])    
def end_bill(request):

    data = {
        'bill_id':request.data.get('bill_id'),

    }
    try:

        bill_obj=Bill.objects.get(id=data['bill_id'])
        bill_obj.is_working='done'
        bill_obj.EndAt=timezone.now()
        bill_obj.save()
       
        Notification.objects.create(
            user=bill_obj.seller,
            message=f' لقد تم اغلاق الفاتورة {bill_obj.client_name} '
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

    return Response({'details:': 'your request has been proceed succefully!'})




@api_view(['POST'])
def addBill(request):
    data = {
        'details': request.data.get('details'),
        'client_name': request.data.get('client_name'),
        'allowed_users_id': request.data.get('allowed_users_id', []),  # Expecting a list of user IDs 
    }
    try:
        print('data',data)
        
        if Bill.objects.filter(client_name=data['client_name']).exists():
            return Response({'error': 'هناك فاتورة بنفس اسم العميل, نرجو إدخال اسم آخر'}, status=status.HTTP_400_BAD_REQUEST)
        user=request.user
        reposotory_obj=user.repository
        print('1')


        bill_obj=Bill.objects.create(
            client_name=data['client_name'],
            details=data['details'],
            seller=user,
            Reposotory=reposotory_obj,
        )
        if data['allowed_users_id']:
            users = User.objects.filter(id__in=data['allowed_users_id'])
            bill_obj.allowed_users.set(users)
        print('2')


    except Exception as e:
        print(str(e))
        return Response({'error':'data you entered is not enough'})
    print('your request has been proceed succefully!')
    return Response({'details:': 'your request has been proceed succefully!'})


@api_view(['POST'])
def edit_bill(request):
    data = {
        
        'bill_id': request.data.get('bill_id'),
        'details': request.data.get('details'),

        'client_name': request.data.get('client_name'),
        'allowed_users_id': request.data.get('allowed_users_id', []),  # Expecting a list of user IDs 
    }
    try:
        print('here edit bill')
        print('data',data)
        bill_obj = Bill.objects.get(id=data['bill_id'])
        if Bill.objects.filter(client_name=data['client_name']).exclude(id=bill_obj.id).exists():
            return Response({'error': 'هناك فاتورة بنفس اسم العميل, نرجو إدخال اسم آخر'}, status=status.HTTP_400_BAD_REQUEST)
        
        if data['allowed_users_id']:
            users = User.objects.filter(id__in=data['allowed_users_id'])
            bill_obj.allowed_users.set(users)
        bill_obj.details=data['details']
        bill_obj.client_name = data['client_name']
        bill_obj.save()

            
    except Exception as e:
        print(str(e))
        return Response({'error':'data you entered is not enough'})

    return Response({'details:': 'your request has been proceed succefully!'})



@api_view(['POST'])
def addClassToBill(request):
    data = {
        'Bill_id':request.data.get('Bill_id'),
        'class_id': request.data.get('class_id'),
        'amount': request.data.get('amount'),
        'reposotory_id': request.data.get('reposotory_id'),
    }
    try:
        print('addClassToBill')
        print('data',data)
        is_staff = request.user.groups.filter(name="staff").exists()
        if is_staff:    
            reposotory=Reposotory.objects.get(id=data['reposotory_id'])
        else:   
            reposotory=request.user.repository
        print('reposotory',reposotory)
        bill_obj=Bill.objects.get(id=data['Bill_id'])
        print('bill_obj',bill_obj)
        class_obj=Class.objects.get(id=data['class_id'])
        print('class_obj',class_obj)
        name=class_obj.product.name
        type=class_obj.type
        if data['amount'] is None:
            return Response({'error':'data you entered is not enough'})
        if class_obj.product.reposotory !=reposotory:
            return Response ({'error':'المنتج الذي طلبته موجود في مستودع اخر'},status=HTTP_404_NOT_FOUND)
       
        amount=int(data['amount'])
    except Exception as e:
        return Response({'error':'data you entered is not enough'},status=HTTP_400_BAD_REQUEST)
    try:    

        amount_obj=Amounts.objects.filter(is_available='متاح',product_class=class_obj).first()

        print('amount_obj',amount_obj)
        print(data['amount'])
        
        
        if amount_obj.amount >= int(data['amount']):
            user =request.user
            print("user.username")
            print(user)
            

            product = class_obj.product
            product.total_available -= amount
            product.save()
            Add_Delete.objects.create(
                changer=user ,
                change_type='بيع',
                name=name,
                amount=data['amount'],
                type=type,
                reader=user ,
                details=f'الى الزبون {bill_obj.client_name}'
            )
            print(2)
            reservation_obj=Reservations.objects.create(
                amount=data['amount'],
                product_class=class_obj,
                user=user,
                reservation_type='sold',
                bill=bill_obj
            )
            print(3)
            data['is_available'] ='محجوز'
            amount_obj.amount -= amount
            amount_obj.save()
            data['product_id']=class_obj.product.id
            data['type']=type
            print('try2')
            print(data['type'])
            django_request = HttpRequest()
            django_request.method = 'POST'
            django_request.POST = data
            print('try')
            Notification.objects.create(
                user=user,
                message=f' لقد قام {request.user.username}  باضافة {amount} قطعة من المنتج {amount_obj.product_class.type} الى فاتورة {bill_obj.client_name}  '
            )
            
            bill_obj.is_working='Yes'
            bill_obj.save()
            print('done!')

            other_reservation=Reservations.objects.filter(
                        product_class=reservation_obj.product_class,
                        bill=bill_obj,
                        ).exclude(id=reservation_obj.id).first()
            if  other_reservation:
                    print('here if')
                    print('other_reservation',other_reservation if other_reservation else None)
                    
                    reservation_obj.amount+=other_reservation.amount
                    reservation_obj.save()
                    other_reservation.delete()
            return Response({"details": "done!"}, status=HTTP_200_OK)
    except Exception as e:
            return Response({'error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({"error": "You have asked for more than what you have"}, status=HTTP_404_NOT_FOUND)


@api_view(['GET'])
def home_for_reposotory_bill(request):
    # 1. compute totals from Product

    reposotory_id=request.GET.get('reposotory_id')    
    if reposotory_id:
        reposotory_obj=Reposotory.objects.get(id=reposotory_id)
    user=request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    if is_manager:
        base_qs= Product.objects.filter(
            classes__amounts__is_available ='متاح',reposotory=reposotory_obj
        ).exclude(reposotory__name='الورشات')
    else:
        base_qs= Product.objects.filter(
            classes__amounts__is_available ='متاح',
            reposotory=user.repository
        ).exclude(reposotory__name='الورشات')
    filtered_qs = home_filter(request.GET, queryset=base_qs).qs

    # 4. serialize
    serializer = ProductSerializer(
        filtered_qs, many=True, context={'request': request}
    )
    raw = serializer.data  # this is a list of {'name':…, 'description':…}

    # 5. dedupe by (name, description)
    unique = []
    seen = set()
    for item in raw:
        key = (item.get('name'), item.get('description'))
        if key not in seen:
            seen.add(key)
            unique.append(item)

   

    
    # print(user.store_na)
    # 6. return deduped list
    return Response({

        'serialize': unique,
    }, status=HTTP_200_OK)



@api_view(['GET'])
def reposotories_for_bill(request):
    user=request.user
    is_manager = request.user.groups.filter(name="staff").exists()
    if is_manager:
        reposotories_for_bill=Reposotory.objects.filter(is_working='Yes').exclude(name='الورشات')
    else:
        reposotories_for_bill=Reposotory.objects.filter(name=user.repository.name,is_working='Yes')

    serializer=ReposotorySerializer(reposotories_for_bill,many=True)

    return Response({
        'reposotories': serializer.data

    })



@api_view(['GET'])
@permission_classes([AllowAny])
def my_script(request):
    min_time_data = Reservations.objects.filter(
        finalActionTime__isnull=False
    ).aggregate(Min('finalActionTime'))
    
    min_time = min_time_data['finalActionTime__min']

    if min_time:
        # 2. Find objects where finalActionTime is null
        null_objects = Reservations.objects.filter(finalActionTime__isnull=True)
        count = null_objects.count()

        # 3. Bulk update those objects
        null_objects.update(finalActionTime=min_time)
        
        print(f"Successfully updated {count} objects with timestamp: {min_time}")
    else:
        print("No reference minimum time found (database might be empty or all are null).")


    return Response({"done": "Script executed successfully"}, status=200)        