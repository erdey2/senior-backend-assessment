from django.db.models import Q

def apply_filters(queryset, filters):
    q = Q()

    for f in filters:
        field = f.get("field")
        op = f.get("op", "eq")
        value = f.get("value")

        if op == "eq":
            q &= Q(**{field: value})

        elif op == "neq":
            q &= ~Q(**{field: value})

        elif op == "in":
            q &= Q(**{f"{field}__in": value})

        elif op == "nin":
            q &= ~Q(**{f"{field}__in": value})

        elif op == "gt":
            q &= Q(**{f"{field}__gt": value})

        elif op == "lt":
            q &= Q(**{f"{field}__lt": value})

    return queryset.filter(q)
