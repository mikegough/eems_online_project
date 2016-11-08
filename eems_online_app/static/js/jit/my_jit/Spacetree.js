var labelType, useGradients, nativeTextSupport, animate;
modelForTree="intactness"
resultsJSON=""

//default renderer
//renderer=EEMSParams['defaultRenderer']
renderer="continuous"

function switchRenderer(node_id,renderer_arg){
    if (renderer_arg=="classified") {
        $("#" + node_id + "_classified").prop("checked", true)
    }
    else if (renderer_arg=="stretched") {
        $("#" + node_id + "_stretched").prop("checked", true)
    }
}

(function() {

  var ua = navigator.userAgent,
      iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
      typeOfCanvas = typeof HTMLCanvasElement,
      nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
      textSupport = nativeCanvasSupport 
        && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
  //I'm setting this based on the fact that ExCanvas provides text support for IE
  //and that as of today iPhone/iPad current text support is lame
  labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
  nativeTextSupport = labelType == 'Native';
  useGradients = nativeCanvasSupport;
  animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
  elem: false,
  write: function(text){
    if (!this.elem) 
      this.elem = document.getElementById('log');
    this.elem.innerHTML = text;
    //this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
    this.elem.style.left = 0 + 'px';
    this.elem.style.top = -30 + 'px';
    this.elem.style.verticalAlign = 'top';
  }
};


//function for scaling the labels when you zoom (mouse wheel in and out)
function setLabelScaling() {

    var x = st.canvas.scaleOffsetX,

    y = st.canvas.scaleOffsetY;

    $(".node").css("-moz-transform", "scale(" + x +"," +  y + ")");

    $(".node").css("-webkit-transform", "scale(" + x +"," + y + ")");

    $(".node").css("-ms-transform", "scale(" + x +"," +  y + ")");

    $(".node").css("-o-transform", "scale(" + x +"," +  y + ")");

}

function init(json, eems_file_name){
   $("#infovis").empty()
   JitInitializationComplete=true
    //Create a new ST instance
    st = new $jit.ST({
        //id of viz container element
        injectInto: 'infovis',
        orientation:"top",
        //Higher numbers = higher on the page
        //offsetY:120,
        offsetY:200,
        //To Show all nodes. Set to false. modify LevelsToShow.
        constrained:true,
        levelsToShow: 4,
        //set duration for the animation
        duration: 800,
        //set animation transition type
        transition: $jit.Trans.Quart.easeInOut,
        //set distance between node and its children
        levelDistance: 50,
        //enable panning
        Navigation: {
          enable:true,
          panning:true,
          zooming:20,
        },
        //set node and edge styles
        //set overridable=true for styling individual
        //nodes or edges
        Node: {
            height: 70,
            width: 159,
            type: 'rectangle',
            color: '#B6BFD3',
            overridable: true,
            //align:'center',
            alpha:1
        },
        Edge: {
            type: 'bezier',
            overridable: true
        },

        onMouseWheel: function(node){
            setLabelScaling()
        },

        onBeforeCompute: function(node){
            loadingTitle=node.name.split(':')[0].replace('<br>',' ').replace('<br>',' ') +"..."
            //Log.write("Loading " + loadingTitle);
            Log.write("Loading EEMS Model Diagram...");
        },
        
        onAfterCompute: function(){
            //Log.write(EEMSParams["models"][modelForTree][1] + ": Click boxes to show inputs");
            Log.write("Click boxes to show inputs");
            //$(".EEMS_Tree_Value").remove()
            //$("#" + top_node).append("<div class='EEMS_Tree_Value'>"  + resultsJSON['c5tmids1t1_avg'] + "</div>")
            if (typeof resultsJSON[modelForTree+"_avg"] != 'undefined') {
                $(".EEMS_Tree_Value").remove()
                $("#" + top_node).append("<div class='EEMS_Tree_Value'>" + resultsJSON[modelForTree+"_avg"] + "</div>")

            }
        },

        onPlaceLabel: function(label, node, controllers){
            //override label styles
            var style = label.style;

            if (node.selected) {
              //style.color = '';
              //style.fontWeight= 'bold';
            }
            else {
              //style.fontWeight= 'normal';
              //style.color = '#fff';
            }
            // show the label and let the canvas clip it
            //This is what prevents the text from disappearing when a node goes off the canvas
            style.display = '';
        },

        //This method is called on DOM label creation.
        //Use this method to add event handlers and styles to
        //your node.
        onCreateLabel: function(label, node){
            label.id = node.id;

            alias=node.name.split(':')[0]
            layer_index=node.name.split(':')[1]

            if (typeof(node.data.short_desc) != 'undefined') {
                label.innerHTML = alias + "<br>" + "<div id='" + node.id + "_current_operator' class='EEMS_Tree_Operation' title='" + node.data.short_desc + "'> " + node.data.operation + "</div>";
            } else {
                label.innerHTML = alias + "<br>" + "<div id='" + node.id + "_current_operator' class='EEMS_Tree_Operation' title='This is the operation used to create this node'> " + node.data.operation + "</div>";
            }

            /*
            $("#" + node.id + "_change_button").click(function( event ) {
                    alert(this)
                    event.stopPropagation();
            });
            */

            // Get a list of direct children for this node for making the form.

            eems_children_dict[node.id]=[]

            node.eachSubnode(function(child){
               //eems_children_dict[node.id].push(child)
               eems_children_dict[node.id].push(child.name)
            });

            if (node.data.operation != "Read") {
                label.innerHTML += "<span id='close_span' title='Click to change the EEMS operations'><img id='close_icon' onclick=\"remove_node('" + label.id + "')\" src='static/img/close.svg'></span>"
                label.innerHTML += "<span id='modify_span' title='Click to change the EEMS operations'><img id='modify_icon' onclick=\"changeEEMSOperator('" + node.id + "','" + alias + "','" + node.data.operation + "','" + eems_children_dict[node.id] + "')\" src='static/img/gear_icon.svg'></span>"
            }

            if (EEMSParams['hasSubNodeImageOverlays']){

                if (node.id.indexOf("Fz") >= 1) {
                    //Change renderer options. Clicking a color ramp selects the corresponding radio button.
                    //Whichever radio button is set to checked below sets the default renderer.
                    /*
                    label.innerHTML += '<span style="display:none"><input type="radio" name="' + node.id + '" id="' + node.id + '_classified" value="classified">class</span>';
                    label.innerHTML += '<span style="display:none"><input type="radio" checked   name="' + node.id + '"id="' + node.id + '_stretched" value="stretched">stretch</span>';
                    label.innerHTML += '<span title="Click to apply a classified renderer to the map" style="position:absolute; float:right; top:0px; right:12px"><img onclick=switchRenderer("' + node.id + '","classified") id="' + node.id + '_image" style="height:51px; width:10px" src="' + static_url + 'Leaflet/myPNG/climate/' + climateParams['imageOverlayDIR'] + '/Legends/' + EEMSParams["models"][modelForTree][2] + '.png"></span>'
                    label.innerHTML += '<span title="Click to apply a stretched renderer to the map" style="position:absolute; float:right; top:-7px; right:-30px"><img onclick=switchRenderer("' + node.id + '","stretched") id="' + node.id + '_image" style="height:62px; width:40px" src="' + static_url + 'Leaflet/myPNG/climate/' + climateParams['imageOverlayDIR'] + '/Stretched/' + legendImage + '.png"></span>'
                    */
                } else {
                    //Non-Fuzzy inputs don't have a classified renderer.
                    label.innerHTML += '<span style="display:none"><input type="radio"  checked name="' + node.id + '"id="' + node.id + '_stretched" value="stretched">stretch</span>';
                }
            }

            label.onclick = function(){


                //Fix for nodes shooting off the screen after panning then clicking.
                var m = {
                    offsetX:st.canvas.translateOffsetX,
                    offsetY:st.canvas.translateOffsetY + 130
                };

                st.onClick(node.id, { Move: m });

                //if( normal.checked) {
                if( 1==1) {
            	st.onClick(node.id);

                    if (EEMSParams['hasSubNodeImageOverlays'] == true) {

                        //Get renderer type on click based on the selected hidden radio button option
                        renderer = $("#" + node.id + " input[type='radio']:checked").val()

                        eems_node_image_name = eems_file_name.replace(".eem", "") + "_" + node.id
                        //Note: have to do swapImageOverlay before swapLegend
                        //swapImageOverlay(eems_node_image_name, 'EEMSmodel')

                        //For stretched
                        if (renderer == 'stretched') {
                            //swapLegend(node.id + "_legend", node.name, 'EEMSmodelTREE_Stretched')
                            //swapLegend(node.id, node.name, 'EEMSmodelTREE_Stretched')
                        }
                        //For classified (original)
                        else {
                            //swapLegend(modelForTree, node.name, 'EEMSmodelTREE_Standard')
                        }
                    }
                    $('#legendHeader').html(alias)

            	} else {
                    st.setRoot(node.id, 'animate');
            	}

               //Code for expanding/contracting nodes (toggle) Not working correctly

                /*
               if(!node.anySubnode("exist")) {
                     node['collapsed']=true;
                     node.eachSubgraph(function(subnode) {
                                               if(node.id!=subnode.id)
                                                 {
                                                    subnode.drawn=false;
                                                    subnode.setData('alpha',1);
                                                 }
                                });
                   st.onClick(node.id, { Move: m });

               } else {
                    node['collapsed']=false;

                        node.eachSubgraph(function(subnode) {
                               if(node.id!=subnode.id)
                                 {
                                  subnode.exist=false;
                                  subnode.drawn=false;
                                  subnode.setData('alpha',0);
                                 }

                                });
                   st.onClick(node.id, { Move: m });

               }
               */

            };

            //set label styles
            //Width + Padding should equal the node width to prevent formatting issues.
            var style = label.style;
            style.width = 125 + 'px';
            style.height = 65 + 'px';
            style.cursor = 'pointer';
            style.color = '#000000';
            style.fontWeight = 'normal';
            style.fontSize = '.8em';
            style.textAlign = 'center';
            style.paddingTop = '5px';
            style.paddingLeft = '15px';
            style.paddingRight = '18px';
            style.fontFamily = 'Verdana';
            style.overflow= 'hidden';
            style.boxShadow= '0px 0px 3px rgba(0, 0, 0, 0.8)';

        },

        
        //This method is called right before plotting
        //a node. It's useful for changing an individual node
        //style properties before plotting it.
        //The data properties prefixed with a dollar
        //sign will override the global node style properties.
        onBeforePlotNode: function(node){
            setLabelScaling()
            //add some color to the nodes in the path between the
            //root node and the selected node.
            if (node.selected) {
                node.data.$color = "#99C199";
            }
            else {
                delete node.data.$color;
                //if the node belongs to the last plotted level
                if(!node.anySubnode("exist")) {
                    //count children number
                    var count = 0;
                    node.eachSubnode(function(n) { count++; });
                    //assign a node color based on
                    //how many children it has
                    //node.data.$color = ['#aaa', '#baa', '#caa', '#daa', '#eaa', '#faa'][count];
                    node.data.$color = ['#AAAAAA','#B2BCD0','#B2BCD0','#B2BCD0','#B2BCD0','#B2BCD0','#B2BCD0','#B2BCD0'][count];
                    node.data.$color = ['#AAAAAA','#B6BFD3','#B6BFD3','#B6BFD3','#B6BFD3','#B6BFD3','#B6BFD3','#B6BFD3'][count];
                    /*
                    if (count == 0){
                        node.data.$color = '#aaa';
                    }
                    else{
                        node.data.$color = '#baa';
                    }
                    */
                }
            }
        },
        
        //This method is called right before plotting
        //an edge. It's useful for changing an individual edge
        //style properties before plotting it.
        //Edge data proprties prefixed with a dollar sign will
        //override the Edge global style properties.
        onBeforePlotLine: function(adj){
            if (adj.nodeFrom.selected && adj.nodeTo.selected) {
                adj.data.$color = "#eed";
                adj.data.$lineWidth = 3;
            }
            else {
                delete adj.data.$color;
                delete adj.data.$lineWidth;
            }
        }
    });
    //load json data
    st.loadJSON(json);
    //compute node positions and layout
    st.compute();
    //optional: make a translation of the tree
    //st.geom.translate(new $jit.Complex(-200, 0), "current");
    //emulate a click on the root node.
    st.onClick(st.root);


    //end
    //Add event handlers to switch spacetree orientation.
    var top = $jit.id('r-top'), 
        left = $jit.id('r-left'), 
        bottom = $jit.id('r-bottom'), 
        right = $jit.id('r-right'),
        normal = $jit.id('s-normal');


    function changeHandler() {
        if(this.checked) {
            top.disabled = bottom.disabled = right.disabled = left.disabled = true;
            st.switchPosition(this.value, "animate", {
                onComplete: function(){
                    top.disabled = bottom.disabled = right.disabled = left.disabled = false;
                }
            });
        }
    };

    //top.onchange = left.onchange = bottom.onchange = right.onchange = changeHandler;
    //end

}

function remove_node(label_id) {
    alertify.confirm("<b>Notice</b>: This will remove the " +  label_id + " node and all of its children nodes. <br><br><b>This action cannot be undone.</b>", function (e, str) {
        if (e) {
            removing = true;
            Log.write("removing subtree...");
            //remove the subtree
            st.removeSubtree(label_id, true, 'animate', {
                hideLabels: false,
                onComplete: function () {
                    removing = false;
                    Log.write("subtree removed");
                }
            });
        }
    });
}








