from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clints", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeaturedProject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("title", models.CharField(max_length=120)),
                ("category", models.CharField(max_length=80)),
                ("description", models.CharField(max_length=240)),
                ("image_url", models.CharField(max_length=500)),
                ("project_url", models.CharField(default="/projects/", max_length=300)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["order", "id"]},
        ),
    ]

