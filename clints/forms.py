from django import forms

from .models import ContactSubmission


class ContactSubmissionForm(forms.ModelForm):
    custom_budget = forms.CharField(required=False, max_length=120)

    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "company", "budget", "message"]

    def clean(self):
        cleaned_data = super().clean()
        budget = cleaned_data.get("budget", "")
        custom_budget = cleaned_data.get("custom_budget", "").strip()

        if budget == "custom" and not custom_budget:
            self.add_error("custom_budget", "Please enter your custom budget range.")

        if budget == "custom":
            cleaned_data["budget"] = custom_budget

        return cleaned_data
