#target photoshop

// Ask for color filter value
var colorArg;
var useColor = confirm("Will you include a color filter?");
var input = true; // used as a proceed flag
if (useColor) {
    var fg = app.foregroundColor;
    var r = Math.round(fg.rgb.red);
    var g = Math.round(fg.rgb.green);
    var b = Math.round(fg.rgb.blue);
    colorArg = "filterByColor(float3(" + r + ", " + g + ", " + b + "), o0)";
} else {
    colorArg = "true";
}

var doc = app.activeDocument;
var lines = [];

for (var i = doc.layers.length - 1; i >= 0; i--) {
    var layer = doc.layers[i];
    if (!layer.visible) continue;
    if (layer.name.indexOf("Dikdörtgen") === -1) continue;

    var b = layer.bounds;
    var x      = Math.round(b[0].as("px"));
    var y      = Math.round(b[1].as("px"));
    var width  = Math.round(b[2].as("px")) - x;
    var height = Math.round(b[3].as("px")) - y;

    lines.push(
        "filterText(" +
        "filterByPosition(" +
        x + ", " + y + ", " + width + ", " + height +
        ", pos), " + colorArg +
        ", o0); // " + layer.name
    );
}

var output = lines.join("\n");

var f = new File("~/Desktop/setRange_output.txt");
f.open("w");
f.write(output);
f.close();
f.execute(); // opens the file