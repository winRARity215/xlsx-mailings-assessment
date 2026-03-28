from django.contrib import admin
from .models import OutgoingEmail


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    
    list_display = [
        "external_id", 
        "user", 
        "email", 
        "subject", 
        "status_display", 
        "created_at"
    ]
    list_filter = [
        "status", 
        "created_at"
    ]
    search_fields = [
        "external_id", 
        "user__username", 
        "email", 
        "subject"
    ]
    
    def status_display(self, obj: OutgoingEmail) -> str:
        colors = {
            "PENDING": "orange",
            "SENT": "green", 
            "ERROR": "red"
        }
        color = colors.get(obj.status, "black")
        return f'<span style="color: {color}">{obj.status}</span>'
    
    status_display.short_description = "Статус"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != OutgoingEmail.Status.PENDING:
            return ["external_id", "user", "email", "subject", "message", "created_at", "sent_at", "last_error"]
        return self.readonly_fields
