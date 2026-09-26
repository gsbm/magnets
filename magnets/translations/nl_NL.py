"""Dutch (nl_NL) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magneten",
    ("*", "Snapping"): "Vastklikken",
    ("*", "Guides"): "Hulplijnen",
    ("*", "Alignment"): "Uitlijning",
    ("*", "Guide Types"): "Typen hulplijnen",
    ("*", "Presets"): "Voorinstellingen",
    ("*", "Show"): "Tonen",
    ("*", "Axes"): "Assen",
    ("*", "Reference Points"): "Referentiepunten",
    ("*", "Frame"): "Referentiesysteem",
    ("*", "Object"): "Object",
    ("*", "Indicators"): "Indicatoren",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Enable Guides"): "Hulplijnen inschakelen",
    ("*", "Snap to Guides"): "Vastklikken op hulplijnen",
    ("*", "Even Spacing"): "Gelijke tussenruimte",
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
    ("*", "Alignment Frame"): "Uitlijnreferentie",
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
    ("*", "Which gap the equal-spacing guides equalise between objects"): (
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
    ("*", "Stretch guide lines across the 3D viewport"): (
        "Hulplijnen over de 3D-viewport uitstrekken"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Doorzichtbaarheid van hulplijnen geleidelijk verhogen "
        "wanneer de cursor de vastklikzone nadert"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("*", "Centers"): "Centra",
    ("*", "Edges"): "Randen",
    ("*", "Both"): "Beide",
    ("*", "Distribute object centers evenly"): (
        "Objectcentra gelijkmatig verdelen"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Zichtbare tussenruimtes tussen begrenzingsboxen verdelen"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Gelijke tussenruimte van centra en randen detecteren"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("*", "World"): "Wereld",
    ("*", "Local"): "Lokaal",
    ("*", "View"): "Weergave",
    ("*", "Parent"): "Ouder",
    ("*", "Collection"): "Collectie",
    ("*", "Custom"): "Aangepast",
    ("*", "Align to world X/Y/Z axes"): "Uitlijnen op wereldassen X/Y/Z",
    ("*", "Align to the moving object's local axes"): (
        "Uitlijnen op de lokale assen van het bewegende object"
    ),
    ("*", "Align to the 3D View axes"): "Uitlijnen op de assen van de 3D-weergave",
    ("*", "Align to the parent object's local axes"): (
        "Uitlijnen op de lokale assen van het ouderobject"
    ),
    ("*", "Align to a collection instance empty"): (
        "Uitlijnen op de empty van een collectieinstantie"
    ),
    ("*", "Align to a custom reference object"): (
        "Uitlijnen op een aangepast referentieobject"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Gelijke tussenruimte",
    ("*", "Equal Size"): "Gelijke grootte",
    ("*", "Midpoint"): "Middelpunt",
    ("*", "Tangency"): "Raaklijn",
    ("*", "Parallel"): "Parallel",
    ("*", "Perpendicular"): "Loodrecht",
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
    ("*", "Detect and show Tangency markers"): (
        "Raaklijnmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Paralleliteitsmarkeringen detecteren en tonen"
    ),
    ("*", "Detect and show Perpendicular markers"): (
        "Loodrechtmarkeringen detecteren en tonen"
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
        "Bind G / R / S to the Magnets modal operators, which lock onto a "
        "guide while dragging. Leave off to use Blender's native transform, "
        "which snaps to the engaged guide when released",
    ): (
        "Koppel G / R / S aan de modale Magnetenoperatoren, die tijdens "
        "het slepen aan een hulplijn vastklikken. Uit laten om de native "
        "transformatie van Blender te gebruiken, die bij loslaten "
        "vastklikt op de actieve hulplijn"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Magnetendiagnostiek naar de systeemconsole schrijven "
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
        "Het vastklikken van Magneten overslaan wanneer Blenders eigen vastklikken actief is voor de transformatie, zodat de twee elkaar nooit tegenwerken"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Object waarvan de assen de uitlijnreferentie bepalen"
    ),
    ("*", "Guides only, no snapping"): "Alleen hulplijnen, geen vastklikken",
    ("*", "Locks onto guides while dragging"): "Klikt vast tijdens het slepen",
    ("*", "Snaps when you release G/R/S"): "Klikt vast bij loslaten G/R/S",
    ("*", "Blender snapping takes over"): "Blender-vastklikken gaat voor",
    ("*", "Blender Snap"): "Blender-vastklikken",
    ("*", "Yield"): "Voorrang geven",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Knop in de kopbalk"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "De aan/uit-knop van Magneten en het instellingenmenu in de kopbalk van de 3D-viewport tonen"
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
    ("*", "Alignment guides use the theme's X/Y/Z axis colors; other guides use the Active Color"): (
        "Uitlijnhulplijnen gebruiken de X/Y/Z-askleuren van het thema; andere hulplijnen de actieve kleur"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Alle vastgeklikte hulplijnen gebruiken de actieve kleur"
    ),
    ("*", "Shortcut"): (
        "Sneltoets"
    ),
    ("Operator", "Toggle Magnets"): (
        "Magneten aan/uit"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Hulplijnen en vastklikken van Magneten aan- of uitzetten"
    ),
    ("*", "More options in the sidebar (N)"): "Meer opties in de zijbalk (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("*", "Preset"): "Voorinstelling",
    ("*", "Precise"): "Precies",
    ("*", "Balanced"): "Gebalanceerd",
    ("*", "Loose"): "Ruim",
    ("*", "Tight tolerances for close work"): (
        "Nauwe toleranties voor fijn werk"
    ),
    ("*", "Default tolerances"): "Standaardtoleranties",
    ("*", "Wide tolerances for blocking out"): (
        "Ruime toleranties voor het grove opzetten"
    ),
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Grab"): "Magneten: Verplaatsen",
    ("Operator", "Magnets Rotate"): "Magneten: Draaien",
    ("Operator", "Magnets Scale"): "Magneten: Schalen",
    ("Operator", "Magnets Extrude"): "Magneten: Extruderen",
    ("Operator", "Magnets Bevel"): "Magneten: Afschuinen",
    ("Operator", "Magnets Inset"): "Magneten: Inzetten",
    ("Operator", "Magnets Knife"): "Magneten: Mes",
    ("Operator", "Magnets Preset"): "Magneten: Voorinstelling",
    ("Operator", "Reset Magnets Options"): "Magnetenopties herstellen",
    ("Operator", "Magnets: No-op"): "Magneten: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Verplaatsen met geometrische Magnetenhulplijnen"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Draaien met geometrische Magnetenhulplijnen"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Schalen met geometrische Magnetenhulplijnen"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Gebied extruderen en daarna verplaatsen met Magnetenhulplijnen"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Afschuinen en daarna aanpassen met Magnetenhulplijnen"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Vlakken inzetten en daarna verplaatsen met Magnetenhulplijnen"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Met mes snijden en daarna verplaatsen met Magnetenhulplijnen"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Vastkliktoleranties op een voorinstellingsprofiel zetten"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Alle Magnetenscèneopties naar de standaardwaarden herstellen"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Interne Magnetenoperator voor de registratietest"
    ),
}
