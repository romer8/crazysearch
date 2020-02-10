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
    list = {}
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
        list['servers'] = hs_list
        list['errors'] = error_list

    context = {"hs_list": hs_list, "error_list": error_list}

    return render(request, 'hydroexplorer/his.html', context)

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
    list = {}
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
    list["hydroserver"] = hs_list

    return JsonResponse(list)

def delete(request):

    list = {}

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
            list[i_string] = title
            i=i+1
    return JsonResponse(list)

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
    list = {}
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
    list["hydroservers"] = hydroserver_groups_list
    # print(list)
    return JsonResponse(list)


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
##############################LOAD THE HYDROSERVERS OF AN SPECIFIC GROUP###################################
######*****************************************************************************************################
def catalog_group(request):
    specific_group=request.GET.get('group')
    print(specific_group)
    print(request.GET)
    list = {}
    print("catalogs_groups controllers.py FUNCTION inside")

    SessionMaker = app.get_persistent_store_database(Persistent_Store_Name, as_sessionmaker=True)

    # print(SessionMaker)
    session = SessionMaker()  # Initiate a session
    hydroservers_group = session.query(Groups).filter(Groups.title == specific_group)[0].hydroserver
    h1=session.query(Groups).join("hydroserver")
    hs_list = []
    for hydroservers in hydroservers_group:
        name = hydroservers.title
        print(hydroservers.title)
        print(hydroservers.url)
        layer_obj = {}
        layer_obj["title"] = hydroservers.title
        layer_obj["url"] = hydroservers.url.strip()
        layer_obj["siteInfo"] = hydroservers.siteinfo
        hs_list.append(layer_obj)

    list["hydroserver"] = hs_list
    print("------------------------------------------")
    print("printing the lsit of hydroservers of the group")
    print(list)


    # hs_list = []
    # for server in hydroservers:
    #     layer_obj = {}
    #     layer_obj["title"] = server.title
    #     layer_obj["url"] = server.url.strip()
    #     layer_obj["siteInfo"] = server.siteinfo
    #
    #     hs_list.append(layer_obj)
    # # A json list object with the HydroServer metadata. This object will be
    # # used to add layers to the catalog table on the homepage.
    # list["hydroserver"] = hs_list

    return JsonResponse(list)
