from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clints", "0002_featuredproject"),
    ]

    operations = [
        migrations.AddField(
            model_name="featuredproject",
            name="image_file",
            field=models.FileField(blank=True, null=True, upload_to="featured_projects/"),
        ),
        migrations.AlterField(
            model_name="featuredproject",
            name="image_url",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]

