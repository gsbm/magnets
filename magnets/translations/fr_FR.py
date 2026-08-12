"""French (fr_FR) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Aimants",
    ("*", "Snapping"): "Accrochage",
    ("*", "Guides"): "Guides",
    ("*", "Alignment"): "Alignement",
    ("*", "Guide Types"): "Types de guides",
    ("*", "Presets"): "Préréglages",
    ("*", "Show"): "Afficher",
    ("*", "Axes"): "Axes",
    ("*", "Reference Points"): "Points de référence",
    ("*", "Frame"): "Repère",
    ("*", "Object"): "Objet",
    ("*", "Indicators"): "Indicateurs",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Enable Guides"): "Activer les guides",
    ("*", "Snap to Guides"): "Accrocher aux guides",
    ("*", "Even Spacing"): "Espacement régulier",
    ("*", "Angle Snap"): "Accrochage d’angle",
    ("*", "Snap Tolerance"): "Tolérance d’accrochage",
    ("*", "Break Distance"): "Distance de rupture",
    ("*", "Re-engage Gap"): "Écart de réengagement",
    ("*", "Range"): "Portée",
    ("*", "Maximum Guides"): "Nombre max. de guides",
    ("*", "Spacing"): "Espacement",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Guides passifs",
    ("*", "Feature Hints"): "Indices de géométrie",
    ("*", "Ticks"): "Graduations",
    ("*", "Extend to Viewport"): "Étendre à la vue",
    ("*", "Proximity Fade"): "Fondu de proximité",
    ("*", "Alignment Frame"): "Repère d’alignement",
    ("*", "Custom Frame Object"): "Objet de repère personnalisé",
    ("*", "Origin"): "Origine",
    ("*", "Pivot"): "Pivot",
    ("*", "Centroid"): "Centroïde",
    ("*", "Face Centers"): "Centres de faces",
    ("*", "Bounding Box Corners"): "Coins de la boîte englobante",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Afficher les guides géométriques et l’accrochage pendant les transformations"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "S’accrocher au guide engagé à la fin de la transformation. "
        "En mode précision, s’y verrouiller pendant le glissement"
    ),
    ("*", "Which gap the equal-spacing guides equalise between objects"): (
        "Quel écart les guides d’espacement égal égalisent entre les objets"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Accrocher la rotation à cet incrément en degrés. 0 pour désactiver"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Distance à l’écran à laquelle un guide s’engage"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Distance supplémentaire au-delà de la tolérance d’accrochage "
        "avant qu’un guide engagé se libère"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Distance dont le curseur doit s’éloigner de la zone d’accrochage "
        "avant qu’un guide puisse se réengager"
    ),
    ("*", "Screen distance within which guides appear"): (
        "Distance à l’écran dans laquelle les guides apparaissent"
    ),
    ("*", "Largest number of guides shown at once"): (
        "Nombre maximal de guides affichés en même temps"
    ),
    ("*", "Minimum screen distance between shown guides"): (
        "Distance minimale à l’écran entre les guides affichés"
    ),
    ("*", "Allow snapping to align on the X axis"): (
        "Autoriser l’accrochage d’alignement sur l’axe X"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Autoriser l’accrochage d’alignement sur l’axe Y"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Autoriser l’accrochage d’alignement sur l’axe Z"
    ),
    ("*", "Show guides before they engage"): (
        "Afficher les guides avant qu’ils ne s’engagent"
    ),
    ("*", "Show the reference feature next to each guide"): (
        "Afficher la géométrie de référence à côté de chaque guide"
    ),
    ("*", "Show tick marks at guide reference points"): (
        "Afficher des graduations aux points de référence des guides"
    ),
    ("*", "Stretch guide lines across the 3D viewport"): (
        "Étirer les lignes de guide à travers la vue 3D"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Faire apparaître progressivement l’opacité des guides "
        "quand le curseur approche la zone d’accrochage"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("*", "Centers"): "Centres",
    ("*", "Edges"): "Bords",
    ("*", "Both"): "Les deux",
    ("*", "Distribute object centers evenly"): (
        "Répartir régulièrement les centres des objets"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Répartir les écarts visibles entre les boîtes englobantes"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Détecter un espacement régulier des centres et des bords"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("*", "World"): "Monde",
    ("*", "Local"): "Local",
    ("*", "View"): "Vue",
    ("*", "Parent"): "Parent",
    ("*", "Collection"): "Collection",
    ("*", "Custom"): "Personnalisé",
    ("*", "Align to world X/Y/Z axes"): "Aligner sur les axes X/Y/Z du monde",
    ("*", "Align to the moving object's local axes"): (
        "Aligner sur les axes locaux de l’objet en mouvement"
    ),
    ("*", "Align to the 3D View axes"): "Aligner sur les axes de la vue 3D",
    ("*", "Align to the parent object's local axes"): (
        "Aligner sur les axes locaux de l’objet parent"
    ),
    ("*", "Align to a collection instance empty"): (
        "Aligner sur l’empty d’une instance de collection"
    ),
    ("*", "Align to a custom reference object"): (
        "Aligner sur un objet de référence personnalisé"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Espacement égal",
    ("*", "Equal Size"): "Taille égale",
    ("*", "Midpoint"): "Milieu",
    ("*", "Tangency"): "Tangence",
    ("*", "Parallel"): "Parallèle",
    ("*", "Perpendicular"): "Perpendiculaire",
    ("*", "Collinear"): "Colinéaire",
    ("*", "Coplanar"): "Coplanaire",
    ("*", "Concentric"): "Concentrique",
    ("*", "Symmetry"): "Symétrie",
    ("*", "Detect and show Alignment markers"): (
        "Détecter et afficher les marqueurs d’alignement"
    ),
    ("*", "Detect and show Equal Spacing markers"): (
        "Détecter et afficher les marqueurs d’espacement égal"
    ),
    ("*", "Detect and show Equal Size markers"): (
        "Détecter et afficher les marqueurs de taille égale"
    ),
    ("*", "Detect and show Midpoint markers"): (
        "Détecter et afficher les marqueurs de milieu"
    ),
    ("*", "Detect and show Tangency markers"): (
        "Détecter et afficher les marqueurs de tangence"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Détecter et afficher les marqueurs de parallélisme"
    ),
    ("*", "Detect and show Perpendicular markers"): (
        "Détecter et afficher les marqueurs de perpendicularité"
    ),
    ("*", "Detect and show Collinear markers"): (
        "Détecter et afficher les marqueurs de colinéarité"
    ),
    ("*", "Detect and show Coplanar markers"): (
        "Détecter et afficher les marqueurs de coplanarité"
    ),
    ("*", "Detect and show Concentric markers"): (
        "Détecter et afficher les marqueurs de concentricité"
    ),
    ("*", "Detect and show Symmetry markers"): (
        "Détecter et afficher les marqueurs de symétrie"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Mode précision",
    ("*", "Debug Logging"): "Journal de débogage",
    ("*", "Passive Color"): "Couleur passive",
    ("*", "Active Color"): "Couleur active",
    ("*", "Line Width"): "Épaisseur de ligne",
    ("*", "Solid Lines"): "Lignes continues",
    ("*", "Snap Anchor Dot"): "Point d’ancrage d’accrochage",
    ("*", "Dot Radius"): "Rayon du point",
    ("*", "Intersection Dot"): "Point d’intersection",
    ("*", "Snap Pulse"): "Impulsion d’accrochage",
    (
        "*",
        "Bind G / R / S to the Magnets modal operators, which lock onto a "
        "guide while dragging. Leave off to use Blender's native transform, "
        "which snaps to the engaged guide when released",
    ): (
        "Lier G / R / S aux opérateurs modaux Aimants, qui se verrouillent "
        "sur un guide pendant le glissement. Désactiver pour utiliser "
        "la transformation native de Blender, qui s’accroche au guide "
        "engagé à la fin du mouvement"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Journaliser les diagnostics Aimants dans la console système "
        "(Fenêtre ▸ Afficher la console système)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Couleur du guide à l’approche de la zone d’accrochage"
    ),
    ("*", "Guide color while engaged"): "Couleur du guide une fois engagé",
    ("*", "Guide line width in pixels"): "Épaisseur de ligne des guides en pixels",
    ("*", "Draw solid guide lines, otherwise dashed"): (
        "Dessiner des lignes de guide continues, sinon en pointillés"
    ),
    ("*", "Draw a dot at the coincident point when a guide is engaged"): (
        "Dessiner un point au point de coïncidence quand un guide est engagé"
    ),
    ("*", "Radius of the snap anchor dot in pixels"): (
        "Rayon du point d’ancrage d’accrochage en pixels"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Dessiner un marqueur à l’intersection de deux guides engagés"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Bref flash de luminosité au moment où un guide s’engage"
    ),
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("*", "Preset"): "Préréglage",
    ("*", "Precise"): "Précis",
    ("*", "Balanced"): "Équilibré",
    ("*", "Loose"): "Large",
    ("*", "Tight tolerances for close work"): (
        "Tolérances serrées pour le travail de précision"
    ),
    ("*", "Default tolerances"): "Tolérances par défaut",
    ("*", "Wide tolerances for blocking out"): (
        "Tolérances larges pour l’ébauche / le blocage des formes"
    ),
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Grab"): "Aimants : Déplacer",
    ("Operator", "Magnets Rotate"): "Aimants : Tourner",
    ("Operator", "Magnets Scale"): "Aimants : Redimensionner",
    ("Operator", "Magnets Extrude"): "Aimants : Extruder",
    ("Operator", "Magnets Bevel"): "Aimants : Biseauter",
    ("Operator", "Magnets Inset"): "Aimants : Insérer",
    ("Operator", "Magnets Knife"): "Aimants : Couteau",
    ("Operator", "Magnets Preset"): "Aimants : Préréglage",
    ("Operator", "Reset Magnets Options"): "Réinitialiser les options Aimants",
    ("Operator", "Magnets: No-op"): "Aimants : No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Déplacer avec les guides géométriques Aimants"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Tourner avec les guides géométriques Aimants"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Redimensionner avec les guides géométriques Aimants"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Extruder la région puis déplacer avec les guides Aimants"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Biseauter puis ajuster avec les guides Aimants"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Insérer les faces puis déplacer avec les guides Aimants"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Couper au couteau puis déplacer avec les guides Aimants"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Appliquer un profil de tolérances d’accrochage"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Réinitialiser toutes les options Aimants de la scène à leurs valeurs par défaut"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Opérateur interne Aimants pour le test d’enregistrement"
    ),
}
