from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting, SpatialDatasetServiceSetting, CustomSetting



class Crazysearch(TethysAppBase):
    """
    Tethys app class for Crazysearch.
    """

    name = 'Crazysearch'
    index = 'crazysearch:home'
    icon = 'crazysearch/images/crazy_search.jpg'
    package = 'crazysearch'
    root_url = 'crazysearch'
    color = '#f2910d'
    description = 'This app is query tool in which data from different hydroservers and catalogs can be added and query, so the user can see  different data available'
    tags = '&quot;Hydroserver&quot;, &quot;Query&quot;,&quot;BYU&quot;,&quot;Geoglows&quot;, &quot;Data Share&quot;'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='crazysearch',
                controller='crazysearch.controllers.home'
            ),
            UrlMap(name='his-server',
                   url='crazysearch/his-server',
                   controller='crazysearch.controllers.get_his_server'),
            # Returns the selected HIS server from the select HIS
            # server modal.
            UrlMap(name='soap',
                   url='crazysearch/soap',
                   controller='crazysearch.controllers.soap'),
            # Create's a geoserver layer based on the HydroServer SOAP endpoint and add's
            # that HydroServer metadata to a persistant store
            UrlMap(name='catalog',
                   url='crazysearch/catalog',
                   controller='crazysearch.controllers.catalog'),
           UrlMap(name='delete',
                   url='crazysearch/delete',
                   controller='crazysearch.controllers.delete'),
            # Deletes a selected HydroServer from the local database
            UrlMap(name='add-central',
                   url='crazysearch/add-central',
                   controller='crazysearch.controllers.add_central'),
            # Add a central catalog, but it is still in progress.
            UrlMap(name='create-group',
                   url='crazysearch/create-group',
                   controller='crazysearch.controllers.create_group'),
            # Create a new group for the hydroservers ##
            UrlMap(name='load-groups',
                   url='crazysearch/load-groups',
                   controller='crazysearch.controllers.get_groups_list'),
            # Load groups for the hydroservers ##
            UrlMap(name='add-hydrosever-groups',
                   url='crazysearch/soap-group',
                   controller='crazysearch.controllers.soap_group'),
            # Load groups for the hydroservers ##
            UrlMap(name='load-hydroserver-of-groups',
                   url='crazysearch/catalog-group',
                   controller='crazysearch.controllers.catalog_group'),
            # Load the hydroservers from a specific group##

            UrlMap(name='delete-group-hydroserver',
                   url='crazysearch/delete-group-hydroserver',
                   controller='crazysearch.controllers.delete_group_hydroserver'),
            ## Delete an speicific hydroserver or multiple from a specific group ##

            UrlMap(name='delete-group',
                   url='crazysearch/delete-group',
                   controller='crazysearch.controllers.delete_group'),
            ## Delete an speicific hydroserver or multiple from a specific group ##
            UrlMap(name='keyword-group',
                   url='crazysearch/keyword-group',
                   controller='crazysearch.controllers.keyWordsForGroup'),
            ## Find the keywords for each hydrpserver in a group##
            UrlMap(name='get-values-hs',
                   url='crazysearch/get-values-hs',
                   controller='crazysearch.controllers.get_values_hs'),
            ## Get the variables of a hydroserver
            UrlMap(name='get-values-hs',
                   url='crazysearch/get-values-graph-hs',
                   controller='crazysearch.controllers.get_values_graph_hs'),
            ## Get the values of a hydroserver
        )

        return url_maps

    def custom_settings(self):
        custom_settings = (
            CustomSetting(
                name='Boundary Geoserver Endpoint',
                type = CustomSetting.TYPE_STRING,
                description='Geoserver endpoint for the hydroshare resource containning the layer (e.g:"https://geoserver.hydroshare.org/geoserver/layerID")',
                required=False
            ),
            CustomSetting(
                name='Boundary Workspace Name',
                type = CustomSetting.TYPE_STRING,
                description='workspace and layer name (e.g workspace:layername)',
                required=False
            ),
            CustomSetting(
                name='Boundary Layer Name',
                type = CustomSetting.TYPE_STRING,
                description='layer name (e.g workspace:layername)',
                required=False
            ),
            CustomSetting(
                name='Boundary Color',
                type = CustomSetting.TYPE_STRING,
                description='The color style for the boundary (e.g #ffcc33)',
                required=False
            ),
            CustomSetting(
                name='Boundary Width',
                type = CustomSetting.TYPE_STRING,
                description='Width of the boundary. A number from 1 to 10',
                required=False
            ),
        )
        # return
        return custom_settings
    def persistent_store_settings(self):
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='catalog_db',
                description='catalogs database',
                initializer='crazysearch.init_stores.init_catalog_db',
                required=True
            ),
        )
        return ps_settings
