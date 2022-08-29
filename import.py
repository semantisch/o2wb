### Import dependencies

import datetime
import sys

from rdflib import Graph, Namespace
from rdflib import URIRef
from rdflib.term import Literal
from rdflib.namespace import NamespaceManager, RDF, RDFS, OWL

from python_wikibase import PyWikibase
from python_wikibase.utils.data_types import class_to_data_type

# Authenticate with Wikibase
py_wb = PyWikibase(config_path="config.json")

# Initialize the rdflib Graph to store the contents of the ontology
g = Graph()

try:
    # Check whether ontology file path is specified when calling the script
    if(len(sys.argv) < 2):
        raise Exception()

    # Parse ontology files into one Graph
    ontArgs = sys.argv[1:]
    for oFile in ontArgs:
        g.parse(oFile) #'foaf.rdf'
except:
    print('Please, specify path to the ontology file that you want to import as argument to calling this script!')
    print('E.g. "python import.py pathTo/ontology.rdf"')
    quit()

classes = []
properties = []

URIdictionaty = {} #stores all encountered URIs
propDictionaty = {} #stores all encountered properties
itemDictionaty = {} #stores all encountered items

# Get all existing Wikibase datatypes
datatypesAll = class_to_data_type.keys()
datatypes = [e for e in datatypesAll if e not in ('Form','Lexeme','Math','Sense')]

# Get time to be used in naming the Item representing the imported ontology
timeNow = datetime.datetime.now().isoformat()

# Create an Item representing the imported ontology
ontologyName = "o2wb:importedOntology_" + timeNow
ontologyImportValue = py_wb.Item().create(ontologyName)

# Create an Item representing the imported ontology class
classImportValue = py_wb.Item().create("o2wb:Ontology")

# Create an Item for the class of blank node representations
blankNodeImportValue = py_wb.Item().create("o2wb:BlankNodeRepresentation")

# Create an Item for the class of IRI representations
IRINodeImportValue = py_wb.Item().create("o2wb:IRIRepresentation")

# Create the o2wb:typeOf Property
try:
    typeOfProperty = py_wb.Property().create("o2wb:typeOf", data_type='Item')
except:
    typeOfProperty = py_wb.Property().create("o2wb:typeOf_" + timeNow, data_type='Item')

# Create the o2wb:fromOntology Property
try:
    ontologyImportProperty = py_wb.Property().create("o2wb:fromOntology", data_type='Item')
except:
    ontologyImportProperty = py_wb.Property().create("o2wb:fromOntology_" + timeNow, data_type='Item')

# Create the o2wb:representsIRI Property
try:
    ontologyURIProperty = py_wb.Property().create("o2wb:representsIRI", data_type='Item')
except:
    ontologyURIProperty = py_wb.Property().create("o2wb:representsIRI_" + timeNow, data_type='Item')

# Print all imported namespaces (used to name Entities)
namespaces = {a:b for a,b in g.namespace_manager.namespaces()}
print(namespaces)

# Iterate over all triples to transform them into statements
for s, p, o in g:
    print(s, p, o)

    # Remember every unique property
    if(p.n3() not in propDictionaty):

        # Shorten URIS to their prefixed form if namespace is in the namespaces
        prefixedP = p
        for prefix, prefixURI in namespaces.items():
            prefixedP = prefixedP.replace(prefixURI, prefix + ":")

        # Cleate all property representations
        propDict = {} #stores all representations

        # Represent property as Item
        print("Creating Item " + prefixedP)
        try:
            propDict["Item"] = py_wb.Item().create(prefixedP)
        except:
            print("Exception: Creating Item " + prefixedP)

        # Represent property as Properties with different Datatypes
        for datatype in datatypes:
            newPropertyName = prefixedP + "_" + datatype
            print("Creating Property " + newPropertyName + " with datatype: " + datatype)
            try:
                propDict[datatype] = py_wb.Property().create(newPropertyName, data_type=datatype)
            except:
                newPropertyName = newPropertyName + "_" + timeNow
                print("Exception: Creating Property " + newPropertyName + " with datatype: " + datatype)
                propDict[datatype] = py_wb.Property().create(newPropertyName, data_type=datatype)

            propDict[datatype].claims.add(ontologyImportProperty, ontologyImportValue)
            propDict[datatype].claims.add(ontologyURIProperty, py_wb.StringValue().create( str(p) ))


        propDictionaty[p.n3()] = propDict
    else:
        print(p + ' is already in the dictionary')

    if(s.n3() not in itemDictionaty):

        # Shorten URIS to their prefixed form if namespace is in the namespaces
        prefixedS = s
        for prefix, prefixURI in namespaces.items():
            prefixedS = prefixedS.replace(prefixURI, prefix + ":")

        # Create Item representation
        print("Creating item " + prefixedS)
        wbItem = py_wb.Item().create(prefixedS)
        wbItem.claims.add(ontologyImportProperty, ontologyImportValue)
        wbItem.claims.add(ontologyURIProperty, py_wb.StringValue().create( str(s) ))

        itemDictionaty[s.n3()] = wbItem
    else:
        print(s + ' is already in the dictionary')
    if(o.n3() not in itemDictionaty):
        #print(o)
        #Check if literal and pass if true -> don't need to declare literals
        if( not( isinstance(o, Literal) ) ):
            # Shorten URIS to their prefixed form if namespace is in the namespaces
            prefixedO = o

            for prefix, prefixURI in namespaces.items():
                prefixedO = prefixedO.replace(prefixURI, prefix + ":")
                #print("prefixed: " + prefixedO)

            print("Creating item " + prefixedO)
            wbItem = py_wb.Item().create(prefixedO)
            wbItem.claims.add(ontologyImportProperty, ontologyImportValue)
            wbItem.claims.add(ontologyURIProperty, py_wb.StringValue().create( str(o) ))

            itemDictionaty[o.n3()] = wbItem
    else:
        print(o + ' is already in the dictionary')

    # Represent the triple as a Statement (Snak)
    item = itemDictionaty[s.n3()]
    prop = propDictionaty[p.n3()]
    if(isinstance(o, Literal)):
        value = py_wb.StringValue().create( o.n3() )
        prop = propDictionaty[p.n3()]['StringValue']
    elif(isinstance(o, URIRef)):
        value = itemDictionaty[o.n3()]
        prop = propDictionaty[p.n3()]['Item']

    item.claims.add(prop, value)
    #TODO: add qualifier that it was imported from an ontology

    #print(URIdictionaty) #URIs with corresponding items (for properties dict wiht all datatypes)
    #break

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
