import datetime
import sys
import time
import re
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
from wikibaseintegrator.wbi_enums import ActionIfExists


def main():
    # Print iterations progress
    def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total:
            print()

    # Initialize WBI
    # Create the parser
    parser = argparse.ArgumentParser()
    # Add an argument
    parser.add_argument("-n", '--name', type=str, required=True)
    parser.add_argument("-u", '--url', type=str, required=False)
    parser.add_argument("-f", '--file', type=str, required=False)
    parser.add_argument("-r", '--recursive', type=str, required=False)
    parser.add_argument("-m", '--mapping', type=str, required=False)
    parser.add_argument("-c", '--config', type=str, required=True)
    # Parse the argument
    args = parser.parse_args()
    print(args)

    f = open(args.config)
    data = json.load(f)
    f.close()
    if args.url == None and args.file == None:
         raise Exception("Neither URL nor File defined.")

    # wbi_config['MEDIAWIKI_API_URL'] = 'http://localhost:80/w/api.php'
    # wbi_config['SPARQL_ENDPOINT_URL'] = 'http://localhost:8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    # wbi_config['WIKIBASE_URL'] = 'http://localhost:80'
    # login_instance = wbi_login.Login(user='Admin@Bot1', password='pbus363dbliksejsmm559s74dbf8ae2v')

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
        oFile = args.file
        # g.parse(oFile, format="ttl")
        g.parse(oFile)
        oName = args.name
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
    # namespaces['pq'] = URIRef('https://data.wu.ac.at/ns/o2wb#')

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
        # genFullURI("o2wb:UUID", namespaces.items()):{"type":"property", "datatype":"string", "label":"o2wb:UUID", "repr":None, "reprID":None},
    }

    for ontElement, elParams in ontElements.items():
        # print(ontElement)
        # Check existance:

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

    def easyGetRepr(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["repr"]
    def easyGetReprID(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["reprID"]
    def easyGetReprDirect(prefixedOntForm):
        return ontElements[genFullURI(prefixedOntForm, namespaces.items())]["repr"].replace(namespaces['wb'],namespaces['wbt'])

    # Check ontology existance & create
    sparqlResponses = sparqlQuery('SELECT * WHERE {?ont <http://www.w3.org/2000/01/rdf-schema#label> "'+oName+'"@en ; <'+str(easyGetReprDirect("o2wb:typeOf"))+'> <'+str(easyGetRepr("o2wb:Ontology"))+'> . }')["results"]["bindings"]
    # for response in sparqlResponses:
    #     print(response)
    if len(sparqlResponses) > 0:
        print('Ontology with this name already exists. Choose another name.')
        quit()
    else:
        # print('Creating the ontology ' + oName)
        item = wbi.item.new()
        item.labels.set(language='en', value=oName)
        data = Item(value=easyGetReprID("o2wb:Ontology"), prop_nr=easyGetReprID("o2wb:typeOf"))
        item.claims.add(data, action_if_exists=ActionIfExists.FORCE_APPEND)
        newItem = item.write()
        # print(newItem)
        newItemURI =  URIRef(genFullURI("wb:", namespaces.items()) + newItem.id)
        ontElements[oName] = {"type":"item", "label":oName, "repr":newItemURI, "reprID":newItem.id}
        # print(ontElements[oName])

    # Create representation


    mapping = {}

    def coinProp(el, dt, label):
        property = wbi.property.new()
        property.datatype = dt.DTYPE
        property.labels.set( value=label)
        dataIRIRepr = Item(value=easyGetReprID("o2wb:IRIRepresentation"), prop_nr=easyGetReprID("o2wb:typeOf"))
        property.claims.add(dataIRIRepr, action_if_exists=ActionIfExists.FORCE_APPEND)
        dataIRI = URL(value=str(el), prop_nr=easyGetReprID("o2wb:representsIRI"))
        property.claims.add(dataIRI, action_if_exists=ActionIfExists.FORCE_APPEND)
        newProperty = property.write()
        dictEl = {}
        dictEl["repr"] =  URIRef(genFullURI("wb:", namespaces.items()) + str(newProperty.id))
        dictEl["reprID"] =  str(newProperty.id)
        # dictEl["prop"] = newProperty

        return dictEl

    datatypesList.remove(BaseDataType)
    datatypesList.remove(Form)
    datatypesList.remove(Lexeme)
    datatypesList.remove(Math)
    datatypesList.remove(MusicalNotation)
    datatypesList.remove(Sense)

    triples = 0
    for s, p, o in g:
        triples = triples + 1
    counter = 0
    # Initial call to print 0% progress
    printProgressBar(counter, triples, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for s, p, o in g:
        for el in [s,p,o]:

            if((isinstance(el, URIRef) or isinstance(el, BNode)) and not el in mapping):

                try:
                    mapping[el] = {}
                    # Create all mappings:
                    # Item:
                    item = wbi.item.new()
                    item.labels.set(language='en', value=genPrefixedURI(el, namespaces.items()))
                    # data = Item(value=easyGetReprID("o2wb:Ontology"), prop_nr=easyGetReprID("o2wb:typeOf"))
                    # item.claims.add(data)
                    if(isinstance(el, BNode)):
                        dataBNodeRepr = Item(value=easyGetReprID("o2wb:BlankNodeRepresentation"), prop_nr=easyGetReprID("o2wb:typeOf"))
                        item.claims.add(dataBNodeRepr, action_if_exists=ActionIfExists.FORCE_APPEND)
                    elif(isinstance(el, URIRef)):
                        dataIRIRepr = Item(value=easyGetReprID("o2wb:IRIRepresentation"), prop_nr=easyGetReprID("o2wb:typeOf"))
                        item.claims.add(dataIRIRepr, action_if_exists=ActionIfExists.FORCE_APPEND)
                        dataIRI = URL(value=str(el), prop_nr=easyGetReprID("o2wb:representsIRI"))
                        item.claims.add(dataIRI, action_if_exists=ActionIfExists.FORCE_APPEND)

                    newItem = item.write()
                    mapping[el]["Item"] = {}
                    mapping[el]["Item"]["repr"] =  URIRef(genFullURI("wb:", namespaces.items()) + str(newItem.id))
                    mapping[el]["Item"]["reprID"] =  str(newItem.id)
                except Exception as e:
                    raise

                try:
                    if(not isinstance(el, BNode)):
                        for dt in datatypesList:
                            result = None
                            # i = 0
                            # nameQualifier = ""
                            nameQualifier = "_" + str(uuid.uuid4())
                            while result is None:
                                try:
                                    result = coinProp(el, dt, genPrefixedURI(el, namespaces.items()) + "_" + dt.DTYPE + nameQualifier)
                                except Exception as e:
                                    raise
                                    # BaseDataType, Form, Lexeme, Math, MusicalNotation, Sense,
                                    # print(e)
                                    # i = i + 1
                                    # nameQualifier = "_" + str(i)

                            mapping[el][dt.DTYPE] = result
                except Exception as e:
                    raise

                # print("Created: " + str(el))

        try:
            # for a in mapping.items():
            #     print(a)
            # time.sleep(10)

            it = wbi.item.get(entity_id=mapping[s]["Item"]["reprID"])
            if(isinstance(o, URIRef) or isinstance(o, BNode)):
                dat = Item(value=mapping[o]["Item"]["reprID"], prop_nr=mapping[p]["wikibase-item"]["reprID"])
            elif(isinstance(o, Literal)):
                dat = String(value=str(o), prop_nr=mapping[p]["string"]["reprID"])

            dat.references.add(reference=Item(value=ontElements[oName]["reprID"],prop_nr=easyGetReprID("o2wb:fromOntology")))
            # dat.qualifiers.add(qualifier=String(value=str(uuid.uuid4()),prop_nr=easyGetReprID("o2wb:UUID")))
            it.claims.add(dat, action_if_exists=ActionIfExists.FORCE_APPEND)
            # print(dat)
            newIt= it.write()

            counter = counter + 1
            printProgressBar(counter, triples, prefix = 'Progress:', suffix = 'Complete', length = 50)

        except Exception as e:
            raise
