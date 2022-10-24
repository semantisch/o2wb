### Import dependencies

import datetime
import json
import sys

from rdflib import Graph, Namespace
from rdflib import URIRef
from rdflib.term import Literal
from rdflib.namespace import NamespaceManager, RDF, RDFS, OWL

from python_wikibase import PyWikibase
from python_wikibase.utils.data_types import class_to_data_type

import tkinter
from tkinter import filedialog
from tkinter.filedialog import askopenfile

import threading
from subprocess import Popen, PIPE
from time import sleep
import tkinter as tk
from tkinter import *


def uniPrint(text, text_box):
    text_box.insert("1.0", str(text) + "\n")
    print(text)

def importOnt(configPath, text_box, ontPath):
    # Authenticate with Wikibase

    try:
        py_wb = PyWikibase(config_path=configPath)

        # Initialize the rdflib Graph to store the contents of the ontology
        g = Graph()

        try:
            # Check whether ontology file path is specified when calling the script
            #if(len(sys.argv) < 2):
            #    raise Exception()

            # Parse ontology files into one Graph
            #ontArgs = sys.argv[1:]
            #for oFile in ontArgs:
            #    g.parse(oFile) #'foaf.rdf'
            g.parse(ontPath)
        except:
            uniPrint('Please, specify path to the ontology file that you want to import as argument to calling this script!', text_box)
            uniPrint('E.g. "python import.py pathTo/ontology.rdf"', text_box)
            #quit()

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
                #print("Creating Item " + prefixedP)
                uniPrint("Creating Item " + prefixedP, text_box)
                try:
                    propDict["Item"] = py_wb.Item().create(prefixedP)
                except:
                    #print("Exception: Creating Item " + prefixedP)
                    uniPrint("Exception: Creating Item " + prefixedP, text_box)

                # Represent property as Properties with different Datatypes
                for datatype in datatypes:
                    newPropertyName = prefixedP + "_" + datatype
                    #print("Creating Property " + newPropertyName + " with datatype: " + datatype)
                    uniPrint("Creating Property " + newPropertyName + " with datatype: " + datatype, text_box)
                    try:
                        propDict[datatype] = py_wb.Property().create(newPropertyName, data_type=datatype)
                    except:
                        newPropertyName = newPropertyName + "_" + timeNow
                        #print("Exception: Creating Property " + newPropertyName + " with datatype: " + datatype)
                        uniPrint("Exception: Creating Property " + newPropertyName + " with datatype: " + datatype, text_box)
                        propDict[datatype] = py_wb.Property().create(newPropertyName, data_type=datatype)

                    propDict[datatype].claims.add(ontologyImportProperty, ontologyImportValue)
                    propDict[datatype].claims.add(ontologyURIProperty, py_wb.StringValue().create( str(p) ))


                propDictionaty[p.n3()] = propDict
            else:
                #print(p + ' is already in the dictionary')
                uniPrint(p + ' is already in the dictionary', text_box)

            if(s.n3() not in itemDictionaty):

                # Shorten URIS to their prefixed form if namespace is in the namespaces
                prefixedS = s
                for prefix, prefixURI in namespaces.items():
                    prefixedS = prefixedS.replace(prefixURI, prefix + ":")

                # Create Item representation
                #print("Creating item " + prefixedS)
                uniPrint("Creating item " + prefixedS, text_box)
                wbItem = py_wb.Item().create(prefixedS)
                wbItem.claims.add(ontologyImportProperty, ontologyImportValue)
                wbItem.claims.add(ontologyURIProperty, py_wb.StringValue().create( str(s) ))

                itemDictionaty[s.n3()] = wbItem
            else:
                #print(s + ' is already in the dictionary')
                uniPrint(s + ' is already in the dictionary', text_box)

            if(o.n3() not in itemDictionaty):
                #print(o)
                #Check if literal and pass if true -> don't need to declare literals
                if( not( isinstance(o, Literal) ) ):
                    # Shorten URIS to their prefixed form if namespace is in the namespaces
                    prefixedO = o

                    for prefix, prefixURI in namespaces.items():
                        prefixedO = prefixedO.replace(prefixURI, prefix + ":")
                        #print("prefixed: " + prefixedO)

                    #print("Creating item " + prefixedO)
                    uniPrint("Creating item " + prefixedO, text_box)
                    wbItem = py_wb.Item().create(prefixedO)
                    wbItem.claims.add(ontologyImportProperty, ontologyImportValue)
                    wbItem.claims.add(ontologyURIProperty, py_wb.StringValue().create( str(o) ))

                    itemDictionaty[o.n3()] = wbItem
            else:
                #print(o + ' is already in the dictionary')
                uniPrint(o + ' is already in the dictionary', text_box)

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

        uniPrint('Import complete.', text_box)
    except Exception as e:
        uniPrint(e, text_box)

#Create an instance of Tkinter frame
win= tkinter.Tk()


#Set the geometry of Tkinter frame
win.geometry("1200x750")
win.title('O2WB Ontology Import')

def startImport():
   config1 = {
     "apiUrl": entry1.get(),
     "loginCredentials": {
       "botUsername": entry2.get(),
       "botPassword": entry3.get()
     }
   }
   with open('config.json','w') as f:
       f.write(json.dumps(config1))

   importOnt('config.json', text_box, b1.cget('text'))

#Initialize a Label and Entry to display the User Input
label1=tkinter.Label(win, text="Wikibase API URL")
label1.pack(pady=20)

entry1=tkinter.Entry(win, width= 40)
entry1.insert(0, 'http://localhost/w/api.php')
entry1.pack()

#Initialize a Label and Entry to display the User Input
label2=tkinter.Label(win, text="Bot username")
label2.pack(pady=20)

entry2=tkinter.Entry(win, width= 40)
entry2.pack()

#Initialize a Label and Entry to display the User Input
label3=tkinter.Label(win, text="Bot password")
label3.pack(pady=20)

entry3=tkinter.Entry(win, width= 40)
entry3.pack()

#filename = "ontologies/test/ontology.rdf"
def upload_file():
    f_types = [('RDF Files', '*.rdf')]
    filename = filedialog.askopenfilename(filetypes=f_types, title="Upload the ontology file")
    b1.configure(text=filename)

#Initialize a Label and Entry to display the User Input
b1 = tkinter.Button(win, text='Upload the ontology file',
    width=20,command = lambda:upload_file())
b1.pack(pady=40)

#Create a Button to validate Entry Widget
tkinter.Button(win, text= "Import ontology!",width= 20, command= startImport).pack(pady=20)

text_box = tkinter.Text(win, width = 40, height=3)
text_box.pack(pady=20)

win.mainloop()
