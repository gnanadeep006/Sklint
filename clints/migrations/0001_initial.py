from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BudgetOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("value", models.CharField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=120)),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="ContactPageContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("badge_text", models.CharField(default="Work With Us", max_length=120)),
                ("hero_gradient_text", models.CharField(default="Have an idea", max_length=200)),
                ("hero_italic_text", models.CharField(default="worth building?", max_length=200)),
                (
                    "hero_description",
                    models.TextField(
                        default=(
                            "Tell us about your project. We'd love to hear what you're working on "
                            "and explore how we might help bring it to life."
                        )
                    ),
                ),
                ("quick_contact_title", models.CharField(default="Quick Contact", max_length=120)),
                ("quick_contact_email", models.EmailField(default="hello@sklint.studio", max_length=254)),
                ("response_title", models.CharField(default="Response Time", max_length=120)),
                (
                    "response_description",
                    models.TextField(
                        default="We typically respond within 48 hours. For urgent inquiries, please mention it in your message."
                    ),
                ),
                ("next_steps_title", models.CharField(default="What Happens Next?", max_length=120)),
                (
                    "quote_text",
                    models.TextField(
                        default=(
                            "We only take on projects where we can make a real difference. "
                            "If we're not the right fit, we'll tell you honestly and try to point you in the right direction."
                        )
                    ),
                ),
            ],
            options={"verbose_name": "Contact Page Content", "verbose_name_plural": "Contact Page Content"},
        ),
        migrations.CreateModel(
            name="ContactStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("text", models.CharField(max_length=255)),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="ContactSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("company", models.CharField(blank=True, max_length=160)),
                ("budget", models.CharField(blank=True, max_length=50)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

