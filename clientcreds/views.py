# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license. See full license at the bottom of this file.
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
import logging
from clientcreds.clientcredhelper import get_client_cred_authorization_url, get_access_token
from clientcreds.o365service import make_api_call

# Used for debug logging
logger = logging.getLogger('clientcreds')

# Home page (just shows a link to admin consent)
def home(request):
  redirect_url = request.build_absolute_uri(reverse('clientcreds:consent'))
  sign_in_url = get_client_cred_authorization_url(redirect_url, 'https://outlook.office365.com/')
  return HttpResponse('<a href="' + sign_in_url + '">Click here to sign in with an admin account</a>')

# Consent action. Marked CSRF exempt because it is called from Azure
@csrf_exempt  
def consent(request):
  # We're expecting a POST with form data
  if request.method == "POST":
    # The ID token we requested is included as the "id_token" form field
    id_token = request.POST["id_token"]
    redirect_url = request.build_absolute_uri(reverse('clientcreds:consent'))
    # Get an access token
    access_token = get_access_token(id_token, redirect_url, 'https://outlook.office365.com/')
    if (access_token['access_token']):
      # Save the token in the session
      request.session['access_token'] = access_token['access_token']
      # Redirect to the mail page
      return HttpResponseRedirect(reverse('clientcreds:mail'))
    else:
      return HttpResponse("ERROR: " + access_token['error_description'])
  else:
    return HttpResponseRedirect(reverse('clientcreds:home'))
    
def mail(request):
  # The mail page uses a form to set the user, so we only do work
  # if this is a POST from that form.
  if request.method == "POST":
    # Get the user (user@domain.com)
    user = request.POST["user_email"]
    logger.debug('POST to mail for user: {0}'.format(user))
    access_token = request.session['access_token']
    # Build the user-specific API endpoint to /User/Messages
    messages_url = "https://outlook.office365.com/api/v1.0/users('{0}')/Messages/".format(user)
    # Use query parameters to only request properties we use, to sort by time received, and to limit
    # the results to 10 items.
    query_params = '?$select=From,Subject,DateTimeReceived&$orderby=DateTimeReceived desc&$top=10'
    messages = make_api_call('GET', messages_url + query_params, access_token).json()
    context = {
                'user_email': user,
                'messages': messages['value'],
              }
  else:
    context = { 'user_email': 'NONE' }

  return render(request, 'clientcreds/mail.html', context)

# MIT License: 
 
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the 
# ""Software""), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions: 
 
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software. 
 
# THE SOFTWARE IS PROVIDED ""AS IS"", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.