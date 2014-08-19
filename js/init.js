	/*
	Script used to retrieve status content based on the given names, and update the tables
	on the status page
	
	Adam Alyyan - aalyyan@memphis.edu
*/

hostip="sol.cs.memphis.edu";
pubprefix = "/ndn/memphis.edu/internal/status";
var ndn;
var face;

console.log("In: " + pubprefix);

// Enables the tabs to work
$('#myTab a').click(function (e) {
	e.preventDefault()
	$(this).tab('show')
})

function onData(interest, data) {
	console.log("Got data");
	console.log(data)
               //var content = upcallInfo.contentObject;
		console.log("Name: " + data.name.getName())
                var nameStr = data.name.getName().split("/").slice(5,6);
		console.log(nameStr)

                if (nameStr == "prefix") {
                        // Grab the JSON content and parse via the prefix function
                        var s = DataUtils.toString(data.content);
			console.log("S IS: " + s);
                        prefix(s);
                } else if (nameStr == "link") {
                        // Grab the JSON content and parse via the link function
                        var s = DataUtils.toString(data.content);
                        link(s);
                } else {
                        // Grab the JSON content and update the status information section
                        var data = DataUtils.toString(data.content);
                        var obj = jQuery.parseJSON(data);

                        document.getElementById("lastupdated").innerHTML = obj.lastupdated;
                        document.getElementById("lastlog").innerHTML = obj.lastlog;
                        document.getElementById("lasttimestamp").innerHTML = obj.lasttimestamp;
                }
}

function onTimeout(interest)
    {
      console.log("onTimeout called. Re-expressing the interest.");
      console.log("Host: " + face.connectionInfo.toString());
      face.expressInterest(interest, onData, onTimeout);
    }


function getStatus(name) {
	console.log("loading...");

	face.expressInterest(new Name(pubprefix + "/" + name), onData, onTimeout);
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

	$.get("scripts/execute.php", function() {
		openHandle = function() {
			console.log("Connected");
			getStatus("metadata");
			getStatus("prefix");
			getStatus("link");
		};

		closeHandle = function() {
			 $('.alert-message')
                         	.append('<div class="alert alert-danger">NDN.js could not establish a connection to Netlogic. Please check back soon.</div>')
                                .fadeIn(500);
		};

		console.log(openHandle);
                console.log('connecting to ws')
                
                face = new Face({host:"sol.cs.memphis.edu"});
                
                //face.transport.connect(face, openHandle);
                getStatus("metadata")
                getStatus("prefix")
                getStatus("link")

		$(".loader").fadeOut(500, function() {
				$('.alert-message')
					.append('<div class="alert alert-success">Routing Status loaded <strong>successfully</strong>.</div>')
					.fadeIn(500);
		});

	});
});
