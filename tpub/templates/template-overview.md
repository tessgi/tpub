Title: Publications
Save_as: publications.html

[TOC]

We request that scientific publications using data obtained from the TESS project include one of the following acknowledgments:

*This paper includes data collected by the TESS mission. Funding for
the TESS mission is provided by the NASA's Science Mission Directorate.*

## Publication database

The TESS Science Support Center curates a list of scientific publications
pertaining to TESS.
The database contains {{ metrics["publication_count"] }} publications,
of which {{ metrics["refereed_count"] }} are peer-reviewed.
It demonstrates the important impact of TESS data
on astronomical research.

You can access the full publication list:

 * [TESS publications >>](tpub.html)

Or seach by topic:

 * [Exoplanet publications >>](tpub-exoplanets.html)
 * [Astrophysics publications >>](tpub-astrophysics.html)

If you spot an error in the database, such as a missing entry,
please get in touch or open an issue in the <a href="https://github.com/tessgi/tpub">GitHub repository</a> of the database.

Last update: {{ now.strftime('%d %b %Y') }}.

<hr/>

## Breakdown by year & mission

The graph below shows the number of publications as a function
of year.

![Publication rate by year](images/tpub/tpub-publication-rate.png)

<hr/>

## Breakdown by subject

Both TESS data have been used for scientific applications
that reach far beyond exoplanet research.
While {{ metrics["exoplanets_count"] }} works relate to exoplanets
({{ "%.0f"|format(metrics["exoplanets_fraction"]*100) }}%),
a total of {{ metrics["astrophysics_count"] }}
pertain to other areas of astrophysics
({{ "%.0f"|format(metrics["astrophysics_fraction"]*100) }}%).


![Publications by subject](images/tpub/tpub-piechart.png)

<hr/>

## Most-cited publications

TESS publications have cumulatively been cited
{{ metrics["citation_count"] }} times.
The list below shows the most-cited publications,
based on the citation count obtained from NASA ADS.

{% for art in most_cited %}
{{loop.index}}. {{art['title'][0].upper()}}  
{{ ', '.join(art['author'][0:3]) }}{% if art['author']|length > 3 %}, et al.{% endif %}    
{{ '[{bibcode}](http://adsabs.harvard.edu/abs/{bibcode})'.format(**art) }}
<span class="badge">{{ art['citation_count'] }} citations</span>
{% endfor -%}

<hr/>

<!-- 
## Most-read publications

The read count shown below is obtained from the ADS API
and indicates the number of times the article has been downloaded
within the last 90 days.

{% for art in most_read %}
{{loop.index}}. {{art['title'][0].upper()}}  
{{ ', '.join(art['author'][0:3]) }}{% if art['author']|length > 3 %}, et al.{% endif %}    
{{ '[{bibcode}](http://adsabs.harvard.edu/abs/{bibcode})'.format(**art) }}
<span class="badge">{{ "%.0f"|format(art['read_count']) }} reads</span>
{% endfor -%}

<hr/>

-->

<!-- ## Most-active authors

The entries in the publication database have been authored and co-authored
by a total of {{ metrics["author_count"] }} unique author names.
Here we list the most-active authors, defined as those with six or more first-author publications in our database.

{% for author in most_active_first_authors %}
 * {{author[0]}} ({{ "%.0f"|format(author[1]) }} publications)
{% endfor -%} -->
