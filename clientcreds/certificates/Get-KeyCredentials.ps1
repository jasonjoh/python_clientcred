# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license. See full license at the bottom of this file.
# This script automates the steps outlined in 
# http://blogs.msdn.com/b/exchangedev/archive/2015/01/21/building-demon-or-service-apps-with-office-365-mail-calendar-and-contacts-apis-oauth2-client-credential-flow.aspx
# For getting the base64 cert value and thumprint from an X509 .cer file.
Param([string]$certFilePath)

$outFile = ".\keyCredentials.txt"
Clear-Content $outFile

Write-Host "Loading certificate from" $certFilePath

$cer = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$cer.Import($certFilePath)

$data = $cer.GetRawCertData()
$base64Value = [System.Convert]::ToBase64String($data)

$hash = $cer.GetCertHash()
$base64Thumbprint = [System.Convert]::ToBase64String($hash)

$keyid = [System.Guid]::NewGuid().ToString()

Add-Content $outFile '"keyCredentials": ['
Add-Content $outFile '  {'
$stringToAdd = '    "customKeyIdentifier": "' + $base64Thumbprint + '",'
Add-Content $outFile $stringToAdd
$stringToAdd = '    "keyId": "' + $keyid  + '",'
Add-Content $outFile $stringToAdd
Add-Content $outFile '    "type": "AsymmetricX509Cert",'
Add-Content $outFile '    "usage": "Verify",'
$stringToAdd = '    "value": "'  + $base64Value + '"'
Add-Content $outFile $stringToAdd
Add-Content $outFile '  }'
Add-Content $outFile '],'

Write-Host "Key Credential entry created in" $outFile

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