import datetime
import sys

from rdflib import Graph, Namespace
from rdflib import URIRef
from rdflib.term import Literal
from rdflib.namespace import NamespaceManager, RDF, RDFS, OWL

#from wikidataintegrator import wdi_core, wdi_login
from python_wikibase import PyWikibase
from python_wikibase.utils.data_types import class_to_data_type

# Authenticate with Wikibase
py_wb = PyWikibase(config_path="config.json")

for x in range(int(sys.argv[1]), int(sys.argv[2])):
    iId = "Q" + str(x)
    try:
        item = py_wb.Item().get(entity_id=iId)
        print('Deleting ' + str(item.get().label) + ' | ' + str(item.get().entity_id))
        item.delete()
    except:
        print("No item " + iId)

    pId = "P" + str(x)
    try:
        property = py_wb.Property().get(entity_id=pId)
        print('Deleting ' + str(property.get().label) + ' | ' + str(property.get().entity_id))
        property.delete()
    except:
        print("No item " + pId)

print('End-----------------------------------------------------------')


#print(g.namespaces())

#for c in classes:
#    print(c)
#    item = py_wb.Item().create(c)

#py_wb.Item().create('Hello')

#prop = py_wb.Property().create("test2", data_type="Item")
#propGet1 = prop.get();
#propGet2 = py_wb.Property().get(entity_id="P1")

#print(propGet1)
#print('--------------------------------------------------------------')
#print(propGet2)

#print('--------------------------------------------------------------')

#itemA = py_wb.Item().get(entity_id="Q1")
#propA = py_wb.Property().get(entity_id="P1")
#valueItemA = py_wb.Item().get(entity_id="Q1")
#itemA.claims.add(propA, valueItemA)

#print('--------------------------------------------------------------')

#item = py_wb.Item().get(entity_id="Q1")
#claim_list = list(item.claims)
#or
#claim_list = item.claims.to_list()
#print(claim_list)
# Returns list of the following form:
# [<Claim>, <Claim>, <Claim>]

# Fetch item and "coordinate location" property
#item = py_wb.Item().get(entity_id="Q2")
#prop = py_wb.Property().get(entity_id="P1")

#Create new GeoLocation value
#value = py_wb.GeoLocation().create(1.23, 4.56)

#Create GeoLocation claim
#claim = item.claims.add(prop, value)
