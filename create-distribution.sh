#!/bin/sh
rm -r dist/Nethack-Records
mkdir -p dist/Nethack-Records/lib/HTML
mkdir -p dist/Nethack-Records/docs
mkdir -p dist/Nethack-Records/tmpl
cp -a CREDITS LICENSE CHANGELOG INSTALL README nethack.css records.cgi *.png dist/Nethack-Records
cp -a lib/HTML/Template.pm lib/HTML/ARTISTIC lib/HTML/GPL lib/HTML/ANNOUNCE lib/HTML/FAQ lib/HTML/README dist/Nethack-Records/lib/HTML
cp -a lib/optionsParser.pm dist/Nethack-Records/lib
cp -a docs/* dist/Nethack-Records/docs
#cp -a tmpl/* dist/Nethack-Records/tmpl
cp -a *.tmpl dist/Nethack-Records/
cp -a options.cfg dist/Nethack-Records/
cd dist
tar cvzf ../Nethack-Records.tar.gz Nethack-Records
cd ..


