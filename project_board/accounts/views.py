from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

from project_board.mmo_board.forms import CustomSignupForm


class SignUp(CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('account_login')
    template_name = 'account/signup.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs