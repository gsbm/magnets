"""Spanish (es) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels
and operator buttons; ``Magnets`` for the frame, spacing and preset options, whose short
names collide with unrelated entries in Blender's own catalogue.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("*", "Snapping"): "Adherencia",
    ("*", "Guides"): "Guías",
    ("*", "Alignment"): "Alineación",
    ("*", "Guide Types"): "Tipos de guía",
    ("*", "Show"): "Mostrar",
    ("*", "Axes"): "Ejes",
    ("*", "Reference Points"): "Puntos de referencia",
    ("Magnets", "Frame"): "Sistema de referencia",
    ("*", "Object"): "Objeto",
    ("*", "Indicators"): "Indicadores",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "Adherir a las guías",
    ("Magnets", "Even Spacing"): "Espaciado uniforme",
    ("*", "Angle Snap"): "Adherir a ángulos",
    ("*", "Snap Tolerance"): "Tolerancia de adherencia",
    ("*", "Break Distance"): "Distancia de liberación",
    ("*", "Re-engage Gap"): "Margen de reenganche",
    ("*", "Range"): "Alcance",
    ("*", "Maximum Guides"): "Máximo de guías",
    ("*", "Spacing"): "Espaciado",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Guías pasivas",
    ("*", "Feature Hints"): "Indicaciones de elementos",
    ("*", "Ticks"): "Marcas",
    ("*", "Extend to Viewport"): "Extender a la vista",
    ("*", "Proximity Fade"): "Atenuar por proximidad",
    ("Magnets", "Alignment Frame"): "Sistema de alineación",
    ("*", "Custom Frame Object"): "Objeto de referencia personalizado",
    ("*", "Origin"): "Origen",
    ("*", "Pivot"): "Pivote",
    ("*", "Centroid"): "Centroide",
    ("*", "Face Centers"): "Centros de caras",
    ("*", "Bounding Box Corners"): "Esquinas de la caja delimitadora",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Mostrar guías geométricas y adherencia durante las transformaciones"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "Adherir a la guía activa al soltar la transformación. "
        "En modo precisión, bloquearse a ella mientras se arrastra"
    ),
    ("Magnets", "Which gaps the Equal Spacing guides compare between objects"): (
        "Qué separación igualan las guías de espaciado uniforme entre objetos"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Adherir la rotación a este incremento en grados. 0 lo desactiva"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Distancia en pantalla a la que una guía se activa"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Distancia adicional más allá de la tolerancia de adherencia "
        "antes de que una guía activa se libere"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Distancia que el cursor debe alejarse de la zona de adherencia "
        "antes de que una guía pueda activarse de nuevo"
    ),
    ("*", "Screen distance within which guides appear"): (
        "Distancia en pantalla dentro de la cual aparecen las guías"
    ),
    ("*", "Largest number of guides shown at once"): (
        "Número máximo de guías mostradas a la vez"
    ),
    ("*", "Minimum screen distance between shown guides"): (
        "Distancia mínima en pantalla entre las guías mostradas"
    ),
    ("*", "Allow snapping to align on the X axis"): (
        "Permitir la adherencia de alineación en el eje X"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Permitir la adherencia de alineación en el eje Y"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Permitir la adherencia de alineación en el eje Z"
    ),
    ("*", "Show guides before they engage"): (
        "Mostrar las guías antes de que se activen"
    ),
    ("*", "Show the reference feature next to each guide"): (
        "Mostrar el elemento de referencia junto a cada guía"
    ),
    ("*", "Show tick marks at guide reference points"): (
        "Mostrar marcas en los puntos de referencia de las guías"
    ),
    ("*", "Stretch edge guide lines across the 3D Viewport (alignment guides join the two objects)"): (
        "Extender las líneas de guía de aristas a lo ancho de la vista 3D (las guías de alineación unen los dos objetos)"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Aumentar gradualmente la opacidad de las guías "
        "cuando el cursor se acerca a la zona de adherencia"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Centros",
    ("Magnets", "Edges"): "Bordes",
    ("Magnets", "Both"): "Ambos",
    ("Magnets", "Distribute object centers evenly"): (
        "Distribuir los centros de los objetos de forma uniforme"
    ),
    ("Magnets", "Distribute the visible gaps between bounding boxes"): (
        "Distribuir los huecos visibles entre las cajas delimitadoras"
    ),
    ("Magnets", "Detect even spacing of centers and of edges"): (
        "Detectar espaciado uniforme de centros y de bordes"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("Magnets", "World"): "Global",
    ("Magnets", "Local"): "Local",
    ("Magnets", "View"): "Vista",
    ("Magnets", "Parent"): "Padre",
    ("Magnets", "Collection"): "Colección",
    ("Magnets", "Custom"): "Personalizado",
    ("Magnets", "Align to world X/Y/Z axes"): "Alinear a los ejes X/Y/Z globales",
    ("Magnets", "Align to the moving object's local axes"): (
        "Alinear a los ejes locales del objeto en movimiento"
    ),
    ("Magnets", "Align to the 3D Viewport axes"): "Alinear a los ejes de la vista 3D",
    ("Magnets", "Align to the parent object's local axes"): (
        "Alinear a los ejes locales del objeto padre"
    ),
    ("Magnets", "Align to a collection instance empty"): (
        "Alinear al vacío de una instancia de colección"
    ),
    ("Magnets", "Align to a custom reference object"): (
        "Alinear a un objeto de referencia personalizado"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Espaciado igual",
    ("*", "Equal Size"): "Tamaño igual",
    ("*", "Midpoint"): "Punto medio",
    ("*", "Tangency"): "Tangencia",
    ("*", "Parallel"): "Paralelo",
    ("*", "Collinear"): "Colineal",
    ("*", "Coplanar"): "Coplanar",
    ("*", "Concentric"): "Concéntrico",
    ("*", "Symmetry"): "Simetría",
    ("*", "Detect and show Alignment markers"): (
        "Detectar y mostrar marcadores de alineación"
    ),
    ("*", "Detect and show Equal Spacing markers"): (
        "Detectar y mostrar marcadores de espaciado igual"
    ),
    ("*", "Detect and show Equal Size markers"): (
        "Detectar y mostrar marcadores de tamaño igual"
    ),
    ("*", "Detect and show Midpoint markers"): (
        "Detectar y mostrar marcadores de punto medio"
    ),
    ("*", "Detect and show Tangency markers"): (
        "Detectar y mostrar marcadores de tangencia"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Detectar y mostrar marcadores de paralelismo"
    ),
    ("*", "Detect and show Collinear markers"): (
        "Detectar y mostrar marcadores de colinealidad"
    ),
    ("*", "Detect and show Coplanar markers"): (
        "Detectar y mostrar marcadores de coplanaridad"
    ),
    ("*", "Detect and show Concentric markers"): (
        "Detectar y mostrar marcadores de concentricidad"
    ),
    ("*", "Detect and show Symmetry markers"): (
        "Detectar y mostrar marcadores de simetría"
    ),
    # ── Candidate and depth options, Repeat Size ────────────────────────────
    ("*", "Repeat Size"): (
        "Repetir tamaño"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Detectar y mostrar marcadores de repetir tamaño"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Priorizar objetos cercanos"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Ignorar los objetos fuera de la vista y limitar los lejanos a guías de alineación cerca de la adherencia. Más rápido en escenas grandes"
    ),
    ("*", "Diagonal Guides"): (
        "Guías diagonales"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Ofrecer también guías de punto medio y de repetir tamaño entre puntos en diagonal de un objeto, no solo a lo largo de los ejes de alineación"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Límite del eje de profundidad"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Ignorar guías y adherencias en direcciones dentro de este ángulo de la dirección de vista, donde un movimiento hacia dentro de la pantalla es difícil de ver"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Modo precisión",
    ("*", "Debug Logging"): "Registro de depuración",
    ("*", "Passive Color"): "Color pasivo",
    ("*", "Active Color"): "Color activo",
    ("*", "Line Width"): "Grosor de línea",
    ("*", "Solid Lines"): "Líneas continuas",
    ("*", "Snap Anchor Dot"): "Punto de anclaje de adherencia",
    ("*", "Dot Radius"): "Radio del punto",
    ("*", "Intersection Dot"): "Punto de intersección",
    ("*", "Snap Pulse"): "Pulso de adherencia",
    (
        "*",
        "Replace G / R / S with the Magnets transform, which locks onto a guide while "
        "dragging. When off, Blender's own transform is used and the snap is applied on release",
    ): (
        "Sustituir G / R / S por la transformación de Magnets, que se fija a una guía mientras se arrastra. Si está desactivado, se usa la transformación propia de Blender y la adherencia se aplica al soltar"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Registrar diagnósticos de Magnets en la consola del sistema "
        "(Ventana ▸ Alternar consola del sistema)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Color de la guía al acercarse a la zona de adherencia"
    ),
    ("*", "Guide color while engaged"): "Color de la guía cuando está activa",
    ("*", "Guide line width in pixels"): "Grosor de línea de las guías en píxeles",
    ("*", "Draw solid guide lines, otherwise dashed"): (
        "Dibujar líneas de guía continuas; de lo contrario, discontinuas"
    ),
    ("*", "Draw a dot at the coincident point when a guide is engaged"): (
        "Dibujar un punto en el lugar de coincidencia cuando una guía está activa"
    ),
    ("*", "Radius of the snap anchor dot in pixels"): (
        "Radio del punto de anclaje de adherencia en píxeles"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Dibujar un marcador donde se cruzan dos guías activas"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Breve destello de brillo en el momento en que una guía se activa"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Ceder a la adherencia de Blender"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Omitir la adherencia de Magnets cuando la adherencia propia de Blender está activo en la transformación, para que ambos nunca entren en conflicto"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Objeto cuyos ejes definen el sistema de alineación"
    ),
    ("*", "Guides only, no snapping"): "Solo guías, sin adherencia",
    ("*", "Locks onto guides while dragging"): "Se fija a las guías al arrastrar",
    ("*", "Snaps when G/R/S is released"): "Se adhiere al soltar G/R/S",
    ("*", "Blender snapping takes over"): "Prevalece la adherencia de Blender",
    ("*", "Blender Snap"): "Adherencia de Blender",
    ("*", "Yield"): "Ceder",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Botón en la cabecera"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Mostrar el botón de activar/desactivar Magnets y el panel de adherencias en la cabecera de la vista 3D"
    ),
    ("*", "Engaged Colors"): (
        "Colores de guía activa"
    ),
    ("*", "How engaged guides are colored"): (
        "Cómo se colorean las guías activas"
    ),
    ("*", "Axis Colors"): (
        "Colores de eje"
    ),
    ("*", "Alignment labels use the theme's X/Y/Z axis colors; guide lines use the Active Color"): (
        "Las etiquetas de alineación usan los colores de eje X/Y/Z del tema; las líneas de guía, el color activo"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Todas las guías activas usan el color activo"
    ),
    ("*", "Shortcut"): (
        "Atajo"
    ),
    ("Operator", "Toggle Magnets"): (
        "Alternar Magnets"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Activar o desactivar las guías y la adherencia de Magnets"
    ),
    ("*", "More options in the sidebar (N)"): "Más opciones en la barra lateral (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("Magnets", "Preset"): "Preajuste",
    ("Magnets", "Precise"): "Preciso",
    ("Magnets", "Balanced"): "Equilibrado",
    ("Magnets", "Loose"): "Amplio",
    ("Magnets", "Tight tolerances for close work"): (
        "Tolerancias estrechas para trabajo de precisión"
    ),
    ("Magnets", "Default tolerances"): "Tolerancias predeterminadas",
    ("Magnets", "Wide tolerances for blocking out"): (
        "Tolerancias amplias para el boceto / bloqueo de formas"
    ),
    # ── Preset buttons (drawn as operator buttons) and reports ─────────────────
    ("Operator", "Precise"): "Preciso",
    ("Operator", "Balanced"): "Equilibrado",
    ("Operator", "Loose"): "Amplio",
    ("*", "Magnets on"): "Magnets activado",
    ("*", "Magnets off"): "Magnets desactivado",
    ("*", "Snapped"): "Adherido",
    ("*", "X/Y/Z: lock axis"): "X/Y/Z: bloquear eje",
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Move"): "Magnets: Mover",
    ("Operator", "Magnets Rotate"): "Magnets: Rotar",
    ("Operator", "Magnets Scale"): "Magnets: Escalar",
    ("Operator", "Magnets Extrude"): "Magnets: Extrudir",
    ("Operator", "Magnets Bevel"): "Magnets: Biselar",
    ("Operator", "Magnets Inset"): "Magnets: Insetar",
    ("Operator", "Magnets Knife"): "Magnets: Cuchilla",
    ("Operator", "Magnets Preset"): "Magnets: Preajuste",
    ("Operator", "Reset Magnets Options"): "Restablecer opciones de Magnets",
    ("Operator", "Magnets: No-op"): "Magnets: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Mover con las guías geométricas de Magnets"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Rotar con las guías geométricas de Magnets"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Escalar con las guías geométricas de Magnets"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Extrudir la región y luego mover con las guías de Magnets"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Biselar y luego ajustar con las guías de Magnets"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Insetar caras y luego mover con las guías de Magnets"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Cortar con cuchilla y luego mover con las guías de Magnets"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Aplicar un perfil de tolerancias de adherencia"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Restablecer todas las opciones de Magnets de la escena a sus valores predeterminados"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Operador interno de Magnets para la prueba de registro"
    ),
}
