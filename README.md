# email_to_tcp
Tunnel a TCP connection by sending emails. It's so ridiculous, it had 
to be done.

## Backstory

You've woken up and found yourself in the middle of a desert with only 
one tool: a satellite phone with access to a single email account. You 
really, really want to check (reddit)[http://www.reddit.com]. It's time
for `smtp_to_tcp`.

# Set up

**WARNING**

*Given the chance, this code will kill you and everyone you care 
about.* Make sure to thoroughly test all of these settings before you 
embark on a journey into the desert, and note that the code is not
designed for high-reliability needs. You've been warned.

## Basic requirements

While you can test-drive this software with only one computer, you'll 
only be able to use it in the desert if you've set up at least 
two computers.  We'll call these computers the `local` and the `remote`
machines. 

  - The `local` machine lets you browse the internet using your email 
  connection. The local machine needs access to an SMTP and IMAP 
  server. 
  
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
to check that your email supports IDLE push.
 
[google-fu]: http://www.urbandictionary.com/define.php?term=google-fu

## Installation (both machines)


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
use this special proxy server to access the internet.  **The following
instructions apply to Firefox on a Mac.**
   
  1. Install Firefox.
  2. Go to Preferences -> Advanced -> Network and click on `Settings...`
  3. Click on `Manual proxy configuration:` and (assuming you are using 
  the default proxy settings) set the HTTP Proxy to `127.0.0.1` and Port to
  `9999`. Leave the other boxes blank.
  4. Click `OK`.
  
If everything works, you should be able to access the internet. Try 
[hacker news](http://news.ycombinator.com) or 
[reddit](http://www.reddit.com). 

# Questions?
 
 Submit an issue, or email me at `my_address`, where
 
     my_address = '.'.join(['michael', 'b', 'mccoy', '@', 'gmail', 'com'])
 

# TODO

 - Support HTTPS
 
 - Support IMAP servers that don't use IDLE push notifications 
   
 - Multi-thread requests
 
 - Write meaningful tests
 
 