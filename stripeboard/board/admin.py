from django.contrib import admin

from stripeboard.board.models import Profile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'livemode', 'stripe_user_id')
    raw_id_fields = ['user']
admin.site.register(Profile, ProfileAdmin)