"""French (fr_FR) UI translations for Magnets."""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("Magnets", "Snapping"): "Aimantation",
    ("*", "Guides"): "Guides",
    ("*", "Alignment"): "Alignement",
    ("*", "Guide Types"): "Types de guides",
    ("*", "Show"): "Afficher",
    ("*", "Axes"): "Axes",
    ("*", "Reference Points"): "Points de référence",
    ("Magnets", "Frame"): "Repère",
    ("*", "Object"): "Objet",
    ("*", "Indicators"): "Indicateurs",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "Aimanter aux guides",
    ("Magnets", "Even Spacing"): "Espacement régulier",
    ("*", "Angle Snap"): "Aimantation angulaire",
    ("*", "Snap Tolerance"): "Tolérance d’aimantation",
    ("*", "Break Distance"): "Distance de rupture",
    ("*", "Re-engage Gap"): "Écart de réengagement",
    ("*", "Range"): "Intervalle",
    ("*", "Maximum Guides"): "Nombre maximal de guides",
    ("*", "Spacing"): "Espacement",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Guides passifs",
    ("*", "Feature Hints"): "Indices de géométrie",
    ("*", "Ticks"): "Graduations",
    ("*", "Extend to Viewport"): "Étendre à la vue",
    ("*", "Proximity Fade"): "Fondu de proximité",
    ("Magnets", "Alignment Frame"): "Repère d’alignement",
    ("*", "Custom Frame Object"): "Objet de repère personnalisé",
    ("*", "Origin"): "Origine",
    ("*", "Pivot"): "Pivot",
    ("*", "Centroid"): "Centroïde",
    ("*", "Face Centers"): "Centres de faces",
    ("*", "Bounding Box Corners"): "Coins de la boîte englobante",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Afficher les guides géométriques et l’aimantation pendant les transformations"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "S’aimanter au guide engagé à la fin de la transformation. "
        "En mode précision, s’y verrouiller pendant le glissement"
    ),
    ("*", "Which gaps the Equal Spacing guides compare between objects"): (
        "Quel écart les guides d’espacement égal égalisent entre les objets"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Aimanter la rotation à cet incrément en degrés. 0 pour désactiver"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Distance à l’écran à laquelle un guide s’engage"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Distance supplémentaire au-delà de la tolérance d’aimantation "
        "avant qu’un guide engagé se libère"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Distance dont le curseur doit s’éloigner de la zone d’aimantation "
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
        "Autoriser l’aimantation d’alignement sur l’axe X"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Autoriser l’aimantation d’alignement sur l’axe Y"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Autoriser l’aimantation d’alignement sur l’axe Z"
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
    ("*", "Stretch edge guide lines across the 3D Viewport (alignment guides join the two objects)"): (
        "Étirer les guides d’arêtes à travers la vue 3D (les guides d’alignement relient les deux objets)"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Faire apparaître progressivement les guides "
        "quand le curseur approche de la zone d’aimantation"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Centres",
    ("Magnets", "Edges"): "Bords",
    ("Magnets", "Both"): "Les deux",
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
    ("Magnets", "World"): "Monde",
    ("Magnets", "Local"): "Local",
    ("Magnets", "View"): "Vue",
    ("Magnets", "Parent"): "Parent",
    ("Magnets", "Collection"): "Collection",
    ("Magnets", "Custom"): "Personnalisé",
    ("*", "Align to world X/Y/Z axes"): "Aligner sur les axes X/Y/Z du monde",
    ("*", "Align to the moving object's local axes"): (
        "Aligner sur les axes locaux de l’objet en mouvement"
    ),
    ("*", "Align to the 3D Viewport axes"): "Aligner sur les axes de la vue 3D",
    ("*", "Align to the parent object's local axes"): (
        "Aligner sur les axes locaux de l’objet parent"
    ),
    ("*", "Align to a collection instance empty"): (
        "Aligner sur l’objet vide d’une instance de collection"
    ),
    ("*", "Align to a custom reference object"): (
        "Aligner sur un objet de référence personnalisé"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("Magnets", "Alignment"): "Alignement",
    ("Magnets", "Equal Spacing"): "Espacement égal",
    ("Magnets", "Equal Size"): "Taille égale",
    ("Magnets", "Midpoint"): "Point milieu",
    ("Magnets", "Surface Contact"): "Contact de surface",
    ("Magnets", "Sphere Tangency"): "Tangence de sphère",
    ("Magnets", "Parallel"): "Parallèle",
    ("Magnets", "Collinear"): "Colinéaire",
    ("Magnets", "Coplanar"): "Coplanaire",
    ("Magnets", "Concentric"): "Concentrique",
    ("Magnets", "Symmetry"): "Symétrie",
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
        "Détecter et afficher les marqueurs de point milieu"
    ),
    ("*", "Detect and show Surface Contact markers"): (
        "Détecter et afficher les marqueurs de contact de surface"
    ),
    ("*", "Detect and show Sphere Tangency markers"): (
        "Détecter et afficher les marqueurs de tangence de sphère"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Détecter et afficher les marqueurs de parallélisme"
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
    # ── Candidate and depth options, Repeat Size ────────────────────────────
    ("Magnets", "Repeat Size"): (
        "Répétition de taille"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Détecter et afficher les marqueurs de répétition de taille"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Prioriser les objets proches"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Ignorer les objets hors de la vue et limiter les objets éloignés aux guides d’alignement proches de l’aimantation. Plus rapide dans les grandes scènes"
    ),
    ("*", "Diagonal Guides"): (
        "Guides diagonaux"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Proposer aussi des guides de point milieu et de répétition de taille entre des points en diagonale sur un objet, pas seulement le long des axes d’alignement"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Seuil de l’axe de profondeur"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Ignorer les guides et aimantations dans les directions à moins de cet angle de la direction de vue, où un déplacement dans l’écran est difficile à voir"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Mode précision",
    ("*", "Debug Logging"): "Journal de débogage",
    ("*", "Passive Color"): "Couleur passive",
    ("*", "Active Color"): "Couleur active",
    ("*", "Line Width"): "Épaisseur de ligne",
    ("*", "Solid Lines"): "Lignes continues",
    ("*", "Snap Anchor Dot"): "Point d’ancrage d’aimantation",
    ("*", "Dot Radius"): "Rayon du point",
    ("*", "Intersection Dot"): "Point d’intersection",
    ("*", "Snap Pulse"): "Impulsion d’aimantation",
    (
        "*",
        "Replace G / R / S with the Magnets transform, which locks onto a guide while "
        "dragging. When off, Blender's own transform is used and the snap is applied on release",
    ): (
        "Remplacer G / R / S par la transformation Magnets, qui se verrouille sur un guide pendant le glissement. Si désactivé, la transformation de Blender est utilisée et l’aimantation est appliquée au relâchement"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Journaliser les diagnostics Magnets dans la console système "
        "(Fenêtre ▸ (Dés)activer la console système)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Couleur du guide à l’approche de la zone d’aimantation"
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
        "Rayon du point d’ancrage d’aimantation en pixels"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Dessiner un marqueur à l’intersection de deux guides engagés"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Bref flash de luminosité au moment où un guide s’engage"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Céder à l’aimantation de Blender"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Ignorer l’aimantation Magnets lorsque l’aimantation de Blender est active pour la transformation, afin que les deux n’entrent jamais en conflit"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Objet dont les axes définissent le repère d’alignement"
    ),
    ("*", "Guides only, no snapping"): "Guides seuls, sans aimantation",
    ("*", "Locks onto guides while dragging"): "Se verrouille sur les guides pendant le glissement",
    ("*", "Snaps when G/R/S is released"): "S’aimante au relâchement de G/R/S",
    ("*", "Blender snapping takes over"): "L’aimantation de Blender prend le relais",
    ("*", "Blender Snap"): "Aimantation de Blender",
    ("*", "Yield"): "Céder",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Bouton dans l’en-tête"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Afficher le bouton marche/arrêt Magnets et le menu des réglages dans l’en-tête de la vue 3D"
    ),
    ("*", "Engaged Colors"): (
        "Couleurs des guides engagés"
    ),
    ("*", "How engaged guides are colored"): (
        "Couleur des guides engagés"
    ),
    ("*", "Axis Colors"): (
        "Couleurs des axes"
    ),
    ("*", "Alignment labels use the theme's X/Y/Z axis colors; guide lines use the Active Color"): (
        "Les étiquettes d’alignement prennent les couleurs d’axe X/Y/Z du thème ; les lignes de guide la couleur active"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Tous les guides engagés utilisent la couleur active"
    ),
    ("*", "Shortcut"): (
        "Raccourci"
    ),
    ("Operator", "Toggle Magnets"): (
        "(Dés)activer Magnets"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Activer ou désactiver les guides et l’aimantation Magnets"
    ),
    ("*", "More options in the sidebar (N)"): "Plus d’options dans la barre latérale (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("Magnets", "Preset"): "Préréglage",
    ("Magnets", "Precise"): "Précis",
    ("Magnets", "Balanced"): "Équilibré",
    ("Magnets", "Loose"): "Large",
    ("*", "Tight tolerances for close work"): (
        "Tolérances serrées pour le travail de précision"
    ),
    ("*", "Default tolerances"): "Tolérances par défaut",
    ("*", "Wide tolerances for blocking out"): (
        "Tolérances larges pour l’ébauche"
    ),
    # ── Preset buttons (drawn as operator buttons) and reports ─────────────────
    ("Operator", "Precise"): "Précis",
    ("Operator", "Balanced"): "Équilibré",
    ("Operator", "Loose"): "Large",
    ("*", "Magnets on"): "Magnets activé",
    ("*", "Magnets off"): "Magnets désactivé",
    ("*", "Snapped"): "Aimanté",
    ("*", "X/Y/Z: lock axis"): "X/Y/Z : verrouiller l’axe",
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Move"): "Magnets : Déplacer",
    ("Operator", "Magnets Rotate"): "Magnets : Tourner",
    ("Operator", "Magnets Scale"): "Magnets : Redimensionner",
    ("Operator", "Magnets Extrude"): "Magnets : Extruder",
    ("Operator", "Magnets Bevel"): "Magnets : Biseauter",
    ("Operator", "Magnets Inset"): "Magnets : Incruster",
    ("Operator", "Magnets Knife"): "Magnets : Couteau",
    ("Operator", "Magnets Preset"): "Magnets : Préréglage",
    ("Operator", "Reset Magnets Options"): "Réinitialiser les options Magnets",
    ("Operator", "Magnets: No-op"): "Magnets : No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Déplacer avec les guides géométriques Magnets"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Tourner avec les guides géométriques Magnets"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Redimensionner avec les guides géométriques Magnets"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Extruder la région puis déplacer avec les guides Magnets"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Biseauter puis ajuster avec les guides Magnets"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Incruster les faces puis déplacer avec les guides Magnets"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Projeter une découpe au couteau puis déplacer avec les guides Magnets"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Appliquer un profil de tolérances d’aimantation"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Réinitialiser toutes les options Magnets de la scène à leurs valeurs par défaut"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Opérateur interne Magnets pour le test d’enregistrement"
    ),
}
