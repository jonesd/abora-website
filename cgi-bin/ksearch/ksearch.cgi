#!/usr/bin/perl

# KSearch v1.4
# Copyright (C) 2000 David Kim (kscripts.com)

# Parts of this script are Copyright
# www.perlfect.com (C)2000 G.Zervas. All rights reserved

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

use Benchmark;	# time search
my $t0 = new Benchmark;
use locale;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use Fcntl;

{
  $0 =~ /(.*)\//;
  push @INC, $1 if $1;
}

###### You may have to add the full path to your configuration file below######
###############################################################################
require 'configuration/configuration.pl';	           #CONFIGURATION PATH#

my $usehash = 1;
my $dbm_package;

# To use the -T switch uncomment the next 2 lines and comment the following 11 line section
# Note: You must have the DB_File perl module to run taint mode
# and add ./ in front of the  CONFIGURATION PATH below.

#use DB_File;
#$dbm_package = 'DB_File';
if ($USE_DBM) {
	package AnyDBM_File;
	@ISA = qw(DB_File GDBM_File SDBM_File ODBM_File NDBM_File) unless @ISA;
	for (@ISA) {
  		if (eval "require $_") {
        	if ($_ =~ /[SON]DBM_File/) {
        	        $usehash = 0;
			}
			$dbm_package = $_;
			last;
		}
	}
	package main;
}

my %f_file_db;			# file path
my %f_date_db;			# file modification date
my %f_size_db;			# file size
my %f_termcount_db;		# number of non-space characters for score
my %descriptions_db;		# file description
my %filenames_db;		# file names
my %titles_db;			# file title
my %contents_db;		# file contents

my %alt_text_db;		# alt text
my %meta_description_db;	# meta descriptions
my %meta_keyword_db;		# meta keywords
my %meta_author_db;		# meta authors
my %links_db;			# links

if ($USE_DBM) {
	tie %f_file_db, $dbm_package, $F_FILE_DB_FILE, O_RDONLY, 0755 or die "Cannot open $F_FILE_DB_FILE: $!";
	tie %f_date_db, $dbm_package, $F_DATE_DB_FILE, O_RDONLY, 0755 or die "Cannot open $F_DATE_DB_FILE: $!";
	tie %f_size_db, $dbm_package, $F_SIZE_DB_FILE, O_RDONLY, 0755 or die "Cannot open $F_SIZE_DB_FILE: $!";
	tie %f_termcount_db, $dbm_package, $F_TERMCOUNT_DB_FILE, O_RDONLY, 0755 or die "Cannot open $F_TERMCOUNT_DB_FILE: $!";
	tie %descriptions_db, $dbm_package, $DESCRIPTIONS_DB_FILE, O_RDONLY, 0755 or die "Cannot open $DESCRIPTIONS_DB_FILE: $!";
	tie %titles_db, $dbm_package, $TITLES_DB_FILE, O_RDONLY, 0755 or die "Cannot open $TITLES_DB_FILE: $!";
	tie %filenames_db, $dbm_package, $FILENAMES_DB_FILE, O_RDONLY, 0755 or die "Cannot open $FILENAMES_DB_FILE: $!";
	if ($usehash) {	# get contents from DBM if no key/value size limits
	        tie %contents_db, $dbm_package, $CONTENTS_DB_FILE, O_RDONLY, 0755 or die "Cannot open $CONTENTS_DB_FILE: $!";
	}
	if ($ALT_TEXT) {
		tie %alt_text_db, $dbm_package, $ALT_TEXT_DB_FILE, O_RDONLY, 0755 or die "Cannot open $ALT_TEXT_DB_FILE: $!";
	}
	if ($META_DESCRIPTION) {
		tie %meta_description_db, $dbm_package, $META_DESCRIPTION_DB_FILE, O_RDONLY, 0755 or die "Cannot open $META_DESCRIPTION_DB_FILE: $!";
	}
	if ($META_KEYWORD) {
		tie %meta_keyword_db, $dbm_package, $META_KEYWORD_DB_FILE, O_RDONLY, 0755 or die "Cannot open $META_KEYWORD_DB_FILE: $!";
	}
	if ($META_AUTHOR) {
		tie %meta_author_db, $dbm_package, $META_AUTHOR_DB_FILE, O_RDONLY, 0755 or die "Cannot open $META_AUTHOR_DB_FILE: $!";
	}
	if ($LINKS) {
	        tie %links_db, $dbm_package, $LINKS_DB_FILE, O_RDONLY, 0755 or die "Cannot open $LINKS_DB_FILE: $!";
	}
}

my $query = new CGI;
my $html;				# returned HTML page
my $query_terms_copy;			# query
my $bare_query_terms;			# original query
my @terms;				# terms/phrases
my @checked_terms;			# processed terms/phrases
my %stopwords;				# keys are stopterms in query
my $stopwords_regex = ignore_terms();	# stopwords regular expression

my $subsearch;				# true if search within results
my $search_within_results;		# for subsearch loop
my $previous_query;			# previous queries
my $previous_queries;			# previous queries for subsearch to add to links in results page
my @previous_queries;			# previous queries for subsearch for loop
my %previous_results;			# previous results for subsearch loop

my $whole_word;				# true if search for whole words
my $all;				# true if search includes stop terms;
my $case_sensitive;			# true if case sensitive
my $search_body;			# true if search body
my $search_title;			# true if search titles
my $search_meta_description;		# true if search meta descriptions
my $search_meta_keyword; 		# true if search meta keywords
my $search_meta_author; 		# true if search meta authors
my $search_alt_text;			# true if search alt text
my $search_links;			# true if search links
my $search_url;				# true if search url

my $add_plus;			# if true, add + to all non +/- terms/phrases
my @plusf;			# +boolean terms/phrases for search
my @minusf;			# -boolean terms/phrases for search
my @otherf;			# other terms/phrases for search
my @none;			# +boolean terms/phrases without results
my @final_files;		# final files
my %minus;			# keys are files with -boolean term/phrase
my %clean_body;

my $delimitererror;
my $score;		# Score header
my $weight_tip;		# note to user about weights
my $totalmatches;	# total match count
my $totalsize;		# total size of all files with matches
my @sortedanswers;	# final list of sorted answers
my %matches;		# total matches for each file
my %score_numerator;	# characters that match x weights applied
my %score_denominator;	# total characters
my %finalscores;	# final score for each file

# set sorting choice, results per page
$SORT_BY = $query->param('sort') if ($query->param('sort') eq "Scores" || $query->param('sort') eq "Dates" || $query->param('sort') eq "Matches" || $query->param('sort') eq "Sizes" || $query->param('sort') eq "Titles" || $query->param('sort') eq "File Names");
$RESULTS_PER_PAGE = $query->param('display') if ($query->param('display') >= 5 && $query->param('display') <= 100);

$show_matches = $query->param('showm');

# to search within previous results
if ($SEARCH_RESULTS && $query->param('pq') !~ /^\s*$/ && $query->param($FORM_INPUT_NAME) !~ /^\s*$/ && $query->param('help') != 1) {
	$previous_queries = $query->param('pq').'  ';
	@previous_queries = split "  ", CGI::unescape($query->param('pq'));
}
print $query->header;
start_search();

##Subroutines############
sub start_search {
	my $query_terms;	# initialize variables
	$score = 'Score:';
	$totalmatches = ""; $totalsize = ""; $weight_tip = "";
	@checked_terms = (); @plusf = (); @minusf = (); @otherf = (); @none = (); @final_files = ();
	%stopwords = (); %minus = (); %matches = (); %score_numerator = (); %score_denominator = (); %finalscores = ();
	$query_terms_copy = ""; $add_plus = ""; $all = ""; $whole_word = ""; $case_sensitive = ""; $search_title = "";
	$search_meta_description = ""; $search_meta_keyword = ""; $search_meta_author = "";
	$search_alt_text = ""; $search_body = ""; $search_links = ""; $search_url = "";

	#if (@previous_queries && scalar@previous_queries < 7) { # to prevent looping too much
	if (@previous_queries) { # search results of previous queries
		$query_terms = shift @previous_queries;
		$subsearch = 1;
	} else { # search current query
		$query_terms = $query->param($FORM_INPUT_NAME);
  		$query_terms =~ s/(&nbsp;)|(&#160;)/ /gs;     		# remove spaces
		$query_terms = translate_characters($query_terms);	# ISO Latin approximations
		$bare_query_terms = $query_terms;			# original query
		$query_terms = 'all:'.$query_terms if $query->param('all') == 1;
		$query_terms = 'c:'.$query_terms if ($query->param('c') eq "s" && $CASE_SENSITIVE);
		$query_terms = 'w:'.$query_terms if $query->param('w') == 1;
		$query_terms = 'st:'.$query_terms if ($query->param('st') == 1 && $ALL);
		unless ($query->param('default') == 1) { # search content options
			$query_terms = 'b:'.$query_terms if $query->param('b') == 1;
			$query_terms = 't:'.$query_terms if ($query->param('t') == 1);
			$query_terms = 'd:'.$query_terms if ($query->param('d') == 1 && $META_DESCRIPTION);
			$query_terms = 'k:'.$query_terms if ($query->param('k') == 1 && $META_KEYWORD);
			$query_terms = 'au:'.$query_terms if ($query->param('au') == 1 && $META_AUTHOR);
			$query_terms = 'alt:'.$query_terms if ($query->param('alt') == 1 && $ALT_TEXT);
			$query_terms = 'l:'.$query_terms if ($query->param('l') == 1 && $LINKS);
			$query_terms = 'u:'.$query_terms if ($query->param('u') == 1 && $URL);
		}
		$query_terms =~ s/^\s+//;
		$query_terms =~ s/\s+$//;
		$query_terms =~ s/\s+/ /g;
		$previous_query = $query_terms; # query with options for previous query option
		$subsearch = "";
	}
	while ($query_terms =~ s/^(c|[0-9]+|score|date|match|size|title|name|b|t|d|k|au|alt|st|w|l|u|all)\://io) {
		my $option = $1; # let user add options directly in query text field
		$query_terms =~ s/^\s+//;
		if ($option =~ /^c$/i && $CASE_SENSITIVE) { $case_sensitive = 1; next; }
		if ($option =~ /^score$/i) { $SORT_BY = "Scores"; next; }
		if ($option =~ /^date$/i) { $SORT_BY = "Dates"; next; }
		if ($option =~ /^match$/i) { $SORT_BY = "Matches"; next; }
		if ($option =~ /^size$/i) { $SORT_BY = "Sizes"; next; }
		if ($option =~ /^title$/i) { $SORT_BY = "Titles"; next; }
		if ($option =~ /^name$/i) { $SORT_BY = "File Names"; next; }
		if ($option =~ /^b$/i) { $search_body = 1; next; }
		if ($option =~ /^t$/i) { $search_title = 1; next; }
		if ($option =~ /^d$/i && $META_DESCRIPTION) { $search_meta_description = 1; next; }
		if ($option =~ /^k$/i && $META_KEYWORD) { $search_meta_keyword = 1; next; }
		if ($option =~ /^au$/i && $META_AUTHOR) { $search_meta_author = 1; next; }
		if ($option =~ /^alt$/i && $ALT_TEXT) { $search_alt_text = 1; next; }
		if ($option =~ /^u$/i && $URL) { $search_url = 1; next; }
		if ($option =~ /^l$/i && $LINKS) { $search_links = 1; next; }
		if ($option =~ /^st$/i && $ALL) { $all = 1; next; }
		if ($option =~ /^w$/i) { $whole_word = 1; next; }
		if ($option =~ /^all$/i) { $add_plus = 1; next; }
		if ($option =~ /^([0-9]+)$/) {
			if ($option < 5) { $RESULTS_PER_PAGE = 5; }
			elsif ($option > 100) { $RESULTS_PER_PAGE = 100; }
			else { $RESULTS_PER_PAGE = $option; }
		}
	}
	returnresults() if ($query->param('help') == 1 || $query_terms =~ /^\s*$/); # return page if no query or for help
	if (!$search_title && !$search_meta_description && !$search_meta_keyword && !$search_meta_author && !$search_alt_text && !$search_body && !$search_links && !$search_url) {
		$show_matches = $SHOW_MATCHES; $search_body = 1; $search_title = 1; $search_meta_description = 1; # search body, title, and meta description as default
	}
	my @phrases;
	if ($DO_PHRASES) { # get phrases
  		while ($query_terms =~ s/(\+&lt;[0-9]+&gt;)\"([^\"]*)\"/ /) {
                        my $phrase = get_phrase($1,$2);
			push @phrases, $phrase if $phrase;
		}
		while ($query_terms =~ s/(&lt;[0-9]+&gt;)\"([^\"]*)\"/ /) {
                        my $phrase = get_phrase($1,$2);
			push @phrases, $phrase if $phrase;
		}
		while ($query_terms =~ s/(\+?)\"([^\"]*)\"/ /) {
                        my $phrase = get_phrase($1,$2);
			push @phrases, $phrase if $phrase;
		}
	}
	$query_terms =~ s/^\s+//;
	$query_terms =~ s/\s+$//;
	@terms = split /\s+/, $query_terms; 	# get terms
	push @terms, @phrases if $DO_PHRASES;	# append phrases to terms array
	process_terms();
	search_files() if (@otherf || @plusf || @minusf);
	process_booleans();
	get_sorted_answers();
}

sub get_phrase {
	my ($boolean, $phrase) = @_;
	$phrase =~ s/^\s+//;
	$phrase =~ s/\s+$//;
	return $boolean.$phrase if $phrase;
}

sub process_terms {	# get terms and phrases and start search routine
	my %terms;
	foreach my $term (@terms) {
		my $cp = $term;
		my $cp_c;
		$cp =~ s/^\+// if $cp ne '+'; # remove + boolean
		if ($cp !~ /^&lt;[0-9]+&gt;$/ && $cp =~ m/^&lt;([0-9]+)&gt;/) {
			if ($1 >= 2 && $1 <= 10000 && $USER_WEIGHTS) {
				$cp =~ s/^&lt;[0-9]+&gt;//; 	# remove user defined weights
			} elsif ($cp =~ / / && $USER_WEIGHTS) {
				$weight_tip = "<br>Note: Scoring weights must be in the range of &lt;2-10000&gt;";
				$cp =~ s/^&lt;[0-9]+&gt;//; # remove user defined weights
			}
			$cp_c = $cp;
			$cp = lc $cp if !$case_sensitive;
			next if exists $terms{$cp}; # skip repeats
			$terms{$cp} = undef;
		} else {
			$cp_c = $cp;
			$cp = lc $cp if !$case_sensitive;
			next if exists $terms{$cp}; # skip repeats
			$terms{$cp} = undef;
			$cp =~ s/^\-// if $cp ne '-'; # remove - boolean
		}
		unless ($all || $cp =~ /^\S+\*$/) { # ignore stop terms
			if (length $cp < $MIN_TERM_LENGTH || $cp =~ m/^$stopwords_regex$/io || $cp =~ m/^(&lt;|&gt;)$/) {
				$query_terms_copy .= "$cp_c ";
				$cp_c =~ s/^\-// if $cp_c ne '-'; # remove - boolean
				$stopwords{$cp_c} = undef;
				next;
			}
		}
		if ($term ne '+' && $term =~ s/^\+//) {
			@$term = ();
			push @plusf, $term;
			push @checked_terms, $cp_c;
			$query_terms_copy .= ($cp_c =~ / / ? "+\"$cp_c\" " : "+$cp_c ");
		} elsif ($term ne '-' && $term =~ s/^\-//) {
			push @minusf, $term;
			$query_terms_copy .= ($term =~ / / ? "-\"$term\" " : "-$term ");
		} else {
			if ($add_plus) {
				@$term = ();
				push @plusf, $term;
				push @checked_terms, $cp_c;
				$query_terms_copy .= ($cp_c =~ / / ? "+\"$cp_c\" " : "+$cp_c ");
			} else {
				push @otherf, $term;
				push @checked_terms, $cp_c;
				$query_terms_copy .= ($cp_c =~ / / ? "\"$cp_c\" " : "$cp_c ");
			}
		}
	}
}

sub search_files {
	if ($USE_DBM) {
		while (($file, $file_path) = each(%f_file_db)) {
			search_contents($file, $file_path);
		}
	} else {
		my $file_count = 0;
		open (FILEDB, $DATABASEFILE) || die "Can't open database file.\n";
		foreach (<FILEDB>) {
			$file_count++;
			($f_file_db{$file_count}, $filenames_db{$file_count}, $f_date_db{$file_count},$f_size_db{$file_count},$f_termcount_db{$file_count},$descriptions_db{$file_count},$titles_db{$file_count},$contents_db{$file_count},$alt_text_db{$file_count},$meta_description_db{$file_count},$meta_keywords_db{$file_count},$meta_author_db{$file_count},$links_db{$file_count}) = split /\t/, $_;
			my $filepath = $f_file_db{$file_count};
			search_contents($file_count, $filepath);
		}
		close(FILEDB);
	}
}


sub search_contents {
		my $file = $_[0];
		my $file_path = $_[1];
		my $body;
		if ($search_body) {
			$score_denominator{$file} += $f_termcount_db{$file};	# add character count of body
			if ($SAVE_CONTENT) {	# search pre-processed files in database (faster but uses disk space)
				if ($usehash) {	# get contents from DBM if no size limits
					$body = $contents_db{$file};
				} else {	# otherwise get contents from separate files
					open (FILE,$DATABASE_DIR.$file) || die "Cannot open $DATABASE_DIR$file: $!";
					$body = <FILE>;
					close (FILE);
				}
			} else {	# search html file directly (slower but saves disk space)
				open (FILE,$INDEXER_START.$file_path) || die "Cannot open $INDEXER_START$file_path: $!";
				my @LINES = <FILE>;
		        	close (FILE);
		        	$body = join ' ', @LINES;
				# must clean contents and search larger file (slow part)
		        	$body =~ s/(<script[^>]*>.*?<\/script>)|(<style[^>]*>.*?<\/style>)/ /gsi;
				$body =~ s/<digit>|<code>|<\/code>//gsi;
		                $body =~ s/(<[^>]*>)|(&nbsp;)|(&#160;)/ /gs;     # remove html poorly
        		        $body = translate_characters($body);      # ISO Latin approximations
                		$body =~ s/\s+/ /gs;
                		$clean_body{$file} = $body if $show_matches;
			}
		}
		# add character counts for score
		if ($search_title) {
			my $title = $titles_db{$file};
			$title =~ s/\s+//gs;
			$score_denominator{$file} += length $title;
		}
		if ($search_meta_description) {
			my $meta_descript = $meta_description_db{$file};
			$meta_descript =~ s/\s+//gs;
			$score_denominator{$file} += length $meta_descript;
		}
		if ($search_meta_keyword) {
                        my $meta_key = $meta_keyword_db{$file};
                        $meta_key =~ s/\s+//gs;
			$score_denominator{$file} += length $meta_key;
		}
		if ($search_meta_author) {
                        my $meta_aut = $meta_author_db{$file};
                        $meta_aut =~ s/\s+//gs;
			$score_denominator{$file} += length $meta_aut;
		}
		if ($search_alt_text) {
                        my $alt = $alt_text_db{$file};
                        $alt =~ s/\s+//gs;
			$score_denominator{$file} += length $alt;
		}
		if ($search_links) {
                        my $links = $links_db{$file};
                        $links =~ s/\s+//gs;
			$score_denominator{$file} += length $links;
		}
		if ($search_url) {
			my $urltmp = $BASE_URL.$f_file_db{$file};
			$urltmp =~ s/\s+//gs;
			$score_denominator{$file} += length $urltmp;
		}
		foreach my $term (@plusf) {	# find +boolean terms/phrases
			my ($weight, $matches, $added);
			my $term_cp = $term;
                	if ($term_cp =~ m/^&lt;([0-9]+)&gt;/ && $term_cp !~ /^&lt;[0-9]+&gt;$/) {
	                	if ($1 >= 2 && $1 <= 10000 && $USER_WEIGHTS) {
		                        $term_cp =~ s/^&lt;([0-9]+)&gt;//;	# remove user defined weights
					$weight = $1;
					$SORT_BY = "Scores"; 		# Sort by scores if using weights
					$score = 'Weighted Score:';
                        	} elsif ($term_cp =~ / / && $USER_WEIGHTS) {
	                                $term_cp =~ s/^&lt;[0-9]+&gt;//; # remove user defined weights
	                        }
			}
			$weight ||= 1;
			my $termcp = $term_cp;
			if ($search_body) {
				$matches = find_matches($body, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_title) {
				$matches = find_matches($titles_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $TITLE_WEIGHT * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_meta_description) {
				$matches = find_matches($meta_description_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $META_DESCRIPTION_WEIGHT * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_meta_keyword) {
				$matches = find_matches($meta_keyword_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $META_KEYWORD_WEIGHT * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_meta_author) {
				$matches = find_matches($meta_author_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_alt_text) {
				$matches = find_matches($alt_text_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_links) {
				$matches = find_matches($links_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
			if ($search_url) {
				$matches = find_matches($BASE_URL.$f_file_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$term_cp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $term_cp) * $weight;
					$$term{$file} = undef unless exists $$term{$file};
                        	}
			}
		}
		foreach my $term (@minusf) {	# skip files with -boolean terms/phrases
			if ($search_body) {
				if (find_matches($body, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_title) {
				if (find_matches($titles_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_meta_description) {
				if (find_matches($meta_description_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_meta_keyword) {
				if (find_matches($meta_keyword_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_meta_author) {
				if (find_matches($meta_author_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_alt_text) {
				if (find_matches($alt_text_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_links) {
				if (find_matches($links_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
			if ($search_url) {
				if (find_matches($BASE_URL.$f_file_db{$file}, $term, 'minus')) {
					$minus{$file} = undef;
					return;
				}
			}
		}
		foreach my $term (@otherf) {	# find other terms/phrases
                        my ($weight, $matches);
			my $term_cp = $term;
			if ($term_cp =~ m/&lt;([0-9]+)&gt;/ && $term_cp !~ /^&lt;[0-9]+&gt;$/) {
				if ($1 >= 2 && $1 <= 10000 && $USER_WEIGHTS) {
					$term_cp =~ s/^&lt;([0-9]+)&gt;//;      # remove user defined weights
					$weight = $1;
					$SORT_BY = "Scores";	 		# Sort by scores if using weights
					$score = 'Weighted Score:';
	                        } elsif ($term_cp =~ / / && $USER_WEIGHTS) {
        	                        $term_cp =~ s/^&lt;[0-9]+&gt;//; # remove user defined weights
                	        }
			}
                        $weight ||= 1;
			my $termcp = $term_cp;
			if ($search_body) {
				$matches = find_matches($body, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
                        	}
			}
			if ($search_title) {
				$matches = find_matches($titles_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $TITLE_WEIGHT * $weight;
                        	}
			}
			if ($search_meta_description) {
				$matches = find_matches($meta_description_db{$file}, $term_cp);
				if ($matches) {
	                        	$matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $META_DESCRIPTION_WEIGHT * $weight;
                        	}
			}
			if ($search_meta_keyword) {
				$matches = find_matches($meta_keyword_db{$file}, $term_cp);
				if ($matches) {
	        	                $matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $META_KEYWORD_WEIGHT * $weight;
        	                }
			}
			if ($search_meta_author) {
				$matches = find_matches($meta_author_db{$file}, $term_cp);
				if ($matches) {
	        	                $matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
        	                }
			}
			if ($search_alt_text) {
				$matches = find_matches($alt_text_db{$file}, $term_cp);
				if ($matches) {
		                        $matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
        	                }
			}
			if ($search_links) {
				$matches = find_matches($links_db{$file}, $term_cp);
				if ($matches) {
		                        $matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
        	                }
			}
			if ($search_url) {
				$matches = find_matches($BASE_URL.$f_file_db{$file}, $term_cp);
				if ($matches) {
                 		        $matches{$file} += $matches;
					$termcp =~ s/\s+//g;   # if it is a phrase
					$score_numerator{$file} += $matches * (length $termcp) * $weight;
                		}
			}
		}
}

sub process_booleans {
	my $noplus;
	foreach my $term (@plusf) { # first check if matches exist for each + term
		 if (!%$term) {
			$noplus = 1;
                        my $term_cp = $term;
                        if ($term_cp =~ m/^&lt;([0-9]+)&gt;/ && $term_cp !~ /^&lt;[0-9]+&gt;$/) {
                                if ($1 >= 2 && $1 <= 10000 && $USER_WEIGHTS) {
                                        $term_cp =~ s/^&lt;([0-9]+)&gt;//;      # remove user defined weights
                                } elsif ($term_cp =~ / / && $USER_WEIGHTS) {
                                        $term_cp =~ s/^&lt;[0-9]+&gt;//;	# remove user defined weights
                                }
                        }
			# if there no files with +boolean term
			if ($term_cp =~ / /) {	# if it is a phrase
				push @none, '"'.$term_cp.'"';
			} else {		# if it is a term
				push @none, $term_cp;
			}
		}
	}
	if (!$noplus) {	# if all + terms have matches find intersection
		my ($i, $si ) = ( 0, scalar keys %{ $plusf[0] });
		my ($j, $sj );
		for ( $j= 1; $j < @plusf; $j++ ) { # find smallest hash first
			$sj = scalar keys %{ $plusf[ $j ] };
			( $i, $si ) = ( $j, $sj ) if $sj < $si;
		}
		my ( $hashvalue, %intersection );
		NEXTHASH: # Check each hash against remaining ones
		foreach $hashvalue ( keys %{ splice @plusf, $i, 1 } ) {
			foreach ( @plusf ) {
				next NEXTHASH unless exists $$_{ $hashvalue };
			}
			$intersection{ $hashvalue } = undef;
		}
		@final_files = ( keys %intersection );
	}
}

sub get_sorted_answers {
	if (@none || (!@final_files && (@plusf))) {	# if there are no results
        	returnresults();
	}
	@final_files = keys %matches if !@final_files;		# get files with matches
	foreach my $answer (@final_files) {		# get final answers
	        unless (exists $minus{$answer}) {	# remove files with -boolean terms/phrases
			if ($search_within_results) {	# search within previous results if option is chosen
				unless (exists $previous_results{$answer}) { next; }
			}
			if ($score_denominator{$answer} != 0) {
				$finalscores{$answer} = sprintf("%.2f", 100*($score_numerator{$answer}/$score_denominator{$answer}));
			} else {
				$finalscores{$answer} = "n/a";
			}
			$totalmatches += $matches{$answer};
			$totalsize += $f_size_db{$answer};
		}
	}
	if ($subsearch) {	# loop through results of each previous query to search within results
		$search_within_results = 1;
		%previous_results = %finalscores;
		start_search();
		return;
	}
  	if ($SORT_BY eq "Matches") {  # sort answers
        	  @sortedanswers = sort {$matches{$b} <=> $matches{$a}
                                           ||
                        $finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $f_date_db{$b} <=> $f_date_db{$a}
                                           ||
                        $f_size_db{$b} <=> $f_size_db{$a}
                        		   ||
 			lc($titles_db{$a}) cmp lc($titles_db{$b})
                        		   ||
 			lc($filenames_db{$a}) cmp lc($filenames_db{$b}) } keys %finalscores;
  	} elsif ($SORT_BY eq "Scores") {
        	  @sortedanswers = sort {$finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $matches{$b} <=> $matches{$a}
                                           ||
                        $f_date_db{$b} <=> $f_date_db{$a}
                                           ||
                        $f_size_db{$b} <=> $f_size_db{$a}
                        		   ||
 			lc($titles_db{$a}) cmp lc($titles_db{$b})
 					   ||
 			lc($filenames_db{$a}) cmp lc($filenames_db{$b}) } keys %finalscores;
  	} elsif ($SORT_BY eq "Dates") {
  	        @sortedanswers = sort {$f_date_db{$b} <=> $f_date_db{$a}
                                           ||
                        $matches{$b} <=> $matches{$a}
                                           ||
                        $finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $f_size_db{$b} <=> $f_size_db{$a}
                        		   ||
 			lc($titles_db{$a}) cmp lc($titles_db{$b})
                        		   ||
 			lc($filenames_db{$a}) cmp lc($filenames_db{$b}) } keys %finalscores;
  	} elsif ($SORT_BY eq "Sizes") {
        	  @sortedanswers = sort {$f_size_db{$b} <=> $f_size_db{$a}
                                           ||
                        $matches{$b} <=> $matches{$a}
                                           ||
                        $finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $f_date_db{$b} <=> $f_date_db{$a}
                        		   ||
 			lc($titles_db{$a}) cmp lc($titles_db{$b})
                         		   ||
 			lc($filenames_db{$a}) cmp lc($filenames_db{$b}) } keys %finalscores;
  	} elsif ($SORT_BY eq "Titles") {
        	  @sortedanswers = sort {lc($titles_db{$a}) cmp lc($titles_db{$b})
                        		   ||
 			lc($filenames_db{$a}) cmp lc($filenames_db{$b})
                                           ||
                        $matches{$b} <=> $matches{$a}
                                           ||
                        $finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $f_date_db{$b} <=> $f_date_db{$a}
                        		   ||
 			$f_size_db{$b} <=> $f_size_db{$a} } keys %finalscores;
  	} else {
        	  @sortedanswers = sort {lc($filenames_db{$a}) cmp lc($filenames_db{$b})
                        		   ||
 			lc($titles_db{$a}) cmp lc($titles_db{$b})
                                           ||
                        $matches{$b} <=> $matches{$a}
                                           ||
                        $finalscores{$b} <=> $finalscores{$a}
                                           ||
                        $f_date_db{$b} <=> $f_date_db{$a}
                        		   ||
 			$f_size_db{$b} <=> $f_size_db{$a} } keys %finalscores;
  	}
	returnresults();
}

sub returnresults {	# creates HTML page from template file
	my %h;
	my ($options, $sortby, $casesearch, $commonterms, $subsearch_string, $subsearch_info);
	my $rank = 0;
	$query_terms_copy =~ s/\s$//;
	my $bare_query = $query_terms_copy;
	my $query_str = CGI::escape($bare_query_terms);
	my $previous_query_str = CGI::escape($previous_query);
	$bare_query_terms =~ s/\"/\&quot\;/g;
	$h{query_str} = $bare_query_terms;
	$h{version} = $VERSION;
	$h{search_url} = $SEARCH_URL;
	$h{input_name} = $FORM_INPUT_NAME;
	$html = get_template($KSEARCH_TEMPLATE);
	my $results = @sortedanswers;
	my $currentpage = $query->param('p');
	$currentpage ||= 1;
	if ($SEARCH_RESULTS && $query->param('pq') !~ /^\s*$/) {
		$subsearch_string = '&pq='.CGI::escape($query->param('pq'));
		$subsearch_info = ' from previous results';
	}
	my ($search_sources, $search_options);
	#### Search form options format ####
	if ($add_plus) {
		$options .= '&all=1';
		$h{add_plus} = '<INPUT type=checkbox name="all" value=1 checked>+';
	} else {
		$h{add_plus} = '<INPUT type=checkbox name="all" value=1>+';
	}
	$h{default} = '<INPUT type=checkbox name="default" value=1>Default';
	if ($case_sensitive) {
		$options .= '&c=s';
		$casesearch = 'case sensitive';
		$h{c} = '<INPUT type=checkbox name="c" value="s" checked>Case Sensitive';
	} else {
		$casesearch = "";
		$h{c} = '<INPUT type=checkbox name="c" value="s">Case Sensitive' if $CASE_SENSITIVE;
	}
        if ($show_matches && $SHOW_MATCHES) {
                $options .= "\&showm=$show_matches";
                $h{show_matches} = '<INPUT type=checkbox name="showm" value="'.$show_matches.'" checked>Show Matches in Descriptions';
        } elsif ($SHOW_MATCHES) {
                $h{show_matches} = '<INPUT type=checkbox name="showm" value="'.$SHOW_MATCHES.'">Show Matches in Descriptions';
        } else {
		$h{show_matches} = "";
	}
	if ($whole_word) {
		$options .= '&w=1';
		$h{w} = '<INPUT type=checkbox name="w" value="1" checked>Whole Words Only';
	} else {
		$h{w} = '<INPUT type=checkbox name="w" value="1">Whole Words Only';
	}
	if ($all) {
		$options .= '&st=1';
		$h{st} = '<INPUT type=checkbox name="st" value="1" checked>Include Stop-Terms';
	} else {
		$h{st} = '<INPUT type=checkbox name="st" value="1">Include Stop-Terms' if $ALL;
	}
	if ($search_body) {
		$search_sources .= " Body,";
		$options .= '&b=1';
		$h{b} = '<INPUT type=checkbox name="b" value="1" checked>Body';
	} else {
		$h{b} = '<INPUT type=checkbox name="b" value="1">Body';
	}
	if ($search_title) {
		$search_sources .= " Title,";
		$options .= '&t=1';
		$h{t} = '<INPUT type=checkbox name="t" value="1" checked>Title';
	} else {
		$h{t} = '<INPUT type=checkbox name="t" value="1">Title';
	}
	if ($search_meta_description) {
		$search_sources .= " Meta-Description,";
		$options .= '&d=1';
		$h{d} = '<INPUT type=checkbox name="d" value="1" checked>Meta-Description';
	} else {
		$h{d} = '<INPUT type=checkbox name="d" value="1">Meta-Description' if $META_DESCRIPTION;
	}
	if ($search_meta_keyword) {
		$search_sources .= " Meta-Keywords,";
		$options .= '&k=1';
		$h{k} = '<INPUT type=checkbox name="k" value="1" checked>Meta-Keywords';
	} else {
		$h{k} = '<INPUT type=checkbox name="k" value="1">Meta-Keywords' if $META_KEYWORD;
	}
	if ($search_meta_author) {
		$search_sources .= " Meta-Authors,";
		$options .= '&au=1';
		$h{au} = '<INPUT type=checkbox name="au" value="1" checked>Meta-Authors';
	} else {
		$h{au} = '<INPUT type=checkbox name="au" value="1">Meta-Authors' if $META_AUTHOR;
	}
	if ($search_alt_text) {
		$search_sources .= " Alt-Text,";
		$options .= '&alt=1';
		$h{alt} = '<INPUT type=checkbox name="alt" value="1" checked>Alt-Text';
	} else {
		$h{alt} = '<INPUT type=checkbox name="alt" value="1">Alt-Text' if $ALT_TEXT;
	}
	if ($search_links) {
		$options .= '&l=1';
		$search_sources .= " Links,";
		$h{l} = '<INPUT type=checkbox name="l" value="1" checked>Links';
	} else {
		$h{l} = '<INPUT type=checkbox name="l" value="1">Links' if $LINKS;
	}
	if ($search_url) {
		$search_sources .= " Url,";
		$options .= '&u=1';
		$h{u} = '<INPUT type=checkbox name="u" value="1" checked>Url';
	} else {
		$h{u} = '<INPUT type=checkbox name="u" value="1">Url' if $URL;
	}
	$search_sources =~ s/,$//;
	if ($SORT_BY eq "Matches") {
		$h{sort} = '<OPTION SELECTED>Matches<OPTION>Scores<OPTION>Dates<OPTION>Sizes<OPTION>Titles<OPTION>File Names';
	} elsif ($SORT_BY eq "Scores") {
		$h{sort} = '<OPTION>Matches<OPTION SELECTED>Scores<OPTION>Dates<OPTION>Sizes<OPTION>Titles<OPTION>File Names';
	} elsif ($SORT_BY eq "Dates") {
		$h{sort} = '<OPTION>Matches<OPTION>Scores<OPTION SELECTED>Dates<OPTION>Sizes<OPTION>Titles<OPTION>File Names';
	} elsif ($SORT_BY eq "Sizes") {
		$h{sort} = '<OPTION>Matches<OPTION>Scores<OPTION>Dates<OPTION SELECTED>Sizes<OPTION>Titles<OPTION>File Names';
	} elsif ($SORT_BY eq "Titles") {
		$h{sort} = '<OPTION>Matches<OPTION>Scores<OPTION>Dates<OPTION>Sizes<OPTION SELECTED>Titles<OPTION>File Names';
	} else {
		$h{sort} = '<OPTION>Matches<OPTION>Scores<OPTION>Dates<OPTION>Sizes<OPTION>Titles<OPTION SELECTED>File Names';
	}
	$sortby = '&sort='.$SORT_BY;
	if ($RESULTS_PER_PAGE == 5) {
		$h{display} = '<OPTION SELECTED>5<OPTION>10<OPTION>25<OPTION>50<OPTION>100';
	} elsif ($RESULTS_PER_PAGE == 10) {
		$h{display} = '<OPTION>5<OPTION SELECTED>10<OPTION>25<OPTION>50<OPTION>100';
	} elsif ($RESULTS_PER_PAGE == 25) {
		$h{display} = '<OPTION>5<OPTION>10<OPTION SELECTED>25<OPTION>50<OPTION>100';
	} elsif ($RESULTS_PER_PAGE == 50) {
		$h{display} = '<OPTION>5<OPTION>10<OPTION>25<OPTION SELECTED>50<OPTION>100';
	} elsif ($RESULTS_PER_PAGE == 100) {
		$h{display} = '<OPTION>5<OPTION>10<OPTION>25<OPTION>50<OPTION SELECTED>100';
	} else {
		$h{display} = '<OPTION SELECTED>'.$RESULTS_PER_PAGE.'<OPTION>5<OPTION>10<OPTION>25<OPTION>50<OPTION>100';
	}
	my $first = ($currentpage - 1) * $RESULTS_PER_PAGE;
	my $last  = $first + $RESULTS_PER_PAGE - 1;
	if ($last >= $results) {
		$last = $results - 1;
	}
	#################### Header Format Start ####################
	if (keys %stopwords) {
		my $s = (scalar keys %stopwords == 1 ? " was" : "s were");
		$commonterms = '<br>The following stop-term'.$s.' ignored: <b>'.(join " ", keys %stopwords).'</b>';
	}

	my $ww = ' whole words in' if $whole_word;
	$search_sources = "<br>Searched$ww: <b>".$search_sources.'</b>';
	if ($query->param('help') == 1) {
		$h{header} = '<b>General and Advanced Search Tips</b>';
		open(FILE,$HELP_FILE) || die "Cannot open $HELP_FILE: $!";
		my @help = <FILE>;
		close(FILE);
		my $help = join " ", @help;
		$h{help} = $help;
		$h{form_link} = $FORM_LINK;
	} elsif (!@terms) {
		$h{header} = 'Please enter search terms in the box below';
		$h{help} = $SEARCH_TITLE if $SEARCH_TITLE;
	} elsif (@none) {
		$h{header} = 'Your '.$casesearch.' search for <b>'.$bare_query.'</b> did not match any documents'.$subsearch_info;
		$h{subheader} = '<br>No pages were found containing: <B>'.(join " ", @none).'</B>'.$commonterms.$search_sources.$weight_tip;
		$h{help} = $SEARCH_TITLE if $SEARCH_TITLE;
	} elsif (!$results) {
		$h{header} = 'Your '.$casesearch.' search for <b>'.$bare_query.'</b> did not match any documents'.$subsearch_info;
		$h{subheader} = $commonterms.$search_sources.$weight_tip;
		$h{help} = $SEARCH_TITLE if $SEARCH_TITLE;
	} else {
		my $documents;
		if ($first == $last) {
			$documents = 'Result <b>'.($first+1).'</b>';
		} else {
			$documents = 'Results <b>'.($first+1).'-'.($last+1).'</b>';
		}
		$h{help} = $RESULTS_TITLE if $RESULTS_TITLE;
		my $s = ($totalmatches == 1 ? "" : "es");
		$h{header} = $documents.' of <b>'.$results.' ('.$totalsize.'KB)</b> for <b>'.$bare_query.'</b> with <b>'.$totalmatches.'</b> total '.$casesearch.' match'.$s.$subsearch_info;
		# $commonterms = $commonterms.' (see <a href="'.$SEARCH_URL.'?'.$FORM_INPUT_NAME.'='.$query_str.'&help=1&display='.$RESULTS_PER_PAGE.$sortby.$options.'" title="Search Tips" alt="Search Tips"><b>tips</b></a>)' if $commonterms;
		$h{subheader} = $commonterms.$search_sources.$weight_tip;
		$h{results} = $documents.' of <b>'.$results.'</b>';
		my $checked = ' checked' if $query->param('pq') !~ /^\s*$/;
		$h{subsearch} = '<INPUT type="checkbox" name="pq" value="'.$previous_queries.$previous_query_str.'"'.$checked.'>Search Within Results' if $SEARCH_RESULTS;
		$h{form_link} = $FORM_LINK;
	}

	#################### Header Format End ####################
	# Display Search Results (loop)
	foreach ((@sortedanswers)[$first..$last]) {
		my ($title, $desc);
		if ($show_matches) {
			$desc = &show_matches(\@checked_terms, $_);
		} else {
			$desc = (($meta_description_db{$_} && $search_meta_description) ? $meta_description_db{$_} : $descriptions_db{$_});
		}
		if ($SORT_BY eq "File Names") {
		   #$title = $filenames_db{$_}." - ".$titles_db{$_};
		   $title = $filenames_db{$_};
		} else {
		   $title = $titles_db{$_};
		}
		my ($scoreA, $scoreB, $scoreC, $scoreD);
		if ($SORT_BY eq "Matches") {
			$scoreA = '<b>Matches:</b> '.$matches{$_};
			$scoreB = "<b>$score</b> ".$finalscores{$_};
			$scoreC = '<b>Last Updated:</b> '.get_date($f_date_db{$_});
			$scoreD = '<b>File Size:</b> '.$f_size_db{$_}.'KB';
		} elsif ($SORT_BY eq "Scores") {
			$scoreA = "<b>$score</b> ".$finalscores{$_};
			$scoreB = '<b>Matches:</b> '.$matches{$_};
			$scoreC = '<b>Last Updated:</b> '.get_date($f_date_db{$_});
			$scoreD = '<b>File Size:</b> '.$f_size_db{$_}.'KB';
		} elsif ($SORT_BY eq "Dates")  {
			$scoreA = '<b>Last Updated:</b> '.get_date($f_date_db{$_});
			$scoreB = '<b>Matches:</b> '.$matches{$_};
			$scoreC = "<b>$score</b> ".$finalscores{$_};
			$scoreD = '<b>File Size:</b> '.$f_size_db{$_}.'KB';
		} else {
			$scoreA = '<b>Matches:</b> '.$matches{$_};
			$scoreB = '<b>File Size:</b> '.$f_size_db{$_}.'KB';
			$scoreC = "<b>$score</b> ".$finalscores{$_};
			$scoreD = '<b>Last Updated:</b> '.get_date($f_date_db{$_});
		}
		my $display_url = $BASE_URL.$f_file_db{$_};

		if ($BOLD_TERMS_BG_COLOR) { # bold terms in description and title
			foreach my $term (@checked_terms) {
				my $boldterm = $term;
				$boldterm =~ s/([^\w\s])/\\$1/g;
				$boldterm = add_wildcard($boldterm) if ($boldterm =~ /\S\\\* / || $boldterm =~ /\S\\\*$/);
				if ($whole_word) {
					if ($case_sensitive) {
						$desc =~ s/\b($boldterm)\b/\n\t$1\n \t/gs if ($search_meta_description || $search_body || $show_matches);
						$title =~ s/\b($boldterm)\b/\n\t$1\n \t/gs if $search_title;
						$display_url =~ s/\b($boldterm)\b/\n\t$1\n \t/gs if $search_url;
					} else {
						$desc =~ s/\b($boldterm)\b/\n\t$1\n \t/gis if ($search_meta_description || $search_body || $show_matches);
						$title =~ s/\b($boldterm)\b/\n\t$1\n \t/gis if $search_title;
						$display_url =~ s/\b($boldterm)\b/\n\t$1\n \t/gis if $search_url;
					}
				} else {
					if ($case_sensitive) {
						$desc =~ s/($boldterm)/\n\t$1\n \t/gs if ($search_meta_description || $search_body || $show_matches);
						$title =~ s/($boldterm)/\n\t$1\n \t/gs if $search_title;
						$display_url =~ s/($boldterm)/\n\t$1\n \t/gs if $search_url;
					} else {
						$desc =~ s/($boldterm)/\n\t$1\n \t/gis if ($search_meta_description || $search_body || $show_matches);
						$title =~ s/($boldterm)/\n\t$1\n \t/gis if $search_title;
						$display_url =~ s/($boldterm)/\n\t$1\n \t/gis if $search_url;
					}
				}
			}
			$desc =~ s/\n\t/<B style="background:$BOLD_TERMS_BG_COLOR">/gs;
			$title =~ s/\n\t/<B style="background:$BOLD_TERMS_BG_COLOR">/gs;
			$display_url =~ s/\n\t/<B style="background:$BOLD_TERMS_BG_COLOR">/gs;
			$desc =~ s/\n \t/<\/B>/gs;
			$desc =~ s/\n  \t/<BR>/gs;
			$title =~ s/\n \t/<\/B>/gs;
			$display_url =~ s/\n \t/<\/B>/gs;
		}

		# add info to titles of PDF files if configured to
		if ($PDF_TO_TEXT && $PDF_INFO && $f_file_db{$_} =~ m/\.pdf$/i) {
			$title = $title.' &nbsp; - &nbsp; <b><i>PDF '.$f_size_db{$_}.'KB</i></b>';
		}

		$desc = $desc.'<br>' if $desc !~ /^\s*$/;
		template_results([{rank => $first+(++$rank),
                                        url => $BASE_URL.$f_file_db{$_},
					display_url => $display_url,
                                        title => $title,
                                        scoreA => $scoreA,
                                        scoreB => $scoreB,
                                        scoreC => $scoreC,
                                        scoreD => $scoreD,
                                        description => $desc,
		}]);
	}
	$html =~ s/<!--\s*loop:\s*results\s*-->.*<!--\s*end:\s*results\s*-->//s;
	my $lastpage = ceil($results, $RESULTS_PER_PAGE);
	$lastpage ||= 1;
	if ($currentpage == 1) {
		$h{previous} = "";
		if ($lastpage > $currentpage) {
			$h{next} = " &nbsp; <A href=\"$SEARCH_URL?".$FORM_INPUT_NAME."=".$query_str."&display=".$RESULTS_PER_PAGE."&p=2".$subsearch_string.$options.$sortby."\" title=\"To page 2\" alt=\"To page 2\"> $NEXT</A>\n";
		} else {
			$h{next} = "";
		}
	} elsif ($currentpage == $lastpage) {
		$h{previous} = "<A href=\"$SEARCH_URL?".$FORM_INPUT_NAME."=".$query_str."&display=".$RESULTS_PER_PAGE."&p=".($lastpage-1).$subsearch_string.$options.$sortby."\" title=\"To page ".($lastpage-1)."\" alt=\"To page ".($lastpage-1)."\">$PREVIOUS </A> &nbsp;\n";
		$h{next} = "";
	} else {
		$h{previous} = "<A href=\"$SEARCH_URL?".$FORM_INPUT_NAME."=".$query_str."&display=".$RESULTS_PER_PAGE."&p=".($currentpage-1).$subsearch_string.$options.$sortby."\" title=\"To page ".($currentpage-1)."\" alt=\"To page ".($currentpage-1)."\">$PREVIOUS </A> &nbsp; \n";
		$h{next} = " &nbsp; <A href=\"$SEARCH_URL?".$FORM_INPUT_NAME."=".$query_str."&display=".$RESULTS_PER_PAGE."&p=".($currentpage+1).$subsearch_string.$options.$sortby."\" title=\"To page ".($currentpage+1)."\" alt=\"To page ".($currentpage+1)."\"> $NEXT</A>\n";
	}
	if ($lastpage == 1) {
		$h{navbar} = "";
	} else {
		for (1..$lastpage) {
			my $resultspage;
			my $first_result = ($_ * $RESULTS_PER_PAGE) - ($RESULTS_PER_PAGE - 1);
			my $last_result = $_ * $RESULTS_PER_PAGE;
			if ($last_result > $results && $_ == $lastpage) { $last_result = $results; }
			if ($first_result == $last_result) { $resultspage = $first_result; } else { $resultspage = "$first_result-$last_result"; }
			if ($_ != $currentpage) {
				$h{navbar} .= " <A href=\"$SEARCH_URL?".$FORM_INPUT_NAME."=".$query_str."&display=".$RESULTS_PER_PAGE."&p=".$_.$subsearch_string.$options.$sortby."\" title=\"Page ".$_."\" alt=\"Page ".$_."\">$resultspage</A> \n";
			} else {
				$h{navbar} .= " <B style=\"background:$BOLD_RESULTS_BG_COLOR\">$resultspage</B> \n";
			}
		}
	}
	if ($query->param('help') == 1) {	# add 'back' link to help page
		$h{tips} = '<a href="'.$SEARCH_URL.'?'.$FORM_INPUT_NAME.'='.$query_str.'&p='.$currentpage.'&display='.$RESULTS_PER_PAGE.$subsearch_string.$options.$sortby.'" title="Back to Previous Page" alt="Back to Previous Page"><b>Back</b></a>';
		$h{navbar} = ""; $h{next} = ""; $h{previous} = "";
		$currentpage = 1;
	} else {				# add 'tips' link to results page
		$h{tips} = '<a href="'.$SEARCH_URL.'?'.$FORM_INPUT_NAME.'='.$query_str.'&p='.$currentpage.'&help=1&display='.$RESULTS_PER_PAGE.$subsearch_string.$options.$sortby.'" title="Search Tips" alt="Search Tips" class="help"><b>Tips</b></a>';
	}
	if (timestr(timediff(new Benchmark, $t0)) =~ /\=\s*([0-9\.]+)\s*CPU/i && !@none && $results) { # only cpu time
#	if (timestr(timediff(new Benchmark, $t0)) =~ /^(.+)$/i && !@none && $results) { # wallclock, usr, and sys times
		$h{searchtime} = '<br>Required Time: <b>'.($1 == 1 ? "$1 second" : "$1 seconds")."</b>";
		if ($1 >= $SPEED_TIP_TIME) {$h{searchtime} .= '<br>Note: Use less common terms to speed up searches.'; }
	} else {
		$h{searchtime} = "";
	}

	$h{current_page} = $currentpage;
	$h{total_pages}  = $lastpage;
	$html =~ s/<!--\s*cgi:\s*(\S+?)\s*-->/$h{$1}/gis;
	print $html;	# finally print the HTML page

	# log search
	if ( $bare_query !~ /^\s*$/ && $LOG_SEARCH ) {
		open(FILE, ">>$LOG_SEARCH");
		print FILE localtime()."\n";
		print FILE "REMOTE IP: $ENV{'REMOTE_ADDR'}\n" if $ENV{'REMOTE_ADDR'};
		print FILE "REMOTE HOST: $ENV{'REMOTE_HOST'}\n" if $ENV{'REMOTE_HOST'};
		print FILE "QUERY: $bare_query\n";
		my $results_number = scalar@sortedanswers;
		$results_number ||= '0';
		print FILE "RESULTS: $results_number\n\n";
		close(FILE);
	}

	exit;		# end program
}

sub ceil {
	my $x = $_[0];
	my $y = $_[1];
	if ($x % $y == 0) {
		return $x / $y;
	} else {
		return int($x / $y + 1);
	}
}

sub find_matches {	# slow part
	my ($content, $term, $minus) = @_;
	my $matches;
	$term =~ s/([^\w\s])/\\$1/g; # escape special characters for regex
	if ($case_sensitive) {
		$term = add_wildcard($term) if ($term =~ /\S\\\* / || $term =~ /\S\\\*$/);
		if ($whole_word) {
			while ($content =~ m/\b$term\b/g) {
				$matches++;
				last if $minus eq 'minus';
			}
		} else {
			while ($content =~ m/$term/g) {
				$matches++;
				last if $minus eq 'minus';
			}
		}
	} else {
		$content = lc $content;	# faster than /regex/i for case insensitivity
		$term = lc $term;
		$term = add_wildcard($term) if ($term =~ /\S\\\* / || $term =~ /\S\\\*$/);
		if ($whole_word) {
			while ($content =~ m/\b$term\b/g) {
				$matches++;
				last if $minus eq 'minus';
			}
		} else {
			while ($content =~ m/$term/g) {
				$matches++;
				last if $minus eq 'minus';
			}
		}
	}
	return $matches;
}

sub add_wildcard {	# unescape * for wildcard
	my @termw = split ' ', $_[0];
	foreach (@termw) {
		$_ =~ s/^(\S+)\\\*$/$1\\S\*/g;
	}
	my $unescaped = join ' ', @termw;
	$unescaped = '\b'.$unescaped unless $whole_word;
	return $unescaped;
}

sub ignore_terms {
  my @stopwords;
  my $stopwords_regex;
  open (FILE, $IGNORE_TERMS_FILE) or (warn "Cannot open $IGNORE_TERMS_FILE: $!" and next);
  while (<FILE>) {
    chomp;
    $_ =~ s/#.*$//g;
    $_ =~ s/\s//g;
    next if /^\s*$/;
    $_ =~ s/([^\w\s])/\\$1/g;
    push @stopwords, $_;
  }
  close(FILE);
  $stopwords_regex = '(' . join('|', @stopwords) . ')';
  return $stopwords_regex;
}

sub get_date {  # gets date of last modification
   my $updatetime = $_[0]*8640;
   my @month = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec');
   my ($mday,$mon,$yr) = (localtime($updatetime))[3,4,5];
   $yr += 1900;
   my $date = "$month[$mon] $mday, $yr";
   $date ||= "n/a";
   return $date;
}

sub get_template {
   my $file = $_[0];
   my $template;
   open(FILE, $file) or die "Cannot open file $file: $!";
   while(<FILE>) {
       next if /^##USAGE##/;
       $template .= $_;
       last if /<\/html>/i;
   }
   close(FILE);
   return $template;
}

sub template_results {
   my $results_values = $_[0];
   $html =~ m/<!--\s*loop:\s*results\s*-->(.*)<!--\s*end:\s*results\s*-->/s;
   my $loop = $1;
   my $loop_copy = $loop;
   my $out;
   foreach (@{$results_values}) {
     $loop = $loop_copy;
     $loop =~ s/<!--\s*item:\s*(\S+?)\s*-->/$$_{$1}/gis;
     $out .= $loop;
   }
   $html =~ s/(<!--\s*loop:\s*results\s*-->).*(<!--\s*end:\s*results\s*-->)/$out$1$loop_copy$2/s;
}

sub show_matches {
	my @checked_terms = @{$_[0]};
	my ($desc, $line, $pre, $post, $match, $prem, $postm, $bdy);
	my @lines;
	$bdy .= ( $SAVE_CONTENT ? $contents_db{$_[1]} : $clean_body{$_[1]}) if $search_body;
	my $spaces = " " x $SHOW_MATCHES_LENGTH;
	if ($search_meta_description) {
		$bdy .= "$spaces$meta_description_db{$_[1]}";
	}
	if ($search_meta_keyword) {
		$bdy .= "$spaces$meta_keyword_db{$_[1]}";
	}
	if ($search_meta_author) {
		$bdy .= "$spaces$meta_author_db{$_[1]}";
	}
	if ($search_alt_text) {
		$bdy .= "$spaces$alt_text_db{$_[1]}";
	}
	if ($search_links) {
		$bdy .= "$spaces$links_db{$_[1]}";
	}
	foreach my $term (@checked_terms) {
		my $count;
		my $boldterm = $term;
                $boldterm =~ s/([^\w\s])/\\$1/g;
                $boldterm = &add_wildcard($boldterm) if ($boldterm =~ /\S\\\* / || $boldterm =~ /\S\\\*$/);
		if ($whole_word) {
			if ($case_sensitive) {
				while ($count < $show_matches && $bdy =~ /\b$boldterm\b/gs) {
					$count++; $pre = "$`"; $post = "$'"; $match = $&;
					my $LENGTH = int (($SHOW_MATCHES_LENGTH - length $match)/2);
					$pre =~ m/\b(.{0,$LENGTH})$/; $prem = $1; $pre = "$`";
					$post =~ m/^(.{0,$LENGTH})\b/; $postm = $1; $post = "$'", $bdy = "$pre $post";
					$line = join("", '...', $prem, $match, $postm, '...');
					push @lines, $line;
				}
			} else {
				while ($count < $show_matches && $bdy =~ /\b$boldterm\b/gis) {
					$count++; $pre = "$`"; $post = "$'"; $match = $&;
					my $LENGTH = int (($SHOW_MATCHES_LENGTH - length $match)/2);
					$pre =~ m/\b(.{0,$LENGTH})$/; $prem = $1;
					$post =~ m/^(.{0,$LENGTH})\b/; $postm = $1; $post = "$'", $bdy = "$pre $post";
					$line = join("", '...', $prem, $match, $postm, '...');
					push @lines, $line;
				}
			}
		} else {
			if ($case_sensitive) {
				while ($count < $show_matches && $bdy =~ /$boldterm/gs) {
					$count++; $pre = "$`"; $post = "$'"; $match = $&;
					my $LENGTH = int (($SHOW_MATCHES_LENGTH - length $match)/2);
					$pre =~ m/\b(.{0,$LENGTH})$/; $prem = $1;
					$post =~ m/^(.{0,$LENGTH})\b/; $postm = $1; $post = "$'", $bdy = "$pre $post";
					$line = join("", '...', $prem, $match, $postm, '...');
					push @lines, $line;
				}
			} else {
				while ($count < $show_matches && $bdy =~ /$boldterm/gis) {
					$count++; $pre = "$`"; $post = "$'"; $match = $&;
					my $LENGTH = int (($SHOW_MATCHES_LENGTH - length $match)/2);
					$pre =~ m/\b(.{0,$LENGTH})$/; $prem = $1;
					$post =~ m/^(.{0,$LENGTH})\b/; $postm = $1; $post = "$'", $bdy = "$pre $post";
					$line = join("", '...', $prem, $match, $postm, '...');
					push @lines, $line;
				}
			}
		}
	}
	return join("\n  \t", @lines);
}


sub translate_characters {
	# From http://www.utoronto.ca/webdocs/HTMLdocs/NewHTML/iso_table.html
	my $translated_term = $_[0];

	if (!$TRANSLATE_CHARACTERS) { return $translated_term; }

	$translated_term =~ s/&(.?)(acute|grave|circ|uml|tilde);/$1/gs;
	$translated_term =~ s/(&#247|&(nbsp|divide);)/ /og;
	$translated_term =~ s/(&#(192|193|194|195|196|197|224|225|226|227|228|229|230);|À|Á|Â|Ã|Ä|Å|à|á|â|ã|ä|æ|å|&(.ring|aelig);)/a/og;
	$translated_term =~ s/(&#223;|ß|&szlig;)/b/og;
	$translated_term =~ s/(&#(199|231);|Ç|ç|&.cedil;)/c/og;
	$translated_term =~ s/(&#(198|200|201|202|203|232|233|234|235);|Æ|È|É|Ê|Ë|è|é|ê|ë|&AElig;)/e/og;
	$translated_term =~ s/(&#(204|205|206|207|236|238|239);|Ì|Í|Î|Ï|ì|í|î|ï)/i/og;
	$translated_term =~ s/(&#(209|241);|ñ|Ñ)/n/og;
	$translated_term =~ s/(&#(216|210|211|212|213|214|240|242|243|244|245|246|248);|Ø|Ò|Ó|Ô|Õ|Ö|ð|ò|ó|ô|õ|ö|ø|&(.slash|eth);)/o/og;
	$translated_term =~ s/(&#(217|218|219|220|249|250|251|252);|Ù|Ú|Û|Ü|ù|ú|û|ü)/u/og;
	$translated_term =~ s/(&#(222|254);|Þ|þ|&thorn;)/p/og;
	$translated_term =~ s/(&#215;|×|&times;)/x/og;
	$translated_term =~ s/(&#(221|253);|Ý|ý)/y/og;

	$translated_term =~ s/(&#34|&quot);/"/og;
	$translated_term =~ s/&#35;/#/og;
	$translated_term =~ s/&#36;/\$/og;
	$translated_term =~ s/&#37;/\%/og;
	$translated_term =~ s/(&#38|&amp);/&/og;
        $translated_term =~ s/(<|&#60;)/&lt;/og;
        $translated_term =~ s/(>|&#62;)/&gt;/og;
	return $translated_term;
}
