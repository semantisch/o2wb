import datetime
import sys
import json
import time
import os
import time
import uuid
import argparse

from rdflib import Graph, Namespace
from rdflib import URIRef
from rdflib.term import Literal
from rdflib.term import BNode
from rdflib.namespace import NamespaceManager, RDF, RDFS, OWL

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.datatypes import BaseDataType
from wikibaseintegrator.datatypes  import CommonsMedia
from wikibaseintegrator.datatypes  import ExternalID
from wikibaseintegrator.datatypes  import Form
from wikibaseintegrator.datatypes  import GeoShape
from wikibaseintegrator.datatypes  import GlobeCoordinate
from wikibaseintegrator.datatypes  import Item
from wikibaseintegrator.datatypes  import Lexeme
from wikibaseintegrator.datatypes  import Math
from wikibaseintegrator.datatypes  import MonolingualText
from wikibaseintegrator.datatypes  import MusicalNotation
from wikibaseintegrator.datatypes  import Property
from wikibaseintegrator.datatypes  import Quantity
from wikibaseintegrator.datatypes  import Sense
from wikibaseintegrator.datatypes  import String
from wikibaseintegrator.datatypes  import TabularData
from wikibaseintegrator.datatypes  import Time
from wikibaseintegrator.datatypes  import URL
from wikibaseintegrator import datatypes
from wikibaseintegrator import wbi_helpers

def main():

    # Print iterations progress
    def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        if total != 0:
            percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
            filledLength = int(length * iteration // total)
            bar = fill * filledLength + '-' * (length - filledLength)
            print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
            # Print New Line on Complete
        if iteration == total:
            print()

        # Create the parser
        parser = argparse.ArgumentParser()
        # Add an argument
        parser.add_argument("-n", '--name', type=str, required=True)
        parser.add_argument("-f", '--file', type=str, required=False)
        parser.add_argument("-m", '--mapping', type=str, required=False)
        parser.add_argument("-c", '--config', type=str, required=True)
        # Parse the argument
        args = parser.parse_args()
        print(args)

        f = open(args.config)
        data = json.load(f)
        f.close()

    # Initial call to print 0% progress
    counter = 0
    printProgressBar(counter, 100, prefix = 'Progress:', suffix = 'Complete', length = 50)

    # Initialize WBI

    wbi_config['MEDIAWIKI_API_URL'] = data['MEDIAWIKI_API_URL']
    wbi_config['SPARQL_ENDPOINT_URL'] = data['SPARQL_ENDPOINT_URL']
    wbi_config['WIKIBASE_URL'] = data['WIKIBASE_URL']
    login_instance = wbi_login.Login(user=data['USER'], password=data['PASSWORD'])

    wbi = WikibaseIntegrator(login=login_instance)

    # Initialize the rdflib Graph to store the contents of the ontology

    g = Graph()

    try:
        # Check whether ontology file path is specified when calling the script
        if(len(sys.argv) < 3):
            raise Exception()

        # Parse ontology files into one Graph
        oFile = sys.argv[1]
        # g.parse(oFile, format="ttl")
        # g.parse(oFile)
        oName = sys.argv[2]
    except Exception as e:
        print(e)
        print('Please, specify path to the ontology file that you want to import and ontology name as arguments to calling this script!')
        print('E.g. "python import.py pathTo/ontology.rdf myOntology"')
        quit()

    # Get all existing Wikibase datatypes,
    # BaseDataType, Form, Lexeme, Math, MusicalNotation, Sense
    datatypesList = [BaseDataType, Form, Lexeme, Math, MusicalNotation, Sense, CommonsMedia, ExternalID, GeoShape, GlobeCoordinate, Item, MonolingualText, Property, Quantity, String, TabularData, Time, URL]
    # print(datatypesList)

    namespaces = {a:b for a,b in g.namespace_manager.namespaces()}
    namespaces['o2wb'] = URIRef('https://data.wu.ac.at/ns/o2wb#')
    BaseURL = "http://wikibase.svc/"
    namespaces['wb'] = URIRef(BaseURL+'entity/')
    namespaces['wbs'] = URIRef(BaseURL+'entity/statement/')
    namespaces['wbv'] = URIRef(BaseURL+'value')
    namespaces['wbt'] = URIRef(BaseURL+'prop/direct/')
    namespaces['wikibase'] = URIRef('http://wikiba.se/ontology#')
    namespaces['p'] = URIRef(BaseURL+'prop/direct/')
    namespaces['ps'] = URIRef(BaseURL+'prop/statement/')
    namespaces['pq'] = URIRef(BaseURL+'prop/qualifier/')

    def genFullURI(prefixedURI, prefixes): # Get a prefixed String and turn it into a full URIRef
        fullURI = prefixedURI
        for prefix, prefixURI in prefixes:
                    if(fullURI.startswith(prefix)):
                        fullURI = URIRef( fullURI.replace(prefix + ':', prefixURI) )
                        break
        return fullURI

    def genPrefixedURI(fullURI, prefixes): # Get a full URIRef and turn it into a prefixed String
        prefixedURI = str(fullURI)
        for prefix, prefixURI in prefixes:
                    if(prefixedURI.startswith(prefixURI)):
                        prefixedURI = prefixedURI.replace(prefixURI, prefix + ':')
                        break
        return prefixedURI

    def sparqlQuery(query): # SPARQL query
        responseJSON = wbi_helpers.execute_sparql_query(query,None,wbi_config['SPARQL_ENDPOINT_URL'],None, 10, 1)
        return responseJSON

    # Check meta-ontological elements:
    ontElements = {
        genFullURI("o2wb:typeOf", namespaces.items()):{"type":"property", "datatype":"wikibase-item", "label":"o2wb:typeOf", "repr":None, "reprID":None},
        genFullURI("o2wb:Ontology", namespaces.items()):{"type":"item", "label":"o2wb:Ontology", "repr":None, "reprID":None},
        genFullURI("o2wb:BlankNodeRepresentation", namespaces.items()):{"type":"item", "label":"o2wb:BlankNodeRepresentation", "repr":None, "reprID":None},
        genFullURI("o2wb:representsIRI", namespaces.items()):{"type":"property", "datatype":"url", "label":"o2wb:representsIRI", "repr":None, "reprID":None},
        genFullURI("o2wb:IRIRepresentation", namespaces.items()):{"type":"item", "label":"o2wb:IRIRepresentation", "repr":None, "reprID":None},
        genFullURI("o2wb:fromOntology", namespaces.items()):{"type":"property", "datatype":"wikibase-item", "label":"o2wb:fromOntology", "repr":None, "reprID":None},
    }

    def easyGetRepr(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["repr"]
    def easyGetReprID(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["reprID"]
    def easyGetReprDirect(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["repr"].replace(namespaces['wb'],namespaces['wbt'])

    # sparqlResponse = sparqlQuery('SELECT ?sLabel ?pLabel ?pqLabel ?oLabel WHERE {?s ?p [ <http://wikibase.svc/prop/qualifier/P7605> wd:Q901; ?pq ?o ]. SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }}')["results"]["bindings"]



    #
    for ontElement, elParams in ontElements.items():
        # print(ontElement)

        try:
            QorP = "Q"
            if(elParams["type"] == "property"):
                QorP = "P"
            sparqlResponse = sparqlQuery('SELECT ?s WHERE {?s <http://www.w3.org/2000/01/rdf-schema#label> "'+elParams["label"]+'"@en . FILTER regex( str(?s), "^'+str(namespaces['wb'])+QorP+'[0-9]+$", "i" ) }')["results"]["bindings"]
            if len(sparqlResponse) > 0:
                elParams["repr"] = URIRef(sparqlResponse[0]["s"]["value"])
                # print(elParams["repr"])
                elParams["reprID"] = str(elParams["repr"]).replace(str(namespaces['wb']), "")
                # print(elParams["reprID"])
            else:
                if(elParams["type"] == "property"):
                    property = wbi.property.new()
                    property.datatype = elParams["datatype"]
                    property.labels.set(language='en', value=elParams["label"])
                    newProperty = property.write()
                    elParams["repr"] =  URIRef(genFullURI("wb:", namespaces.items()) + str(newProperty.id))
                    elParams["reprID"] =  str(newProperty.id)
                    # print(elParams["repr"] + ' : ' + elParams["reprID"])
                else:
                    item = wbi.item.new()
                    item.labels.set(language='en', value=elParams["label"])
                    newItem = item.write()
                    elParams["repr"] =  URIRef(genFullURI("wb:", namespaces.items()) + str(newItem.id))
                    elParams["reprID"] =  str(newItem.id)
                    # print(elParams["repr"] + ' : ' + elParams["reprID"])
        except Exception as e:
            # raise
            print(e)


    sparqlResponse = sparqlQuery("""
        SELECT ?s ?wdt ?o
        WHERE {
            ?s ?wdt ?o .
            ?s ?p ?statement .
            ?statement ?ps ?o .
            ?statement prov:wasDerivedFrom ?refnode .
            ?refnode pr:"""+str(easyGetReprID("o2wb:fromOntology"))+""" ?ont .
            ?ont rdfs:label '"""+str(oName)+"""'@en.
        }
    """)["results"]["bindings"]

    print(sparqlResponse)

    # Initial call to print 0% progress
    printProgressBar(counter, len(sparqlResponse), prefix = 'Progress:', suffix = 'Complete', length = 50)

    triples = []

    for resp in sparqlResponse:
        triple = {}
        # print(resp["o"])
        # print(resp["s"]["value"]  + " : " + resp["wdt"]["value"] + " : " + resp["o"]["value"])

        elType = sparqlQuery("SELECT ?type WHERE {<"+resp["s"]["value"]+">  wdt:"+str(easyGetReprID("o2wb:typeOf"))+" ?type}")["results"]["bindings"][0]["type"]["value"]
        # print("--------------------" + elType +"----------------")
        # print("--------------------" + easyGetRepr("o2wb:IRIRepresentation") +"----------------")
        if elType == str(easyGetRepr("o2wb:IRIRepresentation")):
            elIRI = sparqlQuery("SELECT ?IRI WHERE {<"+resp["s"]["value"]+">  wdt:"+str(easyGetReprID("o2wb:representsIRI"))+" ?IRI}")["results"]["bindings"][0]["IRI"]["value"]
            triple["s"] = URIRef(elIRI)
        else:
            elBN = sparqlQuery("SELECT ?BN WHERE {<"+resp["s"]["value"]+">  rdfs:label ?BN}")["results"]["bindings"][0]["BN"]["value"]
            triple["s"] = BNode(elBN)
        # print(triple["s"])

        wbValue = resp["wdt"]["value"].replace(namespaces['wbt'],namespaces['wb'])
        el2IRI = sparqlQuery("SELECT ?IRI WHERE {<"+wbValue+">  wdt:"+str(easyGetReprID("o2wb:representsIRI"))+" ?IRI}")["results"]["bindings"][0]["IRI"]["value"]
        triple["p"] = URIRef(el2IRI)
        # print(triple["p"])

        if resp["o"]["type"] == "literal":
            triple["o"] = Literal(resp["o"]["value"])
        else:
            el3Type = sparqlQuery("SELECT ?type WHERE {<"+resp["o"]["value"]+">  wdt:"+str(easyGetReprID("o2wb:typeOf"))+" ?type}")["results"]["bindings"][0]["type"]["value"]
            if el3Type == str(easyGetRepr("o2wb:IRIRepresentation")):
                el3IRI = sparqlQuery("SELECT ?IRI WHERE {<"+resp["o"]["value"]+">  wdt:"+str(easyGetReprID("o2wb:representsIRI"))+" ?IRI}")["results"]["bindings"][0]["IRI"]["value"]
                triple["o"] = URIRef(el3IRI)
            else:
                el3BN = sparqlQuery("SELECT ?BN WHERE {<"+resp["o"]["value"]+">  rdfs:label ?BN}")["results"]["bindings"][0]["BN"]["value"]
                triple["o"] = BNode(el3BN)

        triples.append(triple)
        counter = counter + 1
        printProgressBar(counter, len(sparqlResponse), prefix = 'Progress:', suffix = 'Complete', length = 50)
        # print(triple)

    for triple in triples:
        g.add((triple["s"], triple["p"], triple["o"]))
        # print(triple)

    # print(g.serialize(format='ttl'))
    formatExt = os.path.splitext(oFile)[1]
    formatExt = formatExt.replace('.','')

    try:
        if formatExt.lower() == 'owl':
            formatExt = 'pretty-xml'
        g.serialize(destination=oFile, format=formatExt)
    except Exception as e:
        print(e)
        print('Undefined export serialization, defaulting to TTL.')
        g.serialize(destination=oFile, format='ttl')
