#import "assets/imports/template.typ": conf, title
#import "assets/imports/utils.typ": *
#import "assets/imports/math.typ": formula as f
#import "assets/helpers/load.typ": load

#show: conf
#title[Resource loading]
#let data = load(read("assets/data.json", encoding: none))
#assert.eq(f(data.value), 84)
#label-for(f(data.value))

#image("assets/diagram.svg", width: 60mm, alt: "A circle points to a square.")
