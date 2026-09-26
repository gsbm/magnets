"""Spanish (es / es_ES) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Imanes",
    ("*", "Snapping"): "Ajuste",
    ("*", "Guides"): "Guías",
    ("*", "Alignment"): "Alineación",
    ("*", "Guide Types"): "Tipos de guía",
    ("*", "Presets"): "Preajustes",
    ("*", "Show"): "Mostrar",
    ("*", "Axes"): "Ejes",
    ("*", "Reference Points"): "Puntos de referencia",
    ("*", "Frame"): "Sistema de referencia",
    ("*", "Object"): "Objeto",
    ("*", "Indicators"): "Indicadores",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Enable Guides"): "Activar guías",
    ("*", "Snap to Guides"): "Ajustar a las guías",
    ("*", "Even Spacing"): "Espaciado uniforme",
    ("*", "Angle Snap"): "Ajuste angular",
    ("*", "Snap Tolerance"): "Tolerancia de ajuste",
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
    ("*", "Alignment Frame"): "Sistema de alineación",
    ("*", "Custom Frame Object"): "Objeto de referencia personalizado",
    ("*", "Origin"): "Origen",
    ("*", "Pivot"): "Pivote",
    ("*", "Centroid"): "Centroide",
    ("*", "Face Centers"): "Centros de caras",
    ("*", "Bounding Box Corners"): "Esquinas de la caja delimitadora",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Mostrar guías geométricas y ajuste durante las transformaciones"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "Ajustar a la guía activa al soltar la transformación. "
        "En modo precisión, bloquearse a ella mientras se arrastra"
    ),
    ("*", "Which gap the equal-spacing guides equalise between objects"): (
        "Qué separación igualan las guías de espaciado uniforme entre objetos"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Ajustar la rotación a este incremento en grados. 0 lo desactiva"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Distancia en pantalla a la que una guía se activa"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Distancia adicional más allá de la tolerancia de ajuste "
        "antes de que una guía activa se libere"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Distancia que el cursor debe alejarse de la zona de ajuste "
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
        "Permitir el ajuste de alineación en el eje X"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Permitir el ajuste de alineación en el eje Y"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Permitir el ajuste de alineación en el eje Z"
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
    ("*", "Stretch guide lines across the 3D viewport"): (
        "Extender las líneas de guía a lo ancho de la vista 3D"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Aumentar gradualmente la opacidad de las guías "
        "cuando el cursor se acerca a la zona de ajuste"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("*", "Centers"): "Centros",
    ("*", "Edges"): "Bordes",
    ("*", "Both"): "Ambos",
    ("*", "Distribute object centers evenly"): (
        "Distribuir los centros de los objetos de forma uniforme"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Distribuir los huecos visibles entre las cajas delimitadoras"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Detectar espaciado uniforme de centros y de bordes"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("*", "World"): "Global",
    ("*", "Local"): "Local",
    ("*", "View"): "Vista",
    ("*", "Parent"): "Padre",
    ("*", "Collection"): "Colección",
    ("*", "Custom"): "Personalizado",
    ("*", "Align to world X/Y/Z axes"): "Alinear a los ejes X/Y/Z globales",
    ("*", "Align to the moving object's local axes"): (
        "Alinear a los ejes locales del objeto en movimiento"
    ),
    ("*", "Align to the 3D View axes"): "Alinear a los ejes de la vista 3D",
    ("*", "Align to the parent object's local axes"): (
        "Alinear a los ejes locales del objeto padre"
    ),
    ("*", "Align to a collection instance empty"): (
        "Alinear al vacío de una instancia de colección"
    ),
    ("*", "Align to a custom reference object"): (
        "Alinear a un objeto de referencia personalizado"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Espaciado igual",
    ("*", "Equal Size"): "Tamaño igual",
    ("*", "Midpoint"): "Punto medio",
    ("*", "Tangency"): "Tangencia",
    ("*", "Parallel"): "Paralelo",
    ("*", "Perpendicular"): "Perpendicular",
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
    ("*", "Detect and show Perpendicular markers"): (
        "Detectar y mostrar marcadores de perpendicularidad"
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
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Modo precisión",
    ("*", "Debug Logging"): "Registro de depuración",
    ("*", "Passive Color"): "Color pasivo",
    ("*", "Active Color"): "Color activo",
    ("*", "Line Width"): "Grosor de línea",
    ("*", "Solid Lines"): "Líneas continuas",
    ("*", "Snap Anchor Dot"): "Punto de anclaje de ajuste",
    ("*", "Dot Radius"): "Radio del punto",
    ("*", "Intersection Dot"): "Punto de intersección",
    ("*", "Snap Pulse"): "Pulso de ajuste",
    (
        "*",
        "Bind G / R / S to the Magnets modal operators, which lock onto a "
        "guide while dragging. Leave off to use Blender's native transform, "
        "which snaps to the engaged guide when released",
    ): (
        "Asignar G / R / S a los operadores modales de Imanes, que se "
        "bloquean a una guía al arrastrar. Desactivar para usar la "
        "transformación nativa de Blender, que se ajusta a la guía activa "
        "al soltar"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Registrar diagnósticos de Imanes en la consola del sistema "
        "(Ventana ▸ Alternar consola del sistema)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Color de la guía al acercarse a la zona de ajuste"
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
        "Radio del punto de anclaje de ajuste en píxeles"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Dibujar un marcador donde se cruzan dos guías activas"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Breve destello de brillo en el momento en que una guía se activa"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Ceder al ajuste de Blender"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Omitir el ajuste de Imanes cuando el ajuste propio de Blender está activo en la transformación, para que ambos nunca entren en conflicto"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Objeto cuyos ejes definen el sistema de alineación"
    ),
    ("*", "Guides only, no snapping"): "Solo guías, sin ajuste",
    ("*", "Locks onto guides while dragging"): "Se fija a las guías al arrastrar",
    ("*", "Snaps when you release G/R/S"): "Ajusta al soltar G/R/S",
    ("*", "Blender snapping takes over"): "Prevalece el ajuste de Blender",
    ("*", "Blender Snap"): "Ajuste de Blender",
    ("*", "Yield"): "Ceder",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("*", "Preset"): "Preajuste",
    ("*", "Precise"): "Preciso",
    ("*", "Balanced"): "Equilibrado",
    ("*", "Loose"): "Amplio",
    ("*", "Tight tolerances for close work"): (
        "Tolerancias estrechas para trabajo de precisión"
    ),
    ("*", "Default tolerances"): "Tolerancias predeterminadas",
    ("*", "Wide tolerances for blocking out"): (
        "Tolerancias amplias para el boceto / bloqueo de formas"
    ),
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Grab"): "Imanes: Mover",
    ("Operator", "Magnets Rotate"): "Imanes: Rotar",
    ("Operator", "Magnets Scale"): "Imanes: Escalar",
    ("Operator", "Magnets Extrude"): "Imanes: Extrudir",
    ("Operator", "Magnets Bevel"): "Imanes: Biselar",
    ("Operator", "Magnets Inset"): "Imanes: Insetar",
    ("Operator", "Magnets Knife"): "Imanes: Cuchilla",
    ("Operator", "Magnets Preset"): "Imanes: Preajuste",
    ("Operator", "Reset Magnets Options"): "Restablecer opciones de Imanes",
    ("Operator", "Magnets: No-op"): "Imanes: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Mover con las guías geométricas de Imanes"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Rotar con las guías geométricas de Imanes"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Escalar con las guías geométricas de Imanes"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Extrudir la región y luego mover con las guías de Imanes"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Biselar y luego ajustar con las guías de Imanes"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Insetar caras y luego mover con las guías de Imanes"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Cortar con cuchilla y luego mover con las guías de Imanes"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Aplicar un perfil de tolerancias de ajuste"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Restablecer todas las opciones de Imanes de la escena a sus valores predeterminados"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Operador interno de Imanes para la prueba de registro"
    ),
}
