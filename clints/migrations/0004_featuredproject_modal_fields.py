from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clints", "0003_featuredproject_image_file_and_url_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="featuredproject",
            name="overview",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="featuredproject",
            name="outcome",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="featuredproject",
            name="problem",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="featuredproject",
            name="slug",
            field=models.SlugField(blank=True, max_length=140, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="featuredproject",
            name="solution",
            field=models.TextField(blank=True, default=""),
        ),
    ]

