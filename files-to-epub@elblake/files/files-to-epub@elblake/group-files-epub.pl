#!/usr/bin/perl

##
## Create EPUB from some images and text files.
##
## Author: Edward Blake
## License: MIT

use strict;
use warnings;
use utf8;

use IO::Uncompress::Unzip;
use IO::Compress::Zip qw(zip $ZipError :zip_method);
use Compress::Raw::Zlib;
use IPC::Open2;
use UUID qw(uuid);
use File::Basename qw(dirname basename);
use Encode qw(encode decode);

use Gtk3 -init;
use Glib ('TRUE','FALSE');
use Locale::gettext;
use URI::Escape;
use POSIX;
use UUID qw(uuid);
use Cwd qw(getcwd);

use constant {
    CONFIG_DIR => 'files-to-epub',
    UUID => 'files-to-epub@elblake'
};

setlocale(LC_MESSAGES, "");
textdomain(UUID);
bindtextdomain(UUID, $ENV{HOME}."/.local/share/locale");

sub _ {
    my ($str) = @_;
    my $str1 = dgettext(UUID, $str);
    if ($str1 eq '') {
        return $str;
    }
    return $str1;
}


my @extensions_txt = ();
my @extensions_markdown = ();
my @extensions_xhtml = ();
my %extensions_images = ();
my %extensions_fonts = ();

## Read mime.types file to get the mime types. text/plain, markdown, images
## and fonts mime types are placed in the different extension types by
## the keyword appearing somewhere in the mime type.
##
sub read_mime_types ($) {
    my ($filename) = @_;
    if (open my $h, '<', $filename) {
        while (<$h>) {
            chomp;
            s/^\s+|\s+$//g;
            next if /^#/;

            my @arr = split(/\s+/);
            next if @arr < 2;

            my $mime = $arr[0];
            if (lc($mime) eq 'text/plain') {
                for (my $i = 1; $i < @arr; ++$i) {
                    push @extensions_txt, '.' . $arr[$i];
                }
            }
            elsif (lc($mime) eq 'application/xhtml+xml') {
                for (my $i = 1; $i < @arr; ++$i) {
                    push @extensions_xhtml, '.' . $arr[$i];
                }
            }
            elsif ($mime =~ /markdown/i) {
                for (my $i = 1; $i < @arr; ++$i) {
                    push @extensions_markdown, '.' . $arr[$i];
                }
            }
            elsif ($mime =~ /image/i) {
                for (my $i = 1; $i < @arr; ++$i) {
                    $extensions_images{'.' . $arr[$i]} = $mime;
                }
            }
            elsif ($mime =~ /font/i) {
                for (my $i = 1; $i < @arr; ++$i) {
                    $extensions_fonts{'.' . $arr[$i]} = $mime;
                }
            }
        }
        close $h;
    }

}

read_mime_types(dirname(__FILE__) . '/mime.types');

##
## Generate EPUB
##

## Escape the important characters.
##
sub esc ($) {
    my ($l) = @_;
    
    $l =~ s/&/&amp;/g;
    $l =~ s/"/&quot;/g;
    $l =~ s/</&lt;/g;
    $l =~ s/>/&gt;/g;
    
    return $l;
}

sub html_w ($$$$) {
    my ($htmlattrs, $title, $stylelinks, $cont) = @_;
    my $html = '';

    $html .= "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    $html .= "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\"\n";
    $html .= " \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n";
    $html .= "<html xmlns=\"http://www.w3.org/1999/xhtml\"$htmlattrs>\n";
    $html .= "<head>\n";
    $html .= "<meta http-equiv=\"Content-Type\" content=\"application/xhtml+xml; charset=utf-8\"/>\n";
    $html .= "<title>" . esc($title) . "</title>\n";
    $html .= $stylelinks;
    $html .= "</head>\n";
    $html .= "<body>\n";
    $html .= "$cont\n";
    $html .= "</body>\n";
    $html .= "</html>\n";
    return $html;
}


sub html_css_file ($) {
    my ($epub_st) = @_;
    my $stylelinks = '';
    foreach my $css (@{$epub_st->{'css'}}) {
        my $mimetype = 'text/css';
        $stylelinks .= '<link rel="stylesheet" ' . 
            'href="' . esc($css) . '" ' . 
            'type="' . esc($mimetype) . '"/>'."\n";
    }
    return $stylelinks;
}

##
## Add tags as needed to an existing XHTML document.
##

sub add_tags ($$$$) {
    my ($htmlattrs, $title, $stylelinks, $cont) = @_;

    if (!($cont =~ m/<\?xml/)) {
        $cont = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" . $cont;
    }

    if (!($cont =~ m/<!doctype/i)) {
        my $doctype =
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\"\n".
            " \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n";
        $cont =~ s/(<html)/$doctype$1/si;
    }

    if ($cont =~ m/(.+<html)([^>]*)(>.+)/si) {
        my $h_1 = $1;
        my $inh = $2;
        my $h_2 = $3;
        my $changed = 0;
        if (!($inh =~ m/xmlns\s*=/i)) {
            $inh .= ' xmlns="http://www.w3.org/1999/xhtml"';
            $changed = 1;
        }
        if (!($inh =~ m/lang\s*=/i)) {
            $inh .= $htmlattrs;
            $changed = 1;
        }
        if ($changed) {
            $cont = $h_1 . $inh . $h_2;
        }
    }

    if (!($cont =~ m/<\/head/i)) {
        $cont =~ s/(<body)$/<head><\/head>$1/si;
    }
    if (!($cont =~ m/<title/i)) {
        my $title_1 = "<title>" . esc($title) . "</title>\n";
        $cont =~ s/(<\/head)/$title_1$1/si;
    }
    if (!($cont =~ m/http-equiv=\"Content-Type\"/i)) {
        my $metatag = "<meta http-equiv=\"Content-Type\" content=\"application/xhtml+xml; charset=utf-8\"/>\n";
        $cont =~ s/(<title)/$metatag$1/si;
    }
    if ((!($cont =~ m/<link/i)) && ($stylelinks ne '')) {
        $cont =~ s/(<\/head)/$stylelinks$1/si;
    }

    return $cont;
}

##
##

## Balance tags (and make them lowercase when needed).
##
sub balance_tags ($) {
    my ($cont) = @_;
    
    my @self_closing = qw(
        area base br col hr img link
        meta source track wbr);
    
    my $result = '';
    my @tags = ();
    my @arr = split /
        (  <\/?[\w-][^>]*>
        |  <!--.*?-->
        |  <!\[CDATA\[.*?\]\]>
        )
        /xs, $cont;
    foreach (@arr) {
        my $xt = $_;
        if ($xt =~ m/^<!/) {
            $result .= $xt;
            next;
        }
        if ($xt =~ /^<(\/)?([-\w]+)/s) {
            my $elem = lc $2;
            my $tc = $1;
            if ($elem ne $2) {
                ## Make lowercase
                $xt =~ s/<(\/)?(\w+)/<$1$elem/s;
            }
            if ((defined $tc) && ($tc eq '/')) {
                while (my $et = pop @tags) {
                    if ($et ne $elem) {
                        if (grep {$elem eq $_} @tags) {
                            $result .= "</" . $et . ">";
                        } else {
                            push @tags, $et;
                            $xt = '';
                            last;
                        }
                    } else {
                        last;
                    }
                }
            } else {
                if ($xt =~ /<([^\s]+)\s(.+)>/s) {
                    my $xt1 = $1;
                    my $xt2 = $2;
                    my $xt2_1 = '';
                    while ($xt2 =~ /
                        (\s*[\w-]+)
                        (\s* = \s*(
                            ([^\s]+|
                            '[^']*'|
                            "[^"]*")))?
                    /xgs)
                    {
                        if (! defined $2) {
                            $xt2_1 .= lc($1) . '="' . lc($1) . '"';
                        } else {
                            $xt2_1 .= lc($1) . '=' . $3;
                        }
                    }
                    $xt = '<' . $xt1 . ' ' . $xt2_1 . '>';
                }
                if (grep {$_ eq $elem} @self_closing) {
                    if (!($xt =~ m/\/\s*>$/)) {
                        $xt =~ s/>$/\/>/s;
                    }
                } else {
                    if ($xt =~ m/\/\s*>$/) {
                        $xt =~ s/\/\s*>$/><\/$elem>/s;
                    } else {
                        push @tags, $elem;
                    }
                }
            }
        }
        $result .= $xt;
    }
    while (my $elem = pop @tags) {
        $result .= "</" . $elem . ">";
    }
    
    return $result;
}


## Remove the number prefix from the filename if it another
## file isn't already with that name.
##
sub remove_number_prefix_html ($$) {
    my ($epub_st, $filename_html) = @_;
    if ($filename_html =~ /^([0-9]+[\._-])(.+\.\w+)$/) {
        if (! defined $epub_st->{files}->{$1}) {
            return $2;
        }
    }
    return $filename_html;
}

sub remove_number_prefix_img ($$) {
    my ($epub_st, $img) = @_;
    if ($img =~ /^([0-9]+[\._-])(.+\.\w+)$/) {
        if ((! defined $epub_st->{page_imgs}->{$1}) &&
            (! defined $epub_st->{inline_imgs}->{$1}))
        {
            return $2;
        }
    }
    return $img;
}

sub rename_if_needed ($$) {
    my ($epub_st, $img) = @_;
    return $img;
}


## Unless image is inline, make a small html page for the image, and add it
## to the "spine"
##
sub image_html_file ($$) {
    my ($epub_st, $img) = @_;
    
    if ($img =~ /^(.+)\.(\w+)$/) {
        my $ext = $2;
        my $filename = basename($1);
        
        my $filename_html = $filename . '_' . $ext . '_html.xhtml';

        my $img_1 = basename($img);
        $img_1 = remove_number_prefix_img($epub_st, $img_1);
        $img_1 = rename_if_needed($epub_st, $img_1);

        my $title = basename($filename);
        
        $title =~ s/^[0-9]+\W//s;
        $title =~ s/^\s+|\s+$//gs;
        $title =~ s/[-_]+/ /gs;
        
        if ($title eq '') {
            $title = $filename;
        }
        
        my $htmlattrs = '';

        if ($epub_st->{lang} ne '') {
            $htmlattrs .= ' xml:lang="' . esc($epub_st->{lang}) . '"';
            $htmlattrs .= ' lang="' . esc($epub_st->{lang}) . '"';
        }

        my $stylelinks = html_css_file($epub_st);

        my $imgstyle = '';
        $imgstyle .= 'width:100%;';
        $imgstyle .= 'max-width:100%;';
        $imgstyle .= 'max-height:100%;';
        
        my $imgattrs = '';
        $imgattrs .= ' style="' . esc($imgstyle) . '"';
        $imgattrs .= ' alt="' . esc($title) . '"';
        
        my $cont = '';
        
        $cont .= '<div>';
        $cont .= '<img src="' . esc($img_1) . '"' . $imgattrs . '/>';
        $cont .= '</div>';
        
        $filename_html = remove_number_prefix_html($epub_st, $filename_html);
        $filename_html = rename_if_needed($epub_st, $filename_html);

        my $html = html_w($htmlattrs, $title, $stylelinks, $cont);
        $epub_st->{files}->{$filename_html} = $html;
        $epub_st->{page_imgs}->{$img_1} = $img;

        my $fileid = $filename;
        if ($filename_html =~ /^(.+)\.\w+$/) {
            $fileid = $1;
        }
        
        push @{$epub_st->{set}}, [$fileid, $title, $filename_html];
    }
}


##
##

## Get the image URLs from the markdown output to find which images
## are referenced for inline use.
##
sub html_images ($$) {
    my ($cont, $title) = @_;
    my @list = ();
    my $found_h1 = 0;
    my $in_h1 = 0;
    while ($cont =~ /^(.*?)<(([^>]+|"[^"]*"|'[^']*')+)>(.+)$/gs) {
        my $intag = $3;
        $cont = $4;
        if ($in_h1 == 1) {
            $title = $1;
        }
        if ($intag =~ /^\s*h1/) {
            if ($found_h1 == 0) {
                $in_h1 = 1;
                $found_h1 = 1;
            }
        }
        elsif ($intag =~ /^\s*\/h1/) {
            $in_h1 = 0;
        }
        elsif ($intag =~ /^\s*img\s+(.+)$/) {
            my $inimg = $1;
            $inimg =~ s/\/\s*$//;
            if ($inimg =~ /src\s*=\s*(([^\s]+)|"([^"]+)"|'([^']+)')/i) {
                my $u = $1;
                if ($u =~ /^"(.*)"$/) {
                    $u = $1;
                }
                elsif ($u =~ /^'(.*)'$/) {
                    $u = $1;
                }
                $u =~ s/&quot;/"/gs;
                $u =~ s/&amp;/&/gs;
                push @list, $1;
            }
        }
    }
    return (\@list, $title);
}

sub html ($$$) {
    my ($epub_st, $filename, $cont) = @_;
    my $filename_html = $filename . '.xhtml';
    
    my $dir = dirname($filename_html);
    
    my $title_0 = basename($filename);
    
    $title_0 =~ s/^[0-9]+[_-]+//;
    $title_0 =~ s/[_-]+/ /g;
    
    ## Scan output after for <img > tags, and set those filenames as inline
    my ($image_urls, $title) = html_images($cont, $title_0);
    foreach my $img (@{$image_urls}) {
        next if ($img =~ m/^[\w-]+:/);
        next if ($img =~ /^\//);
        $epub_st->{inline_imgs}->{$img} = 0;
    }
    
    my $htmlattrs = '';
    
    if ($epub_st->{lang} ne '') {
        $htmlattrs .= ' xml:lang="' . esc($epub_st->{lang}) . '"';
        $htmlattrs .= ' lang="' . esc($epub_st->{lang}) . '"';
    }

    my $stylelinks = html_css_file($epub_st);

    $filename_html = remove_number_prefix_html($epub_st, $filename_html);
    $filename_html = rename_if_needed($epub_st, $filename_html);
    
    my $html;
    if (($cont =~ m/<\?xml/) || ($cont =~ m/<html/i)) {
        $html = add_tags($htmlattrs, $title, $stylelinks, balance_tags($cont));
    } else {
        $html = html_w($htmlattrs, $title, $stylelinks, balance_tags($cont));
    }
    $epub_st->{files}->{$filename_html} = $html;

    my $fileid = $filename;
    if ($filename_html =~ /^(.+)\.\w+$/) {
        $fileid = $1;
    }

    push @{$epub_st->{set}}, [$fileid, $title, $filename_html];
}

##
## MD FILES
##

## Markdown files call an external markdown processor which can be
## configured by the user. Since there are many flavours of Markdown,
## some of which might be more suitable for the user's needs. It makes
## more sense to let the user choose.
##

sub markdown_file ($$) {
    my ($filename, $script) = @_;
    if ((!defined $script) || ($script eq '')) {
        my $err = _("Markdown processor not specified");
        print STDERR "$err\n";
        exit 1;
    }
    
    my $output = '';
    if (my $pid = open2(my $o, my $i, $script)) {
        my $r;
        if (open my $h, '<', $filename) {
            while (<$h>) {
                print $i $_;
            }
            close $h;
            close $i;
            waitpid $pid, 0;
            while (<$o>) {
                $output .= decode('UTF-8', $_);
            }
        } else {
            my $err = _("Could not open file");
            print STDERR "501 [$err]: $!\n";
            exit 1;
        }
        return $output;
    } else {
        my $err = _("Could not start processor");
        print STDERR "502 [$err]: $!\n";
        exit 1;
    }
    
    return $output;
}


##
## TXT FILES
##

## The .txt mode is intended to be very user friendly by providing a
## very rudimentary subset of the markdown syntax that shouldn't get
## accidentally activated. The subset being one of the variation of
## the headers syntax.
##
## If no header markup is used at all, then the first line is assumed
## to be the title for the file when it is only a one line paragraph.
## If the paragraph has more than one line then it is treated as any
## other paragraph and there are no headers.
##

sub txt_out ($) {
    my ($st) = @_;
    if ($st->{make_h1} == 1) {
        push @{$st->{out}}, '<h1>' . esc($st->{buff}) . '</h1>';
        $st->{make_h1} = 0;
    }
    elsif ($st->{make_h2} == 1) {
        push @{$st->{out}}, '<h2>' . esc($st->{buff}) . '</h2>';
        $st->{make_h2} = 0;
    }
    else {
        push @{$st->{out}}, '<p>' . esc($st->{buff}) . '</p>';
    }
    $st->{buff} = '';
    $st->{buff_count} = 0;
    $st->{buff_2} = '';
}

sub txt_at_the_second_line ($$) {
    my ($st, $l) = @_;
    if ($l =~ /^\s*---+\s*$/) {
        $st->{make_h2} = 1;
        $st->{buff_2} = $l;
        $st->{buff_count} += 1;
        return 1;
    }
    if ($l =~ /^\s*===+\s*$/) {
        $st->{make_h1} = 1;
        $st->{buff_2} = $l;
        $st->{buff_count} += 1;
        return 1;
    }
    return 0;
}

sub txt_after_the_second_line ($$) {
    my ($st, $l) = @_;
    if ($st->{buff_2} ne '') {
        $st->{buff} .= "\n" . $st->{buff_2};
        $st->{buff_2} = '';
    }
}

## The first paragraph is either just a paragraph or it is
## the "title" for this text file (h1 tag) even if there
## isn't any syntax used for it.
##
sub txt_first_paragraph ($$) {
    my ($st, $l) = @_;

    if ($st->{before} == 1) {
        if ($l eq '') {
            return;
        }
        $st->{before} = 0;
    } else {
        if ($l eq '') {
            if ($st->{buff} ne '') {
                txt_out($st);
            }
            return;
        }
        if ($st->{buff} ne '') {
            if ($st->{buff_count} == 1) {
                if (txt_at_the_second_line($st, $l) == 1) {
                    return;
                }
            }
            elsif ($st->{buff_count} > 1) {
                txt_after_the_second_line($st, $l);
            }
            else {
                $st->{make_h1} = 0;
            }
            $st->{buff} .= "\n";
        }
        $st->{first} = 0;
    }
    $st->{buff} .= $l;
    $st->{buff_count} += 1;
}

## All the other paragraphs of the file
##
sub txt_other_paragraphs ($$) {
    my ($st, $l) = @_;
    if ($l eq '') {
        if ($st->{buff} ne '') {
            txt_out($st);
        }
        return;
    }
    if ($st->{buff} ne '') {
        if ($st->{buff_count} == 1) {
            if (txt_at_the_second_line($st, $l) == 1) {
                return;
            }
        }
        elsif ($st->{buff_count} > 1) {
            txt_after_the_second_line($st, $l);
        }
        $st->{buff} .= "\n";
    }
    $st->{buff} .= $l;
    $st->{buff_count} += 1;
}

sub txt_file ($) {
    my ($filename) = @_;
    my $output = '';
    if (open my $h, '<', $filename) {
        my $st = {
            'before' => 1,
            'first' => 1,
            'out' => [],
            'buff' => '',
            'buff_count' => 0,
            'make_h1' => 1,
            'make_h2' => 0
        };
        while (<$h>) {
            chomp;
            my $l = decode('UTF-8', $_);
            $l =~ s/\s+$//g;
            if ($st->{first} == 1) {
                txt_first_paragraph($st,$l);
            } else {
                txt_other_paragraphs($st,$l);
            }
        }
        txt_other_paragraphs($st,'');
        txt_other_paragraphs($st,'');
        close $h;
        
        foreach (@{$st->{out}}) {
            $output .= $_ . "\n\n";
        }
    } else {
        my $err = _("Could not open file");
        print STDERR "501 [$err]: $!\n";
        exit 1;
    }
    return $output;
}

##
## Make the opf file for the epub.
##

sub make_opf ($) {
    my ($epub_st) = @_;
    my $lang = $epub_st->{lang};
    my $uid = $epub_st->{uid};
    my $title = $epub_st->{title};
    my $author = $epub_st->{author};
    my @navpoints = @{$epub_st->{navpoints}};

    my $manifest = '';
    foreach (@navpoints) {
        my ($ch_id, $ch_name, $ch_filename) = @{$_};
        my $mimetype = 'application/xhtml+xml';
        $manifest .= "    <item id=\"" . esc($ch_id) . "\" " .
                            "href=\"" . esc($ch_filename) . "\" " .
                            "media-type=\"" . esc($mimetype) . "\"/>\n";
    }
    my $i = 1;
    foreach my $css (@{$epub_st->{'css'}}) {
        my $css_id = "__stylesheet" . $i;
        my $mimetype = 'text/css';
        $manifest .= "    <item id=\"" . esc($css_id) . "\" " .
                            "href=\"" . esc($css) . "\" " .
                            "media-type=\"" . esc($mimetype) . "\"/>\n";
        ++$i;
    }
    $i = 1;
    foreach my $fontfile (@{$epub_st->{'fonts'}}) {
        my $mimetype = 'font/ttf';
        my $font_id = "__font" . $i;
        if ($fontfile =~ /(\.\w+)$/i) {
            my $ext = lc $1;
            if (defined $extensions_fonts{$ext}) {
                $mimetype = $extensions_fonts{$ext};
            }
        }
        $manifest .= "    <item id=\"" . esc($font_id) . "\" " .
                            "href=\"" . esc($fontfile) . "\" " .
                            "media-type=\"" . esc($mimetype) . "\"/>\n";
        ++$i;
    }
    $i = 1;

    my @images = ();
    foreach (keys %{$epub_st->{page_imgs}}) {
        push @images, $_;
    }
    foreach (keys %{$epub_st->{inline_imgs}}) {
        push @images, $_;
    }
    foreach my $im_filename (@images) {
        my $mimetype = 'image/png';
        my $im_id = "__image" . $i;
        if ($im_filename =~ /(\.\w+)$/i) {
            my $ext = lc $1;
            if (defined $extensions_images{$ext}) {
                $mimetype = $extensions_images{$ext};
            }
        }
        $manifest .= "    <item id=\"" . esc($im_id) . "\" " .
                            "href=\"" . esc($im_filename) . "\" " .
                            "media-type=\"" . esc($mimetype) . "\"/>\n";
        ++ $i;
    }
    $manifest .= "    <item id=\"ncx\" " .
        "href=\"toc.ncx\" " .
        "media-type=\"application/x-dtbncx+xml\"/>\n";


    my $opf = '';
    $opf .= "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    $opf .= "<package xmlns=\"http://www.idpf.org/2007/opf\" version=\"2.0\" unique-identifier=\"book_id\">\n";
    $opf .= "  <metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:opf=\"http://www.idpf.org/2007/opf\">\n";
    $opf .= "    <dc:title>" . esc($title) . "</dc:title>\n";
    $opf .= "    <dc:language>" . esc($lang) . "</dc:language>\n";
    $opf .= "    <dc:identifier id=\"book_id\" opf:scheme=\"uuid\">" . esc($uid) . "</dc:identifier>\n";
    if ($author ne '') {
        $opf .= "    <dc:creator opf:file-as=\"" . esc($author) . "\" opf:role=\"aut\">" . esc($author) . "</dc:creator>\n";
    }
    $opf .= "  </metadata>\n";
    $opf .= "  <manifest>\n";
    $opf .= $manifest;
    $opf .= "  </manifest>\n";
    $opf .= "  <spine toc=\"ncx\">\n";
    foreach (@navpoints) {
        my ($ch_id, $ch_name, $ch_filename) = @{$_};
        $opf .= "    <itemref idref=\"" . esc($ch_id) . "\" />\n";
    }
    $opf .= "  </spine>\n";
    $opf .= "</package>\n";
}

##
## Make the ncx file for the epub.
##

sub make_ncx ($) {
    my ($epub_st) = @_;
    my $lang = $epub_st->{lang};
    my $uid = $epub_st->{uid};
    my $title = $epub_st->{title};
    my $author = $epub_st->{author};
    my @navpoints = @{$epub_st->{navpoints}};
    my @images = @{$epub_st->{images}};
    
    my $ncxattrs = '';
    
    if ($lang ne '') {
        $ncxattrs .= ' xml:lang="' . esc($lang) . '"';
    }

    my $ncx = "";
    $ncx .= "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    $ncx .= "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\"\n";
    $ncx .= "\"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n";
    $ncx .= "<ncx version=\"2005-1\"$ncxattrs xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n";
    $ncx .= "  <head>\n";
    $ncx .= "    <meta name=\"dtb:uid\" content=\"" . esc($uid) . "\"/>\n";
    $ncx .= "    <meta name=\"dtb:depth\" content=\"1\"/>\n";
    $ncx .= "    <meta name=\"dtb:totalPageCount\" content=\"0\"/>\n";
    $ncx .= "    <meta name=\"dtb:maxPageNumber\" content=\"0\"/>\n";
    $ncx .= "  </head>\n";
    $ncx .= "  <docTitle>\n";
    $ncx .= "    <text>" . esc($title) . "</text>\n";
    $ncx .= "  </docTitle>\n";
    $ncx .= "  <docAuthor>\n";
    $ncx .= "    <text>" . esc($author) . "</text>\n";
    $ncx .= "  </docAuthor>\n";
    $ncx .= "  <navMap>\n";
    my $i = 1;
    foreach (@navpoints) {
        my ($ch_id, $ch_name, $ch_filename) = @{$_};
        $ncx .= "    <navPoint class=\"chapter\" id=\"" . esc($ch_id) . "\" playOrder=\"" . $i . "\">\n";
        $ncx .= "      <navLabel><text>" . esc($ch_name) . "</text></navLabel>\n";
        $ncx .= "      <content src=\"" . esc($ch_filename) . "\"/>\n";
        $ncx .= "    </navPoint>\n";
        ++ $i;
    }
    $ncx .= "  </navMap>\n";
    $ncx .= "</ncx>\n";
}


##
##

sub zip_epub ($$) {
    my ($filename, $epub) = @_;
    return if (! defined $filename);
    if ($filename =~ /\.epub$/i) {
        $filename =~ s/\.epub$/.epub/i;

        my $opffile = 'content.opf';
        
        my $containerfile = ''
            . "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n"
            . "<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">\n"
            . "  <rootfiles>\n"
            . "    <rootfile full-path=\"" . esc($opffile) . "\" media-type=\"application/oebps-package+xml\"/>\n"
            . "  </rootfiles>\n"
            . "</container>\n";
        
        if (my $z = IO::Compress::Zip->new($filename, {Name=>"mimetype",Method=>ZIP_CM_STORE})) {
            $z->print("application/epub+zip");
            $z->newStream(Name => "META-INF/container.xml", Method=>ZIP_CM_DEFLATE);
            $z->print($containerfile);

            foreach (keys %{$epub}) {
                my $k = $_;
                my $v = $epub->{$k};
                $z->newStream(Name => $k, Method=>ZIP_CM_DEFLATE);
                $z->print($v);
            }
            $z->close() ;
        } else {
            my $err = _("Could not create epub zip");
            print STDERR "$err: $!\n";
            exit 1;
        }
    } else {
        my $err = _("File should have a .epub extension");
        print STDERR "$err\n";
        exit 1;
    }
}

##
##

## Find the fonts in the style sheet near the beginning
## of the style sheet.
##

sub stylesheet_font_face_src ($) {
    my ($src) = @_;
    
    my $src_a = {};
    my @src_arr = ();
    while ($src =~ /([\w-]+)\s*\(\s*("[^"]*"|'[^']*'|[^)]*)\s*\)\s*(,)?(.*)/gsi) {
        $src = $4;
        my $key = $1;
        my $val = $2;
        my $next_src = $4;
        if ($val =~ /^"(.+)"$/) {
            $val = $1;
        }
        if ($val =~ /^'(.+)'$/) {
            $val = $1;
        }
        $src_a->{$key} = $val;
        if (defined $next_src) {
            push @src_arr, $src_a;
            $src_a = {};
        }
    }
    return \@src_arr;
}

sub stylesheet_font_faces ($$) {
    my ($font_src, $css) = @_;
    
    my %ext = (
        '.ttf' => 1,
        '.otf' => 1,
        '.woff' => 1,
        '.woff2' => 1
    );

    while ($css =~ /\@font-face\s*{([^}]*)}(.*)/gsi) {
        my $inside = $1;
        $css = $2;
        if ($inside =~ /src\s*:(.*)/gsi) {
            my $src_set = $1;
            my $src_arr_1 = stylesheet_font_face_src($src_set);
            foreach my $s (@{$src_arr_1}) {
                if ((defined $s->{'url'}) && ($s->{'url'} =~ /(\.\w+)$/s)) {
                    next if ! defined $ext{lc $1};
                    my $url = $s->{'url'};
                    next if $url =~ m/[:;#&?*\%\\]/;
                    next if $url =~ m/^\//;
                    while ($url =~ /^\.\/(.+)$/gs) {
                        $url = $1;
                    }
                    next if $url =~ m/(^|\/)\.\.(\/|$)/;
                    $url =~ s/^\/\.\//\//gs;
                    push @{$font_src}, $url;
                }
            }
        }
    }
}

## Get the fonts that are included with the
## style sheet by looking at the beginning of
## the style sheet.
##
sub stylesheet_fonts_src ($) {
    my ($stylecont) = @_;
    my $found = 0;
    my $cont = '';
    my $font_src = [];
    my @lines = split /\n/, $stylecont;
    foreach (@lines) {
        if (($found == 1) && (m/[}]/)) {
            $cont .= $_;
            stylesheet_font_faces($font_src, $cont);
            $cont = '';
            $found = 0;
        }
        if (m/\@font-face/) {
            $found = 1;
        }
        elsif (($found == 0) && (m/[{]/)) {
            last;
        }
        if ($found == 1) {
            $cont .= $_;
        }
    }
    return $font_src;
}


##
##

sub binary_file ($) {
    my ($filename) = @_;
    if (-f $filename) {
        if (open my $h, '<', $filename) {
            use bytes;
            binmode $h;
            my $filebytes = '';
            while (! eof $h) {
                read $h, (my $bytes), 1024;
                $filebytes .= $bytes;
            }
            close $h;
            return $filebytes;
        }
    }
    return undef;
}

sub add_font ($$$$) {
    my ($cssdir, $fontfile, $epub, $epub_st) = @_;
    my $fontbytes = binary_file($cssdir . '/' . $fontfile);
    if (defined $fontbytes) {
           push @{$epub_st->{'fonts'}}, "style/" . $fontfile;
        $epub->{"style/" . $fontfile} = $fontbytes;
    }
}

sub add_style_sheet ($$$) {
    my ($cssfilename, $epub, $epub_st) = @_;
    if (open my $h, '<', $cssfilename) {
        my $csscont = '';
        while (<$h>) {
            $csscont .= $_;
        }
        close $h;
        
        my $cssdir = dirname($cssfilename);
        my $fontfiles = stylesheet_fonts_src($csscont);
        foreach (@{$fontfiles}) {
            add_font($cssdir, $_, $epub, $epub_st);
        }

        my $cssf = "style/" . basename($cssfilename);
        push @{$epub_st->{'css'}}, $cssf;
        $epub->{$cssf} = $csscont;
        return 1;
    } else {
        my $err = _("Could not load css");
        print STDERR "$err: $!\n";
    }
}

sub find_style ($$$$) {
    my ($epub_st, $epub, $styledir, $style) = @_;
    return undef if (! defined $style) || ($style eq '');

    my $cssfilename;
    if (($style =~ m/\.css$/i)
        && (-f "$styledir/$style")
        && (! -d "$styledir/$style"))
    {
        $cssfilename = "$styledir/$style";
    }
    elsif ((-f "$styledir/$style.css")
        && (! -d "$styledir/$style.css"))
    {
        $cssfilename = "$styledir/$style.css";
    }
    if (defined $cssfilename) {
        if (add_style_sheet($cssfilename, $epub, $epub_st)) {
            return 1;
        }
    }
    return undef;
}

##
##

sub style_dir_list ($) {
    my ($config) = @_;

    my @dir_list = ();
    my $style_dir = $config->{'style_dir'};
    if ((defined $style_dir) && ($style_dir ne '')) {
        my @list = split(/;/, $style_dir);
        foreach (@list) {
            my $dir_entry = $_;
            $dir_entry =~ s/^\s+|\s+$//g;
            next if $dir_entry eq '';
            if ($dir_entry =~ m/^\//) {
            } elsif ($dir_entry =~ /^~\/(.+)$/) {
                $dir_entry = $ENV{HOME} . '/' . $1;
            } else {
                $dir_entry = $ENV{HOME} . '/' . $dir_entry;
            }
            push @dir_list, $dir_entry;
        }
    }
    push @dir_list, dirname(__FILE__) . '/styles/';
    return \@dir_list;
}

my %default_conf_v = (
    'markdown_processor' => "python3 -m markdown",
    'default_author' => _("Unknown")
);
sub default_config ($) {
    my ($config) = @_;
    foreach (keys %default_conf_v) {
        if ((! defined $config->{$_}) || ($config->{$_} eq '')) {
            my $v = $default_conf_v{$_};
            $config->{$_} = $v;
        }
    }
}

sub epub_st_images ($) {
    my ($epub_st) = @_;

    my @all_images = ();
    foreach my $file (keys %{$epub_st->{inline_imgs}}) {
        push @all_images, $file;
    }
    foreach my $file (keys %{$epub_st->{page_imgs}}) {
        push @all_images, $file;
    }
    $epub_st->{images} = \@all_images;
}

sub remove_inexistent_inlines ($) {
    my ($epub_st) = @_;
    my @remove = ();
    foreach (keys %{$epub_st->{inline_imgs}}) {
        if ($epub_st->{inline_imgs}->{$_} == 0) {
            push @remove, $_;
        }
    }
    foreach (@remove) {
        my $err = _("Inline image not found");
        print STDERR "$err: '$_'\n";
        delete $epub_st->{inline_imgs}->{$_};
    }
}


sub main_make_epub ($$) {
    my ($args, $config) = @_;
    my @args = @{$args};
    if (@args < 1) {
        exit 1;
    }
    
    read_settings($config);
    default_config($config);

    my $epub_st = {
        'files' => {},
        'set' => [],
        'inline_imgs' => {},
        'inline_imgs_fullpath' => {},
        'page_imgs' => {},
        'uid' => uuid(),
        'title' => '',
        'lang' => '',
        'author' => '',
        'sequence' => [],
        'navpoints' => [],
        'images' => [],
        'stylesheet' => '',
        'css' => [],
        'fonts' => [],
        'style_dirs' => style_dir_list($config)
    };
    my %epub = ();

    if (defined $config->{'extra_mime_types'}) {
        my $mimefile = $config->{'extra_mime_types'};
        $mimefile =~ s/^\s+|\s+$//g;
        if ($mimefile ne '') {
            read_mime_file($mimefile);
        }
    }
    
    my $tried_loading_style = 0;
    my $outepub;
    my @images = ();
    for (my $i = 0; $i < @args; ++$i) {
        my $arg = $args[$i];
        if ($arg eq '--out') {
            ++$i;
            $outepub = $args[$i];
            next;
        }
        if ($arg eq '--proc') {
            ++$i;
            $config->{'markdown_processor'} = $args[$i];
            next;
        }
        if ($arg eq '--lang') {
            ++$i;
            $epub_st->{'lang'} = $args[$i];
            next;
        }
        if ($arg eq '--author') {
            ++$i;
            $epub_st->{'author'} = $args[$i];
            next;
        }
        if ($arg eq '--title') {
            ++$i;
            $epub_st->{'title'} = $args[$i];
            next;
        }
        if ($arg eq '--sequence') {
            ++$i;
            my @list = split(';',$args[$i]);
            $epub_st->{'sequence'} = \@list;
            next;
        }
        if ($arg eq '--style') {
            ++$i;
            $epub_st->{'stylesheet'} = $args[$i];
            next;
        }
        if ($arg eq '--add-style-path') {
            ++$i;
            my @list = split(';',$args[$i]);
            foreach (@list) {
                unshift @{$epub_st->{'style_dirs'}}, $_;
            }
            next;
        }
        if ((length($arg) >= 2) && (substr($arg,0,2) eq '--')) {
            print STDERR "Unknown switch '$arg'\n";
            exit 1;
        }
        
        if (! defined $outepub) {
            my $err = _("Missing output epub filename");
            print STDERR "504 [$err]\n";
            exit 1;
        }

        if ((@{$epub_st->{'css'}} == 0) && ($epub_st->{'stylesheet'} ne '')) {
            my $style = $epub_st->{'stylesheet'};
            $tried_loading_style = 1;
            my $found_style = 0;
            foreach my $styledir (@{$epub_st->{'style_dirs'}}) {
                if (find_style($epub_st, \%epub, $styledir, $style)) {
                    $found_style = 1;
                    last;
                }
            }
            if ($found_style == 0) {
                my $err = _("Could not find style sheet");
                print STDERR "$err: '$style'\n";
            }
        }

    
        if ($epub_st->{'lang'} eq '') {
            my $language = '';
            if (defined $ENV{'LANGUAGE'}) {
                $language = $ENV{'LANGUAGE'};
            }
            if (defined $ENV{'LANG'}) {
                $language = $ENV{'LANG'};
            }
            if (defined $ENV{'LC_PAPER'}) {
                $language = $ENV{'LC_PAPER'};
            }
            if ($language =~ /^([a-z]+)/i) {
                $language = $1;
            }
            $epub_st->{'lang'} = $language;
        }
        
        
        my $filename = $arg;
        if ($filename =~ /^(.+?)(\.[^\/.]+)$/) {
            my $filename_no_ext = basename($1);
            my $ext = lc $2;
            if (grep { $_ eq $ext } @extensions_txt) {
                my $output = txt_file($filename);
                html($epub_st, $filename_no_ext, $output);
            }
            elsif (grep { $_ eq $ext } @extensions_markdown)
            {
                my $processor = $config->{'markdown_processor'};
                my $output = markdown_file($filename, $processor);
                html($epub_st, $filename_no_ext, $output);
            }
            elsif (grep { $_ eq $ext } @extensions_xhtml)
            {
                my $output = '';
                if (open my $xh, '<', $filename) {
                    while (<$xh>) {
                        $output .= $_;
                    }
                    close $xh;

                    html($epub_st, $filename_no_ext, $output);
                } else {
                    my $err = _("Can't use xhtml file");
                    print STDERR "205 [$err]: $filename\n";
                }
            }
            elsif (grep { $_ eq $ext } (keys %extensions_images))
            {
                push @images, $filename;
            }
            else {
                my $err = _("Can't use file");
                print STDERR "205 [$err]: $filename\n";
            }
        } else {
            my $output = txt_file($filename);
            html($epub_st, basename($filename), $output);
        }
    }
    
    foreach my $img (@images) {
        my $img1 = basename($img);
        if (defined $epub_st->{inline_imgs}->{$img1}) {
            $epub_st->{inline_imgs}->{$img1} = 1;
            $epub_st->{inline_imgs_fullpath}->{$img1} = $img;
            next;
        }
        image_html_file($epub_st, $img);
    }

    remove_inexistent_inlines($epub_st);

    if ($epub_st->{'author'} eq '') {
        $epub_st->{'author'} = $config->{'default_author'};
    }

    
    @{$epub_st->{set}} = sort { $a->[0] cmp $b->[0] } @{$epub_st->{set}};

    foreach my $arr (@{$epub_st->{set}}) {
        my ($fileid, $title, $filename_html) = @{$arr};
        push @{$epub_st->{navpoints}}, [$fileid, $title, $filename_html];
    }

    epub_st_images($epub_st);
    
    $epub{"content.opf"} = make_opf($epub_st);
    $epub{"toc.ncx"} = make_ncx($epub_st);
    foreach my $k (keys %{$epub_st->{files}}) {
        $epub{$k} = $epub_st->{files}->{$k};
    }
    my %img_files = ();
    foreach my $file (keys %{$epub_st->{inline_imgs_fullpath}}) {
        my $file1 = basename($file);
        $img_files{$file1} = $epub_st->{inline_imgs_fullpath}->{$file};
    }
    foreach my $file (keys %{$epub_st->{page_imgs}}) {
        my $file1 = basename($file);
        $img_files{$file1} = $epub_st->{page_imgs}->{$file};
    }

    foreach my $k (keys %img_files) {
        my $file = $img_files{$k};
        my $imgbytes = binary_file($file);
        if (defined $imgbytes) {
            $epub{$k} = $imgbytes;
        }
    }

    zip_epub($outepub, \%epub);
}

##
##

sub conf_dir ($) {
    my ($file) = @_;
    my $confdir = '';
    if (! defined $ENV{'HOME'}) {
        return undef;
    }
    if ((defined $ENV{'XDG_CONFIG_HOME'}) &&
        ($ENV{'XDG_CONFIG_HOME'} ne ''))
    {
        $confdir = $ENV{'XDG_CONFIG_HOME'};
    }
    if ($confdir eq '') {
        $confdir = $ENV{'HOME'} . '/.config/';
    }
    $confdir .= CONFIG_DIR . '/' . $file;
    return $confdir;
}

## Read settings from config file.
##
sub read_settings ($) {
    my ($config) = @_;
    my $unused = '';
    if (my $conffile = conf_dir('settings.conf')) {
        if (open my $h, '<', $conffile) {
            while (<$h>) {
                if (/^\s*(\w+)\s*=\s*(.*)$/) {
                    my $k = $1;
                    my $v = $2;
                    $v =~ s/^\s+|\s+$//g;
                    if ((! defined $config->{$k}) && ($v ne '')) {
                        $config->{$k} = $v;
                    }
                } else {
                    $unused .= $_;
                }
            }
            close $h;
            return $unused;
        } else {
            return '';
        }
    }
    return undef;
}

## Write settings from config file.
##
sub write_settings ($) {
    my ($config) = @_;
    if (my $conffile = conf_dir('settings.conf')) {
        mkdir dirname($conffile);
        my $unused = read_settings($config);
        if (defined $unused) {
            if (open my $h, '>', $conffile) {
                if ($unused ne '') {
                    print $h $unused;
                    if (!($unused =~ m/\n$/gs)) {
                        print $h "\n";
                    }
                }
                foreach my $k (keys %{$config}) {
                    my $v = $config->{$k};
                    $v =~ s/[\r\n\t\v]+/ /g;
                    $v =~ s/^\s+|\s+$//g;
                    if (($v ne '') && ((!defined $default_conf_v{$k}) || ($v ne $default_conf_v{$k}))) {
                        print $h $k . "=" . $v . "\n";
                    }
                }
                close $h;
            } else {
                print STDERR "Could not write settings file: $!\n";
            }
        }
    }
}

##
## GUI
##

sub yes_no_dialog ($$) {
    my ($dialog, $message) = @_;
    my $d = Gtk3::MessageDialog->new($dialog,
            [qw( modal destroy-with-parent )],
            'warning',
            'yes-no',
            $message);
    my $c = $d->run();
    $d->destroy();
    if ($c eq 'yes') {
        return 1;
    }
    return 0;
}

sub error_dialog ($$) {
    my ($dialog, $message) = @_;
    my $d = Gtk3::MessageDialog->new($dialog,
            [qw( modal destroy-with-parent )],
            'warning',
            'ok',
            $message);
    $d->run();
    $d->destroy();
}

sub choose_folder ($$) {
    my ($dialog, $entry) = @_;
    my $title = _("Choose Folder");
    
    my $browse_dialog = Gtk3::FileChooserDialog->new(
        $title,
        $dialog,
        'select-folder',
        ('gtk-cancel', 'cancel', 'gtk-open', 'accept'));
    $browse_dialog->set_modal(TRUE);
    $browse_dialog->signal_connect('response' => sub {
        my ($dialog, $res) = @_;
        if ($res eq 'accept') {
            my $file = $dialog->get_filename();
            $entry->set_text($file);
            $dialog->destroy;
        }
        elsif ($res eq 'cancel') {
            $dialog->destroy;
        }
    });

    $browse_dialog->show();
}

##
##
sub settings_dialog_button_row ($$$$) {
    my ($prefix, $dialog, $save_settings, $ui_state) = @_;
    my $btn_label = _("Okay");
    my $btn_dismiss_label = _("Cancel");
    my $hbox = Gtk3::HBox->new;

    my $button = Gtk3::Button->new($btn_label);
    $hbox->pack_end($button, FALSE, TRUE, 0);
    $button->signal_connect(clicked => sub {
        &{$save_settings}($ui_state);
        $dialog->hide();
        $dialog->destroy();
    });

    my $button_dismiss = Gtk3::Button->new($btn_dismiss_label);
    $hbox->pack_end($button_dismiss, FALSE, TRUE, 0);
    $button_dismiss->signal_connect(clicked => sub {
        $dialog->hide();
        $dialog->destroy();
    });

    return $hbox;
}

sub settings_dialog ($$) {
    my ($changed_settings, $config) = @_;
    my $prefix = "no";
    my $title = _("Settings");

    my $mimefile_label_str = _("User Mime Types File:");
    my $markdown_label_str = _("Markdown Processor:");
    my $author_label_str = _("Default Author:");
    my $style_label_str = _("Custom Style Folder:");
    my $btn_browse_label = _("Browse");

    my $window = Gtk3::Window->new('toplevel');
    $window->set_border_width(10);
    $window->set_title($title);
    $window->resize(350, 220);
    $window->set_type_hint('dialog');

    my $vbox = Gtk3::VBox->new;

    my $author_label = Gtk3::Label->new($author_label_str);
    $author_label->set_xalign(0.0);
    $vbox->pack_start($author_label, TRUE, TRUE, 0);
    my $author_entry = Gtk3::Entry->new;
    $vbox->pack_start($author_entry, TRUE, TRUE, 0);

    my $style_label = Gtk3::Label->new($style_label_str);
    $style_label->set_xalign(0.0);
    $vbox->pack_start($style_label, TRUE, TRUE, 0);
    my $style_entry = Gtk3::Entry->new;
    $vbox->pack_start($style_entry, TRUE, TRUE, 0);
    my $button_style_browse = Gtk3::Button->new($btn_browse_label);
    $vbox->pack_start($button_style_browse, FALSE, TRUE, 0);
    $button_style_browse->signal_connect(clicked => sub {
        choose_folder($window, $style_entry);
    });

    my $markdown_label = Gtk3::Label->new($markdown_label_str);
    $markdown_label->set_xalign(0.0);
    $vbox->pack_start($markdown_label, TRUE, TRUE, 0);
    my $markdown_entry = Gtk3::Entry->new;
    $vbox->pack_start($markdown_entry, TRUE, TRUE, 0);

    my $mimefile_label = Gtk3::Label->new($mimefile_label_str);
    $mimefile_label->set_xalign(0.0);
    $vbox->pack_start($mimefile_label, TRUE, TRUE, 0);
    my $mimefile_entry = Gtk3::Entry->new;
    $vbox->pack_start($mimefile_entry, TRUE, TRUE, 0);

    default_config($config);

    my $default_author = '';
    if (defined $config->{'default_author'}) {
        $default_author = $config->{'default_author'};
    }
    $author_entry->set_text($default_author);

    my $style_dir = '';
    if (defined $config->{'style_dir'}) {
        $style_dir = $config->{'style_dir'};
    }
    $style_entry->set_text($style_dir);

    my $markdown_processor = '';
    if (defined $config->{'markdown_processor'}) {
        $markdown_processor = $config->{'markdown_processor'};
    }
    $markdown_entry->set_text($markdown_processor);

    my $extra_mime_file = '';
    if (defined $config->{'extra_mime_types'}) {
        $extra_mime_file = $config->{'extra_mime_types'};
    }
    $mimefile_entry->set_text($extra_mime_file);

    my $ui_state = {
        'author_entry' => $author_entry,
        'style_entry' => $style_entry,
        'markdown_entry' => $markdown_entry,
        'mimefile_entry' => $mimefile_entry,
        'config' => $config
    };

    my $save_settings = sub ($) {
        my ($ui_state) = @_;
        my $config = $ui_state->{config};
        $config->{'default_author'} = $ui_state->{author_entry}->get_text();
        $config->{'style_dir'} = $ui_state->{style_entry}->get_text();
        $config->{'markdown_processor'} = $ui_state->{markdown_entry}->get_text();
        $config->{'extra_mime_types'} = $ui_state->{mimefile_entry}->get_text();
        write_settings($config);
        &$changed_settings();
    };

    $vbox->pack_start(
        settings_dialog_button_row(
            $prefix, $window, $save_settings, $ui_state),
        FALSE, TRUE, 0);
    $window->add($vbox);

    $window->show_all();
}

##
##

## Build the argument list to pass to the build process.
##
sub construct_args ($$) {
    my ($dialog, $epub_gui_st) = @_;

    my $msg_no_epub = _("No epub file specified.");
    my $msg_epub_no_dir = _("Epub output directory does not exist.");
    my $msg_epub_already = _("Epub with that filename already exists, overwrite?");

    my $dir = $epub_gui_st->{'dir'};

    my $language_entry = $epub_gui_st->{'lang_entry'};
    my $author_entry = $epub_gui_st->{'author_entry'};
    my $title_entry = $epub_gui_st->{'title_entry'};
    my $style_list = $epub_gui_st->{'style_entry'};
    my $filename_entry = $epub_gui_st->{'epub_filename_entry'};

    my $language = $language_entry->get_text();
    my $author = $author_entry->get_text();
    my $title = $title_entry->get_text();
    my $style = '';
    my $style_active = $style_list->get_active();
    if (($style_active >= 0) || ($style_active >= @{$epub_gui_st->{styles_str_list}})) {
        $style = $epub_gui_st->{styles_str_list}->[$style_active];
    }

    my $filename = $filename_entry->get_text();

    my @arglist = ();

    if ($language ne '') {
        push @arglist, '--lang';
        push @arglist, $language;
    }
    if ($author ne '') {
        push @arglist, '--author';
        push @arglist, $author;
    }
    if ($title ne '') {
        push @arglist, '--title';
        push @arglist, $title;
    }
    if ($style ne '') {
        push @arglist, '--style';
        push @arglist, $style;
    }

    if ($filename ne '') {
        my $epub_filename = '';
        if ($filename =~ /^(.+)\.epub$/i) {
            $filename = $1 . '.epub';
        } else {
            $filename = $filename . '.epub';
        }
        if ($filename =~ m/\//) {
            $epub_filename = $filename;
        }
        else {
            $epub_filename = $dir . '/' . $filename;
        }
        if (! -d dirname($epub_filename)) {
            error_dialog($dialog, $msg_epub_no_dir);
            return undef;
        }
        if (-f $epub_filename) {
            my $ov = yes_no_dialog($dialog, $msg_epub_already);
            if (!$ov) {
                return undef;
            }
        }
        push @arglist, '--out';
        push @arglist, $epub_filename;
    } else {
        error_dialog($dialog, $msg_no_epub);
        return undef;
    }

    foreach (@{$epub_gui_st->{'files'}}) {
        my $f = $_;
        if (! defined $dir) {
            $f = $dir . '/' . $f;
        }
        push @arglist, $f;
    }
    return \@arglist;
}

sub epub_filename_entry ($$) {
    my ($epub_gui_st, $filename) = @_;
    my $entry = $epub_gui_st->{epub_filename_entry};

    if ((defined $epub_gui_st->{dir}) && ($epub_gui_st->{dir} ne '')) {
        my $dir1 = $epub_gui_st->{dir};
        if (!($dir1 =~ m/\/$/)) {
            $dir1 .= '/';
        }
        my $dir2 = dirname($filename);
        if (!($dir2 =~ m/\/$/)) {
            $dir2 .= '/';
        }
        if ($dir1 eq $dir2) {
            $filename = basename($filename);
        }
    }
    
    $entry->set_text($filename);
}

## Read auto fill values from settings file.
##
sub read_auto_fill ($$) {
    my ($config, $epub_gui_st) = @_;

    read_settings($config);
    
    if ((defined $config->{'set_lang'}) && ($config->{'set_lang'} ne '')) {
        $epub_gui_st->{'auto_fill_lang'} = $config->{'set_lang'};
    }
    if ((defined $config->{'set_author'}) && ($config->{'set_author'} ne '')) {
        $epub_gui_st->{'auto_fill_author'} = $config->{'set_author'};
    }
    if ((defined $config->{'set_style'}) && ($config->{'set_style'} ne '')) {
        $epub_gui_st->{'auto_fill_style'} = $config->{'set_style'};
    }
}

## Write auto fill values to settings file.
##
sub write_auto_fill ($$) {
    my ($config, $epub_gui_st) = @_;

    my $language_entry = $epub_gui_st->{'lang_entry'};
    my $author_entry = $epub_gui_st->{'author_entry'};
    my $style_list = $epub_gui_st->{'style_entry'};

    my $language = $language_entry->get_text();
    my $author = $author_entry->get_text();
    my $style = '';
    my $style_active = $style_list->get_active();
    if (($style_active >= 0) || ($style_active >= @{$epub_gui_st->{styles_str_list}})) {
        $style = $epub_gui_st->{styles_str_list}->[$style_active];
    }

    my $changed = 0;
    if ($epub_gui_st->{'auto_fill_lang'} ne $language) {
        $changed = 1;
    }
    if ($epub_gui_st->{'auto_fill_author'} ne $author) {
        $changed = 1;
    }
    if ($epub_gui_st->{'auto_fill_style'} ne $style) {
        $changed = 1;
    }
    if ($changed) {
        $config->{'set_lang'} = $language;
        $config->{'set_author'} = $author;
        $config->{'set_style'} = $style;
        write_settings($config);
    }
}

sub group_files_epub_dialog_button_row ($$$$) {
    my ($dialog, $config, $epub_gui_st, $changed_settings) = @_;
    my $btn_label = _("Create EPUB");
    my $btn_dismiss_label = _("Cancel");
    my $btn_settings_label = _("Settings");

    my $msg_not_write_epub = _("Could not write EPUB");

    my $hbox = Gtk3::HBox->new;

    my $button = Gtk3::Button->new($btn_label);
    $hbox->pack_end($button, FALSE, TRUE, 0);
    $button->signal_connect(clicked => sub {
        write_auto_fill($config, $epub_gui_st);
        if (my $args = construct_args($dialog, $epub_gui_st)) {
            ## Spawn a build process and then show the result.
            my $pid = open my $o, '-|';
            if (! defined $pid) {
                error_dialog($dialog, "$msg_not_write_epub:\n\n$!");
            }
            if ($pid == 0) {
                open STDERR, ">&", \*STDOUT;
                if (! exec $0, "build", @{$args}) {
                    print STDERR "\nexec: $!";
                    exit 1;
                }
            }

            my $err = '';
            while (<$o>) {
                $err .= $_;
            }
            close $o;
            
            if ($? == 0) {
                Gtk3::main_quit();
            } else {
                error_dialog($dialog, "$msg_not_write_epub:\n\n$err");
            }
        }
    });

    my $button_dismiss = Gtk3::Button->new($btn_dismiss_label);
    $hbox->pack_end($button_dismiss, FALSE, TRUE, 0);
    $button_dismiss->signal_connect(clicked => sub {
        Gtk3::main_quit();
    });

    my $button_settings = Gtk3::Button->new($btn_settings_label);
    $hbox->pack_start($button_settings, FALSE, TRUE, 0);
    $button_settings->signal_connect(clicked => sub {
        settings_dialog($changed_settings, $config);
    });

    return $hbox;
}

sub get_default_author () {
    my $author = '';
    if (defined $ENV{'USER'}) {
        $author = $ENV{'USER'};
    }
    if ($author eq '') {
        $author = `whoami`;
    }
    return $author;
}

sub lang_env ($$) {
    my ($e, $language) = @_;
    if (defined $ENV{$e}) {
        if ($ENV{$e} =~ /^([a-z]+)/i) {
            $language = $1;
        }
    }
    return $language;
}

sub get_default_language () {
    my $language = '';
    $language = lang_env('LANGUAGE', $language);
    $language = lang_env('LANG', $language);
    $language = lang_env('LC_PAPER', $language);
    return $language;
}

sub list_of_styles ($$$) {
    my ($config, $epub_gui_st, $style_list_store) = @_;

    my $dir_list = style_dir_list($config);

    my @arr = ();
    $style_list_store->clear();
    $style_list_store->set($style_list_store->append(), 0 => '');
    push @arr, '';
    foreach my $dir_entry (@{$dir_list}) {
        if (opendir my $hd, $dir_entry) {
            while (my $stylef=readdir $hd) {
                next if $stylef eq '.' || $stylef eq '..';
                next if !($stylef =~ m/\.css$/i);
                $style_list_store->set($style_list_store->append(), 0 => $stylef);
                push @arr, $stylef;
            }
            closedir $hd;
        }
    }
    $epub_gui_st->{styles_str_list} = \@arr;
}

sub group_files_epub_dialog ($$) {
    my ($epub_gui_st, $config) = @_;
    my $title = _("Create EPUB from files");

    my $filename_label_str = _("Filename:");
    my $title_label_str = _("Title:");
    my $author_label_str = _("Author:");
    my $language_label_str = _("Language:");
    my $style_label_str = _("Style:");

    my $window = Gtk3::Window->new('toplevel');
    $window->set_border_width(10);
    $window->set_title($title);
    $window->resize(400, 220);
    $window->set_type_hint('dialog');

    my $vbox = Gtk3::VBox->new;

    my $filename_label = Gtk3::Label->new($filename_label_str);
    $filename_label->set_xalign(0.0);
    $vbox->pack_start($filename_label, TRUE, TRUE, 0);
    my $filename_entry = Gtk3::Entry->new;
    $vbox->pack_start($filename_entry, TRUE, TRUE, 0);

    my $title_label = Gtk3::Label->new($title_label_str);
    $title_label->set_xalign(0.0);
    $vbox->pack_start($title_label, TRUE, TRUE, 0);
    my $title_entry = Gtk3::Entry->new;
    $vbox->pack_start($title_entry, TRUE, TRUE, 0);

    my $author_label = Gtk3::Label->new($author_label_str);
    $author_label->set_xalign(0.0);
    $vbox->pack_start($author_label, TRUE, TRUE, 0);
    my $author_entry = Gtk3::Entry->new;
    $vbox->pack_start($author_entry, TRUE, TRUE, 0);

    my $language_label = Gtk3::Label->new($language_label_str);
    $language_label->set_xalign(0.0);
    $vbox->pack_start($language_label, TRUE, TRUE, 0);
    my $language_entry = Gtk3::Entry->new;
    $vbox->pack_start($language_entry, TRUE, TRUE, 0);

    my $style_label = Gtk3::Label->new($style_label_str);
    $style_label->set_xalign(0.0);
    $vbox->pack_start($style_label, TRUE, TRUE, 0);
    my $style_list_store = Gtk3::ListStore->new('Glib::String');
    my $style_list = Gtk3::ComboBox->new_with_model($style_list_store);
    $vbox->pack_start($style_list, FALSE, TRUE, 0);
    
    $epub_gui_st->{'lang_entry'} = $language_entry;
    $epub_gui_st->{'author_entry'} = $author_entry;
    $epub_gui_st->{'title_entry'} = $title_entry;
    $epub_gui_st->{'style_entry'} = $style_list;
    $epub_gui_st->{'epub_filename_entry'} = $filename_entry;

    $epub_gui_st->{'auto_fill_lang'} = '';
    $epub_gui_st->{'auto_fill_author'} = '';
    $epub_gui_st->{'auto_fill_style'} = '';
    
    my $style_list_cell = Gtk3::CellRendererText->new();
    $style_list->pack_start($style_list_cell, FALSE);
    $style_list->add_attribute($style_list_cell, 'text', 0);

    read_auto_fill($config, $epub_gui_st);

    my $changed_settings = sub {
        read_settings($config);
        list_of_styles($config, $epub_gui_st, $style_list_store);
    };

    $vbox->pack_start(
        group_files_epub_dialog_button_row(
            $window, $config, $epub_gui_st,
            $changed_settings),
        FALSE, TRUE, 0);
    $window->add($vbox);

    $window->signal_connect(destroy => sub {
        Gtk3::main_quit();
    });
    $window->show_all();

    epub_filename_entry($epub_gui_st, $epub_gui_st->{epub_filename});
    $title_entry->set_text('');

    &$changed_settings();

    if ($epub_gui_st->{'auto_fill_lang'} ne '') {
        $language_entry->set_text($epub_gui_st->{'auto_fill_lang'});
    } else {
        $language_entry->set_text(get_default_language());
    }
    if ($epub_gui_st->{'auto_fill_author'} ne '') {
        $author_entry->set_text($epub_gui_st->{'auto_fill_author'});
    } else {
        $author_entry->set_text(get_default_author());
    }
    if ($epub_gui_st->{'auto_fill_style'} ne '') {
        my $style_active = -1;
        my @arr = @{$epub_gui_st->{styles_str_list}};
        for (my $i = 0; $i < @arr; ++ $i) {
            next if $arr[$i] eq '';
            if ($arr[$i] eq $epub_gui_st->{'auto_fill_style'}) {
                $style_active = $i;
                last;
            }
        }
        if ($style_active >= 0) {
            $style_list->set_active($style_active);
        }
    }

}

sub make_epub_filename ($) {
    my ($epub_gui_st) = @_;
    my @files = @{$epub_gui_st->{files}};
    my $dir = $epub_gui_st->{dir};
    for (my $i = 0; $i < @files; ++$i) {
        my $f0;
        if ($files[$i] =~ m/^\//) {
            $f0 = $files[$i];
        } else {
            $f0 = $dir . '/' . $files[$i];
        }
        if (-f $f0) {
            my $mdir = dirname($f0);
            my $base = basename($mdir);
            my $epub = $mdir . "/" . $base . ".epub";
            $epub_gui_st->{epub_filename} = $epub;
            return;
        }
    }
}

sub show_gui ($) {
    my ($args_ref) = @_;
    my @args = @{$args_ref};
    
    my $epub_gui_st = {
        'files' => [],
        'epub_filename' => '',
        'dir' => ''
    };

    my $dir = getcwd();
    for (my $i = 0; $i < @args; ++$i) {
        if ($args[$i] eq '--dir') {
            ++$i;
            my $use_dir = $args[$i];
            if (-d $use_dir) {
                $dir = $use_dir;
                $epub_gui_st->{dir} = $dir;
            }
            next;
        }
        if ($args[$i] =~ m/^--/) {
            ++$i;
            next;
        }
        my $f0;
        if ($args[$i] =~ m/^\//) {
            push @{$epub_gui_st->{files}}, $args[$i];
        } else {
            push @{$epub_gui_st->{files}}, $args[$i];
            $epub_gui_st->{dir} = $dir;
        }
    }

    if (@{$epub_gui_st->{files}} < 1) {
        my $msg_no_files = _("No files selected.");
        error_dialog(undef, $msg_no_files);
        exit 1;
    }

    my $config = {};
    make_epub_filename($epub_gui_st);
    group_files_epub_dialog($epub_gui_st, $config);
}

sub main () {
    if (@ARGV < 1) {
        my $msg_no_files = _("No files selected.");
        print STDERR $msg_no_files;
        exit 1;
    }
    my @args = @ARGV;

    if ((lc $args[0]) eq 'build') {
        shift @args;
        my $config = {};
        main_make_epub(\@args, $config);
        return;
    }

    show_gui(\@args);
    Gtk3::main;
}

main();



