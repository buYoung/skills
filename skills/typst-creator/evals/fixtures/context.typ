#set page(margin: 20mm)
#set heading(numbering: "1.")
#let total = state("experiment-total", 0)
#let record(value) = total.update(previous => previous + value)

= State and Context <state-heading>
#record(2)
#context {
  assert.eq(total.get(), 2)
  [First total: #total.get()]
}
#record(3)
#context {
  assert.eq(total.get(), 5)
  assert.eq(counter(heading).get().first(), 1)
  assert.eq(query(<state-heading>).len(), 1)
  [Final total: #total.get()]
}

#context [Page #counter(page).display("1")]
