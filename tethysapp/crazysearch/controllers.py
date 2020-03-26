import xmltodict
import logging
import sys
import os
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.conf import settings

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import mapper
from .model import Base, Catalog, HISCatalog, Groups, HydroServer_Individual


from tethys_sdk.gizmos import TimeSeries, SelectInput, DatePicker, TextInput, GoogleMapView
from .model import Catalog, HISCatalog
from .auxiliary import *

import xml.etree.ElementTree as ET
import psycopg2
from owslib.waterml.wml11 import WaterML_1_1 as wml11
from suds.client import Client  # For parsing WaterML/XML
from json import dumps, loads
from pyproj import Proj, transform  # Reprojecting/Transforming coordinates
from datetime import datetime





from django.http import JsonResponse, HttpResponse


Persistent_Store_Name = 'catalog_db'

logging.getLogger('suds.client').setLevel(logging.CRITICAL)

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}
    # readSoap(request)
    return render(request, 'crazysearch/home.html', context)


def readSoap(request):
    "This function is for testing purposes in the Dominican Republic soap endpoint",
    soap_url="http://128.187.106.131/app/index.php/dr/services/cuahsi_1_1.asmx?WSDL"
    client=Client(soap_url)
    # print(client)
    client.set_options(port='WaterOneFlow')
    # site_info=client.service.GetSiteInfo("LOS JENGIBRES")
    # print(site_info)


def get_his_server(request):
    server = {}
    if request.is_ajax() and request.method == 'POST':
        url = request.POST['select_server']
        server['url'] = url
    return JsonResponse(server)

def his(request):
    list_catalog = {}
    hs_list = []
    error_list = []
    logging.getLogger('suds.client').setLevel(logging.CRITICAL)
    his_url = "http://hiscentral.cuahsi.org/webservices/hiscentral.asmx?WSDL"
    client = Client(his_url)
    searchable_concepts = client.service.GetSearchableConcepts()
    service_info = client.service.GetWaterOneFlowServiceInfo()
    # print service_info.ServiceInfo[0].servURL
    services = service_info.ServiceInfo
    for i in services:
        hs = {}
        url = i.servURL
        try:
            print("Testing %s" % (url))
            url_client = Client(url)
            hs['url'] = url
            hs_list.append(hs)
            print("%s Works" % (url))
        except Exception as e:
            print(e)
            hs['url'] = url
            print("%s Failed" % (url))
            error_list.append(hs)
        list_catalog['servers'] = hs_list
        list_catalog['errors'] = error_list

    context = {"hs_list": hs_list, "error_list": error_list}

    return render(request, 'crazysearch/his.html', context)

def soap(request):
    print("inside SOAP function")
    return_obj = {}
    if request.is_ajax() and request.method == 'POST':
        print("inside first if statement of SOAP function")
        url = request.POST.get('soap-url')
        title = request.POST.get('soap-title')
        title = title.replace(" ", "")
        # Getting the current map extent
        true_extent = request.POST.get('extent')

        client = Client(url)
        # True Extent is on and necessary if the user is trying to add USGS or
        # some of the bigger HydroServers.
        if true_extent == 'on':
            extent_value = request.POST['extent_val']
            return_obj['zoom'] = 'true'
            return_obj['level'] = extent_value
            ext_list = extent_value.split(',')
            # Reprojecting the coordinates from 3857 to 4326 using pyproj
            inProj = Proj(init='epsg:3857')
            outProj = Proj(init='epsg:4326')
            minx, miny = ext_list[0], ext_list[1]
            maxx, maxy = ext_list[2], ext_list[3]
            x1, y1 = transform(inProj, outProj, minx, miny)
            x2, y2 = transform(inProj, outProj, maxx, maxy)
            bbox = client.service.GetSitesByBoxObject(
                x1, y1, x2, y2, '1', '')
            # Get Sites by bounding box using suds
            # Creating a sites object from the endpoint. This site object will
            # be used to generate the geoserver layer. See utilities.py.
            wml_sites = parseWML(bbox)

            sites_parsed_json = json.dumps(wml_sites)

            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['siteInfo'] = sites_parsed_json
            return_obj['status'] = "true"

            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = Catalog(title=title,
                             url=url,
                             siteinfo=sites_parsed_json)  # Adding the HydroServer geosever layer metadata to the local database
            session.add(hs_one)
            session.commit()
            session.close()

        else:
            return_obj['zoom'] = 'false'
            # Get a list of all the sites and their respective lat lon.
            sites = client.service.GetSites('[:]')
            print("this are the sites")
            # print(sites)
            sites_dict = xmltodict.parse(sites)
            sites_json_object = json.dumps(sites_dict)

            sites_json = json.loads(sites_json_object)
            # Parsing the sites and creating a sites object. See utilities.py
            print("-------------------------------------")
            # print(sites_json)
            sites_object = parseJSON(sites_json)
            print(sites_object)
            # converted_sites_object=[x['sitename'].decode("UTF-8") for x in sites_object]

            # sites_parsed_json = json.dumps(converted_sites_object)
            sites_parsed_json = json.dumps(sites_object)


            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['siteInfo'] = sites_parsed_json
            return_obj['status'] = "true"
            # print("this is the return on=bject")
            # print(return_obj)
            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = Catalog(title=title,
                             url=url,
                             siteinfo=sites_parsed_json)
            session.add(hs_one)
            session.commit()
            session.close()

    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'

    return JsonResponse(return_obj)

# Retrieve all the list of Hydroservers that have been added to the dataBase..
def catalog(request):
    list_catalog = {}
    print("catalogs controllers.py FUNCTION inside")

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    # print("------------------------------------------")
    # print(Persistent_Store_Name)
    print(SessionMaker)
    session = SessionMaker()  # Initiate a session
    # conn = psycopg2.connect("dbname='catalog_db' user='tethys_super' host='localhost' port='5436' password='pass'")
    # cur = conn.cursor()
    # cur.execute("select * from information_schema.tables where table_name=%s", ('mytable',))
    # print("this is the value")
    # print(bool(cur.rowcount))

    # Query DB for hydroservers
    hydroservers = session.query(Catalog).all()
    print(hydroservers)

    hs_list = []
    for server in hydroservers:
        layer_obj = {}
        layer_obj["title"] = server.title
        layer_obj["url"] = server.url.strip()
        layer_obj["siteInfo"] = server.siteinfo

        hs_list.append(layer_obj)
    # A json list object with the HydroServer metadata. This object will be
    # used to add layers to the catalog table on the homepage.
    list_catalog["hydroserver"] = hs_list

    return JsonResponse(list_catalog)

def delete(request):

    list_catalog = {}

    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()

    # Query DB for hydroservers
    print(request.POST)
    if request.is_ajax() and request.method == 'POST':
        print(type(request.POST))
        print(request.POST.getlist('server'))
        titles=request.POST.getlist('server')
        print(type(titles))
        # title = request.POST['server']
        i=0;
        for title in titles:
            hydroservers = session.query(Catalog).filter(Catalog.title == title).delete(
                synchronize_session='evaluate')  # Deleting the record from the local catalog
            session.commit()
            session.close()

            # Returning the deleted title. To let the user know that the particular
            # title is deleted.
            i_string=str(i);
            # list["title"] = title
            list_catalog[i_string] = title
            i=i+1
    return JsonResponse(list_catalog)

def add_central(request):

    return_obj = {}
    print("function add_central")
    if request.is_ajax() and request.method == 'POST':
        print("here in if statemetn")
        url = request.POST['url']
        title = request.POST['title']

        if url.endswith('/'):
            url = url[:-1]

        if(checkCentral(url)):
            return_obj['message'] = 'Valid HIS Central Found'
            return_obj['status'] = True
            # Add to the database

            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = HISCatalog(title=title, url=url)
            session.add(hs_one)
            session.commit()
            session.close()
        else:
            return_obj['message'] = 'Not a valid HIS Central Catalog'
            return_obj['status'] = False
    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'
        return_obj['status'] = False

    return JsonResponse(return_obj)

######*****************************************************************************************################
######***********************CREATE AN EMPTY GROUP OF HYDROSERVERS ****************************################
######*****************************************************************************************################
def create_group(request):
    group_obj={}
    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()  # Initiate a session

    # Query DB for hydroservers

    # print(request.POST)
    if request.is_ajax() and request.method == 'POST':
        print("inside first if statement of create group")
        description = request.POST.get('textarea')

        # print(description)
        title = request.POST.get('addGroup-title')
        group_obj['title']=title
        group_obj['description']=description
        group_hydroservers=Groups(title=title, description=description)
        session.add(group_hydroservers)
        session.commit()
        session.close()

    else:
        group_obj[
            'message'] = 'There was an error while adding th group.'


    return JsonResponse(group_obj)

######*****************************************************************************************################
######************RETRIEVES THE GROUPS OF HYDROSERVERS THAT WERE CREATED BY THE USER **********################
######*****************************************************************************************################

def get_groups_list(request):
    list_catalog = {}
    print("get_groups_list controllers.py FUNCTION inside")

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    print(SessionMaker)
    session = SessionMaker()  # Initiate a session


    # Query DB for hydroservers
    hydroservers_groups = session.query(Groups).all()

    hydroserver_groups_list = []
    for group in hydroservers_groups:
        layer_obj = {}
        layer_obj["title"] = group.title
        layer_obj["description"] = group.description

        hydroserver_groups_list.append(layer_obj)
    # A json list object with the HydroServer metadata. This object will be
    # used to add layers to the catalog table on the homepage.
    list_catalog["hydroservers"] = hydroserver_groups_list
    print("----------------------------------------------")
    print("----------------------------------------------")
    print("----------------------------------------------")
    print(list_catalog)
    print("----------------------------------------------")
    print("----------------------------------------------")
    print("----------------------------------------------")
    list2={}
    array_example=[]
    for server in session.query(HydroServer_Individual).all():
        layer_obj = {}
        layer_obj["title"] = server.title
        layer_obj["url"] = server.url
        array_example.append(layer_obj)

    list2["servers"] =array_example
    print(list2)

    return JsonResponse(list_catalog)


######*****************************************************************************************################
######**ADD A HYDROSERVER TO THE SELECTED GROUP OF HYDROSERVERS THAT WERE CREATED BY THE USER *################
######*****************************************************************************************################


def soap_group(request):
    print("inside SOAP function")
    return_obj = {}
    if request.is_ajax() and request.method == 'POST':
        print("inside first if statement of SOAP function")
        url = request.POST.get('soap-url')
        print(url)
        title = request.POST.get('soap-title')
        title = title.replace(" ", "")
        print(title)
        group = request.POST.get('actual-group')
        print(group)
        # Getting the current map extent
        true_extent = request.POST.get('extent')

        client = Client(url)
        # True Extent is on and necessary if the user is trying to add USGS or
        # some of the bigger HydroServers.
        if true_extent == 'on':
            extent_value = request.POST['extent_val']
            return_obj['zoom'] = 'true'
            return_obj['level'] = extent_value
            ext_list = extent_value.split(',')
            # Reprojecting the coordinates from 3857 to 4326 using pyproj
            inProj = Proj(init='epsg:3857')
            outProj = Proj(init='epsg:4326')
            minx, miny = ext_list[0], ext_list[1]
            maxx, maxy = ext_list[2], ext_list[3]
            x1, y1 = transform(inProj, outProj, minx, miny)
            x2, y2 = transform(inProj, outProj, maxx, maxy)
            bbox = client.service.GetSitesByBoxObject(
                x1, y1, x2, y2, '1', '')
            # Get Sites by bounding box using suds
            # Creating a sites object from the endpoint. This site object will
            # be used to generate the geoserver layer. See utilities.py.
            wml_sites = parseWML(bbox)

            sites_parsed_json = json.dumps(wml_sites)

            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['siteInfo'] = sites_parsed_json
            return_obj['group']= group
            return_obj['status'] = "true"

            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = Catalog(title=title,
                             url=url,
                             siteinfo=sites_parsed_json)  # Adding the HydroServer geosever layer metadata to the local database
            session.add(hs_one)
            session.commit()
            session.close()

        else:
            return_obj['zoom'] = 'false'
            # Get a list of all the sites and their respective lat lon.
            sites = client.service.GetSites('[:]')
            print("this are the sites")
            # print(sites)
            sites_dict = xmltodict.parse(sites)
            sites_json_object = json.dumps(sites_dict)

            sites_json = json.loads(sites_json_object)
            # Parsing the sites and creating a sites object. See utilities.py
            print("-------------------------------------")
            # print(sites_json)
            sites_object = parseJSON(sites_json)
            # print(sites_object)
            # converted_sites_object=[x['sitename'].decode("UTF-8") for x in sites_object]

            # sites_parsed_json = json.dumps(converted_sites_object)
            sites_parsed_json = json.dumps(sites_object)


            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['siteInfo'] = sites_parsed_json
            return_obj['group'] = group
            return_obj['status'] = "true"
            # print("this is the return on=bject")
            # print(return_obj)
            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            # hydroservers_groups = session.query(Groups).all()
            # for hydro_group in hydroservers_groups:
            #     if hydro_group.title ==group:
            #         print(hydro_group)
            # print(hydroservers_group)
            hydroservers_group = session.query(Groups).filter(Groups.title == group)[0]
            # hydroservers_g = session.query(Groups).filter(Groups.title == group)
            print(hydroservers_group.title)
            print(hydroservers_group.description)

            hs_one = HydroServer_Individual(title=title,
                             url=url,
                             siteinfo=sites_parsed_json)

            hydroservers_group.hydroserver.append(hs_one)
            print(hydroservers_group.hydroserver)
            session.add(hydroservers_group)
            session.commit()
            session.close()

    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'

    return JsonResponse(return_obj)

######*****************************************************************************************################
##############################LOAD THE HYDROSERVERS OF AN SPECIFIC GROUP#######################################
######*****************************************************************************************################
def catalog_group(request):
    # print("Catalog_group function in controllers.py")
    # print("--------------------------------------------------------------------")
    specific_group=request.GET.get('group')
    # print(specific_group)
    # print(request.GET)
    list_catalog = {}
    # print("catalogs_groups controllers.py FUNCTION inside")

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    # print(SessionMaker)
    session = SessionMaker()  # Initiate a session
    hydroservers_group = session.query(Groups).filter(Groups.title == specific_group)[0].hydroserver
    h1=session.query(Groups).join("hydroserver")
    hs_list = []
    for hydroservers in hydroservers_group:
        name = hydroservers.title
        # print(hydroservers.title)
        # print(hydroservers.url)
        layer_obj = {}
        layer_obj["title"] = hydroservers.title
        layer_obj["url"] = hydroservers.url.strip()
        layer_obj["siteInfo"] = hydroservers.siteinfo
        hs_list.append(layer_obj)

    list_catalog["hydroserver"] = hs_list
    print("------------------------------------------")
    # print("printing the lsit of hydroservers of the group")
    # print(list)

    return JsonResponse(list_catalog)

######*****************************************************************************************################
############################## DELETE THE HYDROSERVER OF AN SPECIFIC GROUP ####################################
######*****************************************************************************************################
def delete_group_hydroserver(request):
    print("delete_group_hydroserver_function in controllers.py")
    list_catalog = {}
    print("--------------------------------------------")
    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()

    # Query DB for hydroservers
    print(request.POST)
    if request.is_ajax() and request.method == 'POST':
        print(type(request.POST))
        print(request.POST.getlist('server'))
        titles=request.POST.getlist('server')
        group = request.POST.get('actual-group')

        print(type(titles))
        # title = request.POST['server']
        i=0;
        hydroservers_group = session.query(Groups).filter(Groups.title == group)[0].hydroserver

        # for title in titles:
        #     hydroservers = session.query(Catalog).filter(Catalog.title == title).delete(
        #         synchronize_session='evaluate')  # Deleting the record from the local catalog
        #     session.commit()
        #     session.close()
        #
        #     # Returning the deleted title. To let the user know that the particular
        #     # title is deleted.
        #     i_string=str(i);
        #     # list["title"] = title
        #     list[i_string] = title
        #     i=i+1
        for title in titles:
            hydroservers_group = session.query(HydroServer_Individual).filter(HydroServer_Individual.title == title).delete(
                synchronize_session='evaluate')  # Deleting the record from the local catalog
            session.commit()
            session.close()

            # Returning the deleted title. To let the user know that the particular
            # title is deleted.
            i_string=str(i);
            # list["title"] = title
            list_catalog[i_string] = title
            i=i+1
    return JsonResponse(list_catalog)
######*****************************************************************************************################
############################## DELETE A GROUP OF HYDROSERVERS #############################
######*****************************************************************************************################
def delete_group(request):
    print("delete_group function controllers.py")
    print("--------------------------------------------")
    list_catalog = {}
    list_groups ={}
    list_response = {}
    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()
    print(request.POST)
    if request.is_ajax() and request.method == 'POST':
        groups=request.POST.getlist('groups[]')
        list_groups['groups']=groups
        list_response['groups']=groups
        print(groups)
        i=0
        arrayTitles = []
        for group in session.query(Groups).all():
            print(group.title)

        for group in groups:
            # print(session.query(Groups).filter(Groups.title == group).first())
            hydroservers_group = session.query(Groups).filter(Groups.title == group)[0].hydroserver
            print("printing hydroserver_groups")
            print(hydroservers_group)
            for server in hydroservers_group:
                title=server.title
                arrayTitles.append(title)
                print(server.title)
                i_string=str(i);
                # list["title"] = title
                list_catalog[i_string] = title
                # session.delete(server)
                # server.delete(synchronize_session='evaluate')
                # session.commit()
                # session.close()
                i=i+1
            print(session.query(Groups).filter(Groups.title == group).first().id)
            hydroservers_group = session.query(Groups).filter(Groups.title == group).first()
            session.delete(hydroservers_group)
            session.commit()
            session.close()
        list_response['hydroservers']=arrayTitles


    return JsonResponse(list_response)

def keyWordsForGroup(request):
    list_catalog={}
    print("inside the keywordsgroup function")
    specific_group=request.GET.get('group')

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    # print(SessionMaker)
    session = SessionMaker()  # Initiate a session
    hydroservers_group = session.query(Groups).filter(Groups.title == specific_group)[0].hydroserver
    # h1=session.query(Groups).join("hydroserver")
    hs_list = []
    words_to_search={};

    for hydroservers in hydroservers_group:
        name = hydroservers.title
        # print(hydroservers.title)
        # print(hydroservers.url)
        layer_obj = {}
        layer_obj["title"] = hydroservers.title
        layer_obj["url"] = hydroservers.url.strip()
        layer_obj["siteInfo"] = hydroservers.siteinfo
        client = Client(hydroservers.url.strip())
        keywords = client.service.GetVariables('[:]')

        keywords_dict = xmltodict.parse(keywords)
        keywords_dict_object = json.dumps(keywords_dict)

        keywords_json = json.loads(keywords_dict_object)
        # Parsing the sites and creating a sites object. See utilities.py
        print("-------------------------------------")
        # print(sites_json)
        print(type(keywords_json))
        print(keywords_dict.keys())
        # print(keywords_json['variablesResponse']['variables']['variable'])
        array_variables=keywords_json['variablesResponse']['variables']['variable']
        array_keywords_hydroserver=[]
        print(type(array_variables))
        # print(array_variables)
        if isinstance(array_variables,type([])):
            # print("inside the list iption")
            for words in array_variables:
                # print("priting words")
                # print(type(words))
                # print(words)
                # print(words.get('variableName'))
                # print(words['variableName'])
                array_keywords_hydroserver.append(words['variableName'])
            # words_to_search[name] = array_keywords_hydroserver
        if isinstance(array_variables,dict):
            array_keywords_hydroserver.append(array_variables['variableName'])

        words_to_search[name] = array_keywords_hydroserver
        print(words_to_search)
        # print(type(keywords_json['variablesResponse']['variables']['variable']))
        # layer_obj['keywords']=keywords_json
        # print(keywords_json)

        hs_list.append(layer_obj)

    list_catalog["hydroserver"] = hs_list
    list_catalog["keysSearch"] = words_to_search
    print("------------------------------------------")
    # print(len(hs_list))
    # print(list)
    return JsonResponse(list_catalog)

def get_values_hs(request):
    list_catalog={}
    return_obj={}
    print(request)
    hs_name = request.GET.get('hs_name')
    hs_url = request.GET.get('hs_url')
    site_name = request.GET.get('site_name')
    site_code =  request.GET.get('code')
    network = request.GET.get('network')
    site_desc = network + ':' + site_code


    # variable_text = request.GET.get('variable')
    # code_variable =request.GET.get ('code_variable')


    # print("Inside the get_values_hs function")

    # hs_name = request.GET.get('hs_name')
    # hs_url = request.GET.get('hs_url')
    # site_name = request.GET.get('site_name')

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    # print(SessionMaker)
    session = SessionMaker()  # Initiate a session
    # hydroservers_group = session.query(HydroServer_Individual).filter(Groups.title == hs_name)
    client = Client(hs_url)
    # print(client)
    keywords = client.service.GetVariables('[:]')
    keywords_dict = xmltodict.parse(keywords)
    keywords_dict_object = json.dumps(keywords_dict)

    keywords_json = json.loads(keywords_dict_object)

    site_info_Mc = client.service.GetSiteInfo(site_desc)
    site_info_Mc_dict = xmltodict.parse(site_info_Mc)
    site_info_Mc_json_object = json.dumps(site_info_Mc_dict)
    site_info_Mc_json = json.loads(site_info_Mc_json_object)


    object_methods= site_info_Mc_json['sitesResponse']['site']['seriesCatalog']['series']
    object_with_methods_and_variables = {}
    object_with_descriptions_and_variables = {}
    object_with_time_and_variables = {}
    if(isinstance(object_methods,(dict))):
        print("adding to the methodID as a dict")
        variable_name_ = object_methods['variable']['variableName']
        object_with_methods_and_variables[variable_name_]= object_methods['method']['@methodID']
        object_with_descriptions_and_variables[variable_name_]= object_methods['source'];
        object_with_time_and_variables[variable_name_]= object_methods['variableTimeInterval'];
        print(object_with_methods_and_variables)
    else:
        for object_method in object_methods:
            print("adding to the methodID as an arraylist")
            variable_name_ = object_method['variable']['variableName']
            object_with_methods_and_variables[variable_name_]= object_method['method']['@methodID']
            print(object_method['source'])
            object_with_descriptions_and_variables[variable_name_]= object_method['source'];
            object_with_time_and_variables[variable_name_]= object_method['variableTimeInterval'];
            print(object_with_methods_and_variables)



    array_variables=keywords_json['variablesResponse']['variables']['variable']
    array_keywords_hydroserver=[]
    array_variables_codes = []
    array_variables_lengths = []
    length_values = 0


    if isinstance(array_variables,type([])):
        for words in array_variables:

            variable_text = words['variableName']
            code_variable = words['variableCode']['#text']
            start_date = ""
            end_date = ""
            variable_desc = network + ':' + code_variable
            print(variable_desc)
            print(site_desc)
            values = client.service.GetValues(
                site_desc, variable_desc, start_date, end_date, "")

            values_dict = xmltodict.parse(values)  # Converting xml to dict
            values_json_object = json.dumps(values_dict)
            values_json = json.loads(values_json_object)
            times_series = values_json['timeSeriesResponse'][
                'timeSeries']  # Timeseries object for the variable
            # print(times_series)
            if times_series['values'] is not None:
                length_values= len(times_series['values']['value'])
                print(variable_text," ", length_values )
            else:
                length_values = 0
                print(variable_text," ", length_values )


            array_variables_lengths.append(length_values)


            array_keywords_hydroserver.append(words['variableName'])
            array_variables_codes.append(words['variableCode']['#text'])
        # words_to_search[name] = array_keywords_hydroserver
    if isinstance(array_variables,dict):
        variable_text = array_variables['variableName']
        code_variable = array_variables['variableCode']['#text']
        start_date = ""
        end_date = ""
        variable_desc = network + ':' + code_variable

        values = client.service.GetValues(
            site_desc, variable_desc, start_date, end_date, "")
        # print(values)

        values_dict = xmltodict.parse(values)  # Converting xml to dict
        values_json_object = json.dumps(values_dict)
        values_json = json.loads(values_json_object)
        times_series = values_json['timeSeriesResponse'][
            'timeSeries']  # Timeseries object for the variable
        # print(times_series)
        if times_series['values'] is not None:

            length_values= len(times_series['values']['value'])
            print(variable_text," ", length_values )
        else:
            length_values = 0
            print(variable_text," ", length_values )



        array_variables_lengths.append(length_values)

        array_keywords_hydroserver.append(array_variables['variableName'])
        array_variables_codes.append(array_variables['variableCode']['#text'])


    return_obj['variables']=array_keywords_hydroserver
    return_obj['codes']=array_variables_codes
    return_obj['counts'] = array_variables_lengths
    return_obj['methodsIDs']= object_with_methods_and_variables
    return_obj['description'] = object_with_descriptions_and_variables
    return_obj['times_series'] = object_with_time_and_variables
    return_obj['siteInfo']= site_info_Mc_json

    print("finished with the get_values_hs")
    return JsonResponse(return_obj)

def get_values_graph_hs(request):
# def get_values_graph_hs(hs_name, hs_url, site_name, site_code, network, code_variable):
    # let's do the change baby ok

    list_catalog={}
    return_obj={}
    print("Inside the get_values_graphs function")
    print(request)
    hs_name = request.GET.get('hs_name')
    print(hs_name)
    hs_url = request.GET.get('hs_url')
    print(hs_url)
    site_name = request.GET.get('site_name')
    print(site_name)
    site_code =  request.GET.get('code')
    print(site_code)
    network = request.GET.get('network')
    variable_text = request.GET.get('variable')
    code_variable =request.GET.get ('code_variable')
    dates_request = request.GET.getlist('timeFrame[]')
    print(dates_request)
    start_date = dates_request[0];
    end_date = dates_request[1];
    actual_methodsID = request.GET.get('actual_method');

    variable_desc = network + ':' + code_variable
    print(variable_desc)
    site_desc = network + ':' + site_code
    print(site_desc)
    print("printing methodsIDS")
    print(actual_methodsID)
    print(request.GET)


    client = Client(hs_url)  # Connect to the HydroServer endpoint
    # print(client)
    site_info_Mc = client.service.GetSiteInfo(site_desc)
    site_info_Mc_dict = xmltodict.parse(site_info_Mc)
    site_info_Mc_json_object = json.dumps(site_info_Mc_dict)
    site_info_Mc_json = json.loads(site_info_Mc_json_object)

    values = client.service.GetValues(
        site_desc, variable_desc, start_date, end_date, "")
    # print(values)
    values_dict = xmltodict.parse(values)  # Converting xml to dict
    values_json_object = json.dumps(values_dict)
    values_json = json.loads(values_json_object)
    times_series = values_json['timeSeriesResponse'][
        'timeSeries']  # Timeseries object for the variable
    # print(times_series)
    # return_obj['siteInfo']= site_info_Mc_json
    # object_with_methods_and_variables ={}
    return_obj['values'] = times_series
    # print(site_info_Mc_json)

    if times_series['values'] is not None:

        # return_obj['siteInfo']= site_info_Mc_json
        # methodID = []
        # object_methods= site_info_Mc_json['sitesResponse']['site']['seriesCatalog']['series']
        # print(type(object_methods))
        # if(isinstance(object_methods,(dict))):
        #     print("adding to the methodID as a dict")
        #     methodID.append(object_methods['method']['@methodID'])
        #
        #     variable_name_ = object_methods['variable']['variableName']
        #     object_with_methods_and_variables[variable_name_]= object_methods['method']['@methodID']
        #     print(object_with_methods_and_variables)
        # else:
        #     for object_method in object_methods:
        #         print("adding to the methodID as an arraylist")
        #         methodID.append(object_method['method']['@methodID'])
        #         variable_name_ = object_method['variable']['variableName']
        #         object_with_methods_and_variables[variable_name_]= object_method['method']['@methodID']
        #         print(object_with_methods_and_variables)


        return_obj['values'] = times_series
        # return_obj['methodsID']=methodID
        # return_obj['methods_variables']=object_with_methods_and_variables
    #     print("times series is true")
        graph_json = {}  # json object that will be returned to the front end
        graph_json["variable"] = times_series['variable']['variableName']
        graph_json["unit"] = times_series[
            'variable']['unit']['unitAbbreviation']
        # graph_json["title"] = site_name + ' ' + \
        #     "( " + times_series['variable']['variableName'] + " )"
        graph_json["title"] = times_series['variable']['variableName'] + " (" + graph_json["unit"] + ") vs Time"
        for j in times_series['values']:  # Parsing the timeseries
            print("first for loop")
            print(j)
    #         # empty list which will have the time stamp and values within
    #         # the specified date range.
            data_values = []
            data_values2 = []
            if j == "value":
    #             # If there are multiple timeseries than value the following
    #             # code is executed
                print(type((times_series['values']['value'])))
                # if(isinstance(times_series['values']['value'],(list))):
                #     print("it is a list with isInstace")
                if type(times_series['values']['value']) is list:
                    print("it is a list the timeseries")
                    print(len(times_series['values']['value']))
                    count = 0
                    for k in times_series['values']['value']:
                        # print(k)
                        return_obj['k']= k

                        try:
                            # if k['@methodCode'] == variable_method:
                            # if k['@methodCode'] == methodID[0]:
                            if k['@methodCode'] == actual_methodsID:
                                count = count + 1
                                time = k['@dateTimeUTC']
                                # print(time)
                                time1 = time.replace("T", "-")
                                # print(type(time1))
                                # print(time1[10])
                                # print(time1)

                                time_split = time1.split("-")
                                year = int(time_split[0])
                                month = int(time_split[1])
                                day = int(time_split[2])
                                hour_minute = time_split[3].split(":")
                                hour = int(hour_minute[0])
                                minute = int(hour_minute[1])
                                value = float(str(k['#text']))
                                date_string = datetime(
                                    year, month, day, hour, minute)
                                # Creating a timestamp as javascript cannot
                                # recognize datetime object
                                # print(date_string)
                                # print(type(date_string))
                                date_string_converted = date_string.strftime("%Y-%m-%d %H:%M:%S")
                                # print(date_string_converted)
                                data_values2.append([date_string_converted,value])
                                data_values2.sort()
                                time_stamp = calendar.timegm(
                                    date_string.utctimetuple()) * 1000
                                data_values.append([time_stamp, value])
                                data_values.sort()
                            graph_json["values2"] = data_values2

                            # graph_json["values"] = data_values
                            graph_json["count"] = count
                            # print("we are out of here if not problem")
                        except KeyError:  # The Key Error kicks in when there is only one timeseries
                            count = count + 1
                            time = k['@dateTimeUTC']
                            time1 = time.replace("T", "-")
                            time_split = time1.split("-")
                            year = int(time_split[0])
                            month = int(time_split[1])
                            day = int(time_split[2])
                            hour_minute = time_split[3].split(":")
                            hour = int(hour_minute[0])
                            minute = int(hour_minute[1])
                            value = float(str(k['#text']))
                            date_string = datetime(
                                year, month, day, hour, minute)
                            # print(date_string)
                            data_values2.append([date_string,value])
                            data_values2.sort()
                            time_stamp = calendar.timegm(
                                date_string.utctimetuple()) * 1000
                            data_values.append([time_stamp, value])
                            data_values.sort()
                        graph_json["values2"] = data_values2

                        # graph_json["values"] = data_values
                        graph_json["count"] = count
                        return_obj['graphs']=graph_json
                        # print("we are out of here if problem")

                else:  # The else statement is executed is there is only one value in the timeseries
                    try:
                        print("not list the time series then")
                        print(type(times_series))
                        # if times_series['values']['value']['@methodCode'] == variable_method:
                        # if times_series['values']['value']['@methodCode'] == methodID[0]:
                        if times_series['values']['value']['@methodCode'] == actual_methodsID:
                            time = times_series['values'][
                                'value']['@dateTimeUTC']
                            # print(time)
                            time1 = time.replace("T", "-")
                            # print(time1)
                            time_split = time1.split("-")
                            year = int(time_split[0])
                            month = int(time_split[1])
                            day = int(time_split[2])
                            hour_minute = time_split[3].split(":")
                            hour = int(hour_minute[0])
                            minute = int(hour_minute[1])
                            value = float(
                                str(times_series['values']['value']['#text']))

                            date_string = datetime(
                                year, month, day, hour, minute)
                            print(date_string)

                            data_values2.append([date_string,value])
                            data_values2.sort()
                            time_stamp = calendar.timegm(
                                date_string.utctimetuple()) * 1000
                            data_values.append([time_stamp, value])
                            data_values.sort()
                            graph_json["values2"] = data_values2

                            # graph_json["values"] = data_values
                            graph_json["count"] = 1
                            return_obj['graphs']=graph_json

                    except KeyError:
                        time = times_series['values'][
                            'value']['@dateTimeUTC']
                        time1 = time.replace("T", "-")
                        time_split = time1.split("-")
                        year = int(time_split[0])
                        month = int(time_split[1])
                        day = int(time_split[2])
                        hour_minute = time_split[3].split(":")
                        hour = int(hour_minute[0])
                        minute = int(hour_minute[1])
                        value = float(
                            str(times_series['values']['value']['#text']))
                        date_string = datetime(
                            year, month, day, hour, minute)
                        # print(date_string)

                        time_stamp = calendar.timegm(
                            date_string.utctimetuple()) * 1000
                        data_values.append([time_stamp, value])
                        data_values.sort()

                        data_values2.append([date_string,value])
                        data_values2.sort()
                        graph_json["values2"] = data_values2
                        # graph_json["values"] = data_values
                        graph_json["count"] = 1
                        return_obj['graphs']=graph_json
    # else:
    #     graph_json = {}  # json object that will be returned to the front end
    #     graph_json["count"] = 0
    #     return_obj["graphs"]=graph_json

    print("done with get_values_graph_hs")
    return JsonResponse(return_obj)
# def get_values_graph_hs(request):
# # def get_values_graph_hs(hs_name, hs_url, site_name, site_code, network, code_variable):
#     # let's do the change baby ok
#
#     list_catalog={}
#     return_obj={}
#     print("Inside the get_values_graphs function")
#     print(request)
#     hs_name = request.GET.get('hs_name')
#     print(hs_name)
#     hs_url = request.GET.get('hs_url')
#     print(hs_url)
#     site_name = request.GET.get('site_name')
#     print(site_name)
#     site_code =  request.GET.get('code')
#     print(site_code)
#     network = request.GET.get('network')
#     variable_text = request.GET.get('variable')
#     code_variable =request.GET.get ('code_variable')
#     start_date = ""
#     end_date = ""
#     variable_desc = network + ':' + code_variable
#     print(variable_desc)
#     site_desc = network + ':' + site_code
#     print(site_desc)
#
#
#     client = Client(hs_url)  # Connect to the HydroServer endpoint
#     # print(client)
#     site_info_Mc = client.service.GetSiteInfo(site_desc)
#     site_info_Mc_dict = xmltodict.parse(site_info_Mc)
#     site_info_Mc_json_object = json.dumps(site_info_Mc_dict)
#     site_info_Mc_json = json.loads(site_info_Mc_json_object)
#     values = client.service.GetValues(
#         site_desc, variable_desc, start_date, end_date, "")
#     # print(values)
#     values_dict = xmltodict.parse(values)  # Converting xml to dict
#     values_json_object = json.dumps(values_dict)
#     values_json = json.loads(values_json_object)
#     times_series = values_json['timeSeriesResponse'][
#         'timeSeries']  # Timeseries object for the variable
#     # print(times_series)
#     return_obj['siteInfo']= site_info_Mc_json
#     object_with_methods_and_variables ={}
#     return_obj['values'] = times_series
#     # print(site_info_Mc_json)
#
#     if times_series['values'] is not None:
#
#         return_obj['siteInfo']= site_info_Mc_json
#         methodID = []
#         object_methods= site_info_Mc_json['sitesResponse']['site']['seriesCatalog']['series']
#         print(type(object_methods))
#         if(isinstance(object_methods,(dict))):
#             print("adding to the methodID as a dict")
#             methodID.append(object_methods['method']['@methodID'])
#
#             variable_name_ = object_methods['variable']['variableName']
#             object_with_methods_and_variables[variable_name_]= object_methods['method']['@methodID']
#             print(object_with_methods_and_variables)
#         else:
#             for object_method in object_methods:
#                 print("adding to the methodID as an arraylist")
#                 methodID.append(object_method['method']['@methodID'])
#                 variable_name_ = object_method['variable']['variableName']
#                 object_with_methods_and_variables[variable_name_]= object_method['method']['@methodID']
#                 print(object_with_methods_and_variables)
#
#
#         print(methodID)
#         return_obj['values'] = times_series
#         return_obj['methodsID']=methodID
#         return_obj['methods_variables']=object_with_methods_and_variables
#     #     print("times series is true")
#         graph_json = {}  # json object that will be returned to the front end
#         graph_json["variable"] = times_series['variable']['variableName']
#         graph_json["unit"] = times_series[
#             'variable']['unit']['unitAbbreviation']
#         # graph_json["title"] = site_name + ' ' + \
#         #     "( " + times_series['variable']['variableName'] + " )"
#         graph_json["title"] = times_series['variable']['variableName'] + " (" + graph_json["unit"] + ") vs Time"
#         for j in times_series['values']:  # Parsing the timeseries
#             print("first for loop")
#             print(j)
#     #         # empty list which will have the time stamp and values within
#     #         # the specified date range.
#             data_values = []
#             data_values2 = []
#             if j == "value":
#     #             # If there are multiple timeseries than value the following
#     #             # code is executed
#                 print(type((times_series['values']['value'])))
#                 # if(isinstance(times_series['values']['value'],(list))):
#                 #     print("it is a list with isInstace")
#                 if type(times_series['values']['value']) is list:
#                     print("it is a list the timeseries")
#                     print(len(times_series['values']['value']))
#                     count = 0
#                     for k in times_series['values']['value']:
#                         # print(k)
#                         return_obj['k']= k
#
#                         try:
#                             # if k['@methodCode'] == variable_method:
#                             # if k['@methodCode'] == methodID[0]:
#                             if k['@methodCode'] == object_with_methods_and_variables[times_series['variable']['variableName']]:
#                                 count = count + 1
#                                 time = k['@dateTimeUTC']
#                                 # print(time)
#                                 time1 = time.replace("T", "-")
#                                 # print(type(time1))
#                                 # print(time1[10])
#                                 # print(time1)
#
#                                 time_split = time1.split("-")
#                                 year = int(time_split[0])
#                                 month = int(time_split[1])
#                                 day = int(time_split[2])
#                                 hour_minute = time_split[3].split(":")
#                                 hour = int(hour_minute[0])
#                                 minute = int(hour_minute[1])
#                                 value = float(str(k['#text']))
#                                 date_string = datetime(
#                                     year, month, day, hour, minute)
#                                 # Creating a timestamp as javascript cannot
#                                 # recognize datetime object
#                                 # print(date_string)
#                                 # print(type(date_string))
#                                 date_string_converted = date_string.strftime("%Y-%m-%d %H:%M:%S")
#                                 # print(date_string_converted)
#                                 data_values2.append([date_string_converted,value])
#                                 data_values2.sort()
#                                 time_stamp = calendar.timegm(
#                                     date_string.utctimetuple()) * 1000
#                                 data_values.append([time_stamp, value])
#                                 data_values.sort()
#                             graph_json["values2"] = data_values2
#
#                             # graph_json["values"] = data_values
#                             graph_json["count"] = count
#                             # print("we are out of here if not problem")
#                         except KeyError:  # The Key Error kicks in when there is only one timeseries
#                             count = count + 1
#                             time = k['@dateTimeUTC']
#                             time1 = time.replace("T", "-")
#                             time_split = time1.split("-")
#                             year = int(time_split[0])
#                             month = int(time_split[1])
#                             day = int(time_split[2])
#                             hour_minute = time_split[3].split(":")
#                             hour = int(hour_minute[0])
#                             minute = int(hour_minute[1])
#                             value = float(str(k['#text']))
#                             date_string = datetime(
#                                 year, month, day, hour, minute)
#                             # print(date_string)
#                             data_values2.append([date_string,value])
#                             data_values2.sort()
#                             time_stamp = calendar.timegm(
#                                 date_string.utctimetuple()) * 1000
#                             data_values.append([time_stamp, value])
#                             data_values.sort()
#                         graph_json["values2"] = data_values2
#
#                         # graph_json["values"] = data_values
#                         graph_json["count"] = count
#                         return_obj['graphs']=graph_json
#                         # print("we are out of here if problem")
#
#                 else:  # The else statement is executed is there is only one value in the timeseries
#                     try:
#                         print("not list the time series then")
#                         print(type(times_series))
#                         # if times_series['values']['value']['@methodCode'] == variable_method:
#                         # if times_series['values']['value']['@methodCode'] == methodID[0]:
#                         if times_series['values']['value']['@methodCode'] == object_with_methods_and_variables[times_series['variable']['variableName']]:
#                             time = times_series['values'][
#                                 'value']['@dateTimeUTC']
#                             # print(time)
#                             time1 = time.replace("T", "-")
#                             # print(time1)
#                             time_split = time1.split("-")
#                             year = int(time_split[0])
#                             month = int(time_split[1])
#                             day = int(time_split[2])
#                             hour_minute = time_split[3].split(":")
#                             hour = int(hour_minute[0])
#                             minute = int(hour_minute[1])
#                             value = float(
#                                 str(times_series['values']['value']['#text']))
#
#                             date_string = datetime(
#                                 year, month, day, hour, minute)
#                             print(date_string)
#
#                             data_values2.append([date_string,value])
#                             data_values2.sort()
#                             time_stamp = calendar.timegm(
#                                 date_string.utctimetuple()) * 1000
#                             data_values.append([time_stamp, value])
#                             data_values.sort()
#                             graph_json["values2"] = data_values2
#
#                             # graph_json["values"] = data_values
#                             graph_json["count"] = 1
#                             return_obj['graphs']=graph_json
#
#                     except KeyError:
#                         time = times_series['values'][
#                             'value']['@dateTimeUTC']
#                         time1 = time.replace("T", "-")
#                         time_split = time1.split("-")
#                         year = int(time_split[0])
#                         month = int(time_split[1])
#                         day = int(time_split[2])
#                         hour_minute = time_split[3].split(":")
#                         hour = int(hour_minute[0])
#                         minute = int(hour_minute[1])
#                         value = float(
#                             str(times_series['values']['value']['#text']))
#                         date_string = datetime(
#                             year, month, day, hour, minute)
#                         # print(date_string)
#
#                         time_stamp = calendar.timegm(
#                             date_string.utctimetuple()) * 1000
#                         data_values.append([time_stamp, value])
#                         data_values.sort()
#
#                         data_values2.append([date_string,value])
#                         data_values2.sort()
#                         graph_json["values2"] = data_values2
#                         # graph_json["values"] = data_values
#                         graph_json["count"] = 1
#                         return_obj['graphs']=graph_json
#     # else:
#     #     graph_json = {}  # json object that will be returned to the front end
#     #     graph_json["count"] = 0
#     #     return_obj["graphs"]=graph_json
#
#     print("done with get_values_graph")
#     return JsonResponse(return_obj)
