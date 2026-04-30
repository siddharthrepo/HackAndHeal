from django import forms
from .models import SOAPNote


class SOAPNoteEditForm(forms.ModelForm):
    class Meta:
        model = SOAPNote
        fields = ['subjective', 'objective', 'assessment', 'plan']
        widgets = {
            'subjective': forms.Textarea(attrs={'rows': 5, 'class': 'form-textarea'}),
            'objective': forms.Textarea(attrs={'rows': 5, 'class': 'form-textarea'}),
            'assessment': forms.Textarea(attrs={'rows': 5, 'class': 'form-textarea'}),
            'plan': forms.Textarea(attrs={'rows': 5, 'class': 'form-textarea'}),
        }
