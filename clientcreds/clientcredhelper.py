# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license. See full license at the bottom of this file.
from urllib.parse import quote, urlencode
import requests
import json
import base64
import logging
import uuid
import datetime
import time
import rsa
from clientcreds.clientreg import client_registration

# Used for debug logging
logger = logging.getLogger('clientcreds')

# Constant strings for OAuth2 flow
# The OAuth authority
authority = 'https://login.microsoftonline.com'

# The authorize URL that initiates the OAuth2 client credential flow for admin consent
authorize_url = '{0}{1}'.format(authority, '/common/oauth2/authorize?{0}')

# The token issuing endpoint
token_url = '{0}{1}'.format(authority, '/{0}/oauth2/token')

# Set to False to bypass SSL verification
# Useful for capturing API calls in Fiddler
verifySSL = True

# Plugs in client ID and redirect URL to the authorize URL
# App will call this to get a URL to redirect the user for sign in
def get_client_cred_authorization_url(redirect_uri, resource):
  logger.debug('Entering get_client_cred_authorization_url.')
  logger.debug('  redirect_uri: {0}'.format(redirect_uri))
  logger.debug('  resource: {0}'.format(resource))
  
  # Create a GUID for the nonce value
  nonce = str(uuid.uuid4())
  
  params = { 'client_id': client_registration.client_id(),
             'redirect_uri': redirect_uri,
             'response_type': 'code id_token',
             'scope': 'openid',
             'nonce': nonce,
             'prompt': 'admin_consent',
             'response_mode': 'form_post',
             'resource': resource,
           }
  
  authorization_url = authorize_url.format(urlencode(params))
  
  logger.debug('Authorization url: {0}'.format(authorization_url))
  logger.debug('Leaving get_client_cred_authorization_url.')
  return authorization_url
    
def get_access_token(id_token, redirect_uri, resource):
  # Get the tenant ID from the id token
  parsed_token = parse_token(id_token)
  tenantId = parsed_token['tid']
  if (tenantId):
    logger.debug('Tenant ID: {0}'.format(tenantId))
    get_token_url = token_url.format(tenantId)
    logger.debug('Token request url: '.format(get_token_url))
    
    # Build the client assertion
    assertion = get_client_assertion(get_token_url)
    
    # Construct the required post data
    # See http://www.cloudidentity.com/blog/2015/02/06/requesting-an-aad-token-with-a-certificate-without-adal/
    post_form = {
                  'resource': resource,
                  'client_id': client_registration.client_id(),
                  'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                  'client_assertion': assertion,
                  'grant_type': 'client_credentials',
                  'redirect_uri': redirect_uri,
                }
                
    r = requests.post(get_token_url, data = post_form, verify = verifySSL) 
    logger.debug('Received response from token endpoint.')
    logger.debug(r.json())
    return r.json()
  else:
    logger.debug('Could not parse token: {0}'.format(token))
    return ''
  
def get_client_assertion(get_token_url):
  # Create a GUID for the jti claim
  id = str(uuid.uuid4())
  
  thumbprint = client_registration.cert_thumbprint()
  
  # Build the header
  client_assertion_header = {
                              'alg': 'RS256',
                              'x5t': thumbprint,
                            }
                            
  # Create a UNIX epoch time value for now - 5 minutes
  # Why -5 minutes? To allow for time skew between the local machine
  # and the server.
  now = int(time.time()) - 300
  # Create a UNIX epoch time value for now + 10 minutes
  ten_mins_from_now = now + 900
  
  # Build the payload per
  # http://www.cloudidentity.com/blog/2015/02/06/requesting-an-aad-token-with-a-certificate-without-adal/
  client_assertion_payload = { 'sub': client_registration.client_id(),
                               'iss': client_registration.client_id(),
                               'jti': id,
                               'exp': ten_mins_from_now,
                               'nbf': now,
                               'aud': get_token_url, #.replace('/', '\\/'),
                             }
                     
  string_assertion = json.dumps(client_assertion_payload)
  logger.debug('Assertion: {0}'.format(string_assertion))
  
  # Generate the stringified header blob
  assertion_blob = get_assertion_blob(client_assertion_header, client_assertion_payload)
  
  # Sign the data
  signature = get_signature(assertion_blob)
  
  # Concatenate the blob with the signature
  # Final product should look like:
  # <base64-encoded-header>.<base64-encoded-payload>.<base64-encoded-signature>
  client_assertion = '{0}.{1}'.format(assertion_blob, signature)
  logger.debug('CLIENT ASSERTION: {0}'.format(client_assertion))
  
  return client_assertion
  
def get_assertion_blob(header, payload):
  # Generate the blob, which looks like:
  # <base64-encoded-header>.<base64-encoded-payload>
  header_string = json.dumps(header).encode('utf-8')
  encoded_header = base64.urlsafe_b64encode(header_string).decode('utf-8').strip('=')
  logger.debug('ENCODED HEADER: {0}'.format(encoded_header))
  
  payload_string = json.dumps(payload).encode('utf-8')
  encoded_payload = base64.urlsafe_b64encode(payload_string).decode('utf-8').strip('=')
  logger.debug('ENCODED PAYLOAD: {0}'.format(encoded_payload))
  
  assertion_blob = '{0}.{1}'.format(encoded_header, encoded_payload)
  return assertion_blob
  
def get_signature(message):
  # Open the file containing the private key
  pemFile = open(client_registration.cert_path(), 'rb')
  keyData = pemFile.read()
  logger.debug('KEY FILE: {0}'.format(keyData))
  
  privKey = rsa.PrivateKey.load_pkcs1(keyData)
  
  # Sign the data with the private key
  signature = rsa.sign(message.encode('utf-8'), privKey, 'SHA-256')
  
  logger.debug('SIGNATURE: {0}'.format(signature))
  
  # Base64-encode the signature and remove any trailing '=' 
  encoded_signature = base64.urlsafe_b64encode(signature)
  encoded_signature_string = encoded_signature.decode('utf-8').strip('=')
  
  logger.debug('ENCODED SIGNATURE: {0}'.format(encoded_signature_string))
  return encoded_signature_string

# This function takes the base64-encoded token value and breaks
# it into header and payload, base64-decodes the payload, then
# loads that into a JSON object.
def parse_token(encoded_token):
  logger.debug('Entering parse_token.')
  logger.debug('  encoded_token: {0}'.format(encoded_token))

  try:
      # First split the token into header and payload
      token_parts = encoded_token.split('.')
      
      # Header is token_parts[0]
      # Payload is token_parts[1]
      logger.debug('Token part to decode: {0}'.format(token_parts[1]))
      
      decoded_token = decode_token_part(token_parts[1])
      logger.debug('Decoded token part: {0}'.format(decoded_token))
      logger.debug('Leaving parse_token.')
      return json.loads(decoded_token)
  except:
      return 'Invalid token value: {0}'.format(encoded_token)

def decode_token_part(base64data):
  logger.debug('Entering decode_token_part.')
  logger.debug('  base64data: {0}'.format(base64data))

  # base64 strings should have a length divisible by 4
  # If this one doesn't, add the '=' padding to fix it
  leftovers = len(base64data) % 4
  logger.debug('String length % 4 = {0}'.format(leftovers))
  if leftovers == 2:
      base64data += '=='
  elif leftovers == 3:
      base64data += '='
  
  logger.debug('String with padding added: {0}'.format(base64data))
  decoded = base64.b64decode(base64data)
  logger.debug('Decoded string: {0}'.format(decoded))
  logger.debug('Leaving decode_token_part.')
  return decoded.decode('utf-8')

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