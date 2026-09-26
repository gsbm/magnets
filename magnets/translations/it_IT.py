"""Italian (it_IT) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magneti",
    ("*", "Snapping"): "Aggancio",
    ("*", "Guides"): "Guide",
    ("*", "Alignment"): "Allineamento",
    ("*", "Guide Types"): "Tipi di guida",
    ("*", "Presets"): "Preimpostazioni",
    ("*", "Show"): "Mostra",
    ("*", "Axes"): "Assi",
    ("*", "Reference Points"): "Punti di riferimento",
    ("*", "Frame"): "Sistema di riferimento",
    ("*", "Object"): "Oggetto",
    ("*", "Indicators"): "Indicatori",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Enable Guides"): "Attiva guide",
    ("*", "Snap to Guides"): "Aggancia alle guide",
    ("*", "Even Spacing"): "Spaziatura uniforme",
    ("*", "Angle Snap"): "Aggancio angolare",
    ("*", "Snap Tolerance"): "Tolleranza di aggancio",
    ("*", "Break Distance"): "Distanza di rilascio",
    ("*", "Re-engage Gap"): "Margine di riaggancio",
    ("*", "Range"): "Portata",
    ("*", "Maximum Guides"): "Numero massimo di guide",
    ("*", "Spacing"): "Spaziatura",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Guide passive",
    ("*", "Feature Hints"): "Indicazioni degli elementi",
    ("*", "Ticks"): "Tacche",
    ("*", "Extend to Viewport"): "Estendi alla vista",
    ("*", "Proximity Fade"): "Dissolvenza per prossimità",
    ("*", "Alignment Frame"): "Sistema di allineamento",
    ("*", "Custom Frame Object"): "Oggetto di riferimento personalizzato",
    ("*", "Origin"): "Origine",
    ("*", "Pivot"): "Pivot",
    ("*", "Centroid"): "Baricentro",
    ("*", "Face Centers"): "Centri delle facce",
    ("*", "Bounding Box Corners"): "Angoli del riquadro di delimitazione",
    # ── Scene options (descriptions) ───────────────────────────────────────────
    ("*", "Show geometric guides and snapping during transforms"): (
        "Mostra guide geometriche e aggancio durante le trasformazioni"
    ),
    (
        "*",
        "Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
    ): (
        "Aggancia alla guida attiva al rilascio della trasformazione. "
        "In modalità precisione, bloccala durante il trascinamento"
    ),
    ("*", "Which gap the equal-spacing guides equalise between objects"): (
        "Quale distanza le guide di spaziatura uniforme equalizzano tra gli oggetti"
    ),
    ("*", "Snap rotation to this increment in degrees. 0 disables"): (
        "Aggancia la rotazione a questo incremento in gradi. 0 disattiva"
    ),
    ("*", "Screen distance at which a guide engages"): (
        "Distanza sullo schermo a cui una guida si attiva"
    ),
    (
        "*",
        "Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
    ): (
        "Distanza aggiuntiva oltre la tolleranza di aggancio "
        "prima che una guida attiva si rilasci"
    ),
    (
        "*",
        "Distance the cursor must leave the snap zone before a "
        "guide can engage again",
    ): (
        "Distanza di cui il cursore deve allontanarsi dalla zona di aggancio "
        "prima che una guida possa riattivarsi"
    ),
    ("*", "Screen distance within which guides appear"): (
        "Distanza sullo schermo entro cui appaiono le guide"
    ),
    ("*", "Largest number of guides shown at once"): (
        "Numero massimo di guide mostrate contemporaneamente"
    ),
    ("*", "Minimum screen distance between shown guides"): (
        "Distanza minima sullo schermo tra le guide mostrate"
    ),
    ("*", "Allow snapping to align on the X axis"): (
        "Consenti l’aggancio di allineamento sull’asse X"
    ),
    ("*", "Allow snapping to align on the Y axis"): (
        "Consenti l’aggancio di allineamento sull’asse Y"
    ),
    ("*", "Allow snapping to align on the Z axis"): (
        "Consenti l’aggancio di allineamento sull’asse Z"
    ),
    ("*", "Show guides before they engage"): (
        "Mostra le guide prima che si attivino"
    ),
    ("*", "Show the reference feature next to each guide"): (
        "Mostra l’elemento di riferimento accanto a ciascuna guida"
    ),
    ("*", "Show tick marks at guide reference points"): (
        "Mostra tacche sui punti di riferimento delle guide"
    ),
    ("*", "Stretch guide lines across the 3D viewport"): (
        "Estendi le linee guida attraverso la vista 3D"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Aumenta gradualmente l’opacità delle guide "
        "quando il cursore si avvicina alla zona di aggancio"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("*", "Centers"): "Centri",
    ("*", "Edges"): "Bordi",
    ("*", "Both"): "Entrambi",
    ("*", "Distribute object centers evenly"): (
        "Distribuisci i centri degli oggetti in modo uniforme"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Distribuisci gli spazi visibili tra i riquadri di delimitazione"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Rileva spaziatura uniforme di centri e di bordi"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("*", "World"): "Mondo",
    ("*", "Local"): "Locale",
    ("*", "View"): "Vista",
    ("*", "Parent"): "Genitore",
    ("*", "Collection"): "Collezione",
    ("*", "Custom"): "Personalizzato",
    ("*", "Align to world X/Y/Z axes"): "Allinea agli assi X/Y/Z del mondo",
    ("*", "Align to the moving object's local axes"): (
        "Allinea agli assi locali dell’oggetto in movimento"
    ),
    ("*", "Align to the 3D View axes"): "Allinea agli assi della vista 3D",
    ("*", "Align to the parent object's local axes"): (
        "Allinea agli assi locali dell’oggetto genitore"
    ),
    ("*", "Align to a collection instance empty"): (
        "Allinea all’empty di un’istanza di collezione"
    ),
    ("*", "Align to a custom reference object"): (
        "Allinea a un oggetto di riferimento personalizzato"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Spaziatura uguale",
    ("*", "Equal Size"): "Dimensione uguale",
    ("*", "Midpoint"): "Punto medio",
    ("*", "Tangency"): "Tangenza",
    ("*", "Parallel"): "Parallelo",
    ("*", "Perpendicular"): "Perpendicolare",
    ("*", "Collinear"): "Collineare",
    ("*", "Coplanar"): "Coplanare",
    ("*", "Concentric"): "Concentrico",
    ("*", "Symmetry"): "Simmetria",
    ("*", "Detect and show Alignment markers"): (
        "Rileva e mostra i marcatori di allineamento"
    ),
    ("*", "Detect and show Equal Spacing markers"): (
        "Rileva e mostra i marcatori di spaziatura uguale"
    ),
    ("*", "Detect and show Equal Size markers"): (
        "Rileva e mostra i marcatori di dimensione uguale"
    ),
    ("*", "Detect and show Midpoint markers"): (
        "Rileva e mostra i marcatori di punto medio"
    ),
    ("*", "Detect and show Tangency markers"): (
        "Rileva e mostra i marcatori di tangenza"
    ),
    ("*", "Detect and show Parallel markers"): (
        "Rileva e mostra i marcatori di parallelismo"
    ),
    ("*", "Detect and show Perpendicular markers"): (
        "Rileva e mostra i marcatori di perpendicolarità"
    ),
    ("*", "Detect and show Collinear markers"): (
        "Rileva e mostra i marcatori di collinearità"
    ),
    ("*", "Detect and show Coplanar markers"): (
        "Rileva e mostra i marcatori di coplanarità"
    ),
    ("*", "Detect and show Concentric markers"): (
        "Rileva e mostra i marcatori di concentricità"
    ),
    ("*", "Detect and show Symmetry markers"): (
        "Rileva e mostra i marcatori di simmetria"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Modalità precisione",
    ("*", "Debug Logging"): "Registro di debug",
    ("*", "Passive Color"): "Colore passivo",
    ("*", "Active Color"): "Colore attivo",
    ("*", "Line Width"): "Spessore linea",
    ("*", "Solid Lines"): "Linee continue",
    ("*", "Snap Anchor Dot"): "Punto di ancoraggio dell’aggancio",
    ("*", "Dot Radius"): "Raggio del punto",
    ("*", "Intersection Dot"): "Punto di intersezione",
    ("*", "Snap Pulse"): "Impulso di aggancio",
    (
        "*",
        "Bind G / R / S to the Magnets modal operators, which lock onto a "
        "guide while dragging. Leave off to use Blender's native transform, "
        "which snaps to the engaged guide when released",
    ): (
        "Associa G / R / S agli operatori modali Magneti, che si bloccano "
        "su una guida durante il trascinamento. Lascia disattivato per usare "
        "la trasformazione nativa di Blender, che si aggancia alla guida "
        "attiva al rilascio"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Registra le diagnostiche Magneti nella console di sistema "
        "(Finestra ▸ Mostra/nascondi console di sistema)"
    ),
    ("*", "Guide color while approaching the snap zone"): (
        "Colore della guida all’avvicinamento alla zona di aggancio"
    ),
    ("*", "Guide color while engaged"): "Colore della guida quando è attiva",
    ("*", "Guide line width in pixels"): "Spessore delle linee guida in pixel",
    ("*", "Draw solid guide lines, otherwise dashed"): (
        "Disegna linee guida continue, altrimenti tratteggiate"
    ),
    ("*", "Draw a dot at the coincident point when a guide is engaged"): (
        "Disegna un punto nel luogo di coincidenza quando una guida è attiva"
    ),
    ("*", "Radius of the snap anchor dot in pixels"): (
        "Raggio del punto di ancoraggio dell’aggancio in pixel"
    ),
    ("*", "Draw a marker where two engaged guides cross"): (
        "Disegna un marcatore dove due guide attive si intersecano"
    ),
    ("*", "Brief brightness flash at the moment a guide engages"): (
        "Breve lampo di luminosità nel momento in cui una guida si attiva"
    ),
    # ── Snapping hand-off, mode hints, custom frame ─────────────────────────────
    ("*", "Yield to Blender Snapping"): (
        "Cedi all’aggancio di Blender"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Salta l’aggancio di Magneti quando l’aggancio nativo di Blender è attivo per la trasformazione, così i due non entrano mai in conflitto"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Oggetto i cui assi definiscono il sistema di allineamento"
    ),
    ("*", "Guides only, no snapping"): "Solo guide, senza aggancio",
    ("*", "Locks onto guides while dragging"): "Si blocca sulle guide trascinando",
    ("*", "Snaps when you release G/R/S"): "Aggancia al rilascio di G/R/S",
    ("*", "Blender snapping takes over"): "Prevale l’aggancio di Blender",
    ("*", "Blender Snap"): "Aggancio Blender",
    ("*", "Yield"): "Cedere",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Pulsante nell’intestazione"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Mostra il pulsante di attivazione di Magneti e il popover delle impostazioni nell’intestazione della vista 3D"
    ),
    ("*", "Engaged Colors"): (
        "Colori agganciati"
    ),
    ("*", "How engaged guides are colored"): (
        "Come vengono colorate le guide agganciate"
    ),
    ("*", "Axis Colors"): (
        "Colori degli assi"
    ),
    ("*", "Alignment guides use the theme's X/Y/Z axis colors; other guides use the Active Color"): (
        "Le guide di allineamento usano i colori degli assi X/Y/Z del tema; le altre usano il colore attivo"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Tutte le guide agganciate usano il colore attivo"
    ),
    ("*", "Shortcut"): (
        "Scorciatoia"
    ),
    ("Operator", "Toggle Magnets"): (
        "Attiva/disattiva Magneti"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Attiva o disattiva le guide e l’aggancio di Magneti"
    ),
    ("*", "More options in the sidebar (N)"): "Altre opzioni nella barra laterale (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("*", "Preset"): "Preimpostazione",
    ("*", "Precise"): "Preciso",
    ("*", "Balanced"): "Equilibrato",
    ("*", "Loose"): "Ampio",
    ("*", "Tight tolerances for close work"): (
        "Tolleranze strette per il lavoro di precisione"
    ),
    ("*", "Default tolerances"): "Tolleranze predefinite",
    ("*", "Wide tolerances for blocking out"): (
        "Tolleranze ampie per l’abbozzo / blocco delle forme"
    ),
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Grab"): "Magneti: Sposta",
    ("Operator", "Magnets Rotate"): "Magneti: Ruota",
    ("Operator", "Magnets Scale"): "Magneti: Scala",
    ("Operator", "Magnets Extrude"): "Magneti: Estrudi",
    ("Operator", "Magnets Bevel"): "Magneti: Smussa",
    ("Operator", "Magnets Inset"): "Magneti: Insetta",
    ("Operator", "Magnets Knife"): "Magneti: Coltello",
    ("Operator", "Magnets Preset"): "Magneti: Preimpostazione",
    ("Operator", "Reset Magnets Options"): "Reimposta opzioni Magneti",
    ("Operator", "Magnets: No-op"): "Magneti: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Sposta con le guide geometriche Magneti"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Ruota con le guide geometriche Magneti"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Scala con le guide geometriche Magneti"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Estrudi la regione e poi sposta con le guide Magneti"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Smussa e poi regola con le guide Magneti"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Insetta le facce e poi sposta con le guide Magneti"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Taglia con il coltello e poi sposta con le guide Magneti"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Applica un profilo di tolleranze di aggancio"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Reimposta tutte le opzioni Magneti della scena ai valori predefiniti"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Operatore interno Magneti per il test di registrazione"
    ),
}
