#!/bin/bash
DATE=`date -I`
VERSION=0.5-$DATE
BASEDIR=dist/Nethack-Records-$VERSION

mkdir -p $BASEDIR/lib/HTML
mkdir -p $BASEDIR/docs
mkdir -p $BASEDIR/tmpl
mkdir -p $BASEDIR/css
cp -a CREDITS LICENSE CHANGELOG INSTALL README records.cgi *.png $BASEDIR
cp -a css/*.css $BASEDIR/css
cp -a lib/HTML/Template.pm lib/HTML/ARTISTIC lib/HTML/GPL lib/HTML/ANNOUNCE lib/HTML/FAQ lib/HTML/README $BASEDIR/lib/HTML
cp -a lib/optionsParser.pm $BASEDIR/lib
cp -a docs/* $BASEDIR/docs
cp -a tmpl/* $BASEDIR/tmpl
#cp -a *.tmpl dist/Nethack-Records/
cp -a options.cfg $BASEDIR/
cd dist
tar czf ../Nethack-Records-$VERSION.tar.gz Nethack-Records-$VERSION
cd ..
rm -r $BASEDIR
echo "Distribution created in Nethack-Records-$VERSION.tar.gz"
