"""German (de_DE) UI translations for Magnets."""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("Magnets", "Snapping"): "Einrasten",
    ("*", "Guides"): "Hilfslinien",
    ("*", "Alignment"): "Ausrichtung",
    ("*", "Guide Types"): "Hilfslinien-Typen",
    ("*", "Show"): "Anzeigen",
    ("*", "Axes"): "Achsen",
    ("*", "Reference Points"): "Bezugspunkte",
    ("Magnets", "Frame"): "Bezugssystem",
    ("*", "Object"): "Objekt",
    ("*", "Indicators"): "Indikatoren",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "An Hilfslinien einrasten",
    ("Magnets", "Even Spacing"): "Gleichmäßiger Abstand",
    ("*", "Angle Snap"): "Winkeleinrastung",
    ("*", "Snap Tolerance"): "Einrasttoleranz",
    ("*", "Break Distance"): "Löseabstand",
    ("*", "Re-engage Gap"): "Abstand zum Wiedereinrasten",
    ("*", "Range"): "Bereich",
    ("*", "Maximum Guides"): "Maximale Anzahl Hilfslinien",
    ("*", "Spacing"): "Abstand",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Passive Hilfslinien",
    ("*", "Feature Hints"): "Elementhinweise",
    ("*", "Ticks"): "Teilstriche",
    ("*", "Labels"): "Beschriftungen",
    ("*", "Extend to Viewport"): "Auf Ansichtsfenster ausdehnen",
    ("*", "Proximity Fade"): "Einblenden bei Annäherung",
    ("Magnets", "Alignment Frame"): "Ausrichtungsbezug",
    ("*", "Custom Frame Object"): "Benutzerdefiniertes Bezugsobjekt",
    ("*", "Origin"): "Ursprung",
    ("*", "Pivot"): "Drehpunkt",
    ("*", "Centroid"): "Schwerpunkt",
    ("*", "Face Centers"): "Flächenmittelpunkte",
    ("*", "Bounding Box Corners"): "Ecken des Begrenzungsrahmens",
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
    ("*", "Which gaps the Equal Spacing guides compare between objects"): (
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
    ("*", "Show a text label next to each engaged guide"): (
        "Neben jeder greifenden Hilfslinie eine Beschriftung anzeigen"
    ),
    ("*", "Stretch edge guide lines across the 3D Viewport (alignment guides join the two objects)"): (
        "Kanten-Hilfslinien über das 3D-Ansichtsfenster strecken (Ausrichtungs-Hilfslinien verbinden die beiden Objekte)"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Deckkraft der Hilfslinien schrittweise erhöhen, "
        "wenn sich der Cursor der Einrastzone nähert"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Mittelpunkte",
    ("Magnets", "Edges"): "Kanten",
    ("Magnets", "Both"): "Beides",
    ("*", "Distribute object centers evenly"): (
        "Objektmittelpunkte gleichmäßig verteilen"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Sichtbare Abstände zwischen Begrenzungsrahmen verteilen"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Gleichmäßigen Abstand von Mittelpunkten und Kanten erkennen"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("Magnets", "World"): "Welt",
    ("Magnets", "Local"): "Lokal",
    ("Magnets", "View"): "Ansicht",
    ("Magnets", "Parent"): "Elternteil",
    ("Magnets", "Collection"): "Sammlung",
    ("Magnets", "Custom"): "Benutzerdefiniert",
    ("*", "Align to world X/Y/Z axes"): "An den Weltachsen X/Y/Z ausrichten",
    ("*", "Align to the moving object's local axes"): (
        "An den lokalen Achsen des bewegten Objekts ausrichten"
    ),
    ("*", "Align to the 3D Viewport axes"): "An den Achsen des 3D-Ansichtsfensters ausrichten",
    ("*", "Align to the parent object's local axes"): (
        "An den lokalen Achsen des Elternobjekts ausrichten"
    ),
    ("*", "Align to a collection instance empty"): (
        "Am leeren Objekt einer Sammlungsinstanz ausrichten"
    ),
    ("*", "Align to a custom reference object"): (
        "An einem benutzerdefinierten Bezugsobjekt ausrichten"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("Magnets", "Alignment"): "Ausrichtung",
    ("Magnets", "Equal Spacing"): "Gleicher Abstand",
    ("Magnets", "Equal Size"): "Gleiche Größe",
    ("Magnets", "Midpoint"): "Mittelpunkt",
    ("Magnets", "Surface Contact"): "Oberflächenkontakt",
    ("Magnets", "Sphere Tangency"): "Kugeltangente",
    ("Magnets", "Parallel"): "Parallel",
    ("Magnets", "Collinear"): "Kollinear",
    ("Magnets", "Coplanar"): "Komplanar",
    ("Magnets", "Concentric"): "Konzentrisch",
    ("Magnets", "Symmetry"): "Symmetrie",
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
    ("*", "Detect and show Surface Contact markers"): (
        "Oberflächenkontakt-Marker erkennen und anzeigen"
    ),
    ("*", "Detect and show Sphere Tangency markers"): (
        "Kugeltangenten-Marker erkennen und anzeigen"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Parallelitätsmarker erkennen und anzeigen"
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
    # ── Candidate and depth options, Repeat Size ────────────────────────────
    ("Magnets", "Repeat Size"): (
        "Größenwiederholung"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Marker für Größenwiederholung erkennen und anzeigen"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Nahe Objekte bevorzugen"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Objekte außerhalb der Ansicht ignorieren und entfernte Objekte auf Ausrichtungs-Hilfslinien nahe dem Einrasten beschränken. Schneller in großen Szenen"
    ),
    ("*", "Diagonal Guides"): (
        "Diagonale Hilfslinien"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Hilfslinien für Mittelpunkt und Größenwiederholung auch zwischen diagonal liegenden Punkten eines Objekts anbieten, nicht nur entlang der Ausrichtungsachsen"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Grenzwinkel der Tiefenachse"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Hilfslinien und Einrasten in Richtungen ignorieren, die weniger als diesen Winkel von der Blickrichtung abweichen, wo eine Bewegung in den Bildschirm hinein schwer zu sehen ist"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Präzisionsmodus",
    ("*", "Debug Logging"): "Debug-Protokollierung",
    ("*", "Passive Color"): "Passive Farbe",
    ("*", "Active Color"): "Aktive Farbe",
    ("*", "Line Width"): "Linienbreite",
    ("*", "Solid Lines"): "Durchgezogene Linien",
    ("*", "Snap Anchor Dot"): "Einrast-Ankerpunkt",
    ("*", "Dot Radius"): "Punktradius",
    ("*", "Intersection Dot"): "Schnittpunkt",
    ("*", "Snap Pulse"): "Einrastimpuls",
    (
        "*",
        "Replace G / R / S with the Magnets transform, which locks onto a guide while "
        "dragging. When off, Blender's own transform is used and the snap is applied on release",
    ): (
        "G / R / S durch die Magnets-Transformation ersetzen, die während des Ziehens an einer Hilfslinie einrastet. Wenn aus, wird Blenders eigene Transformation verwendet und beim Loslassen eingerastet"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Magnets-Diagnosen in die Systemkonsole schreiben "
        "(Fenster ▸ Systemkonsole umschalten)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Farbe der Hilfslinie beim Annähern an die Einrastzone"
    ),
    ("*", "Guide color while engaged"): "Farbe der Hilfslinie im aktiven Zustand",
    ("*", "Guide line width in pixels"): "Linienbreite der Hilfslinien in Pixeln",
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
        "Das Magnets-Einrasten überspringen, wenn Blenders eigenes Einrasten für die Transformation aktiv ist, damit sich beide nie widersprechen"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Objekt, dessen Achsen den Ausrichtungsbezug festlegen"
    ),
    ("*", "Guides only, no snapping"): "Nur Hilfslinien, kein Einrasten",
    ("*", "Locks onto guides while dragging"): "Rastet beim Ziehen an Hilfslinien ein",
    ("*", "Snaps when G/R/S is released"): "Rastet beim Loslassen von G/R/S ein",
    ("*", "Blender snapping takes over"): "Blender-Einrasten hat Vorrang",
    ("*", "Blender Snap"): "Blender-Einrasten",
    ("*", "Yield"): "Vorrang geben",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Schalter in der Kopfleiste"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Den Magnets-Ein/Aus-Schalter und das Einstellungsmenü in der Kopfleiste des 3D-Ansichtsfensters anzeigen"
    ),
    ("*", "Engaged Colors"): (
        "Farben aktiver Hilfslinien"
    ),
    ("*", "How engaged guides are colored"): (
        "Wie aktive Hilfslinien eingefärbt werden"
    ),
    ("*", "Axis Colors"): (
        "Achsenfarben"
    ),
    ("*", "Alignment labels use the theme's X/Y/Z axis colors; guide lines use the Active Color"): (
        "Ausrichtungs-Beschriftungen nutzen die X/Y/Z-Achsenfarben des Themas; Hilfslinien die aktive Farbe"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Alle aktiven Hilfslinien nutzen die aktive Farbe"
    ),
    ("*", "Shortcut"): (
        "Tastenkürzel"
    ),
    ("Operator", "Toggle Magnets"): (
        "Magnets umschalten"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Magnets-Hilfslinien und Einrasten ein- oder ausschalten"
    ),
    ("*", "More options in the sidebar (N)"): "Weitere Optionen in der Seitenleiste (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("Magnets", "Preset"): "Voreinstellung",
    ("Magnets", "Precise"): "Präzise",
    ("Magnets", "Balanced"): "Ausgewogen",
    ("Magnets", "Loose"): "Weit",
    ("*", "Tight tolerances for close work"): (
        "Enge Toleranzen für Feinarbeit"
    ),
    ("*", "Default tolerances"): "Standardtoleranzen",
    ("*", "Wide tolerances for blocking out"): (
        "Weite Toleranzen für das Groblayout"
    ),
    # ── Preset buttons (drawn as operator buttons) and reports ─────────────────
    ("Operator", "Precise"): "Präzise",
    ("Operator", "Balanced"): "Ausgewogen",
    ("Operator", "Loose"): "Weit",
    ("*", "Magnets on"): "Magnets an",
    ("*", "Magnets off"): "Magnets aus",
    ("*", "Snapped"): "Eingerastet",
    ("*", "X/Y/Z: lock axis"): "X/Y/Z: Achse sperren",
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Move"): "Magnets: Verschieben",
    ("Operator", "Magnets Rotate"): "Magnets: Rotieren",
    ("Operator", "Magnets Scale"): "Magnets: Skalieren",
    ("Operator", "Magnets Extrude"): "Magnets: Extrudieren",
    ("Operator", "Magnets Bevel"): "Magnets: Abschrägen",
    ("Operator", "Magnets Inset"): "Magnets: Einrücken",
    ("Operator", "Magnets Knife"): "Magnets: Messer",
    ("Operator", "Magnets Preset"): "Magnets: Voreinstellung",
    ("Operator", "Reset Magnets Options"): "Magnets-Optionen zurücksetzen",
    ("Operator", "Magnets: No-op"): "Magnets: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Mit geometrischen Magnets-Hilfslinien verschieben"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Mit geometrischen Magnets-Hilfslinien rotieren"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Mit geometrischen Magnets-Hilfslinien skalieren"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Bereich extrudieren und danach mit Magnets-Hilfslinien verschieben"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Abschrägen und danach mit Magnets-Hilfslinien anpassen"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Flächen einrücken und danach mit Magnets-Hilfslinien verschieben"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Messerschnitt projizieren und danach mit Magnets-Hilfslinien verschieben"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Einrasttoleranzen auf ein Voreinstellungsprofil setzen"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Alle Magnets-Szenenoptionen auf die Standardwerte zurücksetzen"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Interner Magnets-Operator für den Registrierungstest"
    ),
}
