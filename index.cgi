#!/usr/bin/perl -I.
#
# Bjorn Even Wahlstrom "bjorn at wahlstroem dot org"
#
# $Id: records.cgi 47 2004-03-06 01:21:28Z bjorn $
# $URL$
use strict;
use lib './lib';
use Time::Local;
use CGI;
use HTML::Template;
use optionsParser;
use CGI::Carp qw(fatalsToBrowser);


# static global variables
my $LOGFILE;
my $URI;
my $TEMPLATE;
my $OPTIONS_FILE = "./options.cfg";
my $VERSION = "0.5.0, 08.09.2004";
my $CREATE_RDF;
my $RDF_FILE;
my %OPTIONS;
my %TEMPLATE_OPTIONS;

# nethack stores various statistics in abbreviated form
# these maps abbreviated to full form
my %al_map;
my %sex_map;
my %race_map;
my %class_man;
my %class_woman;
my %dungeon_map;

# dynamic global variables
my @data;
my $q = new CGI;
my $template;
my $sortType;


# read and set options
&setOptions();

# parse nethack logfile, and store sorted by experience
@data = @{&parseFile($LOGFILE)};


# this param is just for testing.. e.g. records.cgi?sortType=topten&bydate=true..
if ($q->param('bydate')) {
    @data= @{&bydate(\@data)};
}


# choose what to do based on input
$sortType = $q->param('sortType');


if ($sortType eq "today") {
    &todayList;
} elsif ($sortType eq "ranking") {
    &ranking($q->param('rank'));
} elsif ($sortType eq "topten") {
    &tenList;
} elsif ($sortType eq "all") {
    &allList;
} elsif ($sortType eq "lastten") {
    &lastten;
} elsif ($sortType eq "commondeath") {
    &commondeath;
} elsif ($sortType eq "links") {
    &links;
} elsif ($sortType eq "char") {
    &characters();
}  elsif ($q->param('name')) {
    &personStat(lc($q->param('name')));
} elsif ($q->param('race')) {
    &stat('race',lc($q->param('race')));
} elsif ($q->param('class')) {
    &stat('class',lc($q->param('class')));
} elsif ($q->param('sex')) {
    &stat('sex',lc($q->param('sex')));
} elsif ($q->param('death')) {
    &stat('death',lc($q->param('death')));
} elsif ($q->param('alignment')) {
    &stat('alignment',lc($q->param('alignment')));
} elsif ($q->param('game')) {
    &game($q->param('game'));
} else {
    # default
    &lastten();
}

# Generates an RDF-file
# should be moved, connected to a script option or something
if ($CREATE_RDF) {
    &genRSS;
}

my %quickstat = %{&quickstat};
$template->param( version => $VERSION);
$template->param( hostname => $URI);

my $r = int(rand(6));
my $qstat;

if ($r==0) {    # today
    $qstat="$quickstat{today_number} people have died today";
} elsif ($r==1) {
    $qstat="$quickstat{week_number} have died the last 7 days";
} elsif ($r==2) {
    $qstat="$quickstat{male_percent}\% of the characters were male";
} elsif ($r==3) {
    $qstat="$quickstat{female_percent}\% of the characters were female";
} elsif ($r==4) {
    $qstat="$quickstat{distinct_number} people have played Nethack!";
} else {
    $qstat="$quickstat{total} games have been played";
}

$template->param( quickstat => $qstat);

print "Content-type: text/html\n";
print "X-Nethack-Games: $#data\n\n";


print $template->output;


#
#
# functions follows
#

# sort @data by experience
sub byexp {
    my @data=@{$_[0]};
    @data = sort {$b->{exp} <=> $a->{exp}} @data;
    return \@data;
}

# Sort @data by date
sub bydate {
    my @data=@{$_[0]};
    @data = sort {$b->{date} <=> $a->{date}} @data;
    return \@data;
}

# Sort @data by original placement
sub byorig {
    my @data=@{$_[0]};
    @data = sort {$b->{place_orig} <=> $a->{place_orig}} @data;
    return \@data;
}

# parse the logfile, returning a \@array-of-hashes reference
sub parseFile {
    my $file = $_[0]; # logfile to parse

    open(FILE,$file) or die("Could not load logfile: $!");
    my @records = <FILE>;
    close(FILE);

    my @data;
    my $line_nr = 0;

    # read in line by line, split up into variables
    #format:
    # version points deathwhere deathlev maxlvl hp maxhp deathdnum enddate
    # startdate usernum class race gender alignment name,death
    foreach (@records) {
        chop;

        # separate all fields into @temp. This works for all fields except death, which is taken care of below
        my @temp = split(' ',$_);   # split by " " separated fields,
            
        # take care of death, field
        my $al = $temp[14];         # first, find alignment
        m/$al\s(.+?),(.+)/;
        my $name = $1;              # use it as anchorpoint to find name
        my $desc = $2;              # and death
        my $start_date = $temp[9];
        my $end_date = $temp[8];
        $start_date =~ m/(\d{4})(\d{2})(\d{2})/;   # year,month,day..

        my $start_year = $1 - 1900;       # perl date convert has the form YY not YYYY
        my $start_month = $2-1;           # and months are from 0..11
        my $start_day = $3;
        $start_date = timelocal(0,0,0,$start_day,$start_month,$start_year);     # convert to seconds
        
        $end_date =~ m/(\d{4})(\d{2})(\d{2})/;   # year,month,day..
        my $end_year = $1 - 1900;       # perl date convert has the form YY not YYYY
        my $end_month = $2-1;           # and months are from 0..11
        my $end_day = $3;
        $end_date = timelocal(0,0,0,$end_day,$end_month,$end_year);     # convert to seconds
                    
        # convert some classes to reflect their sex, e.g. priest->priestess if woman
        my  $class;
        if ($temp[13] eq "Mal") {
            $class = $class_man{$temp[11]};
        } else {
            $class = $class_woman{$temp[11]};
        }

        # older nethack versions write this
        # but we want it to be for the newer version
        if ($desc eq "starvation") {
            $desc="died of starvation";
        }

        # Map dungeon numbers to actual dungeon names
        my $deathwhere = $dungeon_map{$temp[2]};
        
        # the rest of the fields lie nicely in the array @temp

        # put it all into a hash.
        # notice that there are more fields in @temp
        # that are not used, and therefore not put in here
        # if you want to use that data, create a field and
        # you are good to go!
        

        my %record = ( name => lc($name),
                        death => $desc,
                        exp => $temp[1],
                        class => $class,
                        race => $race_map{$temp[12]},
                        alignment => $al_map{$temp[14]},
                        sex => $sex_map{$temp[13]},
                        date => $start_date,
                        end_date => $end_date,
                        place => 0,
                        place_orig => $line_nr++,
                        hp => $temp[5],
                        maxhp => $temp[6],
                        deathlvl => $temp[3],
                        maxlvl => $temp[4],
                        deathwhere => $deathwhere
        );

        push(@data,\%record);   # the hash is stored in @data
    }


    # we are now done saving.
    # now we are going to sort, and then save the place on the highscore list for easy access
    # since this is not available from nethack, we have to iterate ourselves.
    #

    @data=@{&byexp(\@data)};         # sort by experience

    my $place = 1;
    my $real_rank = 0;
    my $previous_score = -1;
    
    # iterating..
    # each %record is by default located in $_
    for (my $x=0;$x < $#data;$x++) {
        
        if ($previous_score != $data[$x]->{exp}) {
            $real_rank = $place;
            $previous_score = $data[$x]->{exp};
        }
        $data[$x]->{place}=$real_rank;    # indirect derefencing with -> to access fields
        $place++;
    }

    return \@data;

}

sub genRSS {
    open(FILE,">$RDF_FILE") or die("Could not create RDF-file");
    print FILE "<?xml version=\"1.0\"?>\n";
    print FILE "<rdf:RDF
    xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"
    xmlns=\"http://my.netscape.com/rdf/simple/0.9/\"
    >\n";


    print FILE "\t<channel>\n";
    print FILE "\t\t<title>Nethack daily statistics</title>\n";
    print FILE "\t\t<link>$URI</link>\n";
    print FILE "\t</channel>\n";
    my $today = time;
    foreach (@data) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";
        my $color="";

        if (($today - $record{date}) <= 86400) {

            my %entry = (   name =>$record{name},
                            class => $record{class},
                            race => $record{race},
                            alignment => $record{alignment},
                            sex => $record{sex},
                            death => $record{death},
                            place => $record{place},
                            date => $date,
                            color => $color,
                            exp => $record{exp}
                        );

            print FILE "\t\t<item>\n";
            print FILE "\t\t\t<title>$record{name}, $record{class} with $record{exp} points</title>\n";
            print FILE "\t\t\t<description>$record{name}, $record{class} with $record{exp} points</description>\n";
            print FILE "\t\t</item>\n";
        }
    }

    print FILE "</rdf:RDF>";

}

sub characters {
    $template = HTML::Template->new(filename => "$TEMPLATE/chars.tmpl",%TEMPLATE_OPTIONS);

    my %persons;
    my @entries;
    
# sort out all characters from logfile
    foreach (@data) {
        $persons{$_->{name}}="";
    }
# save in a template-friendly format
    foreach (keys %persons) {
        my %r = ( name => $_ );
        push(@entries,\%r);
    }
    
    $template->param(entry => \@entries);
    $template->param(uri => "?sortType=char");
}

sub links {
    $template = HTML::Template->new(filename => "$TEMPLATE/links.tmpl",%TEMPLATE_OPTIONS);
}

sub game {
    my $place = $_[0];
    my %record;
    $template = HTML::Template->new(filename => "$TEMPLATE/game.tmpl",%TEMPLATE_OPTIONS);
    $template->param(uri => "?game=$place");

# find the game
    foreach (@data) {
        if ($_->{place_orig} eq $place) {
            %record = %{$_};
            last;
        }
    }
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{date});
    $mon++;
    $year += 1900;
    my $start_date = "$mday.$mon.$year";
    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
    $mon++;
    $year += 1900;
    my $end_date = "$mday.$mon.$year";
    
    $record{date} = $start_date;
    $record{end_date} = $end_date;
    
    my @entry = (\%record);
    $template->param(ENTRY => \@entry);

}

sub commondeath {
    $template = HTML::Template->new(filename => "$TEMPLATE/commondeath.tmpl",%TEMPLATE_OPTIONS);

    $template->param(uri => "?sortType=commondeath");
    my @sortedscores;
    my %score;
    my $helpless = 0;
    foreach (@data) {
        my %r = %{$_};
        my $desc = $r{death};
        my $desc1;
        my $desc2;
        if ($desc =~ /(.+?)\,(.+)/) {
            $desc1 = $1;
            $score{$desc1} += 1;
            $helpless++;
            $desc2 = $2;
        } else {
            $score{$desc} += 1;
        }
    }

    # now sort..
    foreach my $key (sort {$score{$b} <=> $score{$a}} (keys(%score))) {
	    my %tmp = (death => $key, num => $score{$key});
   	    push(@sortedscores,\%tmp);
    }

    $template->param(SCORES => \@sortedscores);
    $template->param(helpless => $helpless);

}

# Sort statistics by a given attribute
# parameter: attribute-name, sortby-attribute
# return: void
sub stat {

    my $type_name = $_[0];
    my $type = $_[1];


    # at this point, $template may be defined (we may be called from personStat)
    # if so, dont initialize new template
    if (!$template) {
        $template = HTML::Template->new(filename => "$TEMPLATE/stat.tmpl",%TEMPLATE_OPTIONS);
        $template->param(uri => "?$type_name=$type");
    }

    $template->param(type => $type);
    $template->param(type_name => $type_name);

    my @games;
    foreach (@data) {
        my %r = %{$_};
# 	this hack may cause unwanted functionality
#       if (lc($r{$type_name}) =~ /^$type/i) {
        if (lc($r{$type_name}) eq $type) {
            push(@games,\%r);
        }
    }

    my $counter = 1;
    my $today = time;
    my @entries;

    foreach (@games) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";

        my $color="";
        if (($today - $record{end_date}) <= 604800) {
            $color="class='uke'";
        }
        if (($today - $record{end_date}) <= 86400) {
            $color="class='dag'";
        }

        $record{date}=$date;
        $record{color}=$color;
        push(@entries,\%record);
    }
    $template->param(STAT => \@entries);

}

# Displays a page containing character statistics, and also
# all games to this person sorted by experience
# parameter: character name
# return: void
sub personStat {
    $template = HTML::Template->new(filename => "$TEMPLATE/person.tmpl",
    					die_on_bad_params=>0,%TEMPLATE_OPTIONS);
    my $name = $_[0];
    $template->param(name => $name);
    $template->param(uri => "?name=$name");

    my @entries;
    my @games;
    my %best_exp;
    my %worst_exp;
    my %first_game;
    my %last_game;

    # find all records belonging to this person
    foreach (@data) {
        my %r = %{$_};
        if ($r{name} eq $name) {
            push(@games,\%r);
	}
    }
    # find first and last game, sort by first game first 
    @games = reverse @{&byorig(\@games)};
    %first_game = %{$games[0]};
    %last_game = %{$games[$#games]};
    %best_exp = %first_game; # default
    %worst_exp = %first_game; # default
    foreach (@games) {
	if ($_->{exp}>=$best_exp{exp}) {%best_exp=%{$_};}
	if ($_->{exp}<=$worst_exp{exp}) {%worst_exp=%{$_};}
    }

    my $dato_start;
    my $dato_end;
    $dato_start = $first_game{date};
    $dato_end = $last_game{date};

    $best_exp{text} = "Best ranking";
    $worst_exp{text} = "Worst ranking";
    $first_game{text} = "First game";
    $last_game{text} = "Last game";

    @entries = (
                \%best_exp,
                \%worst_exp,
                \%first_game,
                \%last_game
                );


    foreach (0..3) {
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($entries[$_]->{date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";
        my $color="";
        my $today=time;
        if (($today - $entries[$_]->{date}) <= 604800) {
            $color="class='uke'";
        }
        if (($today - $entries[$_]->{date}) <= 86400) {
            $color="class='dag'";
        }
        $entries[$_]->{color} = $color;
        $entries[$_]->{date} = $date;
    }
    
    # the 4 statistics are now in place
    $template->param(BEST => \@entries);
    
    # show all death-reasons
    my $times = $#games+1;
    my $playtime = $dato_end - $dato_start;

    my $weeks = $playtime / 60/60/24 /7;
    $weeks =~ s/(\..+)//;
    if ($weeks == 0) { $weeks = 1; }
    my $times_pr_week = $times/$weeks;


    $template->param(times => $times);
    $template->param(times_pr_week => $times_pr_week);


    my @sortedscores;
    my %score;
    my $helpless = 0;
    foreach (@games) {
        my $desc = $_->{death};
        my $desc1;
        my $desc2;
        if ($desc =~ /(.+?)\,(.+)/) {
            $desc1 = $1;
            $score{$desc1} += 1;
            $helpless++;
            $desc2 = $2;
        } else {
            $score{$desc} += 1;
        }
    }

    # now sort by how many times one has died of this death
    foreach my $key (sort {$score{$b} <=> $score{$a}} (keys(%score))) {
	my %tmp = (death => $key, num => $score{$key});
	push(@sortedscores,\%tmp);
    }


    $template->param(SCORES => \@sortedscores);
    $template->param(helpless => $helpless);


    # show all statistics for this person
    &stat('name',$name);
}

# create a quick-statistic
# parameter: void
# return: hash of statistics
sub quickstat {
    my $today = time;
    my $number = 0;
    my $week_number = 0;
    my $female_number = 0;
    my $male_number = 0;
    my %distinct_games;

    foreach (@data) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
        $mon++;
        $year += 1900;

        if (($today - $record{end_date}) <= 86400) {
            $number++;
        }

        if (($today - $record{end_date}) <= 604800) {
            $week_number++;
        }

        if ($record{sex} eq "Male") {
            $male_number++;
        } else {
            $female_number++;
        }
        $distinct_games{$record{name}}+=1;
    }
    my @tmp = keys %distinct_games;
    my $number_distinct = $#tmp;
    my $male_percent = $male_number/$#data *100;
    my $female_percent = $female_number/$#data *100;

    if ($male_percent=~/^(\d+)\..+$/) {
        $male_percent=$1;
    }
    if ($female_percent=~/^(\d+)\..+$/) {
        $female_percent=$1;
    }

    my %stat = ( today_number => $number,
                    week_number => $week_number,
                    male_percent => $male_percent,
                    female_percent => $female_percent,
                    total => $#data+1,
                    distinct_number => $number_distinct
                    );
    return \%stat;
}

# Display statistics for today sorted by experience
# parameter: void
# return: void
sub todayList {
    $template = HTML::Template->new(filename => "$TEMPLATE/today.tmpl",%TEMPLATE_OPTIONS);
    my $today = time;
    my @entries;

    $template->param(uri => "?sortType=today");

    foreach (@data) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";
        my $color="";

        if (($today - $record{end_date}) <= 86400 && $record{exp} != 0) {

            $record{date}=$date;
            $record{color}=$color;
            push(@entries,\%record);
        }
    }
    $template->param( ENTRY => \@entries);

}
# Top 10 list
# parameter: void
# return: void
sub tenList {
    $template = HTML::Template->new(filename => "$TEMPLATE/topten.tmpl",%TEMPLATE_OPTIONS);
    $template->param(uri => "?sortType=topten");

    my $counter = 1;
    my $today = time;
    my @entries;

    foreach (@data) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";

        my $color="";
        if (($today - $record{end_date}) <= 604800) {
            $color="class='uke'";
        }
        if (($today - $record{end_date}) <= 86400) {
            $color="class='dag'";
        }

        
        $record{date}=$date;
        $record{color}=$color;
        $counter++;
        push(@entries,\%record);
        if ($counter > 10) {
            last;
        }
    }

    $template->param( ENTRY => \@entries);
}


# display everything sorted by experience
# parameter: void
# return: void
sub allList {
    $template = HTML::Template->new(filename => "$TEMPLATE/all.tmpl",%TEMPLATE_OPTIONS);
    $template->param(uri => "?sortType=all");

    my $counter = 1;
    my $today = time;
    my @entries;

    
    foreach (@data) {
        my %record=%{$_};
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
        $mon++;
        $year += 1900;
        my $date = "$mday.$mon.$year";
        
        my $color="";
        if (($today - $record{end_date}) <= 604800) {
            $color="class='uke'";
        }
        if (($today - $record{end_date}) <= 86400) {
            $color="class='dag'";
        }

        $record{date}=$date;
        $record{color}=$color;
    
        $counter++;
        if ($record{exp} != 0) {
            push(@entries,\%record);
        }
    }
        $template->param( ENTRY => \@entries);
}



sub lastten {
    $template = HTML::Template->new(filename => "$TEMPLATE/lastten.tmpl",%TEMPLATE_OPTIONS);
    $template->param(uri => "?sortType=lastten");

    @data=@{&byorig(\@data)};
    my @entries;
    my $today = time;

    for (my $x=0;$x<10;$x++) {
	my %record=%{$data[$x]};
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($record{end_date});
	$mon++;
	$year += 1900;
	my $date = "$mday.$mon.$year";
	
	my $color="";
	if (($today - $record{end_date}) <= 604800) {
	    $color="class='uke'";
	}
	if (($today - $record{end_date}) <= 86400) {
	    $color="class='dag'";
	}
	
        $record{date}=$date;
        $record{color}=$color;
        push(@entries,\%record);
    }
    
    $template->param( ENTRY => \@entries);
}

# Display rank by median/average/best exp score thru all games
# parameter: ranktype (exp, average, median)
# return: void
sub ranking {
    my $rankby = $_[0];
    
    my %persons;    # intermediate data, all persons and scores for them
    my @sorted;

    # get all scores for all persons and store into hash
    # e.g.
    # %persons = (player1=>{123,13123,4234243,5345,0,123213},
    #              player2=>{243324,243324,324,2434,234,432});
    foreach (@data) {
        my %r = %{$_};
        my @scores;
        if (defined $persons{$r{name}}) {
            @scores=@{$persons{$r{name}}};
            push(@scores,$r{exp});
        } else {
            push(@scores,$r{exp});
        }
        $persons{$r{name}}=\@scores;
    }

    if ($rankby eq "exp") {
        @sorted = _ranking_byexp(\%persons);
        $template = HTML::Template->new(filename => "$TEMPLATE/ranking_exp.tmpl",%TEMPLATE_OPTIONS);
        $template->param(uri => "?sortType=ranking&rank=exp");
        $template->param(STAT=>\@sorted);
    } elsif ($rankby eq "average") {
        @sorted = _ranking_byaverage(\%persons);
        $template = HTML::Template->new(filename => "$TEMPLATE/ranking_average.tmpl",%TEMPLATE_OPTIONS);
        $template->param(uri => "?sortType=ranking&rank=average");
        $template->param(STAT=>\@sorted);
    } else {
        @sorted = _ranking_bymedian(\%persons);
        $template = HTML::Template->new(filename => "$TEMPLATE/ranking_median.tmpl",%TEMPLATE_OPTIONS);
        $template->param(uri => "?sortType=ranking&rank=median");
        $template->param(STAT=>\@sorted);
    }

}

# internal method used by ranking() to sort
# %persons by average
# parameter %persons
# return: @sortedaverage
sub _ranking_byaverage {
    my %persons = %{$_[0]};
    my %average;
    my @sortedaverage;
    my $place = 1;

    # create a hash with person
    # and average score
    foreach (keys %persons) {
        my @scores = @{$persons{$_}};
        my $average;
        my $number = ($#scores+1);
        @scores = sort {$a <=> $b} @scores;
        foreach (@scores) {
            $average += $_;
        }
        $average{$_}=int($average/$number);
    }

    foreach my $key (sort average (keys(%average))) {
        my %tmp = (name => $key, score => $average{$key}, place=>$place++);
        push(@sortedaverage,\%tmp);
    }

    sub average {
        $average{$b} <=> $average{$a};
    }
    return @sortedaverage;
}

# internal method used by ranking() to sort
# %persons by median
# parameter %persons
# return: \@sortedmedian
sub _ranking_bymedian {
    my %persons = %{$_[0]};
    my %medians;
    my @sortedmedian;
    my $place = 1;
    # create a hash with person
    # and average score
    foreach (keys %persons) {
        my @scores = @{$persons{$_}};
        my $median;
        my $number = ($#scores+1);
        @scores = sort {$a <=> $b} @scores;
        $median = $scores[int($number/2)];
        $medians{$_}=$median;
    }
    # now sort..
    my @sortedmedian;
    foreach my $key (sort median (keys(%medians))) {
        my %tmp = (name => $key, score => $medians{$key}, place=>$place++);
        push(@sortedmedian,\%tmp);
    }
    sub median {
        $medians{$b} <=> $medians{$a};
    }
    return @sortedmedian;
}

# internal method used by ranking() to sort
# %persons by best exp
# parameter %persons
# return: @sortedexp
sub _ranking_byexp {
    my %persons = %{$_[0]};
    my %bestexp;
    my @sortedexp;
    my $place=1;
    # create a hash with person
    # and average score
    foreach (keys %persons) {
        my @scores = @{$persons{$_}};
        @scores = sort {$a <=> $b} @scores;
        my $exp=$scores[$#scores];
        $bestexp{$_}=$exp;
    }
    # now sort..
    my @sortedexp;
    foreach my $key (sort by_exp (keys(%bestexp))) {
        my %tmp = (name => $key, score => $bestexp{$key}, place=>$place++);
        push(@sortedexp,\%tmp);
    }
    sub by_exp {
        $bestexp{$b} <=> $bestexp{$a};
    }
    return @sortedexp;
}

# reads options from optionsfile
# and sets the variables
sub setOptions() {
# read options from options-file
    &optionsParser::init($OPTIONS_FILE);
#&optionsParser::printOptions();
    %OPTIONS = &optionsParser::readOptions();
    
    $LOGFILE = $OPTIONS{'logfile'};
    if (!defined($LOGFILE)) {
        $LOGFILE = "./logfile";
    }
    
# Specify the location of this script
#
    $URI = $OPTIONS{'uri'};
    my $filename = $0;
    
    $filename =~ s/^\/.+\///;   # remove full path before filename
        $filename =~ s/\?.+$//;      # might also be ?blablbl=asdasd attributes in PUT request
        
        if (!defined($URI)) {
            $URI="http://www.lstud.ii.uib.no/~s1393/Nethack-Records/$filename";
        } else {
            $URI = "$URI"."$filename";
        }
    
    
    
# The directory where templates reside
#
    $TEMPLATE = $OPTIONS{'templatedir'};
    if (!defined($TEMPLATE)) {
        $TEMPLATE="./";
    }
# If true (1) it creates an RDF-file on each run.
# Set to false (0) if you do not want this to be created
    $CREATE_RDF = $OPTIONS{'create_rdf'};
    if (!defined($CREATE_RDF)) {
        $CREATE_RDF = 1;
    }
# Specify RDF-file to create. Contains todays-games. Only
# applicable if CREATE_RDF is true
    $RDF_FILE = $OPTIONS{'rdf_file'};
    if (!defined($RDF_FILE)) {
        $RDF_FILE = "./today.rdf";
    }
    
# Specify shared cache on or off
    if (!defined($OPTIONS{'shared_cache'})) {
        $TEMPLATE_OPTIONS{'shared_cache'} = 0;
    } else {
        $TEMPLATE_OPTIONS{'shared_cache'} = $OPTIONS{'shared_cache'};
    }
    
# this is actually a bit dirty, but makes life a lot simpler, and the code a lot cleaner
    $TEMPLATE_OPTIONS{'die_on_bad_params'} = 0;
    
# map dungeon numbers to names
    %dungeon_map = ( 0 => "The Dungeons of Doom",
                                1 => "unknown (1)",
                                2 => "The Gnomish Mines",
                                4 => "Sokoban",
                                5 => "unknown (5)",
                                6 => "unknown (6)",
                                7 => "the Astral Planes" );
                     
# map shortnames to fullnames
    %al_map = ( Cha => "Chaotic",
                Neu => "Neutral",
                Law => "Lawful"
                );
    
    %sex_map = (Mal => "Male",
                Fem => "Female"
                );
    
    %race_map = ( Orc => "Orc",
                  Hum => "Human",
                  Elf => "Elf",
                  Dwa => "Dwarf",
                  Gno => "Gnome"
                  );
    
    %class_man = ('Arc' => 'Archaeologist',
                  'Bar' => 'Barbarian',
                  'Cav' => 'Caveman',
                  'Elf' => 'Elf',
                  'Hea' => 'Healer',
                  'Kni' => 'Knight',
                  'Mon' => 'Monk',
                  'Pri' => 'Priest',
                  'Rog' => 'Rogue',
                  'Ran' => 'Ranger',
                  'Sam' => 'Samurai',
                  'Tou' => 'Tourist',
                  'Val' => 'Valkyrie',
                  'Wiz' => 'Wizard'
                  );
    %class_woman = ('Arc' => 'Archaeologist',
                    'Bar' => 'Barbarian',
                    'Cav' => 'Cavewoman',
                    'Elf' => 'Elf',
                    'Hea' => 'Healer',
                    'Kni' => 'Knight',
                    'Mon' => 'Monk',
                    'Pri' => 'Priestess',
                    'Rog' => 'Rogue',
                    'Ran' => 'Ranger',
                    'Sam' => 'Samurai',
                    'Tou' => 'Tourist',
                    'Val' => 'Valkyrie',
                    'Wiz' => 'Wizard'
                    );
    
    if (!defined($LOGFILE)) {
        $LOGFILE = "./logfile";
    }
}
