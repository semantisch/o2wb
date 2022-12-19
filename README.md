# O2WB

O2WB, a novel tool that enables ontology import into Wikibase.

## Install from PyPI with a package manager

3. Install o2wb through package manager:

pip3 install o2wb

or

## Clone the git repository

3. Alternatively, you can clone this repository to your machine
4. Navigate to the root directory and install the required packages from requirements.txt

## Setting up O2WB

5. Create a new Wikibase bot with permissions related to page editing:

- High-volume editing, 
- Edit existing pages,
- Create, edit, and move pages

6. Copy config.json and replace details and passwords with your own.

## Import an ontology 

7. To import an ontology by running:

o2wb-imp {--url <URL of your ontology> | --file <path to ontology file>} 
--name <ontology name> [--recursive <Depth of recursive imports>] 
[--mapping <path to export the mapping scheme>]

or

python3 import.py {--url <URL of your ontology> | --file <path to ontology file>} 
--name <ontology name> [--recursive <Depth of recursive imports>] 
[--mapping <path to export the mapping scheme>]

in case of a manual installation.

## Export an ontology

8. To export an ontology, run:

o2wb-exp --file <path to ontology file> --name <ontology name> 
[--mapping <path to export the mapping scheme>]

or

python3 export.py --file <path to ontology file> --name <ontology name> 
[--mapping <path to export the mapping scheme>]

in case of the manual installation.

## Other notes

- You can follow the import process through the "Last updates" Special Page
