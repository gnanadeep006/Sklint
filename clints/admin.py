import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import BudgetOption, ContactPageContent, ContactStep, ContactSubmission, FeaturedProject

admin.site.site_header = "SklinT Admin"
admin.site.site_title = "SklinT Admin"
admin.site.index_title = "Content and Leads Dashboard"


@admin.register(ContactPageContent)
class ContactPageContentAdmin(admin.ModelAdmin):
    list_display = ("quick_contact_email",)


@admin.register(ContactStep)
class ContactStepAdmin(admin.ModelAdmin):
    list_display = ("text", "order")
    list_editable = ("order",)


@admin.register(BudgetOption)
class BudgetOptionAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "order")
    list_editable = ("order",)


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "budget", "created_at")
    search_fields = ("name", "email", "company", "message")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)
    actions = ("export_selected_as_csv",)

    @admin.action(description="Export selected submissions as CSV")
    def export_selected_as_csv(self, request, queryset):
        return self._build_csv_response(queryset, filename="contact_submissions_selected.csv")

    def _build_csv_response(self, queryset, filename):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(["Name", "Email", "Company", "Budget", "Message", "Created At"])

        for submission in queryset.iterator():
            writer.writerow(
                [
                    submission.name,
                    submission.email,
                    submission.company,
                    submission.budget,
                    submission.message,
                    submission.created_at.isoformat(),
                ]
            )

        return response


@admin.register(FeaturedProject)
class FeaturedProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "category", "description", "overview", "problem", "solution", "outcome")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "description",
                    "overview",
                    "problem",
                    "solution",
                    "outcome",
                    "image_file",
                    "image_url",
                    "project_url",
                    "order",
                    "is_active",
                ),
                "description": "Prefer uploaded image. If no file is uploaded, image URL will be used.",
            },
        ),
    )
