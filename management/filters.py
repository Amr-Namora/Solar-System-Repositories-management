import django_filters
from django.utils import timezone
from datetime import timedelta
from .models import Add_Delete, Product, Amounts


class Add_Delete_filter(django_filters.FilterSet):
    change_type = django_filters.CharFilter(field_name='change_type', lookup_expr='iexact')
    type = django_filters.CharFilter(field_name='type', lookup_expr='icontains')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    # Custom filter for createAt
    created_range = django_filters.CharFilter(method='filter_by_date_range')

    def filter_by_date_range(self, queryset, name, value):
        today = timezone.now().date()
        if value == "today":
            return queryset.filter(createAt__date=today)
        elif value == "this_week":
            start_of_week = today - timedelta(days=today.weekday())
            return queryset.filter(createAt__date__gte=start_of_week)
        elif value == "this_month":
            start_of_month = today.replace(day=1)
            return queryset.filter(createAt__date__gte=start_of_month)
        elif value == "this_year":
            start_of_year = today.replace(month=1, day=1)
            return queryset.filter(createAt__date__gte=start_of_year)
        elif "-" in value:  # Custom date range filtering (expects format "YYYY-MM-DD,YYYY-MM-DD")
            try:
                start_date, end_date = value.split(",")
                return queryset.filter(createAt__date__range=[start_date, end_date])
            except ValueError:
                return queryset.none()  # Invalid format handling
        return queryset

    class Meta:
        model = Add_Delete
        fields = ['change_type', 'type', 'name', 'created_range','id']


class home_filter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='product_class__product__name', lookup_expr='icontains')
    type = django_filters.CharFilter(field_name='product_class__type', lookup_expr='icontains')
    is_available = django_filters.CharFilter(field_name='is_available', lookup_expr='iexact')
    class Meta:
        model = Amounts
        fields = ['is_available','product_class__product__name','product_class__type']
