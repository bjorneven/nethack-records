Nethack-Records
===============
Nethack-records is a script that lets users view statistics from a nethack logfile. 

It features an on-demand statistics generator for Nethack and is meant to be run on a webserver. It has several types of statistics, ranging from character info to daily and weekly stats. It is implemented with a modern template system, and is very customizable.

Features include:

- Top 10 players view
- All players view
- Sort by various criteria e.g. Class and Cause of death
- Various ranking possibilities
- Last five players view
- Todays games
- View per game statistics

Future enhancements include:

- Support for a player database
- An applet for viewing recorded games
- A comment system

Current version is 0.5.1, 08.06.2007

# View a demo
[http://nethack.uib.no/statistikk/](http://nethack.uib.no/statistikk/)

Installation Instructions
=========================
Nethack-Records requires
 - Perl 5 and CGI capable webserver.
 - It also requires HTML::Template installed,
   but I have included it in the distribution, no further installation 
   is required on that part. Put the script and all the templates
   in a cgi-enabled webfolder and it is good to go.

Oh, by the way, the scripts need access to
 - the nethack-logfile
 - and you have to make sure it can read it by editing the "options.cfg"
   in the script dir.
 - If your webserver does not have access to the logfile
   directly you have to set up a cronjob or something to copy the
   file where the script can read it.
 - Create an options.cfg. Example-file as options.cfg-default included.


# Modify the placement of options.cfg


If you need to move the options file to another place, edit index.cgi to reflect
this. The webserver needs read-permissions to this file.

# Installation on a cgi-bin/ environment

Often, the cgi-bin/ folder of Apache has very restrictive permissions. Therefore
the webbrowser cannot access the css and image-files placed by default inside the 
script-directory.

To remedy this, move the img/ and css/ directories outside of cgi-bin and modify
the variables "css_path" and "img_path" in options.cfg according to the URI path. 
Note that these files need to be in the webserver-directory as they are read by 
a webbrowser, and not the script. 

Example:
Script is in http://example.com/cgi-bin/nhrec/, which is at /var/www/example.com/cgi-bin/nhrec 
on the filesystem. The variable "uri" in options.cfg should then be

uri="http://example.com/cgi-bin/nhrec/";

Move img/ and css/ to a directory, say /var/www/example.com/nhrec/. Then, edit
 css_path and img_path to 

 css_path="/nhrec/css/";
 img_path="/nhrec/img/";

Now the webserver will again find the files requested, and all is good.

Nethack-Records is distributed under the GPL (see LICENSE)

HTML::Template.pm is included with this code, read lib/HTML/GPL, 
lib/HTML/ARTISTIC and lib/HTML/README for more information
about the template engine.

See CREDITS for more information about the contributors, and
docs/Development-Plan.txt for what to expect in the future 
for Nethack-Records.

For updates, visit http://nethack.uib.no/nethack-records.

Be seeing you...
