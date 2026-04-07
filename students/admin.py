from django.contrib import admin
from .models import Student, Payment, Event, Fundraising

admin.site.register(Student)
admin.site.register(Payment)
admin.site.register(Event)
admin.site.register(Fundraising)