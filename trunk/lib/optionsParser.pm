# $Id: optionsParser.pm 46 2004-03-06 01:19:11Z bjorn $
package optionsParser;

my $line = 0;
my @file;
my %options;

sub init() {
    my $opfile = $_[0];
    if (!defined($opfile)) {
        $opfile = "./options.cfg";
    }
    
    open (FILE, $opfile) or die("Could not load optionsfile: $!");
    @file = <FILE>;
    close(FILE);
    
    while (&hasMoreTokens()) {
        my ($attr, $val, $line) = &nextToken();
        if ($val=~/^true$/) { $val=1; }
        elsif ($val=~/^false$/) { $val=0; }
        if ($attr ne "") {
            $options{$attr} = $val;
        }
    }
    
    
}

sub printOptions() {
    foreach (keys(%options)) {
        print "$_ -> $options{$_}\n";
    }
}

sub readOptions() {
    return %options;
}

sub nextToken() {
    my $l = $file[$line]; # read the next line 
	while ($l !~ /\s*(.+?)\s*\=\s*\"(.+?)\"\s*;/) {
		$l = $file[++$line];
		if (!&hasMoreTokens()) {
			return ("","",$line);
		}
	}
	
	$l =~ /\s*(.+?)\s*\=\s*\"(.+?)\"\s*;/;
	$line++;
        return ($1,$2,$line);
}

sub hasMoreTokens() {

    if ($line>$#file) {
	return 0;
    }
	
    return 1;
}
1;
