# email_to_tcp
Tunnel a TCP connection by sending emails. It's so ridiculous, it had 
to be done.

## Backstory

You've woken up and found yourself in the middle of a desert with only 
one tool: a satellite phone with access to a single email account. You 
really, really want to check hacker news. It's time for `smtp_to_tcp`.

## Basic requirements

While you can test-drive this software with only one computer, you'll 
find it's only useful if you use at least two computers.  We'll call 
these computers the `local` and the `remote` machines. 

  - You'll use the `local` machine to browse the internet using only 
  your email connection. The local machine needs access to an SMTP 
  and IMAP server. 
  
  - The `remote` machine reads emails from the local machine and 
   fetches the requested data from the internet.  The remote machine 
   should have unfettered access to the internet.

If you just want to test-drive the code, open up two different 
terminals, one for the `local` machine and one for the `remote` machine.

(TODO: Picture illustrating this basic architecture)

**Note:** The code uses IMAP IDLE push notifications to lower the 
latency of the connection somewhat.  This works well for Google's 
Gmail, but some email providers do not support this convenient 
protocol (*cough* Yahoo! *cough*). Use your [google fu] [google-fu] 
to check that your email supports push.
 
[google-fu]: http://www.urbandictionary.com/define.php?term=google-fu

## Installation (both machines)

*Given the chance, this code will kill you and everyone you care 
about.* Make sure to test all of these settings before you embark on a
journey into the desert. 

To start, first install `python3`  on both the `local` and `remote` 
machines. The code was tested with python 3.4, and your mileage may 
vary with different versions.

You'll also want to install the packages listed in `requirements.txt`. 
The `pip` package manager makes the process painless:
    
     >>> pip3 install -r requirements.txt

## Setting up your `remote` machine

To start the server on the `remote` machine, run the following code

    >>> python3 -m email_to_tcp --remote 

You will be prompted with a series of questions about your email 
username and password. If you see a success message, you are good to 
go. This process needs to be running as long as you want to access the 
internet.

## Setting up your `local` machine

This service requires a bit more work. First, we start the local proxy 
server:

    >>> python3 -m email_to_tcp --local
    
You'll again be prompted with a series of questions. Make sure that 
the `email-to` address matches the email account that the `remote` 
machine is monitoring. 

Once you see the success message, it's time to tell your browser to 
use this special proxy server to access the internet.  **The easiest 
way to do this involves using firefox.**  Other

Assumming that you chose the 
default settings above, you need to set the address 

### TODO

 - Support HTTPS
 
 - Support IMAP servers that don't use IDLE push notifications 
   
 - Multi-thread requests
 
 - Write meaningful tests 

# Architecture

SMTP-to-TCP requires two pieces of software in order for you to access
the internet through an SMTP server and IMAP mailbox that you have 
access to. The code involves a local proxy server (`proxy.py`) and a
remote custom SMTP server (`remote.py`).

## The protocol

The `proxy.py` module provieds a bare-bones HTTP proxy server that 
runs on your local machine. By default, it opens a proxy server on 
`localhost:1111`. When you make a TCP request through this port,
your request is repackaged into an email and sent through your SMTP
server to the mailbox for a domain which is running the `remote.py` 
SMTP server script.

When this email is delivered to `remote.py`, the server unpacks the 
packet and sends it out to the internet for a response. The server
packages this response in another email to the `REPLY-TO` address 
from the original message, keeping the unique string from the subject
line intact.

Now, the subject line of the email includes a unique identifying
string. On the other end, the proxy server has been querying your
IMAP inbox for a response.  When it gets a hit, it unpacks the 
message attachment, and sends it back to your browser as a response
to the original request. 

Yes, it's ridiculous. 

# Setup

*TODO*