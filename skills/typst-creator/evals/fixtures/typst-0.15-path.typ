#import "assets/helpers/load.typ": load
#let data = load(path("assets/data.json"))
#assert.eq(data.value, 42)
Caller-resolved path value: #data.value
