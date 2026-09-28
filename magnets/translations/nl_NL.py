"""Dutch (nl_NL) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels
and operator buttons; ``Magnets`` for the frame, spacing and preset options, whose short
names collide with unrelated entries in Blender's own catalogue.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("*", "Snapping"): "Vastklikken",
    ("*", "Guides"): "Hulplijnen",
    ("*", "Alignment"): "Uitlijning",
    ("*", "Guide Types"): "Typen hulplijnen",
    ("*", "Show"): "Tonen",
    ("*", "Axes"): "Assen",
    ("*", "Reference Points"): "Referentiepunten",
    ("Magnets", "Frame"): "Referentiesysteem",
    ("*", "Object"): "Object",
    ("*", "Indicators"): "Indicatoren",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "Vastklikken op hulplijnen",
    ("Magnets", "Even Spacing"): "Gelijke tussenruimte",
    ("*", "Angle Snap"): "Hoekvastklikken",
    ("*", "Snap Tolerance"): "Vastkliktolerantie",
    ("*", "Break Distance"): "Loslaatafstand",
    ("*", "Re-engage Gap"): "Heractiveringsmarge",
    ("*", "Range"): "Bereik",
    ("*", "Maximum Guides"): "Max. hulplijnen",
    ("*", "Spacing"): "Tussenruimte",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Passieve hulplijnen",
    ("*", "Feature Hints"): "Elementhints",
    ("*", "Ticks"): "Streepjes",
    ("*", "Extend to Viewport"): "Uitbreiden tot viewport",
    ("*", "Proximity Fade"): "Vervagen bij nabijheid",
    ("Magnets", "Alignment Frame"): "Uitlijnreferentie",
    ("*", "Custom Frame Object"): "Aangepast referentieobject",
    ("*", "Origin"): "Oorsprong",
    ("*", "Pivot"): "Draaipunt",
    ("*", "Centroid"): "Zwaartepunt",
    ("*", "Face Centers"): "Vlakcentra",
    ("*", "Bounding Box Corners"): "Hoeken van de begrenzingsbox",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Geometrische hulplijnen en vastklikken tonen tijdens transformaties"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "Vastklikken op de actieve hulplijn bij het loslaten van de transformatie. "
        "In precisiemodus eraan vastzetten tijdens het slepen"
    ),
    ("Magnets", "Which gaps the Equal Spacing guides compare between objects"): (
        "Welke tussenruimte de hulplijnen voor gelijke afstand tussen objecten gelijkmaken"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Rotatie vastklikken op deze stap in graden. 0 schakelt uit"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Schermafstand waarop een hulplijn actief wordt"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Extra afstand voorbij de vastkliktolerantie "
        "voordat een actieve hulplijn loslaat"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Afstand die de cursor van de vastklikzone moet wegbewegen "
        "voordat een hulplijn opnieuw kan activeren"
    ),
    ("*", "Screen distance within which guides appear"): (
        "Schermafstand waarbinnen hulplijnen verschijnen"
    ),
    ("*", "Largest number of guides shown at once"): (
        "Maximaal aantal tegelijk getoonde hulplijnen"
    ),
    ("*", "Minimum screen distance between shown guides"): (
        "Minimale schermafstand tussen getoonde hulplijnen"
    ),
    ("*", "Allow snapping to align on the X axis"): (
        "Vastklikken voor uitlijning op de X-as toestaan"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Vastklikken voor uitlijning op de Y-as toestaan"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Vastklikken voor uitlijning op de Z-as toestaan"
    ),
    ("*", "Show guides before they engage"): (
        "Hulplijnen tonen voordat ze actief worden"
    ),
    ("*", "Show the reference feature next to each guide"): (
        "Het referentieelement naast elke hulplijn tonen"
    ),
    ("*", "Show tick marks at guide reference points"): (
        "Streepjes tonen bij de referentiepunten van hulplijnen"
    ),
    ("*", "Stretch edge guide lines across the 3D Viewport (alignment guides join the two objects)"): (
        "Randhulplijnen over de 3D-viewport uitstrekken (uitlijnhulplijnen verbinden de twee objecten)"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Doorzichtbaarheid van hulplijnen geleidelijk verhogen "
        "wanneer de cursor de vastklikzone nadert"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Centra",
    ("Magnets", "Edges"): "Randen",
    ("Magnets", "Both"): "Beide",
    ("Magnets", "Distribute object centers evenly"): (
        "Objectcentra gelijkmatig verdelen"
    ),
    ("Magnets", "Distribute the visible gaps between bounding boxes"): (
        "Zichtbare tussenruimtes tussen begrenzingsboxen verdelen"
    ),
    ("Magnets", "Detect even spacing of centers and of edges"): (
        "Gelijke tussenruimte van centra en randen detecteren"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("Magnets", "World"): "Wereld",
    ("Magnets", "Local"): "Lokaal",
    ("Magnets", "View"): "Weergave",
    ("Magnets", "Parent"): "Ouder",
    ("Magnets", "Collection"): "Collectie",
    ("Magnets", "Custom"): "Aangepast",
    ("Magnets", "Align to world X/Y/Z axes"): "Uitlijnen op wereldassen X/Y/Z",
    ("Magnets", "Align to the moving object's local axes"): (
        "Uitlijnen op de lokale assen van het bewegende object"
    ),
    ("Magnets", "Align to the 3D Viewport axes"): "Uitlijnen op de assen van de 3D-weergave",
    ("Magnets", "Align to the parent object's local axes"): (
        "Uitlijnen op de lokale assen van het ouderobject"
    ),
    ("Magnets", "Align to a collection instance empty"): (
        "Uitlijnen op de empty van een collectieinstantie"
    ),
    ("Magnets", "Align to a custom reference object"): (
        "Uitlijnen op een aangepast referentieobject"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Gelijke tussenruimte",
    ("*", "Equal Size"): "Gelijke grootte",
    ("*", "Midpoint"): "Middelpunt",
    ("*", "Surface Contact"): "Oppervlaktecontact",
    ("*", "Sphere Tangency"): "Bolraaklijn",
    ("*", "Parallel"): "Parallel",
    ("*", "Collinear"): "Colineair",
    ("*", "Coplanar"): "Coplanair",
    ("*", "Concentric"): "Concentrisch",
    ("*", "Symmetry"): "Symmetrie",
    ("*", "Detect and show Alignment markers"): (
        "Uitlijnmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Equal Spacing markers"): (
        "Markeringen voor gelijke tussenruimte detecteren en tonen"
    ),
    ("*", "Detect and show Equal Size markers"): (
        "Markeringen voor gelijke grootte detecteren en tonen"
    ),
    ("*", "Detect and show Midpoint markers"): (
        "Middelpuntmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Surface Contact markers"): (
        "Oppervlaktecontactmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Sphere Tangency markers"): (
        "Bolraaklijnmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Paralleliteitsmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Collinear markers"): (
        "Colineariteitsmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Coplanar markers"): (
        "Coplanariteitsmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Concentric markers"): (
        "Concentriciteitsmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Symmetry markers"): (
        "Symmetriemarkeringen detecteren en tonen"
    ),
    # ── Candidate and depth options, Repeat Size ────────────────────────────
    ("*", "Repeat Size"): (
        "Grootte herhalen"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Markeringen voor grootte herhalen detecteren en tonen"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Nabije objecten voorrang geven"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Objecten buiten beeld negeren en verre objecten beperken tot uitlijnhulplijnen vlak bij het vastklikken. Sneller in grote scènes"
    ),
    ("*", "Diagonal Guides"): (
        "Diagonale hulplijnen"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Ook middelpunt- en grootte-herhalen-hulplijnen aanbieden tussen punten die diagonaal op een object liggen, niet alleen langs de uitlijnassen"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Grenshoek diepte-as"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Hulplijnen en vastklikken negeren in richtingen binnen deze hoek van de kijkrichting, waar een beweging het scherm in moeilijk te zien is"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Precisiemodus",
    ("*", "Debug Logging"): "Debuglogboek",
    ("*", "Passive Color"): "Passieve kleur",
    ("*", "Active Color"): "Actieve kleur",
    ("*", "Line Width"): "Lijndikte",
    ("*", "Solid Lines"): "Doorgetrokken lijnen",
    ("*", "Snap Anchor Dot"): "Vastklikankerpunt",
    ("*", "Dot Radius"): "Puntradius",
    ("*", "Intersection Dot"): "Snijpunt",
    ("*", "Snap Pulse"): "Vastklikpuls",
    (
        "*",
        "Replace G / R / S with the Magnets transform, which locks onto a guide while "
        "dragging. When off, Blender's own transform is used and the snap is applied on release",
    ): (
        "G / R / S vervangen door de Magnets-transformatie, die tijdens het slepen op een hulplijn vastklikt. Indien uit, wordt Blenders eigen transformatie gebruikt en wordt bij loslaten vastgeklikt"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Magnets-diagnostiek naar de systeemconsole schrijven "
        "(Venster ▸ Systeemconsole tonen/verbergen)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Kleur van de hulplijn bij nadering van de vastklikzone"
    ),
    ("*", "Guide color while engaged"): "Kleur van de hulplijn wanneer actief",
    ("*", "Guide line width in pixels"): "Lijndikte van hulplijnen in pixels",
    ("*", "Draw solid guide lines, otherwise dashed"): (
        "Doorgetrokken hulplijnen tekenen, anders gestippeld"
    ),
    ("*", "Draw a dot at the coincident point when a guide is engaged"): (
        "Een punt tekenen op het samenvalpunt wanneer een hulplijn actief is"
    ),
    ("*", "Radius of the snap anchor dot in pixels"): (
        "Radius van het vastklikankerpunt in pixels"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Een markering tekenen waar twee actieve hulplijnen elkaar kruisen"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Korte helderheidsflits op het moment dat een hulplijn activeert"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Voorrang aan Blender-vastklikken"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Het vastklikken van Magnets overslaan wanneer Blenders eigen vastklikken actief is voor de transformatie, zodat de twee elkaar nooit tegenwerken"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Object waarvan de assen de uitlijnreferentie bepalen"
    ),
    ("*", "Guides only, no snapping"): "Alleen hulplijnen, geen vastklikken",
    ("*", "Locks onto guides while dragging"): "Klikt vast tijdens het slepen",
    ("*", "Snaps when G/R/S is released"): "Klikt vast bij loslaten G/R/S",
    ("*", "Blender snapping takes over"): "Blender-vastklikken gaat voor",
    ("*", "Blender Snap"): "Blender-vastklikken",
    ("*", "Yield"): "Voorrang geven",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Knop in de kopbalk"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "De aan/uit-knop van Magnets en het instellingenmenu in de kopbalk van de 3D-viewport tonen"
    ),
    ("*", "Engaged Colors"): (
        "Kleuren bij vastklikken"
    ),
    ("*", "How engaged guides are colored"): (
        "Hoe vastgeklikte hulplijnen worden gekleurd"
    ),
    ("*", "Axis Colors"): (
        "Askleuren"
    ),
    ("*", "Alignment labels use the theme's X/Y/Z axis colors; guide lines use the Active Color"): (
        "Uitlijnlabels gebruiken de X/Y/Z-askleuren van het thema; hulplijnen de actieve kleur"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Alle vastgeklikte hulplijnen gebruiken de actieve kleur"
    ),
    ("*", "Shortcut"): (
        "Sneltoets"
    ),
    ("Operator", "Toggle Magnets"): (
        "Magnets aan/uit"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Hulplijnen en vastklikken van Magnets aan- of uitzetten"
    ),
    ("*", "More options in the sidebar (N)"): "Meer opties in de zijbalk (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("Magnets", "Preset"): "Voorinstelling",
    ("Magnets", "Precise"): "Precies",
    ("Magnets", "Balanced"): "Gebalanceerd",
    ("Magnets", "Loose"): "Ruim",
    ("Magnets", "Tight tolerances for close work"): (
        "Nauwe toleranties voor fijn werk"
    ),
    ("Magnets", "Default tolerances"): "Standaardtoleranties",
    ("Magnets", "Wide tolerances for blocking out"): (
        "Ruime toleranties voor het grove opzetten"
    ),
    # ── Preset buttons (drawn as operator buttons) and reports ─────────────────
    ("Operator", "Precise"): "Precies",
    ("Operator", "Balanced"): "Gebalanceerd",
    ("Operator", "Loose"): "Ruim",
    ("*", "Magnets on"): "Magnets aan",
    ("*", "Magnets off"): "Magnets uit",
    ("*", "Snapped"): "Vastgeklikt",
    ("*", "X/Y/Z: lock axis"): "X/Y/Z: as vergrendelen",
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Move"): "Magnets: Verplaatsen",
    ("Operator", "Magnets Rotate"): "Magnets: Draaien",
    ("Operator", "Magnets Scale"): "Magnets: Schalen",
    ("Operator", "Magnets Extrude"): "Magnets: Extruderen",
    ("Operator", "Magnets Bevel"): "Magnets: Afschuinen",
    ("Operator", "Magnets Inset"): "Magnets: Inzetten",
    ("Operator", "Magnets Knife"): "Magnets: Mes",
    ("Operator", "Magnets Preset"): "Magnets: Voorinstelling",
    ("Operator", "Reset Magnets Options"): "Magnets-opties herstellen",
    ("Operator", "Magnets: No-op"): "Magnets: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Verplaatsen met geometrische Magnets-hulplijnen"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Draaien met geometrische Magnets-hulplijnen"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Schalen met geometrische Magnets-hulplijnen"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Gebied extruderen en daarna verplaatsen met Magnets-hulplijnen"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Afschuinen en daarna aanpassen met Magnets-hulplijnen"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Vlakken inzetten en daarna verplaatsen met Magnets-hulplijnen"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Met mes snijden en daarna verplaatsen met Magnets-hulplijnen"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Vastkliktoleranties op een voorinstellingsprofiel zetten"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Alle Magnets-scèneopties naar de standaardwaarden herstellen"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Interne Magnets-operator voor de registratietest"
    ),
}
