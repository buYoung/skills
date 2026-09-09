#set page(margin: 20mm)
= Drawing
#path(stroke: blue, (0pt, 0pt), (20pt, 15pt), (40pt, 0pt))
= Tiling
#let dots = pattern(size: (8pt, 8pt), circle(radius: 1pt, fill: blue))
#rect(width: 40pt, height: 20pt, fill: dots)
= Data and Symbols
#let info = json.decode("{\"value\": 42}")
Value: #info.value
$ A sect B quad x plus.circle y $
