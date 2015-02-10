# Python Client Credentials Sample #

This is a very rough sample illustrating how to implement the client credential OAuth2 flow in a Python/Django app. The app allows an administrator to logon and give consent, and then allows the user to view the first 10 emails in the inbox of any user in the organization.

## Required software ##

- [Python 3.4.2](https://www.python.org/downloads/)
- [Django 1.7.1](https://docs.djangoproject.com/en/1.7/intro/install/)
- [Requests: HTTP for Humans](http://docs.python-requests.org/en/latest/)
- [Python-RSA](http://stuvel.eu/rsa)

## Running the sample ##

It's assumed that you have Python and Django installed before starting. Windows users should add the Python install directory and Scripts subdirectory to their PATH environment variable.

1. Download or fork the sample project.
1. Open your command prompt or shell to the directory where `manage.py` is located.
1. If you can run BAT files, run setup_project.bat. If not, run the three commands in the file manually. The last command prompts you to create a superuser, which you'll use later to logon.
1. Install the Requests: HTTP for Humans module from the command line: `pip install requests`
1. Install the Python-RSA module from the command line: `pip install rsa`
1. [Register the app in Azure Active Directory](https://github.com/jasonjoh/office365-azure-guides/blob/master/RegisterAnAppInAzure.md). The app should be registered as a web app with a Sign-on URL of "http://127.0.0.1:8000/", and should be given the permission to "Read mail in all mailboxes in the organization", which is available in the "Application Permissions" dropdown.
1. Configure an X509 certificate for your app following the directions [here](http://blogs.msdn.com/b/exchangedev/archive/2015/01/21/building-demon-or-service-apps-with-office-365-mail-calendar-and-contacts-apis-oauth2-client-credential-flow.aspx).
1. Extract the private key in RSA format from your certificate and save it to a PEM file. (I used openssl to do this).
    `openssl pkcs12 -in <path to PFX file> -nodes -nocerts -passin pass:<cert password> | openssl rsa -out appcert.pem`
1. Edit the `.\clientcreds\clientreg.py` file. 
	1. Copy the client ID for your app obtained during app registration and paste it as the value for the `id` variable. 
	1. Enter the full path to the PEM file containing the RSA private key as the value for the `cert_file_path` variable.
	1. Copy the thumbprint value of your certificate (same value used for the `customKeyIdentifier` value in the application manifest) and paste it as the value for the `cert_file_thumbprint` variable.
	1. Save the file.
1. Start the development server: `python manage.py runserver`
1. You should see output like:
    `Performing system checks...`
    
    `System check identified no issues (0 silenced).`
    `December 18, 2014 - 12:36:32`
    `Django version 1.7.1, using settings 'pythoncontacts.settings'`
    `Starting development server at http://127.0.0.1:8000/`
    `Quit the server with CTRL-BREAK.`
1. Use your browser to go to http://127.0.0.1:8000/.
1. You should now be prompted to login with an adminstrative account. Click the link to do so and login with an Office 365 tenant administrator account.
2. You should be redirect to the mail page. Enter a valid email address for a user in the Office 365 tenant and click the "Set User" button. The most recent 10 emails for the user should load on the page.

## Copyright ##

Copyright (c) Microsoft. All rights reserved.

----------
Connect with me on Twitter [@JasonJohMSFT](https://twitter.com/JasonJohMSFT)

Follow the [Exchange Dev Blog](http://blogs.msdn.com/b/exchangedev/)