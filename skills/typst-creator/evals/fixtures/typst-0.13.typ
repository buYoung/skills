#set page(paper: "a4", margin: 2cm)
#set enum(reversed: true)

= Typst 0.13 Fixture

+ First result
+ Second result
+ Third result

#let inline-data = json(bytes("{\"status\": \"ok\"}"))

Status: #inline-data.status
