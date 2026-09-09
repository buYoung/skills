#set page("a4", flipped: true, columns: 2, supplement: n => [p.])
#set heading(numbering: "1.")
= Measurements <measurements>
#figure(
  table(columns: 2, table.header([Sample], [Value]), [A], [12], [B], [18]),
  kind: "table", caption: [Measured values],
) <measurements-table>
= Diagram <diagram-section>
#figure(
  image(source: "assets/diagram.svg", width: 70%),
  placement: top, scope: "local", caption: [Processing stages],
) <process-diagram>
See @measurements-table and @process-diagram.
