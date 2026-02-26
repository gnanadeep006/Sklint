from django.shortcuts import redirect, render

from .forms import ContactSubmissionForm
from .models import BudgetOption, ContactPageContent, ContactStep


DEFAULT_BUDGET_OPTIONS = [
    {"value": "5-10k", "label": "Rs5,000 - Rs10,000"},
    {"value": "10-25k", "label": "Rs10,000 - Rs25,000"},
    {"value": "25-50k", "label": "Rs25,000 - Rs50,000"},
    {"value": "50k+", "label": "Rs50,000+"},
]
CUSTOM_BUDGET_OPTION = {"value": "custom", "label": "Custom range"}

DEFAULT_STEPS = [
    "We'll review your message and research your space.",
    "We'll schedule a brief discovery call to understand your needs.",
    "If we're a good fit, we'll send a proposal with timeline and approach.",
]


def contact(request):
    content = ContactPageContent.objects.first()
    budget_qs = BudgetOption.objects.all()
    step_qs = ContactStep.objects.all()

    budget_options = list(budget_qs.values("value", "label")) or DEFAULT_BUDGET_OPTIONS
    if not any(option.get("value") == "custom" for option in budget_options):
        budget_options.append(CUSTOM_BUDGET_OPTION)
    steps = list(step_qs.values_list("text", flat=True)) or DEFAULT_STEPS

    if request.method == "POST":
        form = ContactSubmissionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{request.path}?submitted=1")
    else:
        form = ContactSubmissionForm()

    return render(
        request,
        "contact.html",
        {
            "content": content,
            "form": form,
            "budget_options": budget_options,
            "steps": steps,
            "submitted": request.GET.get("submitted") == "1",
        },
    )
