# from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from ielex.profiles.forms import *
from ielex.shortcuts import render_template

@login_required
def view_profile(request, action=None):
    if request.method == 'POST':
        form = UserAlterDetailsForm(request.POST)
        if form.is_valid():
            for key in form.cleaned_data:
                setattr(request.user, key, form.cleaned_data[key])
            request.user.save()
            return HttpResponseRedirect("/accounts/profile/")
        else:
            assert 0 ### form is failing validation
    else:
        form = UserAlterDetailsForm(request.user.__dict__)
    return render_template(request, "profiles/profile.html",
            {"action":action, "form":form})
