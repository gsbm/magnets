"""Italian (it_IT) UI translations for Magnets.

Keys are ``(context, msgid)`` where msgid is the exact English source string.
Contexts: ``*`` for panels/properties/layout; ``Operator`` for operator labels
and operator buttons; ``Magnets`` for the frame, spacing and preset options, whose short
names collide with unrelated entries in Blender's own catalogue.
"""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("*", "Snapping"): "Aggancio",
    ("*", "Guides"): "Guide",
    ("*", "Alignment"): "Allineamento",
    ("*", "Guide Types"): "Tipi di guida",
    ("*", "Show"): "Mostra",
    ("*", "Axes"): "Assi",
    ("*", "Reference Points"): "Punti di riferimento",
    ("Magnets", "Frame"): "Sistema di riferimento",
    ("*", "Object"): "Oggetto",
    ("*", "Indicators"): "Indicatori",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "Aggancia alle guide",
    ("Magnets", "Even Spacing"): "Spaziatura uniforme",
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
    ("Magnets", "Alignment Frame"): "Sistema di allineamento",
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
    ("Magnets", "Which gaps the Equal Spacing guides compare between objects"): (
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
    ("*", "Stretch guide lines across the 3D Viewport"): (
        "Estendi le linee guida attraverso la vista 3D"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Aumenta gradualmente l’opacità delle guide "
        "quando il cursore si avvicina alla zona di aggancio"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Centri",
    ("Magnets", "Edges"): "Bordi",
    ("Magnets", "Both"): "Entrambi",
    ("Magnets", "Distribute object centers evenly"): (
        "Distribuisci i centri degli oggetti in modo uniforme"
    ),
    ("Magnets", "Distribute the visible gaps between bounding boxes"): (
        "Distribuisci gli spazi visibili tra i riquadri di delimitazione"
    ),
    ("Magnets", "Detect even spacing of centers and of edges"): (
        "Rileva spaziatura uniforme di centri e di bordi"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("Magnets", "World"): "Mondo",
    ("Magnets", "Local"): "Locale",
    ("Magnets", "View"): "Vista",
    ("Magnets", "Parent"): "Genitore",
    ("Magnets", "Collection"): "Raccolta",
    ("Magnets", "Custom"): "Personalizzato",
    ("Magnets", "Align to world X/Y/Z axes"): "Allinea agli assi X/Y/Z del mondo",
    ("Magnets", "Align to the moving object's local axes"): (
        "Allinea agli assi locali dell’oggetto in movimento"
    ),
    ("Magnets", "Align to the 3D Viewport axes"): "Allinea agli assi della vista 3D",
    ("Magnets", "Align to the parent object's local axes"): (
        "Allinea agli assi locali dell’oggetto genitore"
    ),
    ("Magnets", "Align to a collection instance empty"): (
        "Allinea all’empty di un’istanza di collezione"
    ),
    ("Magnets", "Align to a custom reference object"): (
        "Allinea a un oggetto di riferimento personalizzato"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("*", "Equal Spacing"): "Spaziatura uguale",
    ("*", "Equal Size"): "Dimensione uguale",
    ("*", "Midpoint"): "Punto medio",
    ("*", "Tangency"): "Tangenza",
    ("*", "Parallel"): "Parallelo",
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
    # ── Candidate and depth options, Repeat Size ────────────────────────────
    ("*", "Repeat Size"): (
        "Ripeti dimensione"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Rileva e mostra i marcatori di ripetizione della dimensione"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Dai priorità agli oggetti vicini"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Ignora gli oggetti fuori dalla vista e limita quelli lontani alle guide di allineamento vicine all’aggancio. Più veloce nelle scene grandi"
    ),
    ("*", "Diagonal Guides"): (
        "Guide diagonali"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Offri anche guide di punto medio e di ripetizione della dimensione tra punti in diagonale su un oggetto, non solo lungo gli assi di allineamento"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Soglia dell’asse di profondità"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Ignora guide e agganci nelle direzioni entro questo angolo dalla direzione di vista, dove uno spostamento dentro lo schermo è difficile da vedere"
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
        "Replace G / R / S with the Magnets transform, which locks onto a guide while "
        "dragging. When off, Blender's own transform is used and the snap is applied on release",
    ): (
        "Sostituisci G / R / S con la trasformazione Magnets, che si blocca su una guida durante il trascinamento. Se disattivato, viene usata la trasformazione di Blender e l’aggancio viene applicato al rilascio"
    ),
    (
        "*",
        "Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
    ): (
        "Registra le diagnostiche Magnets nella console di sistema "
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
        "Salta l’aggancio di Magnets quando l’aggancio nativo di Blender è attivo per la trasformazione, così i due non entrano mai in conflitto"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Oggetto i cui assi definiscono il sistema di allineamento"
    ),
    ("*", "Guides only, no snapping"): "Solo guide, senza aggancio",
    ("*", "Locks onto guides while dragging"): "Si blocca sulle guide trascinando",
    ("*", "Snaps when G/R/S is released"): "Aggancia al rilascio di G/R/S",
    ("*", "Blender snapping takes over"): "Prevale l’aggancio di Blender",
    ("*", "Blender Snap"): "Aggancio Blender",
    ("*", "Yield"): "Cedere",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Pulsante nell’intestazione"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Mostra il pulsante di attivazione di Magnets e il popover delle impostazioni nell’intestazione della vista 3D"
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
        "Attiva/disattiva Magnets"
    ),
    ("*", "Turn Magnets guides and snapping on or off"): (
        "Attiva o disattiva le guide e l’aggancio di Magnets"
    ),
    ("*", "More options in the sidebar (N)"): "Altre opzioni nella barra laterale (N)",
    # ── Preset enum ────────────────────────────────────────────────────────────
    ("Magnets", "Preset"): "Preimpostazione",
    ("Magnets", "Precise"): "Preciso",
    ("Magnets", "Balanced"): "Equilibrato",
    ("Magnets", "Loose"): "Ampio",
    ("Magnets", "Tight tolerances for close work"): (
        "Tolleranze strette per il lavoro di precisione"
    ),
    ("Magnets", "Default tolerances"): "Tolleranze predefinite",
    ("Magnets", "Wide tolerances for blocking out"): (
        "Tolleranze ampie per l’abbozzo / blocco delle forme"
    ),
    # ── Preset buttons (drawn as operator buttons) and reports ─────────────────
    ("Operator", "Precise"): "Preciso",
    ("Operator", "Balanced"): "Equilibrato",
    ("Operator", "Loose"): "Ampio",
    ("*", "Magnets on"): "Magnets attivato",
    ("*", "Magnets off"): "Magnets disattivato",
    ("*", "Snapped"): "Agganciato",
    ("*", "X/Y/Z: lock axis"): "X/Y/Z: blocca asse",
    # ── Operators (labels use Operator context) ────────────────────────────────
    ("Operator", "Magnets Move"): "Magnets: Sposta",
    ("Operator", "Magnets Rotate"): "Magnets: Ruota",
    ("Operator", "Magnets Scale"): "Magnets: Scala",
    ("Operator", "Magnets Extrude"): "Magnets: Estrudi",
    ("Operator", "Magnets Bevel"): "Magnets: Smussa",
    ("Operator", "Magnets Inset"): "Magnets: Insetta",
    ("Operator", "Magnets Knife"): "Magnets: Coltello",
    ("Operator", "Magnets Preset"): "Magnets: Preimpostazione",
    ("Operator", "Reset Magnets Options"): "Reimposta opzioni Magnets",
    ("Operator", "Magnets: No-op"): "Magnets: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Sposta con le guide geometriche Magnets"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Ruota con le guide geometriche Magnets"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Scala con le guide geometriche Magnets"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Estrudi la regione e poi sposta con le guide Magnets"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Smussa e poi regola con le guide Magnets"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Insetta le facce e poi sposta con le guide Magnets"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Taglia con il coltello e poi sposta con le guide Magnets"
    ),
    ("*", "Set snap tolerances to a preset profile"): (
        "Applica un profilo di tolleranze di aggancio"
    ),
    ("*", "Reset all Magnets scene options to their defaults"): (
        "Reimposta tutte le opzioni Magnets della scena ai valori predefiniti"
    ),
    ("*", "Internal Magnets registration smoke-test operator"): (
        "Operatore interno Magnets per il test di registrazione"
    ),
}
