from django.shortcuts import render_to_response
from django.template import RequestContext

def view_profile(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)
    return render_to_response("profiles/profile.html",
            context_instance=RequestContext(request))
