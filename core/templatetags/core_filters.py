from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def rubles(value):
    """Format number as Russian rubles."""
    if value is None:
        return '—'
    try:
        v = float(value)
        return f"{v:,.2f} ₽".replace(',', ' ')
    except (ValueError, TypeError):
        return str(value)


@register.filter
def status_badge(status):
    colors = {
        'draft': 'secondary',
        'submitted': 'primary',
        'approved': 'success',
        'rejected': 'danger',
        'ordered': 'info',
        'completed': 'dark',
        'sent': 'primary',
        'confirmed': 'info',
        'delivered': 'success',
        'cancelled': 'danger',
    }
    return colors.get(status, 'secondary')


@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    try:
        if float(total) == 0:
            return 0
        return round(float(value) / float(total) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def criticality_badge(criticality):
    badges = {
        'low': ('<span class="badge bg-secondary">Низкая</span>'),
        'medium': ('<span class="badge bg-primary">Средняя</span>'),
        'high': ('<span class="badge bg-warning text-dark">Высокая</span>'),
        'critical': ('<span class="badge bg-danger">Критическая</span>'),
    }
    return badges.get(criticality, criticality)


@register.filter
def request_criticality_badge(criticality):
    if criticality == 'emergency':
        return 'danger'
    return 'primary'
