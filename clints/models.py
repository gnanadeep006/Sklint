from django.db import models
from django.utils.text import slugify


class ContactPageContent(models.Model):
    badge_text = models.CharField(max_length=120, default="Work With Us")
    hero_gradient_text = models.CharField(max_length=200, default="Have an idea")
    hero_italic_text = models.CharField(max_length=200, default="worth building?")
    hero_description = models.TextField(
        default=(
            "Tell us about your project. We'd love to hear what you're working on "
            "and explore how we might help bring it to life."
        )
    )
    quick_contact_title = models.CharField(max_length=120, default="Quick Contact")
    quick_contact_email = models.EmailField(default="hello@sklint.studio")
    response_title = models.CharField(max_length=120, default="Response Time")
    response_description = models.TextField(
        default="We typically respond within 48 hours. For urgent inquiries, please mention it in your message."
    )
    next_steps_title = models.CharField(max_length=120, default="What Happens Next?")
    quote_text = models.TextField(
        default=(
            "We only take on projects where we can make a real difference. "
            "If we're not the right fit, we'll tell you honestly and try to point you in the right direction."
        )
    )

    class Meta:
        verbose_name = "Contact Page Content"
        verbose_name_plural = "Contact Page Content"

    def __str__(self):
        return "Contact page content"


class ContactStep(models.Model):
    order = models.PositiveSmallIntegerField(default=1)
    text = models.CharField(max_length=255)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.order:02d} - {self.text[:40]}"


class BudgetOption(models.Model):
    order = models.PositiveSmallIntegerField(default=1)
    value = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.label


class ContactSubmission(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    company = models.CharField(max_length=160, blank=True)
    budget = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.email})"


class FeaturedProject(models.Model):
    order = models.PositiveSmallIntegerField(default=1)
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True)
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    description = models.CharField(max_length=240)
    overview = models.TextField(blank=True, default="")
    problem = models.TextField(blank=True, default="")
    solution = models.TextField(blank=True, default="")
    outcome = models.TextField(blank=True, default="")
    image_url = models.CharField(max_length=500, blank=True, default="")
    image_file = models.FileField(upload_to="featured_projects/", blank=True, null=True)
    project_url = models.CharField(max_length=300, default="/projects/")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:120] or "project"
            slug = base_slug
            count = 2
            while FeaturedProject.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
