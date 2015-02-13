# smtp_to_tcp
Tunnel a TCP connection by sending emails. It's so ridiculous, it had 
to be done.

## Backstory

You've woken up and found yourself in the middle of a desert with only 
one tool: a satellite phone with access to a single email account. You 
really, really want to google something. It's time for `smtp_to_tcp`.
 
## Status

*Core services not yet functional*

 - `proxy.py`
  
   + The core proxy functionality works, but it still 
   frequently results in hung requests. Nevertheless, I've used it
   to browse [reddit](http:/www.reddit.com), so it's not that bad. 
 
  
 - `remote.py` 

### Known limitations

 - The proxy server does not support secure connections.
 
 - The remote server does not support secure connections.
   
 - The current proxy often hangs on requests, making a necessarily 
 slow and gnarly connection even slower and less reliable. 

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