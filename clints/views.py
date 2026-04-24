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


def _budget_options():
    options = list(BudgetOption.objects.values("value", "label")) or DEFAULT_BUDGET_OPTIONS.copy()
    if not any(option.get("value") == CUSTOM_BUDGET_OPTION["value"] for option in options):
        options.append(CUSTOM_BUDGET_OPTION.copy())
    return options


def _contact_steps():
    return list(ContactStep.objects.values_list("text", flat=True)) or DEFAULT_STEPS.copy()


def _contact_context(form, *, submitted):
    return {
        "content": ContactPageContent.objects.first(),
        "form": form,
        "budget_options": _budget_options(),
        "steps": _contact_steps(),
        "submitted": submitted,
    }


def contact(request):
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
        _contact_context(form, submitted=request.GET.get("submitted") == "1"),
    )
