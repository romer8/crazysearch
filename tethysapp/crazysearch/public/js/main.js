/*****************************************************************************
 * FILE:                Main.js
 * BEGGINING DATE:      16 August 2019
 * ENDING DATE:         ---------------
 * AUTHOR:              Giovanni Romero Bustamante
 * COPYRIGHT:           (c) Brigham Young University 2020
 * LICENSE:             MIT
 *
 *****************************************************************************/
/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/
 var staticPath = baseStatic;
 var apiServer = `${staticPath.replace("/static", "/apps")}`;
 window.onbeforeunload = null
 var $myGroup = $("#helpGroup")
 $myGroup.on("show.bs.collapse", ".collapse", function() {
     $myGroup.find(".collapse.in").collapse("hide")
 })
 ;(function() {
     "use strict"
     window.addEventListener(
         "load",
         function() {
             // Fetch all the forms we want to apply custom Bootstrap validation styles to
             var forms = document.getElementsByClassName("needs-validation")
             // Loop over them and prevent submission
             var validation = Array.prototype.filter.call(forms, function(form) {
                 form.addEventListener(
                     "submit",
                     function(event) {
                         if (form.checkValidity() === false) {
                             event.preventDefault()
                             event.stopPropagation()
                         }
                         form.classList.add("was-validated")
                     },
                     false
                 )
             })
         },
         false
     )
 })()

 function featureStyle() {
     var style = new ol.style.Style({
         image: new ol.style.Circle({
             radius: 6,
             stroke: new ol.style.Stroke({
                 color: "white",
                 width: 1
             }),
             fill: new ol.style.Fill({
                 color: `#${(((1 << 24) * Math.random()) | 0).toString(16)}`
             })
         })
     })
     return style
 }

var CRAZYSEARCH_PACKAGE = (function() {
    // Wrap the library in a package function
    "use strict" // And enable strict mode for this library
    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var ContextMenuBase,
        colors,
        current_layer,
        layers,
        layersDict, //Dictionary for keeping track of the new layers that are being added to the map
        map,
        shpSource,
        shpLayer,
        wmsLayer,
        wmsSource,
        cata
      cata=[{
        title:"hola",
        description:" this is just a mere description for the hola example"
      }];
    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var addContextMenuToListItem,
        add_soap,
        addDefaultBehaviorToAjax,
        checkCsrfSafe,
        getCookie,
        click_catalog,
        clear_coords,
        generate_graph,
        generate_plot,
        get_climate_serv,
        get_data_rods,
        get_his_server,
        get_hs_list,
        get_random_color,
        init_map,
        init_menu,
        init_jquery_var,
        init_events,
        load_catalog,
        location_search,
        $modalAddHS,
        $modalAddSOAP,
        set_color,
        $SoapVariable,
        $modalAddGroupHydro,
        $modalHIS,
        $modalClimate,
        $modalDelete,
        $modalDataRods,
        $modalInterface,
        $modalUpload,
        $btnUpload,
        onClickZoomTo,
        onClickDeleteLayer,
        $hs_list,
        prepare_files,
        update_catalog,
        upload_file,
        createExportCanvas,
        createDropdownMenu,
        createDescriptions,
        create_group_hydroservers,
        load_group_hydroservers,
        addExpandableMenu,
        load_individual_hydroservers_group,
        actual_group,
        add_hydroserver,
        delete_hydroserver,
        get_hs_list_from_hydroserver,
        delete_group_of_hydroservers,
        get_keywords_from_group;
    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS : How are these private? JS has no concept of that
     *************************************************************************/
    colors = [
        "#ff0000",
        "#0033cc",
        "#000099",
        "#ff0066",
        "#ff00ff",
        "#800000",
        "#6699ff",
        "#6600cc",
        "#00ffff"
    ]
    createDropdownMenu = function(catalogCreated){
      console.log(catalogCreated);
      let dropdown_classArray=document.getElementsByClassName("selectpicker");
      let element_dropdown=document.getElementById("content_description");
      Array.from(dropdown_classArray).forEach(function(dropdown){
        catalogCreated.forEach(function(element){
          let option = document.createElement("option");
          option.text=element.title;
          dropdown.add(option);
        });
        // Add a function to add a the title description as well
        dropdown.addEventListener("change", function(e){
            console.log("hola nene");
          if(e.target.value !== "Select a group of Hydroservers" ){
            let title_option = e.target.value;
            let description_option= catalogCreated.find(x => x.title === title_option).description;
            createDescriptions("description",title_option, description_option);
          }
          else {
            element_dropdown.style.display="none";

          }
            //add a function to do the change this function probably needs some change in the DOM
        })
      });
      element_dropdown.style.visibility="visible";

    };
    createDescriptions = function(id,option_title, option_description){
      let elementId=document.getElementById(id);
      console.log(elementId);
      let titles= elementId.querySelector("h2");
      console.log(titles);
      titles.innerHTML=option_title;

      let descriptions= elementId.querySelector("p");
      descriptions.innerHTML=option_description;
    };

    // List of colors for generating the styling of the points on the map
    set_color = function() {
        var color = colors[Math.floor(Math.random() * colors.length)]
        return color
    }
    // Return a random color from the list of colors
    clear_coords = function() {
        $("#poly-lat-lon").val("")
        $("#point-lat-lon").val("")
    }
    //Clear the point/polygon coordinates so that its easier for the post request to process the form
    get_random_color = function() {
        var letters = "012345".split("")
        var color = "#"
        color += letters[Math.round(Math.random() * 5)]
        letters = "0123456789ABCDEF".split("")
        for (var i = 0; i < 5; i++) {
            color += letters[Math.round(Math.random() * 15)]
        }
        return color
    }
    // Leaving this here as it is pretty neat snippet of code
    init_map = function() {
        var projection = ol.proj.get("EPSG:3857")
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key:
                    "5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4",
                imagerySet: "AerialWithLabels" // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        })
        //Creating an empty source and layer to store the shapefile geojson object
        shpSource = new ol.source.Vector()
        shpLayer = new ol.layer.Vector({
            source: shpSource
        })
        //Creating an empty source and layer to store the point/polygon features.
        var source = new ol.source.Vector({
            wrapX: false
        })
        var vector_layer = new ol.layer.Vector({
            name: "my_vectorlayer",
            source: source,
            style: new ol.style.Style({
                //color Fill
                fill: new ol.style.Fill({
                    color: "rgba(255, 255, 255, 0.2)"
                }),
                //ourside part of contour //
                stroke: new ol.style.Stroke({
                    color: "#ffcc33",
                    width: 2
                }),

                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: "#ffcc33"
                    })
                })
            })
        })

        layersDict = {}

        layers = [baseLayer, vector_layer, shpLayer]
        map = new ol.Map({
            target: "map",
            layers: layers,
            view: new ol.View({
              // -25.30066, -57.63591
                center: [-11500000, 4735000],
                projection: projection,
                zoom: 4
            }),
            controls: ol.control
                .defaults()
                .extend([
                    new ol.control.ZoomSlider(),
                    new ol.control.FullScreen()
                ]),
            crossOrigin: "anonymous"
        })

        var lastFeature, draw, featureType
        //Remove the last feature before drawing a new one
        var removeLastFeature = function() {
            if (lastFeature) source.removeFeature(lastFeature)
        }
        //Add the point/polygon interaction to the map
        var addInteraction = function(geomtype) {
            var typeSelect = document.getElementById("types")
            var value = typeSelect.value
            $("#data").val("")
            if (value !== "None") {
                if (draw) map.removeInteraction(draw)
                draw = new ol.interaction.Draw({
                    source: source,
                    type: geomtype
                })
                map.addInteraction(draw)
            }
            if (featureType === "Point" || featureType === "Polygon") {
                // draw.on('drawend', function (e) {
                //     removeLastFeature();
                //     lastFeature = e.feature;
                // });
                draw.on("drawend", function(e) {
                    lastFeature = e.feature
                })
                draw.on("drawstart", function(e) {
                    source.clear()
                })
            }
        }
        //Extracting information from the saved json object data
        vector_layer.getSource().on("addfeature", function(event) {
            var feature_json = saveData()
            var parsed_feature = JSON.parse(feature_json)
            var feature_type = parsed_feature["features"][0]["geometry"]["type"]
            //Save the point values to the point-lat-lon field
            if (feature_type == "Point") {
                var coords =
                    parsed_feature["features"][0]["geometry"]["coordinates"]
                var proj_coords = ol.proj.transform(
                    coords,
                    "EPSG:3857",
                    "EPSG:4326"
                )
                $("#gldas-lat-lon").val(proj_coords)
                $modalDataRods.modal("show")
            } else if (feature_type == "Polygon") {
                //Save the coordinates to the cserv-lat-lon field
                $modalClimate.modal("show")
                var coords =
                    parsed_feature["features"][0]["geometry"]["coordinates"][0]
                proj_coords = []
                coords.forEach(function(coord) {
                    var transformed = ol.proj.transform(
                        coord,
                        "EPSG:3857",
                        "EPSG:4326"
                    )
                    proj_coords.push("[" + transformed + "]")
                })
                var json_object =
                    '{"type":"Polygon","coordinates":[[' + proj_coords + "]]}"
                $("#cserv_lat_lon").val(json_object)
            }
        })
        //Save the drawn feature as a json object
        function saveData() {
            // get the format the user has chosen
            var data_type = "GeoJSON",
                // define a format the data shall be converted to
                format = new ol.format[data_type](),
                // this will be the data in the chosen format
                data
            try {
                // convert the data of the vector_layer into the chosen format
                data = format.writeFeatures(
                    vector_layer.getSource().getFeatures()
                )
            } catch (e) {
                // at time of creation there is an error in the GPX format (18.7.2014)
                $("#data").val(e.name + ": " + e.message)
                return
            }
            // $('#data').val(JSON.stringify(data, null, 4));
            return data
        }
        //Change the map based on the interaction type. Add/remove interaction accordingly.
        $("#types")
            .change(function(e) {
                featureType = $(this)
                    .find("option:selected")
                    .val()
                if (featureType == "None") {
                    $("#data").val("")
                    clear_coords()
                    map.removeInteraction(draw)
                    vector_layer.getSource().clear()
                    shpLayer.getSource().clear()
                } else if (featureType == "Point") {
                    clear_coords()
                    shpLayer.getSource().clear()
                    addInteraction(featureType)
                } else if (featureType == "Polygon") {
                    clear_coords()
                    shpLayer.getSource().clear()
                    addInteraction(featureType)
                } else if (featureType == "Upload") {
                    clear_coords()
                    vector_layer.getSource().clear()
                    shpLayer.getSource().clear()
                    map.removeInteraction(draw)
                    $modalUpload.modal("show")
                }
            })
            .change()
        // init_events()
    }
    init_jquery_var = function(){
      $modalAddGroupHydro= $("#modalAddGroupServer");
      // $modalAddHS = $("#modalAddHS");
      $modalAddSOAP = $("#modalAddSoap");
      // $SoapVariable = $("#soap_variable");
      $modalDelete = $("#modalDelete");
      // $modalHIS = $("#modalHISCentral");
      // $modalDataRods = $("#modalDataRods");
      $modalInterface = $("#modalInterface");
      $hs_list = $("#current-servers-list");
      // $modalClimate = $("#modalClimate");
      // $modalUpload = $("#modalUpload");
      // $btnUpload = $("#btn-add-shp");
    }
    addContextMenuToListItem = function($listItem) {
        var contextMenuId
        $listItem.find(".hmbrgr-div img").contextMenu("menu", ContextMenuBase, {
            triggerOn: "click",
            displayAround: "trigger",
            mouseClick: "left",
            position: "right",
            onOpen: function(e) {
                $(".hmbrgr-div").removeClass("hmbrgr-open")
                $(e.trigger.context)
                    .parent()
                    .addClass("hmbrgr-open")
            },
            onClose: function(e) {
                $(e.trigger.context)
                    .parent()
                    .removeClass("hmbrgr-open")
            }
        })
        contextMenuId = $(".iw-contextMenu:last-child").attr("id")
        $listItem.attr("data-context-menu", contextMenuId)
    }

    // PUT IT WHERE THE CLICK EVENT ITS SHOOT TO CALCULATE THE DIFFERET KEY WORDS.
    get_keywords_from_group = function(){
      let hydroserver_group = actual_group.split('=')[1]
      let datastring = Array.from(document.getElementsByClassName("odd gradeX"));
      // console.log(datastring);
      let key_words_to_search=[];
      datastring.forEach(function(data){
        // console.log(Array.from(data.children));
        Array.from(data.children).forEach(function(column){
          if(Array.from(column.children)[0].checked ==true){
            // console.log();
            key_words_to_search.push(Array.from(column.children)[0].nextSibling.nodeValue.trim())
          }
        })
      });
      console.log(key_words_to_search);
      let send_group={
        group: hydroserver_group
      };
      console.log(send_group);
      $.ajax({
        type:"GET",
        url: `${apiServer}/keyword-group/`,
        dataType: "JSON",
        data: send_group,
        success: function(result){
          console.log(result);

          // take out a server and do not display it // for this load all the servers again, and at the end erase the ones that do not have a
          // search keyword//

          //look which servers do not have a selected search keyword//
          let keywords_in_servers=[];
          for (let [key, value] of Object.entries(result.keysSearch)) {
              value.forEach(function(v){
                  key_words_to_search.forEach(function(word_to_search){
                    if(v === word_to_search){
                      if(!keywords_in_servers.includes(key)){
                        keywords_in_servers.push(key);
                      }
                    }
                  })
              })
              console.log(key, value);
          }
          console.log(keywords_in_servers);
          // load only the specific hydroservers
          // clean the list of hydroservers
          $("#current-servers").empty() //Resetting the catalog
          let extent = ol.extent.createEmpty();
          let servers_with_no_keyword=[];
          let all_servers_titles=[];
          // THIS WILL REMOVE ANY LAYERS FROM A HYDROSERVER //
          for (var key of Object.keys(layersDict)) {
              map.removeLayer(layersDict[key])
              delete layersDict[key]
              map.updateSize()
          };

          let all_servers_in_group=result.hydroserver;
          console.log(servers_with_no_keyword);
          console.log(all_servers_in_group);
            all_servers_in_group.forEach(server_in_group => {
              // keywords_in_servers.forEach(function(keyword_in_server){
                // if(server_in_group['title'] !=keyword_in_server){
                //   if(!servers_new.includes(server_in_group['title'])){
                //     servers_new.push(server_in_group['title']);
                //   }
                // }

                      let {
                          title,
                          url,
                          geoserver_url,
                          layer_name,
                          extents,
                          siteInfo
                      } = server_in_group
                      all_servers_titles.push(title);
                      let newHtml = `<li class="ui-state-default" layer-name="${title}">
                      <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                      <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                      </li>`
                      let sites = JSON.parse(siteInfo)
                      // console.log(extents);
                      console.log(sites);
                      sites = sites.map(site => {
                          return {
                              type: "Feature",
                              geometry: {
                                  type: "Point",
                                  coordinates: ol.proj.transform(
                                      [
                                          parseFloat(site.longitude),
                                          parseFloat(site.latitude)
                                      ],
                                      "EPSG:4326",
                                      "EPSG:3857"
                                  )
                              },
                              properties: {
                                  name: site.sitename,
                                  code: site.sitecode,
                                  network: site.network,
                                  hs_url: url,
                                  hs_name: title
                              }
                          }
                      })

                      let sitesGeoJSON = {
                          type: "FeatureCollection",
                          crs: {
                              type: "name",
                              properties: {
                                  name: "EPSG:3857"
                              }
                          },
                          features: sites
                      }

                      const vectorSource = new ol.source.Vector({
                          features: new ol.format.GeoJSON().readFeatures(
                              sitesGeoJSON
                          )
                      })

                      const vectorLayer = new ol.layer.Vector({
                          source: vectorSource,
                          style: featureStyle()
                      })

                      map.addLayer(vectorLayer)
                      ol.extent.extend(extent, vectorSource.getExtent())

                      vectorLayer.set("selectable", true)

                      $(newHtml).appendTo("#current-servers")
                      addContextMenuToListItem(
                          $("#current-servers").find("li:last-child")
                      )

                      layersDict[title] = vectorLayer;
              // })

            })

            console.log(keywords_in_servers);
            servers_with_no_keyword = all_servers_titles.filter(x => !keywords_in_servers.includes(x));
            console.log(servers_with_no_keyword);
            if(servers_with_no_keyword.length != all_servers_titles.length){
              servers_with_no_keyword.forEach(function(server_to_remove_from_map){
                  map.removeLayer(layersDict[server_to_remove_from_map]);
                  delete layersDict[server_to_remove_from_map];
                  map.updateSize();
              });
            }

          // load all the hydroservers again for the group //

          // delete the ones that are not in the keyword search this is done in the display and in the map layer
        },
        error: function(error) {
          console.log(error);
        }
      });
    }
  $("#btn-key-search").on("click", get_keywords_from_group);



//************ THIS FUNCTION CREATES A GROUP OF HYDRSOERVERS AND ADDS IT TO THE MENU *******/////
    create_group_hydroservers = function(){
      //CHECKS IF THE INPUT IS EMPTY ///
      if($("#addGroup-title").val() == ""){
        $modalAddGroupHydro.find(".warning").html(  "<b>Please enter a title. This field cannot be blank.</b>")
        return false
      }
      else {
        $modalAddGroupHydro.find(".warning").html("")
      }

      //CHECKS IF THERE IS AN INPUT THAT IS NOT ALLOWED//
      if ($("#addGroup-title").val() != "") {
        var regex = new RegExp("^(?![0-9]*$)[a-zA-Z0-9_]+$")
        var title = $("#addGroup-title").val()
        if (!regex.test(title)) {
            $modalAddGroupHydro
                .find(".warning")
                .html("<b>Please note that only numbers and other characters besides the underscore ( _ ) are not allowed</b>");
            return false
        }
      }
      else {
          $modalAddGroupHydro.find(".warning").html("");
      }

      //CHECKS IF THERE IS AN EMPTY DESCRIPTION //
      if($("#addGroup-description").val() == ""){
        $modalAddGroupHydro.find(".warning").html(  "<b>Please enter a description for this group. This field cannot be blank.</b>")
        return false
      }
      else {
        $modalAddGroupHydro.find(".warning").html("")
      }
      //MAKE THE AJAX REQUEST///
      let elementForm= $("#modalAddGroupServerForm");
      let datastring= elementForm.serialize();
      console.log(typeof(datastring));
      console.log(datastring);
      $("#soapAddLoading").removeClass("hidden");
      // $("#btn-add-addHydro").hide();

      $.ajax({
          type: "POST",
          url: `${apiServer}/create-group/`,
          dataType: "HTML",
          data: datastring,
          success: function(result) {
              //Returning the geoserver layer metadata from the controller
              var json_response = JSON.parse(result)

              let group=json_response
              if(group.message !== "There was an error while adding th group.") {
                let title=group.title;
                let description=group.description;
                // let newHtml = `<li class="ui-state-default" layer-name="${title}">
                // <input class="chkbx-layer" type="checkbox"><span class="group-name">${title}</span>
                // <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                // </li>
                // <ul class="hydroserver-list" style = "display: none">
                // </ul>`
                let newHtml = `<li class="ui-state-default" id="${title}">
                <input class="chkbx-layer" type="checkbox"><span class="group-name">${title}</span>

                <div>
                  <button class="btn btn-warning" data-toggle="modal" data-target="#modalInterface"> <span class="glyphicon glyphicon-option-vertical"></span> </button>
                </div>

                </li>
                <ul id=${title}list class="ul-list" style = "display: none">
                </ul>`

                $(newHtml).appendTo("#current-Groupservers")
                let $title="#"+title;
                let $title_list="#"+title+"list";

                $($title).click(function(){
                  actual_group = `&actual-group=${title}`;
                  console.log(actual_group);
                  console.log($($title_list).is(":visible"));
                  $(".ul-list").hide();
                  $("#current-servers-list").html("");
                  switch ($($title_list).is(":visible")) {
                    case false:
                      // console.log("making visible");
                      $($title_list).show();
                      $("#pop-up_description").show();
                      // get_keywords_from_group(title);
                      load_individual_hydroservers_group(title);
                      break;
                    case true:
                      $($title_list).hide();
                      $("#pop-up_description").html("");
                      $("#pop-up_description").hide();
                      $("#accordion_servers").hide();

                      break;
                  }
                  // console.log(description);
                  let description_html=`<h3><u>${title}</u></h3>
                  <h5>Description:</h5>
                  <p>${description}</p>`;
                  $("#pop-up_description").html(description_html);

                });

                addContextMenuToListItem(
                    $("#current-Groupservers").find("li:last-child")
                )
                $(".ui-state-default").click(function(){
                  console.log("hola");
                });
                    $("#soapAddLoading").addClass("hidden")
                    $("#soapAddLoading").addClass("hidden")
                    $("#btn-add-addHydro").show()

                    $("#modalAddGroupServer").modal("hide")
                    $("#modalAddGroupServerForm").each(function() {
                        this.reset()
                    })

                    // map.getView().fit(vectorSource.getExtent(), map.getSize());

                    $.notify(
                        {
                            message: `Successfully Created Group of HydroServers to the database`
                        },
                        {
                            type: "success",
                            allow_dismiss: true,
                            z_index: 20000,
                            delay: 5000
                        }
                    )

              } else {
                  $("#soapAddLoading").addClass("hidden")
                  $("#btn-add-addHydro").show()
                  $.notify(
                      {
                          message: `Failed to add to the group. Please check and try again.`
                      },
                      {
                          type: "danger",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )
              }
          },
          error: function(error) {
              $("#soapAddLoading").addClass("hidden")
              $("#btn-add-addHydro").show()
              console.log(error)
              $.notify(
                  {
                      message: `There was an error while adding a group of hydroserver`
                  },
                  {
                      type: "danger",
                      allow_dismiss: true,
                      z_index: 20000,
                      delay: 5000
                  }
              )
          }

      })

    };

    $("#btn-add-addHydro").on("click", create_group_hydroservers);
/*
****** FU1NCTION NAME : delete_group_of_hydroservers *********
****** FUNCTION PURPOSE: DELETES THE HYDROSERVER GROUP AND THE HYDROSERVERS INSIDE THE GROUP*********
*/
  delete_group_of_hydroservers = function(){
    let datastring = Object.values($("#current-Groupservers").find(".chkbx-layer"));
    let groups_to_delete=[];
    datastring.forEach(function(data){
      if(data.checked== true){
        let group_name = data.nextElementSibling.innerHTML
        groups_to_delete.push(group_name);
      }
    });
    console.log(groups_to_delete);
    let groups_to_delete_obj={
      groups:groups_to_delete
    };
    $.ajax({
      type: "POST",
      url: `${apiServer}/delete-group/`,
      dataType: "JSON",
      data: groups_to_delete_obj,
      success: function(result){
        console.log(result);
        // var json_response = JSON.parse(result)
        let groups_to_erase = result.groups;
        let hydroservers_to_erase = result.hydroservers;
        console.log(groups_to_erase);
        console.log(hydroservers_to_erase);
        $("#pop-up_description").empty()


        groups_to_erase.forEach(function(group){
          let element=document.getElementById(group);
          element.parentNode.removeChild(element);
        });

        hydroservers_to_erase.forEach(function(hydroserver){
            let layer_name= $(`.ui-state-default[layer-name=${hydroserver}]`);
            let element_erase= layer_name[0];
            element_erase.parentNode.removeChild(element_erase);
            map.removeLayer(layersDict[hydroserver]);
        });
        map.updateSize();

        // var title = json_response.title
        // WE NEED TO ERASE ONLY THE SELECTED OPTION//

        //need to grab the selected id's from the list and delete them//
        // need to make sure the layers are delete from the interface/map if they are
        // by layer name...for the <li> in the box display and by checking the layerDict in the other
        //so if it is there it gets erased....



          $.notify(
              {
                  message: `Successfully Deleted Group of HydroServer!`
              },
              {
                  type: "success",
                  allow_dismiss: true,
                  z_index: 20000,
                  delay: 5000
              }
          )

      }


    })

    // console.log(datastring);
  }
  $("#btn-delete-hydroserver-group").on("click", delete_group_of_hydroservers);

    addExpandableMenu = function(clName){
      let element= document.getElementsByClassName(className);

    }
/*
****** FU1NCTION NAME : load_individual_hydroservers_group*********
****** FUNCTION PURPOSE: LOADS THE SERVERS OF A HYDROSERVER WHEN THE HYDROSERVER GROUPS IS CLICKED*********

*/
   load_individual_hydroservers_group = function(group_name){
    console.log(layersDict);
    // THIS WILL REMOVE ANY LAYERS FROM A HYDROSERVER //
    for (var key of Object.keys(layersDict)) {
        map.removeLayer(layersDict[key])
        delete layersDict[key]
        map.updateSize()
    };

     let group_name_obj={
       group: group_name
     };
     console.log(group_name_obj);
     $.ajax({
         type: "GET",
         url: `${apiServer}/catalog-group/`,
         dataType: "JSON",
         data: group_name_obj,
         success: result => {
             console.log(result);
             let servers = result["hydroserver"]
             console.log("this are the servers");
             console.log(servers);
             $("#current-servers").empty() //Resetting the catalog
             let extent = ol.extent.createEmpty()
             console.log(servers);
             servers.forEach(server => {
                 let {
                     title,
                     url,
                     geoserver_url,
                     layer_name,
                     extents,
                     siteInfo
                 } = server
                 let newHtml = `<li class="ui-state-default" layer-name="${title}">
                 <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                 <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                 </li>`
                 let sites = JSON.parse(siteInfo)
                 // console.log(extents);
                 console.log(sites);
                 sites = sites.map(site => {
                     return {
                         type: "Feature",
                         geometry: {
                             type: "Point",
                             coordinates: ol.proj.transform(
                                 [
                                     parseFloat(site.longitude),
                                     parseFloat(site.latitude)
                                 ],
                                 "EPSG:4326",
                                 "EPSG:3857"
                             )
                         },
                         properties: {
                             name: site.sitename,
                             code: site.sitecode,
                             network: site.network,
                             hs_url: url,
                             hs_name: title
                         }
                     }
                 })

                 let sitesGeoJSON = {
                     type: "FeatureCollection",
                     crs: {
                         type: "name",
                         properties: {
                             name: "EPSG:3857"
                         }
                     },
                     features: sites
                 }

                 const vectorSource = new ol.source.Vector({
                     features: new ol.format.GeoJSON().readFeatures(
                         sitesGeoJSON
                     )
                 })

                 const vectorLayer = new ol.layer.Vector({
                     source: vectorSource,
                     style: featureStyle()
                 })

                 map.addLayer(vectorLayer)
                 ol.extent.extend(extent, vectorSource.getExtent())

                 vectorLayer.set("selectable", true)

                 $(newHtml).appendTo("#current-servers")
                 addContextMenuToListItem(
                     $("#current-servers").find("li:last-child")
                 )

                 layersDict[title] = vectorLayer
             })

             if (servers.length) {
                 map.getView().fit(extent, map.getSize())
                 map.updateSize()
             }
         },
         error: function(error) {
             console.log(error)
             $.notify(
                 {
                     message: `Something went wrong loading the catalog. Please see the console for details.`
                 },
                 {
                     type: "danger",
                     allow_dismiss: true,
                     z_index: 20000,
                     delay: 5000
                 }
             )
         }
     })

   };
 /*
 ****** FU1NCTION NAME : load_group_hydroservers*********
 ****** FUNCTION PURPOSE: LOADS THE GROUPS OF HYDROSERVERS THAT ARE THERE *********
 */
    load_group_hydroservers = function(){
      console.log("hola");
      $.ajax({
          type: "GET",
          url: `${apiServer}/load-groups/`,
          dataType: "JSON",
          success: result => {
            console.log(result);
              let groups =result["hydroservers"];
              // console.log("this are the servers");
              // console.log(groups);
              $("#current-servers").empty() //Resetting the catalog
              let extent = ol.extent.createEmpty()
              // console.log(groups);
              groups.forEach(group => {
                  let {
                      title,
                      description
                  } = group
                  let newHtml = `<li class="ui-state-default" id="${title}">
                  <input class="chkbx-layer" type="checkbox"><span class="group-name">${title}</span>
                  <div>
                    <button class="btn btn-warning" data-toggle="modal" data-target="#modalInterface"> <span class="glyphicon glyphicon-option-vertical"></span> </button>
                  </div>

                  </li>
                  <ul id=${title}list class="ul-list" style = "display: none">
                  </ul>`
                  $(newHtml).appendTo("#current-Groupservers");
                  let $title="#"+title;
                  let $title_list="#"+title+"list";

                  $($title).click(function(){
                    actual_group = `&actual-group=${title}`;
                    console.log(actual_group);
                    console.log($($title_list).is(":visible"));
                    $(".ul-list").hide();
                    $("#current-servers-list").html("");
                    switch ($($title_list).is(":visible")) {
                      case false:
                        // console.log("making visible");
                        $($title_list).show();
                        $("#pop-up_description").show();
                        // get_keywords_from_group(title);
                        load_individual_hydroservers_group(title);
                        break;
                      case true:
                        $($title_list).hide();
                        $("#pop-up_description").html("");
                        $("#pop-up_description").hide();
                        $("#accordion_servers").hide();

                        break;
                    }
                    // console.log(description);
                    let description_html=`<h3><u>${title}</u></h3>
                    <h5>Description:</h5>
                    <p>${description}</p>`;
                    $("#pop-up_description").html(description_html);

                  });

                  addContextMenuToListItem(
                      $("#current-Groupservers").find("li:last-child")
                  )
              })
      },
      error: function(error) {
          $("#soapAddLoading").addClass("hidden")
          $("#btn-add-addHydro").show()
          console.log(error)
          $.notify(
              {
                  message: `There was an error while adding a group of hydroserver`
              },
              {
                  type: "danger",
                  allow_dismiss: true,
                  z_index: 20000,
                  delay: 5000
              }
          )
      }

    })
  }

  /*
  ****** FU1NCTION NAME: add_hydroserver *********
  ****** FUNCTION PURPOSE: ADD AN INDIVIDUAL HYDROSERVER TO A GROUP *********
  */

  add_hydroserver = function(){
    if($("#extent").is(":checked")){
      var zoom= map.getView().getZoom();
      if(zoom < 8){
          $modalAddSOAP.find(".warning").html("<b>The zoom level has to be 8 or greater. Please check and try again.</b>")
          return false
      }
      else {
        $modalAddSOAP.find(".warning").html("")
      }
      $('#chk_val').empty()
      var level=map.getView().calculateExtent(map.getSize())
      $(
            '<input type="text" name="extent_val" id="extent_val" value=' +
                '"' +
                level +
                '"' +
                " hidden>"
        ).appendTo($("#chk_val"))
    }
    if($("#soap-title").val() == ""){
      $modalAddSOAP.find(".warning").html(  "<b>Please enter a title. This field cannot be blank.</b>")
      return false
    }
    else {
      $modalAddSOAP.find(".warning").html("")
    }
    if(
      $("#soap-url").val() == "http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL" ||
      $("#soap-url").val() =="http://hydroportal.cuahsi.org/nwisuv/cuahsi_1_1.asmx?WSDL")
      {
        $modalAddSOAP
              .find(".warning")
              .html(
                  "<b>Please zoom in further to be able to access the NWIS Values</b>"
              )
          return false
      }
      else {
          $modalAddSOAP.find(".warning").html("")
      }
      if ($("#soap-title").val() != "") {
        var regex = new RegExp("^[a-zA-Z ]+$")
        var title = $("#soap-title").val()
        if (!regex.test(title)) {
            $modalAddSOAP
                .find(".warning")
                .html("<b>Please enter Letters only for the title.</b>");
            return false
        }
      } else {
          $modalAddSOAP.find(".warning").html("");
      }
      var datastring = $modalAddSOAP.serialize();
      datastring += actual_group;

      console.log("This is the serialize string of datastring");
      console.log(datastring);
      //Submitting the data to the controller
      $("#soapAddLoading").removeClass("hidden");
      $("#btn-add-soap").hide();
      $.ajax({
          type: "POST",
          url: `${apiServer}/soap-group/`,
          dataType: "HTML",
          data: datastring,
          success: function(result) {
              //Returning the geoserver layer metadata from the controller
              var json_response = JSON.parse(result)
              console.log("This is the result from the controllers function call");
              console.log(json_response);
              if (json_response.status === "true") {
                  let {title, siteInfo, url, group} = json_response

                  let newHtml = `<li class="ui-state-default" layer-name="${title}">
                  <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                  <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                  </li>`

                  let sites = JSON.parse(siteInfo)
                  console.log("These are the sites");
                  console.log(sites);
                  sites = sites.map(site => {
                      return {
                          type: "Feature",
                          geometry: {
                              type: "Point",
                              coordinates: ol.proj.transform(
                                  [
                                      parseFloat(site.longitude),
                                      parseFloat(site.latitude)
                                  ],
                                  "EPSG:4326",
                                  "EPSG:3857"
                              )
                          },
                          properties: {
                              name: site.sitename,
                              code: site.sitecode,
                              network: site.network,
                              hs_url: url,
                              hs_name: title
                          }
                      }
                  })

                  let sitesGeoJSON = {
                      type: "FeatureCollection",
                      crs: {
                          type: "name",
                          properties: {
                              name: "EPSG:3857"
                          }
                      },
                      features: sites
                  }

                  const vectorSource = new ol.source.Vector({
                      features: new ol.format.GeoJSON().readFeatures(
                          sitesGeoJSON
                      )
                  })

                  const vectorLayer = new ol.layer.Vector({
                      source: vectorSource,
                      style: featureStyle()
                  })

                  map.addLayer(vectorLayer)
                  console.log("this is the vector layer baby");
                  console.log(vectorLayer);
                  console.log("this is the geojson layer baby");
                  console.log(sitesGeoJSON);

                  vectorLayer.set("selectable", true)

                  $(newHtml).appendTo("#current-servers")
                  addContextMenuToListItem(
                      $("#current-servers").find("li:last-child")
                  )

                  layersDict[title] = vectorLayer
                  $("#soapAddLoading").addClass("hidden")
                  $("#btn-add-soap").show()

                  $("#modalAddSoap").modal("hide")
                  $("#modalAddSoap").each(function() {
                      this.reset()
                  })

                  // map.getView().fit(vectorSource.getExtent(), map.getSize());

                  $.notify(
                      {
                          message: `Successfully Added the HydroServer to the Map`
                      },
                      {
                          type: "success",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )
              } else {
                  $("#soapAddLoading").addClass("hidden")
                  $("#btn-add-soap").show()
                  $.notify(
                      {
                          message: `Failed to add server. Please check Url and try again.`
                      },
                      {
                          type: "danger",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )
              }
          },
          error: function(error) {
              $("#soapAddLoading").addClass("hidden")
              $("#btn-add-soap").show()
              console.log(error)
              $.notify(
                  {
                      message: `Invalid Hydroserver SOAP Url. Please check and try again.`
                  },
                  {
                      type: "danger",
                      allow_dismiss: true,
                      z_index: 20000,
                      delay: 5000
                  }
              )
          }
      })

  }

  $("#btn-add-soap").on("click", add_hydroserver);


  delete_hydroserver= function(){
      $modalInterface.find(".success").html("")
      let arrayActual_group=actual_group.split('=')[1];
      var datastring = $modalDelete.serialize() //Delete the record in the database
      datastring += actual_group;
      console.log(datastring);
      $.ajax({
          type: "POST",
          url: `${apiServer}/delete-group-hydroserver/`,
          data: datastring,
          dataType: "HTML",
          success: function(result) {
              console.log(result);
              var json_response = JSON.parse(result)
              // var title = json_response.title
              $("#current-servers").empty() //Resetting the catalog. So that it is updated.
              $("#modalDelete").modal("hide")
              $("#modalDelete").each(function() {
                  this.reset()
              })
              for(let i=0; i<Object.keys(json_response).length; ++i){

                let i_string=i.toString();
                let title=json_response[i_string];
                //Removing layer from the frontend
                console.log(title);
                map.removeLayer(layersDict[title])
                delete layersDict[title]
                map.updateSize()
                console.log(arrayActual_group);
                load_individual_hydroservers_group(arrayActual_group) //Reloading the new catalog

                $.notify(
                    {
                        message: `Successfully Deleted the HydroServer!`
                    },
                    {
                        type: "success",
                        allow_dismiss: true,
                        z_index: 20000,
                        delay: 5000
                    }
                )


              }
              // //Removing layer from the frontend
              // map.removeLayer(layersDict[title])
              // delete layersDict[title]
              // map.updateSize()
              // load_catalog() //Reloading the new catalog
              //
              // $.notify(
              //     {
              //         message: `Successfully Deleted the HydroServer!`
              //     },
              //     {
              //         type: "success",
              //         allow_dismiss: true,
              //         z_index: 20000,
              //         delay: 5000
              //     }
              // )
          },
          error: error => {
              console.log(error)
          }
      })
  }
  $("#btn-del-server").on("click", delete_hydroserver)

  get_hs_list_from_hydroserver = function(){
    if(actual_group == undefined){
      actual_group="";
    }
    let arrayActual_group=actual_group.split('=')[1];
    console.log(arrayActual_group);
      let group_name_obj={
        group: arrayActual_group
      };
      $.ajax({
          type: "GET",
          url: `${apiServer}/catalog-group/`,
          dataType: "JSON",
          data:group_name_obj,
          success: function(result) {
              //Dynamically generate the list of existing hydroservers
              var server = result["hydroserver"]
              var HSTableHtml =
                  '<table id="tbl-hydroservers"><thead><th></th><th>Title</th><th>URL</th></thead><tbody>'
              if (server.length === 0) {
                  $modalDelete
                      .find(".modal-body")
                      .html(
                          "<b>There are no hydroservers in the Catalog.</b>"
                      )
              } else {
                  for (var i = 0; i < server.length; i++) {
                      var title = server[i].title
                      var url = server[i].url
                      HSTableHtml +=
                          "<tr>" +
                          '<td><input type="checkbox" name="server" id="server" value="' +
                          title +
                          '"></td>' +
                          '<td class="hs_title">' +
                          title +
                          "</td>" +
                          '<td class="hs_url">' +
                          url +
                          "</td>" +
                          "</tr>"
                  }
                  HSTableHtml += "</tbody></table>"
                  $modalDelete.find(".modal-body").html(HSTableHtml)
              }
          },
          error: function(error) {
              console.log(error)
          }
      })
  }
  $("#delete-server").on("click", get_hs_list_from_hydroserver);

    add_soap=function(){
      if($("#extent").is(":checked")){
        var zoom= map.getView().getZoom();
        if(zoom < 8){
            $modalAddSOAP.find(".warning").html("<b>The zoom level has to be 8 or greater. Please check and try again.</b>")
            return false
        }
        else {
          $modalAddSOAP.find(".warning").html("")
        }
        $('#chk_val').empty()
        var level=map.getView().calculateExtent(map.getSize())
        $(
              '<input type="text" name="extent_val" id="extent_val" value=' +
                  '"' +
                  level +
                  '"' +
                  " hidden>"
          ).appendTo($("#chk_val"))
      }
      if($("#soap-title").val() == ""){
        $modalAddSOAP.find(".warning").html(  "<b>Please enter a title. This field cannot be blank.</b>")
        return false
      }
      else {
        $modalAddSOAP.find(".warning").html("")
      }
      if(
        $("#soap-url").val() == "http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL" ||
        $("#soap-url").val() =="http://hydroportal.cuahsi.org/nwisuv/cuahsi_1_1.asmx?WSDL")
        {
          $modalAddSOAP
                .find(".warning")
                .html(
                    "<b>Please zoom in further to be able to access the NWIS Values</b>"
                )
            return false
        }
        else {
            $modalAddSOAP.find(".warning").html("")
        }
        if ($("#soap-title").val() != "") {
          var regex = new RegExp("^[a-zA-Z ]+$")
          var title = $("#soap-title").val()
          if (!regex.test(title)) {
              $modalAddSOAP
                  .find(".warning")
                  .html("<b>Please enter Letters only for the title.</b>");
              return false
          }
        } else {
            $modalAddSOAP.find(".warning").html("");
        }
        var datastring = $modalAddSOAP.serialize();

        console.log("This is the serialize string of datastring");
        console.log(datastring);
        //Submitting the data to the controller
        $("#soapAddLoading").removeClass("hidden");
        $("#btn-add-soap").hide();
        $.ajax({
            type: "POST",
            url: `${apiServer}/soap/`,
            dataType: "HTML",
            data: datastring,
            success: function(result) {
                //Returning the geoserver layer metadata from the controller
                var json_response = JSON.parse(result)
                console.log("This is the result from the controllers function call");
                console.log(json_response);
                if (json_response.status === "true") {
                    let {title, siteInfo, url} = json_response

                    let newHtml = `<li class="ui-state-default" layer-name="${title}">
                    <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                    <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                    </li>`

                    let sites = JSON.parse(siteInfo)
                    console.log("These are the sites");
                    console.log(sites);
                    sites = sites.map(site => {
                        return {
                            type: "Feature",
                            geometry: {
                                type: "Point",
                                coordinates: ol.proj.transform(
                                    [
                                        parseFloat(site.longitude),
                                        parseFloat(site.latitude)
                                    ],
                                    "EPSG:4326",
                                    "EPSG:3857"
                                )
                            },
                            properties: {
                                name: site.sitename,
                                code: site.sitecode,
                                network: site.network,
                                hs_url: url,
                                hs_name: title
                            }
                        }
                    })

                    let sitesGeoJSON = {
                        type: "FeatureCollection",
                        crs: {
                            type: "name",
                            properties: {
                                name: "EPSG:3857"
                            }
                        },
                        features: sites
                    }

                    const vectorSource = new ol.source.Vector({
                        features: new ol.format.GeoJSON().readFeatures(
                            sitesGeoJSON
                        )
                    })

                    const vectorLayer = new ol.layer.Vector({
                        source: vectorSource,
                        style: featureStyle()
                    })

                    map.addLayer(vectorLayer)
                    console.log("this is the vector layer baby");
                    console.log(vectorLayer);
                    console.log("this is the geojson layer baby");
                    console.log(sitesGeoJSON);

                    vectorLayer.set("selectable", true)

                    $(newHtml).appendTo("#current-servers")
                    addContextMenuToListItem(
                        $("#current-servers").find("li:last-child")
                    )

                    layersDict[title] = vectorLayer
                    $("#soapAddLoading").addClass("hidden")
                    $("#btn-add-soap").show()

                    $("#modalAddSoap").modal("hide")
                    $("#modalAddSoap").each(function() {
                        this.reset()
                    })

                    // map.getView().fit(vectorSource.getExtent(), map.getSize());

                    $.notify(
                        {
                            message: `Successfully Added the HydroServer to the Map`
                        },
                        {
                            type: "success",
                            allow_dismiss: true,
                            z_index: 20000,
                            delay: 5000
                        }
                    )
                } else {
                    $("#soapAddLoading").addClass("hidden")
                    $("#btn-add-soap").show()
                    $.notify(
                        {
                            message: `Failed to add server. Please check Url and try again.`
                        },
                        {
                            type: "danger",
                            allow_dismiss: true,
                            z_index: 20000,
                            delay: 5000
                        }
                    )
                }
            },
            error: function(error) {
                $("#soapAddLoading").addClass("hidden")
                $("#btn-add-soap").show()
                console.log(error)
                $.notify(
                    {
                        message: `Invalid Hydroserver SOAP Url. Please check and try again.`
                    },
                    {
                        type: "danger",
                        allow_dismiss: true,
                        z_index: 20000,
                        delay: 5000
                    }
                )
            }
        })
    }

    // $("#btn-add-soap").on("click", add_soap);

    get_hs_list = function() {
      console.log("hola");
        $.ajax({
            type: "GET",
            url: `${apiServer}/catalog/`,
            dataType: "JSON",
            success: function(result) {
                //Dynamically generate the list of existing hydroservers
                var server = result["hydroserver"]
                var HSTableHtml =
                    '<table id="tbl-hydroservers"><thead><th></th><th>Title</th><th>URL</th></thead><tbody>'
                if (server.length === 0) {
                    $modalDelete
                        .find(".modal-body")
                        .html(
                            "<b>There are no hydroservers in the Catalog.</b>"
                        )
                } else {
                    for (var i = 0; i < server.length; i++) {
                        var title = server[i].title
                        var url = server[i].url
                        HSTableHtml +=
                            "<tr>" +
                            '<td><input type="checkbox" name="server" id="server" value="' +
                            title +
                            '"></td>' +
                            '<td class="hs_title">' +
                            title +
                            "</td>" +
                            '<td class="hs_url">' +
                            url +
                            "</td>" +
                            "</tr>"
                    }
                    HSTableHtml += "</tbody></table>"
                    $modalDelete.find(".modal-body").html(HSTableHtml)
                }
            },
            error: function(error) {
                console.log(error)
            }
        })
    }
    // $("#delete-server").on("click", get_hs_list);

    //Deleting a layer from the database and then deleting it from the frontend
    update_catalog = function() {
      console.log("hola");
        $modalInterface.find(".success").html("")
        var datastring = $modalDelete.serialize() //Delete the record in the database
        console.log(datastring);
        $.ajax({
            type: "POST",
            url: `${apiServer}/delete/`,
            data: datastring,
            dataType: "HTML",
            success: function(result) {
                console.log(result);
                var json_response = JSON.parse(result)
                // var title = json_response.title
                $("#current-servers").empty() //Resetting the catalog. So that it is updated.
                $("#modalDelete").modal("hide")
                $("#modalDelete").each(function() {
                    this.reset()
                })
                for(let i=0; i<Object.keys(json_response).length; ++i){

                  let i_string=i.toString();
                  let title=json_response[i_string];
                  //Removing layer from the frontend
                  console.log(title);
                  map.removeLayer(layersDict[title])
                  delete layersDict[title]
                  map.updateSize()
                  load_catalog() //Reloading the new catalog

                  $.notify(
                      {
                          message: `Successfully Deleted the HydroServer!`
                      },
                      {
                          type: "success",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )


                }
                // //Removing layer from the frontend
                // map.removeLayer(layersDict[title])
                // delete layersDict[title]
                // map.updateSize()
                // load_catalog() //Reloading the new catalog
                //
                // $.notify(
                //     {
                //         message: `Successfully Deleted the HydroServer!`
                //     },
                //     {
                //         type: "success",
                //         allow_dismiss: true,
                //         z_index: 20000,
                //         delay: 5000
                //     }
                // )
            },
            error: error => {
                console.log(error)
            }
        })
    }

    // $("#btn-del-server").on("click", update_catalog)

    //Load all the existing layers from the database
      load_catalog = () => {
          $.ajax({
              type: "GET",
              url: `${apiServer}/catalog/`,
              dataType: "JSON",
              success: result => {
                  let servers = result["hydroserver"]
                  console.log("this are the servers");
                  console.log(servers);
                  $("#current-servers").empty() //Resetting the catalog
                  let extent = ol.extent.createEmpty()
                  console.log(servers);
                  servers.forEach(server => {
                      let {
                          title,
                          url,
                          geoserver_url,
                          layer_name,
                          extents,
                          siteInfo
                      } = server
                      let newHtml = `<li class="ui-state-default" layer-name="${title}">
                      <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                      <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                      </li>`

                      let sites = JSON.parse(siteInfo)
                      console.log(extents);
                      console.log(sites);
                      sites = sites.map(site => {
                          return {
                              type: "Feature",
                              geometry: {
                                  type: "Point",
                                  coordinates: ol.proj.transform(
                                      [
                                          parseFloat(site.longitude),
                                          parseFloat(site.latitude)
                                      ],
                                      "EPSG:4326",
                                      "EPSG:3857"
                                  )
                              },
                              properties: {
                                  name: site.sitename,
                                  code: site.sitecode,
                                  network: site.network,
                                  hs_url: url,
                                  hs_name: title
                              }
                          }
                      })

                      let sitesGeoJSON = {
                          type: "FeatureCollection",
                          crs: {
                              type: "name",
                              properties: {
                                  name: "EPSG:3857"
                              }
                          },
                          features: sites
                      }

                      const vectorSource = new ol.source.Vector({
                          features: new ol.format.GeoJSON().readFeatures(
                              sitesGeoJSON
                          )
                      })

                      const vectorLayer = new ol.layer.Vector({
                          source: vectorSource,
                          style: featureStyle()
                      })

                      map.addLayer(vectorLayer)
                      ol.extent.extend(extent, vectorSource.getExtent())

                      vectorLayer.set("selectable", true)

                      $(newHtml).appendTo("#current-servers")
                      addContextMenuToListItem(
                          $("#current-servers").find("li:last-child")
                      )

                      layersDict[title] = vectorLayer
                  })

                  if (servers.length) {
                      map.getView().fit(extent, map.getSize())
                      map.updateSize()
                  }
              },
              error: function(error) {
                  console.log(error)
                  $.notify(
                      {
                          message: `Something went wrong loading the catalog. Please see the console for details.`
                      },
                      {
                          type: "danger",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )
              }
          })
      }
  const add_central = () => {
      let modal = $("#addCentral"),
          mWarning = modal.find(".warning"),
          titleVal = $("#title").val()
      // Clear all existing Warnings
      modal.find(".warning").html("")

      if (titleVal == "") {
          mWarning.html(
              "<b>Please enter a title. This field cannot be blank.</b>"
          )
          return false
      } else {
          let regex = new RegExp("^[a-zA-Z ]+$")
          if (!regex.test(titleVal)) {
              mWarning.html("<b>Please enter Letters only for the title.</b>")
              return false
          }
      }
      if ($("#url").val() == "") {
          mWarning.html(
              "<b>Please enter a valid URL. This field cannot be blank.</b>"
          )
          return false
      }
      $.ajax({
          type: "POST",
          url: `${apiServer}/add-central/`,
          dataType: "json",
          data: {
              title: titleVal,
              url: $("#url").val()
          },
          success: result => {
            console.log(result);
              if (result.status) {
                  // Close main modal
                  modal.modal("hide")
                  modal.each(function() {
                      this.reset()
                  })
                  // modal.hide()
                  $.notify(
                      {
                          message: `Server Successfully Added. You may use it to add HydroServers`
                      },
                      {
                          type: "success",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 5000
                      }
                  )
              } else {
                  $.notify(
                      {
                          message: `Error! Couldn't add HIS Catalog service: ${
                              result.message
                          }.`
                      },
                      {
                          type: "danger",
                          allow_dismiss: true,
                          z_index: 20000,
                          delay: 10000
                      }
                  )
              }
          },
          error: error => {
              console.log(error)
              $.notify(
                  {
                      message: `Error! Couldn't add HIS Catalog service: ${
                          error.statusText
                      }. Please check the URL`
                  },
                  {
                      type: "danger",
                      allow_dismiss: true,
                      z_index: 20000,
                      delay: 10000
                  }
              )
          }
      })
  }
  $("#btn-add-central").on("click", add_central);
  //The following three functions are necessary to make dynamic ajax requests
  addDefaultBehaviorToAjax = function() {
      // Add CSRF token to appropriate ajax requests
      $.ajaxSetup({
          beforeSend: function(xhr, settings) {
              if (!checkCsrfSafe(settings.type) && !this.crossDomain) {
                  xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
              }
          }
      })
  }
  checkCsrfSafe = function(method) {
      // these HTTP methods do not require CSRF protection
      return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
  }
  getCookie = function(name) {
      var cookie
      var cookies
      var cookieValue = null
      var i
      if (document.cookie && document.cookie !== "") {
          cookies = document.cookie.split(";")
          for (i = 0; i < cookies.length; i += 1) {
              cookie = $.trim(cookies[i])
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) === name + "=") {
                  cookieValue = decodeURIComponent(
                      cookie.substring(name.length + 1)
                  )
                  break
              }
          }
      }
      return cookieValue
  }
  //Initialize the context menu (The little hamburger in the Current HydroServers list item). It currently supports zoom to or delete layer. You can add more functionality here.
  init_menu = function() {
      ContextMenuBase = [
          {
              name: "Add a HydroServer",
              title: "Add a HydroServer",
              fun: function(e) {
                  onClickZoomTo(e)
              }
          },
          {
              name: "Delete HydroServer",
              title: "Delete hydroserver",
              fun: function(e) {
                  onClickDeleteLayer(e)
              }
          }
      ]
  }

  /************************************************************************
   *                  INITIALIZATION / CONSTRUCTOR
   *************************************************************************/
  $(function() {

      init_jquery_var()
      addDefaultBehaviorToAjax()
      load_group_hydroservers()
      init_menu()
      init_map()
      // load_catalog()
      createDropdownMenu(cata);
  })
})() // End of package wrapper
