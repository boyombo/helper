#from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import user_passes_test
from django import forms

from helpdesk import settings as helpdesk_settings
from tickets.forms import TicketForm
from helpdesk.models import Queue

staff_member_required = user_passes_test(lambda u: u.is_authenticated() and u.is_active and u.is_staff)


def create(request):
    if helpdesk_settings.HELPDESK_STAFF_ONLY_TICKET_OWNERS:
        assignable_users = User.objects.filter(is_active=True, is_staff=True).order_by(User.USERNAME_FIELD)
    else:
        assignable_users = User.objects.filter(is_active=True).order_by(User.USERNAME_FIELD)

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        form.fields['queue'].choices = [('', '--------')] + [[q.id, q.title] for q in Queue.objects.all()]
        form.fields['assigned_to'].choices = [('', '--------')] + [[u.id, u.get_username()] for u in assignable_users]
        if form.is_valid():
            ticket = form.save(user=request.user)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        initial_data = {}
        if request.user.usersettings.settings.get('use_email_as_submitter', False) and request.user.email:
            initial_data['submitter_email'] = request.user.email
        if request.GET.has_key('queue'):
            initial_data['queue'] = request.GET['queue']

        form = TicketForm(initial=initial_data)
        form.fields['queue'].choices = [('', '--------')] + [[q.id, q.title] for q in Queue.objects.all()]
        form.fields['assigned_to'].choices = [('', '--------')] + [[u.id, u.get_username()] for u in assignable_users]
        if helpdesk_settings.HELPDESK_CREATE_TICKET_HIDE_ASSIGNED_TO:
            form.fields['assigned_to'].widget = forms.HiddenInput()

    return render_to_response('tickets/create_ticket.html',
        RequestContext(request, {
            'form': form,
        }))
create = staff_member_required(create)
