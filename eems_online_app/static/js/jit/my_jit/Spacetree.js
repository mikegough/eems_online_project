var labelType, useGradients, nativeTextSupport, animate;

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
        levelsToShow: 40,
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
            //log_text = "<img class='node_icon' src='static/img/node.png'> Click to map the data and show the input nodes</p>" +
            //log_text = "Click on a box <img class='node_icon' src='static/img/node.png'> to map the data and show the inputs. Click on a gear icon <img class='modify_icon_class' src='static/img/gear_icon.svg'>  to modify the operator"
            /*
            log_text = "<img class='node_icon' src='static/img/node.png'> Click on a box to map the data and show the inputs<br>" +
                "<span class='log_text_second_line'><img class='node_and_gear' src='static/img/node_and_gear.png'> Click on a gear icon to modify the operator</span>"
            Log.write(log_text)
            */
            //log_text = "Click on a box to map the data and show the inputs. Click the gear icon to modify the operator."
            //log_text = "Click a box to map the data and show the inputs. &nbsp Click the gear icon to make changes to the operator."
            Log.write("<div class='expand_collapse_meemse_button' id='expand_meemse_button'>Expand Nodes</div><div class='expand_collapse_meemse_button' id='collapse_meemse_button'>Collapse Nodes</div>");

            $("#expand_meemse_button").click(function(){
                st.controller.constrained=false;
                st.refresh();
                $("#expand_meemse_button").hide();
                $("#collapse_meemse_button").show();
            });
            $("#collapse_meemse_button").click(function(){
                st.controller.constrained=true;
                st.refresh();
                $("#expand_meemse_button").show();
                $("#collapse_meemse_button").hide();
            });

            // Remove logic to show eems value in top node
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

            // Get a list of direct children for this node for making the form.

            eems_children_dict[node.id]=[]

            node.eachSubnode(function(child){
               //eems_children_dict[node.id].push(child)
               //eems_children_dict[node.id].push(child.name)
               eems_children_dict[node.id].push(child.id)
            });

            var argument_string="";

            //Convert the argument list to a string that can be easily parsed using the arbitrary separator specified below
            $.each(node.data.arguments, function(index, argument){
                argument_string += argument;
                argument_string += '**##**';
            });

            if (node.data.operation != "Read" && node.data.operation != "EEMSRead") {
                /*label.innerHTML += "<span id='close_span' title='Click to change the EEMS operations'><img id='close_icon' onclick=\"remove_node('" + label.id + "')\" src='static/img/close.svg'></span>"*/
                label.innerHTML += "<span id='modify_span' title='Click to make changes to this operator'><img class='modify_icon_class' id='modify_icon' onclick=\"changeEEMSOperator('" + node.id + "','" + alias + "','" + node.data.operation + "','" + eems_children_dict[node.id] + "','" + argument_string + "')\" src='static/img/gear_icon.svg'></span>"

            } else {
                label.innerHTML += "<span id='modify_span' title='Click to view the histogram'><img class='modify_icon_class' id='modify_icon' onclick=\"showHistogram('" + node.id + "','" + alias + "')\" src='static/img/gear_icon.svg'></span>"
            }

            label.onclick = function(){

                //Fix for nodes shooting off the screen after panning then clicking.
                var m = {
                    offsetX:st.canvas.translateOffsetX,
                    offsetY:st.canvas.translateOffsetY + 130
                };
                 st.onClick(node.id, { Move: m });

                swapImageOverlay(node.id,eems_model_id_for_map_display,0)

               //Code for expanding/contracting nodes (toggle) Not working correctly
               // DELETED //

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
        //Edge data properties prefixed with a dollar sign will
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

    // Load root node image overlay on MEEMSE creation.
    swapImageOverlay(st.root,eems_model_id_for_map_display)

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
    }
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


