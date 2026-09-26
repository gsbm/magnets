"""German (de_DE) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnete",
    ("*", "Snapping"): "Einrasten",
    ("*", "Guides"): "Hilfslinien",
    ("*", "Alignment"): "Ausrichtung",
    ("*", "Guide Types"): "Hilfslinien-Typen",
    ("*", "Presets"): "Voreinstellungen",
    ("*", "Show"): "Anzeigen",
    ("*", "Axes"): "Achsen",
    ("*", "Reference Points"): "Bezugspunkte",
    ("*", "Frame"): "Bezugssystem",
    ("*", "Object"): "Objekt",
    ("*", "Indicators"): "Indikatoren",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Enable Guides"): "Hilfslinien aktivieren",
    ("*", "Snap to Guides"): "An Hilfslinien einrasten",
    ("*", "Even Spacing"): "Gleichmäßiger Abstand",
    ("*", "Angle Snap"): "Winkeleinrastung",
    ("*", "Snap Tolerance"): "Einrasttoleranz",
    ("*", "Break Distance"): "Löseabstand",
    ("*", "Re-engage Gap"): "Wiedereingriff-Abstand",
    ("*", "Range"): "Reichweite",
    ("*", "Maximum Guides"): "Max. Hilfslinien",
    ("*", "Spacing"): "Abstand",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Passive Hilfslinien",
    ("*", "Feature Hints"): "Elementhinweise",
    ("*", "Ticks"): "Teilstriche",
    ("*", "Extend to Viewport"): "Auf Ansicht ausdehnen",
    ("*", "Proximity Fade"): "Nähe-Einblendung",
    ("*", "Alignment Frame"): "Ausrichtungsbezug",
    ("*", "Custom Frame Object"): "Benutzerdefiniertes Bezugsobjekt",
    ("*", "Origin"): "Ursprung",
    ("*", "Pivot"): "Drehpunkt",
    ("*", "Centroid"): "Schwerpunkt",
    ("*", "Face Centers"): "Flächenmittelpunkte",
    ("*", "Bounding Box Corners"): "Ecken der Begrenzungsbox",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Geometrische Hilfslinien und Einrasten während Transformationen anzeigen"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "Beim Loslassen der Transformation an der aktiven Hilfslinie einrasten. "
        "Im Präzisionsmodus während des Ziehens daran festhalten"
    ),
    ("*", "Which gap the equal-spacing guides equalise between objects"): (
        "Welchen Abstand die Hilfslinien für gleichen Abstand zwischen Objekten ausgleichen"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Rotation an diesem Schritt in Grad einrasten. 0 deaktiviert"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Bildschirmabstand, ab dem eine Hilfslinie greift"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Zusätzlicher Abstand über die Einrasttoleranz hinaus, "
        "bevor eine aktive Hilfslinie gelöst wird"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Abstand, den der Cursor die Einrastzone verlassen muss, "
        "bevor eine Hilfslinie erneut greifen kann"
    ),
    ("*", "Screen distance within which guides appear"): (
        "Bildschirmabstand, innerhalb dessen Hilfslinien erscheinen"
    ),
    ("*", "Largest number of guides shown at once"): (
        "Maximale Anzahl gleichzeitig angezeigter Hilfslinien"
    ),
    ("*", "Minimum screen distance between shown guides"): (
        "Minimaler Bildschirmabstand zwischen angezeigten Hilfslinien"
    ),
    ("*", "Allow snapping to align on the X axis"): (
        "Einrasten zur Ausrichtung auf der X-Achse erlauben"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Einrasten zur Ausrichtung auf der Y-Achse erlauben"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Einrasten zur Ausrichtung auf der Z-Achse erlauben"
    ),
    ("*", "Show guides before they engage"): (
        "Hilfslinien anzeigen, bevor sie greifen"
    ),
    ("*", "Show the reference feature next to each guide"): (
        "Das Bezugselement neben jeder Hilfslinie anzeigen"
    ),
    ("*", "Show tick marks at guide reference points"): (
        "Teilstriche an den Bezugspunkten der Hilfslinien anzeigen"
    ),
    ("*", "Stretch guide lines across the 3D viewport"): (
        "Hilfslinien über die 3D-Ansicht strecken"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Deckkraft der Hilfslinien schrittweise erhöhen, "
        "wenn sich der Cursor der Einrastzone nähert"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("*", "Centers"): "Mittelpunkte",
    ("*", "Edges"): "Kanten",
    ("*", "Both"): "Beides",
    ("*", "Distribute object centers evenly"): (
        "Objektmittelpunkte gleichmäßig verteilen"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Sichtbare Abstände zwischen Begrenzungsboxen verteilen"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Gleichmäßigen Abstand von Mittelpunkten und Kanten erkennen"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("*", "World"): "Welt",
    ("*", "Local"): "Lokal",
    ("*", "View"): "Ansicht",
    ("*", "Parent"): "Elternobjekt",
    ("*", "Collection"): "Sammlung",
    ("*", "Custom"): "Benutzerdefiniert",
    ("*", "Align to world X/Y/Z axes"): "An den Weltachsen X/Y/Z ausrichten",
    ("*", "Align to the moving object's local axes"): (
        "An den lokalen Achsen des bewegten Objekts ausrichten"
    ),
    ("*", "Align to the 3D View axes"): "An den Achsen der 3D-Ansicht ausrichten",
    ("*", "Align to the parent object's local axes"): (
        "An den lokalen Achsen des Elternobjekts ausrichten"
    ),
    ("*", "Align to a collection instance empty"): (
        "Am Empty einer Sammlungsinstanz ausrichten"
    ),
    ("*", "Align to a custom reference object"): (
        "An einem benutzerdefinierten Bezugsobjekt ausrichten"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Gleicher Abstand",
    ("*", "Equal Size"): "Gleiche Größe",
    ("*", "Midpoint"): "Mittelpunkt",
    ("*", "Tangency"): "Tangente",
    ("*", "Parallel"): "Parallel",
    ("*", "Perpendicular"): "Senkrecht",
    ("*", "Collinear"): "Kollinear",
    ("*", "Coplanar"): "Komplanar",
    ("*", "Concentric"): "Konzentrisch",
    ("*", "Symmetry"): "Symmetrie",
    ("*", "Detect and show Alignment markers"): (
        "Ausrichtungsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Equal Spacing markers"): (
        "Marker für gleichen Abstand erkennen und anzeigen"
    ),
    ("*", "Detect and show Equal Size markers"): (
        "Marker für gleiche Größe erkennen und anzeigen"
    ),
    ("*", "Detect and show Midpoint markers"): (
        "Mittelpunktmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Tangency markers"): (
        "Tangentenmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Parallelitätsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Perpendicular markers"): (
        "Senkrechtigkeitsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Collinear markers"): (
        "Kollinearitätsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Coplanar markers"): (
        "Komplanaritätsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Concentric markers"): (
        "Konzentrizitätsmarker erkennen und anzeigen"
    ),
    ("*", "Detect and show Symmetry markers"): (
        "Symmetriemarker erkennen und anzeigen"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Präzisionsmodus",
    ("*", "Debug Logging"): "Debug-Protokollierung",
    ("*", "Passive Color"): "Passive Farbe",
    ("*", "Active Color"): "Aktive Farbe",
    ("*", "Line Width"): "Linienstärke",
    ("*", "Solid Lines"): "Durchgezogene Linien",
    ("*", "Snap Anchor Dot"): "Einrast-Ankerpunkt",
    ("*", "Dot Radius"): "Punktradius",
    ("*", "Intersection Dot"): "Schnittpunkt",
    ("*", "Snap Pulse"): "Einrastimpuls",
    (
        "*",
        "Bind G / R / S to the Magnets modal operators, which lock onto a "
        "guide while dragging. Leave off to use Blender's native transform, "
        "which snaps to the engaged guide when released",
    ): (
        "G / R / S an die modalen Magnete-Operatoren binden, die während "
        "des Ziehens an einer Hilfslinie einrasten. Ausgeschaltet wird "
        "die native Transformation von Blender verwendet, die beim Loslassen "
        "an der aktiven Hilfslinie einrastet"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Magnete-Diagnosen in die Systemkonsole schreiben "
        "(Fenster ▸ Systemkonsole umschalten)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Farbe der Hilfslinie beim Annähern an die Einrastzone"
    ),
    ("*", "Guide color while engaged"): "Farbe der Hilfslinie im aktiven Zustand",
    ("*", "Guide line width in pixels"): "Linienstärke der Hilfslinien in Pixeln",
    ("*", "Draw solid guide lines, otherwise dashed"): (
        "Durchgezogene Hilfslinien zeichnen, sonst gestrichelt"
    ),
    ("*", "Draw a dot at the coincident point when a guide is engaged"): (
        "Einen Punkt am Koinzidenzpunkt zeichnen, wenn eine Hilfslinie aktiv ist"
    ),
    ("*", "Radius of the snap anchor dot in pixels"): (
        "Radius des Einrast-Ankerpunkts in Pixeln"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Einen Marker zeichnen, wo sich zwei aktive Hilfslinien kreuzen"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Kurzer Helligkeitsblitz im Moment, in dem eine Hilfslinie greift"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Blender-Einrasten Vorrang geben"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Das Magnete-Einrasten überspringen, wenn Blenders eigenes Einrasten für die Transformation aktiv ist, damit sich beide nie widersprechen"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Objekt, dessen Achsen den Ausrichtungsbezug festlegen"
    ),
    ("*", "Guides only, no snapping"): "Nur Hilfslinien, kein Einrasten",
    ("*", "Locks onto guides while dragging"): "Rastet beim Ziehen ein",
    ("*", "Snaps when you release G/R/S"): "Rastet beim Loslassen ein",
    ("*", "Blender snapping takes over"): "Blender-Einrasten hat Vorrang",
    ("*", "Blender Snap"): "Blender-Einrasten",
    ("*", "Yield"): "Vorrang geben",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Schalter in der Kopfzeile"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Den Magnete-Ein/Aus-Schalter und das Einstellungs-Popover in der Kopfzeile des 3D-Viewports anzeigen"
    ),
    ("*", "Engaged Colors"): (
        "Farben beim Einrasten"
    ),
    ("*", "How engaged guides are colored"): (
        "Wie eingerastete Hilfslinien eingefärbt werden"
    ),
    ("*", "Axis Colors"): (
        "Achsenfarben"
    ),
    ("*", "Alignment guides use the theme's X/Y/Z axis colors; other guides use the Active Color"): (
        "Ausrichtungs-Hilfslinien nutzen die X/Y/Z-Achsenfarben des Themes; andere Hilfslinien die aktive Farbe"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Alle eingerasteten Hilfslinien nutzen die aktive Farbe"
    ),
    ("*", "Shortcut"): (
        "Tastenkürzel"
    ),
    ("Operator", "Toggle Magnets"): (
        "Magnete umschalten"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Magnete-Hilfslinien und Einrasten ein- oder ausschalten"
    ),
    ("*", "More options in the sidebar (N)"): "Weitere Optionen in der Seitenleiste (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("*", "Preset"): "Voreinstellung",
    ("*", "Precise"): "Präzise",
    ("*", "Balanced"): "Ausgewogen",
    ("*", "Loose"): "Weit",
    ("*", "Tight tolerances for close work"): (
        "Enge Toleranzen für Feinarbeit"
    ),
    ("*", "Default tolerances"): "Standardtoleranzen",
    ("*", "Wide tolerances for blocking out"): (
        "Weite Toleranzen für das Groblayout"
    ),
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Grab"): "Magnete: Verschieben",
    ("Operator", "Magnets Rotate"): "Magnete: Rotieren",
    ("Operator", "Magnets Scale"): "Magnete: Skalieren",
    ("Operator", "Magnets Extrude"): "Magnete: Extrudieren",
    ("Operator", "Magnets Bevel"): "Magnete: Abschrägen",
    ("Operator", "Magnets Inset"): "Magnete: Einfügen",
    ("Operator", "Magnets Knife"): "Magnete: Messer",
    ("Operator", "Magnets Preset"): "Magnete: Voreinstellung",
    ("Operator", "Reset Magnets Options"): "Magnete-Optionen zurücksetzen",
    ("Operator", "Magnets: No-op"): "Magnete: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Mit geometrischen Magnete-Hilfslinien verschieben"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Mit geometrischen Magnete-Hilfslinien rotieren"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Mit geometrischen Magnete-Hilfslinien skalieren"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Bereich extrudieren und danach mit Magnete-Hilfslinien verschieben"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Abschrägen und danach mit Magnete-Hilfslinien anpassen"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Flächen einfügen und danach mit Magnete-Hilfslinien verschieben"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Mit Messer schneiden und danach mit Magnete-Hilfslinien verschieben"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Einrasttoleranzen auf ein Voreinstellungsprofil setzen"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Alle Magnete-Szenenoptionen auf die Standardwerte zurücksetzen"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Interner Magnete-Operator für den Registrierungstest"
    ),
}
