#### KSEARCH CONFIGURATION FILE #####################################
#####################################################################
## NOTE: If you change one of the options that's marked 're-index' ##
## you need to run 'indexer.pl' again. If you change one of the    ##
## options that's marked 'edit-help-template' you may need to      ##
## edit the 'help.html' file and your Template file to             ##
## exclude/include options for accuracy.                           ##
#####################################################################
###REQUIRED CONFIGURATION############################################

# Where you want the indexer to start (full path; end with /)
$INDEXER_START = '/home/groups/a/ab/abora/htdocs/'; # re-index

# The base url of your site being indexed
# Be sure it corresponds to the $INDEXER_START directory (end with /)
$BASE_URL = 'http://www.abora.org/';

# The url where ksearch.cgi is located
$SEARCH_URL = "http://www.abora.org/cgi-bin/ksearch/ksearch.cgi";

# The full-path of the ksearch directory (end with /)
$KSEARCH_DIR = '/home/groups/a/ab/abora/cgi-bin/ksearch/'; # re-index

#####################################################################
###OPTIONAL INDEXER CONFIGURATION####################################
#####################################################################
# If you are going to run the indexer (indexer.cgi) from the web,
# you must set @VALID_REFERERS, $INDEXER_URL and $PASSWORD.
#
# Pages from the refering domains below can only run the indexer
@VALID_REFERERS = ("http://www.intelliware.ca");

$INDEXER_URL = "http://www.abora.org/cgi-bin/ksearch/indexer.cgi";

$PASSWORD = "blahblah";		# required for indexer.cgi
#####################################################################

# How many words should be used for the description (may be shorter for meta descriptions)
$DESCRIPTION_LENGTH = 20; # re-index

# Set this to the term number (first term is 0) you want to start your description at
# This allows you to skip common headers in the body and show meaningful content
# This does not change meta descriptions
$DESCRIPTION_START = 0;	# re-index

# Which extensions should be indexed
# options "html, "htm", "shtml", "txt" ...any extensions representing text files
@FILE_EXTENSIONS = ("html", "htm", "shtml"); # re-index

# Set this to 0 if you do not have or do not want to use any DBM module. 
# RECOMMENDED to set to 0 if you do not have the DB_File module.
$USE_DBM = 0; # re-index

# Set this to 0 if you do not want to save the content of each file in the database
# If set to 1, this option increases the search speed 5-20x or more at the cost of disk space
# The disk space needed is usually about half the size of the actual file (depends on HTML and script content)
# HIGHLY RECOMMENDED to set to 1 (option will be depreciated in next versions)
$SAVE_CONTENT = 1; # re-index

# If you want to find common terms and add them to the STOP TERMS file
# set this value to the maximum percentage of files that searchable terms can exist in or set it to 0
# For example: if set to 90, terms that exist in more than 90 percent of all files will be added to the STOP TERMS file
$IGNORE_COMMON_TERMS = 0; # re-index

# Set this to 1 if you want to create a log file of the indexing routine (saved as log.txt)
# This logs information about each file indexed and the indexer configuration
$MAKE_LOG = 0;

#####################################################################
###OPTIONAL PDF INDEXING CONFIGURATION###############################
#####################################################################
##You must have Xpdf installed from http://www.foolabs.com/xpdf/#####
##There is a security risk if you use this option since it will #####
##execute a shell command (the pdftotext executable). See the   #####
##faqs for details. Note: phrase searching may be less accurate #####
##due to the output format of pdftotext.                        #####
#####################################################################

# Set this to the full path of the pdftotext executable from Xpdf
# if you want to index PDF files. You do not need to add .pdf to @FILE_EXTENSIONS above
$PDF_TO_TEXT = '';  # re-index

# Set this to 0 if you do not want to add 'PDF file size' info to the results titles
# if the file is a PDF file (file size info is redundent but is easily readable)
$PDF_INFO = 1;

#####################################################################
###OPTIONAL SEARCH CONFIGURATION#####################################

# How many results should be shown per page as default
# Preferably 5, 10, 25, 50, or 100 since these options are given in the search form
$RESULTS_PER_PAGE = 25;

# The minimum length of terms to search.
$MIN_TERM_LENGTH = 3;

# If you want the option to display matches in context in the descriptions
# set this to the number of matches per term/phrase you want to display
# (If you want it as a default setting just add the hidden form value
# in your initial search form):
#
# <INPUT type=hidden name="showm" value="your SHOW_MATCHES value">
#
$SHOW_MATCHES = 5;

# Set this to the number of characters per line you want to
# display in the description (a line per match; for formating purposes)
$SHOW_MATCHES_LENGTH = 75;

# To log search information from users, set this to the full path of your log file
# This option logs the IP, HOST, search query, and results
# Be sure to choose a unique name for the log file
# example: $LOG_SEARCH = '/www/kscripts/ksearch/search_log.txt';
$LOG_SEARCH = '';

# Set this to 0 if you do not want to allow phrase searches.
$DO_PHRASES = 1; # edit-help-template

# Set this to 0 if you do not want to allow case sensitive searches.
$CASE_SENSITIVE = 1; # edit-help-template

# Set this to 0 if you do not want to allow searching within results
$SEARCH_RESULTS = 1; # edit-help-template

# Set this to 0 if you do not want to allow searching with no restrictions
# (i.e. allow stop-terms and ignore minimum term length limit)
$ALL = 1; # edit-help-template

# Set this to 0 if you do not want to allow searching META descriptions
$META_DESCRIPTION = 1;	# re-index if changing from 0; edit-help-template

# Set this to 0 if you do not want to allow searching META keywords
$META_KEYWORD = 1;	# re-index if changing from 0; # edit-help-template

# Set this to 0 if you do not want to allow searching META authors
$META_AUTHOR = 1;	# re-index if changing from 0; # edit-help-template

# Set this to 0 if you do not want to allow searching alternative texts such as those used for images
$ALT_TEXT = 1;	# re-index if changing from 0; # edit-help-template

# Set this to 0 if you do not want to allow searching all links in documents
$LINKS = 1;	# re-index if changing from 0; # edit-help-template

# Set this to 0 if you do not want to allow searching the url of all documents
$URL = 1; # edit-help-template

# Set this to either "Matches" "Scores" "Dates" or "Sizes" (match case)
# to sort results, respectively (default). These options are given in the search form
$SORT_BY = "Matches";

# Set this to 0 if you do not want to allow users to weight each individual term/phrase.
# Allowable weights are <2-10000>. This setting could effect the score.
# Example query: '<1000>test perl' gives 'test' 1000 times more weight on the score compared to 'perl'.
$USER_WEIGHTS = 1; # edit-help-template

# Set this to how many times more important it is to find terms/phrases in titles
# This setting effects the score
$TITLE_WEIGHT = 1;		# a value 1 or above

# Set this to how many times more important it is to find terms/phrases in meta descriptions
# This setting effects the score
$META_DESCRIPTION_WEIGHT = 1;	# a value 1 or above

# Set this to how many times more important it is to find terms/phrases in meta keywords
# This setting effects the score
$META_KEYWORD_WEIGHT = 1;	# a value 1 or above

# Set this to 0 if you do not want to bold and highlight query terms/phrases in titles and descriptions
# Otherwise set it to the HTML color you want the terms to be highlighted
$BOLD_TERMS_BG_COLOR = "yellow"; #"#dddddd";

# Set this to the HTML color you want the current results in the "navbar" links to be highlighted
# You can always set this to the default background color of your site to avoid highlighting
$BOLD_RESULTS_BG_COLOR = "#dddddd";

# You can add your own title for the search form here (HTML okay) or leave it blank with '';
# example $SEARCH_TITLE = '<b>Search the Perl Documentation</b>';
$SEARCH_TITLE = '<b>Search the Abora website</b>';

# You can add your own title for the results page. (HTML okay) or leave it blank with '';
# example $RESULTS_TITLE = '<b>Perl Documentation Search Results</b>';
$RESULTS_TITLE = '<b><a href="http://www.abora.org"/>Abora</a> website search results</b>';

# You can change the form input name below to avoid editing existing search forms
$FORM_INPUT_NAME = 'terms';	# for form input example <INPUT type="text" name="terms" value="">

# You can change the next and previous links on the resuls page to images that match your site design
# example: <img src="your_next_image.gif" alt="Next" border="0">
$NEXT = 'Next&nbsp;>>';
$PREVIOUS = '<<&nbsp;Previous';

# Set this to 0 if you do not want to change special characters
# to English equivalents.
$TRANSLATE_CHARACTERS = 1;	# re-index if changing from 0; # edit-help-template

#### END OF CONFIGURATION SETTINGS ###############################################################
#### You do not have to edit below unless you want to ############################################
$DATABASE_DIR		 	= $KSEARCH_DIR.'database/';

$DATABASEFILE = $DATABASE_DIR.'database.txt';

$F_FILE_DB_FILE		 	= $DATABASE_DIR.'files';
$F_SIZE_DB_FILE		 	= $DATABASE_DIR.'files_size';
$F_DATE_DB_FILE		 	= $DATABASE_DIR.'files_date';
$F_TERMCOUNT_DB_FILE	 	= $DATABASE_DIR.'files_termcount';
$DESCRIPTIONS_DB_FILE	 	= $DATABASE_DIR.'descriptions';
$TITLES_DB_FILE		 	= $DATABASE_DIR.'titles';
$FILENAMES_DB_FILE		= $DATABASE_DIR.'filenames';
$TERMS_DB_FILE		 	= $DATABASE_DIR.'terms';

$CONTENTS_DB_FILE		= $DATABASE_DIR.'contents';
$ALT_TEXT_DB_FILE		= $DATABASE_DIR.'alt_text';
$LINKS_DB_FILE			= $DATABASE_DIR.'links';
$META_DESCRIPTION_DB_FILE	= $DATABASE_DIR.'meta_description';
$META_KEYWORD_DB_FILE		= $DATABASE_DIR.'meta_keyword';
$META_AUTHOR_DB_FILE		= $DATABASE_DIR.'meta_author';

$CONFIGURATION_DIR = $KSEARCH_DIR.'configuration/';
$IGNORE_FILES_FILE = $CONFIGURATION_DIR.'ignore_files.txt';
$IGNORE_TERMS_FILE = $CONFIGURATION_DIR.'stop_terms.txt';
$HELP_FILE = $KSEARCH_DIR.'help.html';
$LOG_FILE = $KSEARCH_DIR.'log.txt';
$TEMPLATE_DIR = $KSEARCH_DIR.'templates/';
$KSEARCH_TEMPLATE = $TEMPLATE_DIR.'search.html';
$FORM_LINK = '<a href="#form" alt="To Search Form" title="To Search Form" onclick="document.search.'.$FORM_INPUT_NAME.'.focus()">Form</a>';
$SPEED_TIP_TIME = 5;	# time required to get a tip to increase search speed

$VERSION = "1.4";

1;
