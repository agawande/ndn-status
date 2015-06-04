/*
	Script used to retrieve status content based on the given names, and update the tables
	on the status page
	
	Adam Alyyan - aalyyan@memphis.edu
*/

hostip="titan.cs.memphis.edu";
pubprefix = "/ndn/memphis.edu/internal/status";
var ndn;
var face;
var completed = false;

console.log("In: " + pubprefix);

// Enables the tabs to work
$('#myTab a').click(function (e) {
	e.preventDefault()
	$(this).tab('show')
})

function onData(interest, data) {
	console.log("Got data for " + interest.getName().toUri());
        console.log(data.buf().toString('binary'));
        var contentS = data.buf().toString('binary');
    	//console.log("Freshness: " + data.getMetaInfo().getFreshnessPeriod());
	//console.log(data.getContent())
                //var content = upcallInfo.contentObject;
		//console.log("Name: " + data.name.getName());
                var nameStr = interest.getName().toUri().split("/");
		nameStr = nameStr[nameStr.length-2]
		console.log(nameStr);

                if (nameStr == "prefix") {
                        // Grab the JSON content and parse via the prefix function
                        // var s = DataUtils.toString(data.content);
                        var s = contentS;
			console.log("Prefix is: " + s);
                        prefix(s);
			getStatus("link");
                } else if (nameStr == "link") {
                        // Grab the JSON content and parse via the link function
                        // var s = DataUtils.toString(data.content);
                        var s = contentS;
			console.log("Link is: " + s);
                        link(s);
                } else {
                        // Grab the JSON content and update the status information section
                        // var data = DataUtils.toString(data.content);
                        var data = contentS;
                        var obj = jQuery.parseJSON(data);
			console.log("Metadata is: " + obj.lastupdated);

                        document.getElementById("lastupdated").innerHTML = obj.lastupdated;
                        document.getElementById("lastlog").innerHTML = obj.lastlog;
                        document.getElementById("lasttimestamp").innerHTML = obj.lasttimestamp;
			getStatus("prefix");
                }
}

function onTimeout(interest) {
	console.log("Interest timed out: " + interest.getName().toUri());
	console.log("Host: " + face.connectionInfo.toString());

        console.log("Reexpressing interest for " + interest.getName().toUri());

	SegmentFetcher.fetch(face, interest, SegmentFetcher.DontVerifySegment,
                         function(content) {
                           console.log("Got data");
                           onData(interest, content);
                         },
                         function(errorCode, message) {
	                   console.log("Error #" + errorCode + ": " + message);
                           //onTimeout(interest);                                                                                                                       
                         });  
}


function getStatus(name) {
	console.log("loading...");

	var interest = new Interest(new Name(pubprefix + "/" + name + "/%00%00"));

        console.log("Expressing interest for " + interest.getName().toUri());

	//interest.setMustBeFresh(true);  segment fetcher does this

	//var all-content;

	SegmentFetcher.fetch(face, interest, SegmentFetcher.DontVerifySegment,
	                     function(content) {
                               //console.log("----------------------Segment-Fetched-----------------------");
			       //console.log(content.buf().toString('binary'));
                               //console.log("----------------------------End-----------------------------");
	                       onData(interest, content);
                               //all-content += content;
	                     },
	                     function(errorCode, message) {
                                console.log("Error #" + errorCode + ": " + message);
	                        //onTimeout(interest);
	                     });
}


$(document).ready(function() {
	var ospfnRunning;

	$.ajax({ url: 'scripts/ospfnCheck.php',
		 type: 'get',
		 success: function(output) {
			
			output = output.replace(/\s/gm, '');

			if (output === "Down") {
				ospfnRunning = false;
			} else {
				ospfnRunning = true;
			}
		 }
	});
  
        face = new Face({host:"titan.cs.memphis.edu", port:8888});

	$.ajax({
	  url: 'scripts/execute.php',
	  success: function(data) {
	    if(data=="Success\n") { 
		getStatus("metadata");
		$(".loader").fadeOut(500, function() {
                             $('.alert-message')
                                      .append('<div class="alert alert-success">Routing Status loaded <strong>successfully</strong>.</div>')
                                      .fadeIn(500);
                        });
	    } else {
		 $(".loader").fadeOut(500, function() {
				$('.alert-message')
                                	.append('<div class="alert alert-danger">NDN.js could not establish a connection to Titan. Please check back soon.</div>')
	                                .fadeIn(500);
			});
         
		console.log("Check that your path is correct in execute.php!");
	    }
	  }
	});
        //getStatus("metadata");
        //getStatus("prefix");
        //getStatus("link");

});
