#!/usr/bin/perl

# KSearch v1.4
# Copyright (C) 2000 David Kim (kscripts.com)
#
# Parts of this script are Copyright
# www.perlfect.com (C)2000 G.Zervas. All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

my $t0 = time();
use Fcntl;
use locale;

###### You may have to add the full path to your configuration file below######
###############################################################################
my $configuration_file = 'configuration/configuration.pl'; #CONFIGURATION PATH#

require $configuration_file;

my $dbm_package;
if ($USE_DBM) {
	package AnyDBM_File;
	@ISA = qw(DB_File GDBM_File SDBM_File ODBM_File NDBM_File) unless @ISA;
	my $dbminfo;
	for (@ISA) {
  		if (eval "require $_") {
			$dbminfo .= "\n\nUsing DBM Database: $_...\n\n";
  			if ($_ =~ /[SON]DBM_File/) {
				# $USE_DMB = 0;
  				$dbminfo .= "Warning: $_ has block size limits.\n";
				$dbminfo .= "If your site exeeds the limit you will receive error message:\n";
				$dbminfo .= "[ dbm store returned -1, errno 28, key \"trap\" at - line 3. ]\n";
				$dbminfo .= "It is highly recommended to use a flat file database by setting \$USE_DBM to 0 in configuration.pl.\n";
				$dmbinfo .= "See the README file for details.\n\n";
  			}
			print $dbminfo;
			if ($_ =~ /[SON]DBM_File/) {
				print "\nINDEXING WILL CONTINUE IN 15 SECONDS\n";
				sleep 15;
			}
			$dbm_package = $_;
			last;
  		}
	}
	package main;
}

cleanup(); # delete existing db files

if ($MAKE_LOG) {
	my $indexmetadesc = $META_DESCRIPTION ? "yes" : "no";
	my $indexmetakeywords = $META_KEYWORD ? "yes" : "no";
	my $indexmetaauthor = $META_AUTHOR ? "yes" : "no";
	my $indexalttext = $ALT_TEXT ? "yes" : "no";
	my $indexlinks = $LINKS ? "yes" : "no";
	my $indexpdf = $PDF_TO_TEXT ? "yes" : "no";
	my $removecommonterms = $IGNORE_COMMON_TERMS ? "yes [cutoff = $IGNORE_COMMON_TERMS percent]" : "no";
	my $indexcontent = $SAVE_CONTENT ? "yes" : "no (warning: search may be very slow for large sites)";
	open(LOG,">".$LOG_FILE) or (warn "Cannot open log file $LOG_FILE: $!");
	print LOG localtime()."\nConfiguration File: $KSEARCH_DIR$configuration_file\n";
	print LOG $dbminfo;
	print LOG "\nINDEXER SETTINGS:\n";
	print LOG "Minimum term length: $MIN_TERM_LENGTH\n";
	print LOG "Description length: $DESCRIPTION_LENGTH\n";
	print LOG "Index meta descriptions: $indexmetadesc\n";
	print LOG "Index meta keywords: $indexmetakeywords\n";
	print LOG "Index meta authors: $indexmetaauthor\n";
	print LOG "Index alternative text: $indexalttext\n";
	print LOG "Index links: $indexlinks\n";
	print LOG "Index PDF files: $indexpdf\n";
	print LOG "Save file contents to database: $indexcontent\n";
	print LOG "Add Common terms to STOP TERMS file: $removecommonterms\n";
	print LOG "Index files with extensions: ".(join " ", @FILE_EXTENSIONS)."\n";
}

my ($allterms, $filesizetotal, $file_count);
my @ignore_files;
my %terms; 			#key = terms; value = number of files the term is found in;

my %f_file_db;			#file path
my %f_date_db;			#file modification date
my %f_size_db;			#file size
my %f_termcount_db;		#number of non-space characters in each file
my %descriptions_db; 		#file description
my %titles_db; 			#file title
my %filenames_db;		#file name
my %contents_db;		#file contents

my %alt_text_db;		#alt text
my %meta_description_db;	#meta descriptions
my %meta_keywords_db;		#meta keywords
my %meta_author_db;		#meta authors
my %links_db;			#links

if ($USE_DBM) {
	tie %f_file_db, $dbm_package, $F_FILE_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $F_FILE_DB_FILE: $!";
	tie %f_date_db, $dbm_package, $F_DATE_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $F_DATE_DB_FILE: $!";
	tie %f_size_db, $dbm_package, $F_SIZE_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $F_SIZE_DB_FILE: $!";
	tie %f_termcount_db, $dbm_package, $F_TERMCOUNT_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $F_TERMCOUNT_DB_FILE: $!";
	tie %descriptions_db, $dbm_package, $DESCRIPTIONS_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $DESCRIPTIONS_DB_FILE: $!";
	tie %titles_db, $dbm_package, $TITLES_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $TITLES_DB_FILE: $!";
	tie %filenames_db, $dbm_package, $FILENAMES_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $FILENAMES_DB_FILE: $!";
	if ($SAVE_CONTENT) {
		tie %contents_db, $dbm_package, $CONTENTS_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $CONTENTS_DB_FILE: $!";
	}
	if ($ALT_TEXT) {
		tie %alt_text_db, $dbm_package, $ALT_TEXT_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $ALT_TEXT_DB_FILE: $!";
	}
	if ($META_DESCRIPTION) {
		tie %meta_description_db, $dbm_package, $META_DESCRIPTION_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $META_DESCRIPTION_DB_FILE: $!";
	}
	if ($META_KEYWORD) {
		tie %meta_keyword_db, $dbm_package, $META_KEYWORD_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $META_KEYWORD_DB_FILE: $!";
	}
	if ($META_AUTHOR) {
		tie %meta_author_db, $dbm_package, $META_AUTHOR_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $META_AUTHOR_DB_FILE: $!";
	}
	if ($LINKS) {
		tie %links_db, $dbm_package, $LINKS_DB_FILE, O_CREAT|O_RDWR, 0755 or die "Cannot open $LINKS_DB_FILE: $!";
	}
}

push @FILE_EXTENSIONS, 'pdf' if $PDF_TO_TEXT; # if the option to index PDF files is chosen

print "\nLoading files to ignore:\n";
print LOG "\nLoading files to ignore:\n" if $MAKE_LOG;

ignore_files();

print "\n\nUsing stop words file: $IGNORE_TERMS_FILE\n";
print LOG "\n\nUsing stop words file: $IGNORE_TERMS_FILE\n" if $MAKE_LOG;

my $stopwords_regex = ignore_terms();

print "\nStarting indexer at $INDEXER_START\n\n";
print LOG "\nStarting indexer at $INDEXER_START\n\n" if $MAKE_LOG;

if (!$USE_DBM) {
	open(FILEDB, ">$DATABASEFILE") || die "Cannot open database file: $!\n";
}

indexer($INDEXER_START);

close(FILEDB) if (!$USE_DBM);

# remove COMMON TERMS previously appended to STOP TERMS file
clean_stop_terms();

# append COMMON TERMS to STOP TERMS file if configured to do so
append_common_terms() if $IGNORE_COMMON_TERMS;

print "\n\nFinished: Indexed ".$file_count.' files ('.$filesizetotal.'KB) with '.$allterms." total terms.\n";
print LOG "\n\nFinished: Indexed ".$file_count.' files ('.$filesizetotal.'KB) with '.$allterms." total terms.\n" if $MAKE_LOG;

print "Saved information ".$logterms."in logfile:\n $LOG_FILE\n\n" if $MAKE_LOG;

my $timediff = time() - $t0;
my $seconds = $timediff % 60;
my $minutes = ($timediff - $seconds) / 60;
if ($minutes >= 1) { $minutes = ($minutes == 1 ? "$minutes minute" : "$minutes minutes"); } else { $minutes = ""; }
$seconds = ($seconds == 1 ? "$seconds second" : "$seconds seconds");
print "Total run time: $minutes $seconds\n";
print LOG "Total run time: $minutes $seconds\n" if $MAKE_LOG;
close (LOG) if $MAKE_LOG;


####sub routines###########################################################################

sub indexer {
  my $dir = $_[0];
  my ($file_ref, $file);
  chdir $dir or (warn "Cannot chdir $dir: $!\n");
  opendir(DIR, $dir) or (warn "Cannot open $dir: $!\n");
  my @dir_contents = readdir DIR;
  closedir(DIR);
  my @dirs  = grep {-d and not /^\.{1,2}$/} @dir_contents;
  my @files = grep {-f and /^.+\.(.+)$/ and grep {/^\Q$1\E$/} @FILE_EXTENSIONS} @dir_contents;
  FILE: foreach my $file_name (@files) {
    $file = $dir."/".$file_name;
    $file =~ s/\/\//\//og;
    foreach my $skip (@ignore_files) {
      next FILE if $file =~ m/^$skip$/;
    }
    index_file($file);
  }
  DIR: foreach my $dir_name (@dirs) {
    $file = $dir."/".$dir_name;
    $file =~ s/\/\//\//og;
    foreach my $skip (@ignore_files) {
      next DIR if $file =~ /^$skip$/;
    }
    indexer($file);
  }
}

sub index_file {
  my $file = $_[0];
  my ($contents, $f_termcount);
  my %totalterms;
  my %term_total;
  if($PDF_TO_TEXT && $file =~ m/\.pdf$/i) {	# if the file is a PDF file
    if( $file !~ m/^[\/\\\w.+-]*$/ || $file =~ m/\.\./ ) {
      print "\nIgnoring PDF file '$file': filename has illegal characters\n\n";
      print LOG "\nIgnoring PDF file '$file': filename has illegal characters\n\n" if $MAKE_LOG;
      return;
    }
    $contents = `$PDF_TO_TEXT "$file" -` or (print "\nCannot execute '$PDF_TO_TEXT $file -'\nIgnoring PDF file '$file'\n\n");
    unless ($contents) {
	    print LOG "\nCannot execute '$PDF_TO_TEXT $file -'\nIgnoring PDF file '$file'\n\n" if $MAKE_LOG;
    }
  } else {
    undef $/;
    open(FILE, $file) or (warn "Cannot open $file: $!");
    $contents = <FILE>;
    close(FILE);
    $/ = "\n";
  }

  if ($contents =~ /^\s*$/gs) { return; } # skip empty files

  ++$file_count; # file reference number
  $f_size_db{$file_count} = int((((stat($file))[7])/1024)+.5);	# get size of file in kb
  $filesizetotal += $f_size_db{$file_count};			# get total size of all files
  my $update = (stat($file))[9];	 			# get date of last file modification
  $f_date_db{$file_count} = int($update/8640);
  $update = get_date($update);

  print "Indexed $file \n Last Updated: $update \n File Size: $f_size_db{$file_count} KB\n";
  print LOG "Indexed $file \n Last Updated: $update \n File Size: $f_size_db{$file_count} KB\n" if $MAKE_LOG;

  $file =~ m/^$INDEXER_START(.*)$/;
  $file = $1;
  $f_file_db{$file_count} = $file;

  if ($file =~ /[\/\\]([^\/\\]+)$/) {
	  $filenames_db{$file_count} = $1;
  } else {
	  $filenames_db{$file_count} = $file;
  }

  # save content if configured to do so, remove html and scripts
  $contents = process_contents($contents, $file_count, $file);

   while ($contents =~ m/\b(\S+)\b/gs) {
    my $term = $1;
    $f_termcount_db{$file_count} += length $term;			# count all non-space characters in file
    $f_termcount++;
    if ($IGNORE_COMMON_TERMS) {						# count terms in file
	    next if $term =~ m/^$stopwords_regex$/io;			# skip stop words
	    if (length $term >= $MIN_TERM_LENGTH && !$term_total{$term}) {	# each term in file if valid
	      $term_total{$term} = undef;
	    }
    }
  }
  $allterms += $f_termcount;					# count all terms in all files
  if ($IGNORE_COMMON_TERMS) {
	  foreach (keys %term_total) {
	    $terms{$_}++;					# count files with each term
	  }
  }


##########################################################################################

 if (!$USE_DBM) {
 	# Save all hash data into flat files with | delimiter

	my $file_entry = $f_file_db{$file_count};			# file path
	my $filename_entry = $filenames_db{$file_count};		# file name
	my $date_entry = $f_date_db{$file_count};			#file modification date
	my $size_entry = $f_size_db{$file_count};			#file size
	my $termcount_entry = $f_termcount_db{$file_count};		#number of non-space characters in each file
	my $descriptions_entry = $descriptions_db{$file_count}; 	#file description
	my $titles_entry = $titles_db{$file_count}; 			#file title
	my $contents_entry = $contents_db{$file_count};			#file contents
	my $alt_text_entry = $alt_text_db{$file_count};			#alt text
	my $meta_desc_entry = $meta_description_db{$file_count};	#meta descriptions
	my $meta_key_entry = $meta_keywords_db{$file_count};		#meta keywords
	my $meta_auth_entry = $meta_author_db{$file_count};		#meta authors
	my $links_entry = $links_db{$file_count};			#links

	print FILEDB "$file_entry\t$filename_entry\t$date_entry\t$size_entry\t$termcount_entry\t$descriptions_entry\t$titles_entry\t$contents_entry\t$alt_text_entry\t$meta_desc_entry\t$meta_key_entry\t$meta_auth_entry\t$links_entry\n";

}

##########################################################################################

}

sub get_date {  # gets date of last modification
   my $updatetime = $_[0];
   my @month = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec');
   my ($mday,$mon,$yr) = (localtime($updatetime))[3,4,5];
   $yr += 1900;
   my $date = "$month[$mon] $mday, $yr";
   $date ||= "n/a";
   return $date;
}

sub process_contents {  # process contents
  my ($contents, $file_ref, $filename) = @_;
  if ($ALT_TEXT) {
	my $alt_text;
	while ($contents =~ m/\s+alt\s*=\s*[\"\'](.*?)[\"\'][> ]/gis) {
	        $alt_text .= "$1 ";
	}
	$alt_text =~ s/\s+/ /g;
	$alt_text_db{$file_ref} = $alt_text if $alt_text;
  }
  if ($LINKS) {
	my $links;
	while ($contents =~ m/<\s*a\s+href\s*=\s*[\"\'](.*?)[\"\'][> ]/gis) {
	        $links .= "$1 ";
	}
	$links =~ s/\s+/ /g;
	$links_db{$file_ref} = $links if $links;
  }
  if ($META_DESCRIPTION) {
  	if ($contents =~ m/<\s*META\s+name\s*=\s*[\"\']?description[\"\']?\s+content\s*=\s*[\"\']?(.*?)[\"\']?\s*>/is) {
		my $meta_descript = $1;
		$meta_descript =~ s/\s+/ /g;
		$meta_description_db{$file_ref} = $meta_descript;
	}
  }
  if ($META_KEYWORD) {
  	if ($contents =~ m/<\s*META\s+name\s*=\s*[\"\']?keywords[\"\']?\s+content\s*=\s*[\"\']?(.*?)[\"\']?\s*>/is) {
		my $meta_key = $1;
		$meta_key =~ s/\s+/ /g;
		$meta_keyword_db{$file_ref} = $meta_key;
	}
  }
  if ($META_AUTHOR) {
  	if ($contents =~ m/<\s*META\s+name\s*=\s*[\"\']?author[\"\']?\s+content\s*=\s*[\"\']?(.*?)[\"\']?\s*>/is) {
		my $meta_aut = $1;
		$meta_aut =~ s/\s+/ /g;
		$meta_author_db{$file_ref} = $meta_aut;
	}
  }
  $contents =~ s/(<\s*script[^>]*>.*?<\s*\/script\s*>)|(<\s*style[^>]*>.*?<\s*\/style\s*>)/ /gsi;	# remove scripts and styles

  record_description($file_ref, $filename, $contents);	# record titles and descriptions

  $contents =~ s/<\s*TITLE\s*>\s*(.*?)\s*<\s*\/TITLE\s*>//gsi;	# remove title
  $contents =~ s/<digit>|<code>|<\/code>//gsi;
  $contents =~ s/(<[^>]*>)|(&nbsp;)|(&#160;)/ /gs;		# remove html poorly
  $contents = translate_characters($contents);			# translate ISO Latin special characters to English approximations
  $contents =~ s/^\s+//gs;
  $contents =~ s/\s+$//gs;
  $contents =~ s/\s+/ /gs;

  if ($SAVE_CONTENT) {				# may use a lot of disk space (for hybrid data structure)
	$contents_db{$file_ref} = $contents;	# saves cleaned file content for faster searching
	if ($USE_DBM) {	# use DBM if no size limits
		print " Saved file contents to DBM database\n\n";
		print LOG " Saved file contents to DBM database\n\n" if $MAKE_LOG;
	} else {
		print " Saved file contents to Flat File database\n\n";
		print LOG " Saved file contents to Flat File database\n\n" if $MAKE_LOG;
	}
  } else {
	print "\n";
	print LOG "\n";
  }
  return lc $contents;
}

sub record_description {  # record descriptions and titles
  my ($file_ref, $file, $contents) = @_;
  my ($description, $title);
  my @temparray;
  if ($contents =~ m/<\s*BODY.*?>(.*)<\s*\/BODY\s*>/si) {
	$description = $1;
  } else {
	$description = $contents;
  }
  $description =~ s/<\s*TITLE\s*>\s*(.*?)\s*<\s*\/TITLE\s*>//gsi;	# remove title
  $description =~ s/<digit>|<code>|<\/code>//gsi;
  $description =~ s/(<[^>]*>)|(&nbsp;)|(&#160;)/ /gs;			# remove html poorly
  $description = translate_characters($description);			# translate ISO Latin special characters to English approximations
  $description =~ s/^\s+//gs;
  $description =~ s/\s+$//gs;
  $description =~ s/\s+/ /gs;

  @temparray = split " ", $description;
  my $start_desc = $DESCRIPTION_START;
  my $end_desc = $DESCRIPTION_START + $DESCRIPTION_LENGTH;
  $start_desc = ($end_desc > scalar@temparray ? 0 : $DESCRIPTION_START);
  $description = join " ", @temparray[$start_desc..$end_desc];
  $description = '...'.$description if $start_desc;
  $description =~ s/\s+$//;
  $descriptions_db{$file_ref} = $description.'...';

  if ($contents =~ m/<\s*TITLE\s*>\s*(.*?)\s*<\s*\/TITLE\s*>/is) {
	  $title = $1;
  }
  $file =~ s/^.*\/([^\/]+)$/$1/g;
  $title ||= $file;
  $title =~ s/(<[^>]*>)|(&nbsp;)|(&#160;)/ /gs;	# remove html poorly
  $title =~ s/\s+/ /gs;				# remove spaces
  $title = translate_characters($title);	# translate ISO Latin special characters to English approximations
  $titles_db{$file_ref} = $title;
  print " Title: $title\n Description: $description\n";
  print LOG " Title: $title\n Description: $description\n" if $MAKE_LOG;
}

sub ignore_files {
  my @list;
  if (-e $IGNORE_FILES_FILE) {
    open (FILE, $IGNORE_FILES_FILE) or (warn "Cannot open $IGNORE_FILES_FILE: $!\n");
    while (<FILE>) {
      chomp;
      $_ =~ s/\r//g;
      $_ =~ s/\#.*$//g;
      $_ =~ s/[\/\s]*$//;
      next if /^\s*$/;
      push @list, "$_\n";
      $_ = quotemeta;
      $_ =~ s/\\\*/\.\*/g;
      push @ignore_files, $_;
    }
    close (FILE);
    if (scalar@list > 0) { print @list; print LOG @list; } else { print "List is empty\n\n"; print LOG "List is empty\n\n"; }
  } else {
    print STDERR "Warning: Can't find $IGNORE_FILES_FILE.\n";
  }
}

sub ignore_terms {
  my @stopwords;
  my $stopwords_regex;
  open (FILE, $IGNORE_TERMS_FILE) or (warn "Cannot open $IGNORE_TERMS_FILE: $!");
  while (<FILE>) {
    chomp;
    last if /\#DO NOT EDIT/;
    $_ =~ s/\#.*$//g;
    $_ =~ s/\s//g;
    next if /^\s*$/;
    $_ =~ s/([^\w\s])/\\$1/g;
    push @stopwords, $_;
  }
  close(FILE);
  $stopwords_regex = '(' . join('|', @stopwords) . ')';
  return $stopwords_regex;
}

sub cleanup {
  print "Deleting existing db files:\n";
    foreach (($CONTENTS_DB_FILE, $F_TERMCOUNT_DB_FILE, $F_FILE_DB_FILE, $F_DATE_DB_FILE, $F_SIZE_DB_FILE, $DESCRIPTIONS_DB_FILE, $TITLES_DB_FILE, $ALT_TEXT_DB_FILE, $META_DESCRIPTION_DB_FILE, $META_KEYWORD_DB_FILE, $META_AUTHOR_DB_FILE, $LINKS_DB_FILE, $FILENAMES_DB_FILE))
{
    if (-e $_.'.pag') {
      print "\t $_\n";
      unlink $_.'.pag' or (warn "Cannot unlink $_: $!");
    }
    if (-e $_) {
      print "\t $_\n";
      unlink $_ or (warn "Cannot unlink $_: $!");
    }
  }
    foreach (($CONTENTS_DB_FILE, $F_TERMCOUNT_DB_FILE, $F_FILE_DB_FILE, $F_DATE_DB_FILE, $F_SIZE_DB_FILE, $DESCRIPTIONS_DB_FILE, $TITLES_DB_FILE, $ALT_TEXT_DB_FILE, $META_DESCRIPTION_DB_FILE, $META_KEYWORD_DB_FILE, $META_AUTHOR_DB_FILE, $LINKS_DB_FILE, $FILENAMES_DB_FILE))
{
    if (-e $_.'.dir') {
      print "\t $_\n";
      unlink $_.'.dir' or (warn "Cannot unlink $_: $!");
    }
  }
}

sub append_common_terms { # appends common terms to STOP TERMS file
	my (@common_terms, @stop_terms, @stop_terms_copy);
	while (($term,$files) = each %terms) {
		if ($files > ($IGNORE_COMMON_TERMS/100 * $file_count)) {
			push @common_terms, $term;
		}
	}
	if (@common_terms) {
		open(STOPTERMS,'>>'.$IGNORE_TERMS_FILE) || die "Cannot open $IGNORE_TERMS_FILE: $!";
		print STOPTERMS "\n#DO NOT EDIT: Terms present in over $IGNORE_COMMON_TERMS percent of all files\n";
		foreach $term (@common_terms) {
			print "$term\n";
			print LOG "$term\n" if $MAKE_LOG;
			print STOPTERMS "$term\n";
		}
		print "\nThe above terms were present in over $IGNORE_COMMON_TERMS percent of all files and were added to your STOP TERMS file:\n $IGNORE_TERMS_FILE";
		print LOG "\nThe above terms were added to your STOP TERMS file:\n $IGNORE_TERMS_FILE" if $MAKE_LOG;
		close (STOPTERMS);
	} else {
		print "\nNo common terms were present in over $IGNORE_COMMON_TERMS percent of all files";
		print LOG "\nNo common terms were present in over $IGNORE_COMMON_TERMS percent of all files" if $MAKE_LOG;
	}
}

sub clean_stop_terms {
	my (@stop_terms, @stop_terms_copy);
	open(STOPTERMS,$IGNORE_TERMS_FILE) || die "Cannot open $IGNORE_TERMS_FILE: $!";
	@stop_terms = <STOPTERMS>;
        close (STOPTERMS);
        foreach (@stop_terms) {
		last if /#DO NOT EDIT/;
		next if /^\s*$/;
		push @stop_terms_copy, $_;
	}
	open(STOPTERMS,'>'.$IGNORE_TERMS_FILE) || die "Cannot open $IGNORE_TERMS_FILE: $!";
        print STOPTERMS @stop_terms_copy;
	close(STOPTERMS);
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
