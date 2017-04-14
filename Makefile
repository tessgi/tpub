update:
	git pull
	tpub-update

push:
	tpub-export > data/tpub-export.csv
	git add data/tpub.db data/tpub-export.csv
	git commit -m "Regular db update"
	git push

refresh:
	# Update the metadata by re-fetching all entries from the ADS API
	# this will e.g. update the citation counts and bibcodes
	tpub-export > data/tpub-export.csv
	rm data/tpub.db
	tpub-import data/tpub-export.csv

