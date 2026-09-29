"""Italian (it_IT) UI translations for Magnets."""

TRANSLATIONS: dict[tuple[str, str], str] = {
    # ── Panels / category ──────────────────────────────────────────────────────
    ("*", "Magnets"): "Magnets",
    ("Magnets", "Snapping"): "Aggancio",
    ("*", "Guides"): "Guide",
    ("*", "Alignment"): "Allineamento",
    ("*", "Guide Types"): "Tipi di Guida",
    ("*", "Show"): "Mostra",
    ("*", "Axes"): "Assi",
    ("*", "Reference Points"): "Punti di Riferimento",
    ("Magnets", "Frame"): "Sistema di Riferimento",
    ("*", "Object"): "Oggetto",
    ("*", "Indicators"): "Indicatori",
    # ── Scene options (names) ──────────────────────────────────────────────────
    ("*", "Snap to Guides"): "Aggancia alle Guide",
    ("Magnets", "Even Spacing"): "Spaziatura Uniforme",
    ("*", "Angle Snap"): "Aggancio agli Angoli",
    ("*", "Snap Tolerance"): "Tolleranza di Aggancio",
    ("*", "Break Distance"): "Distanza di Rilascio",
    ("*", "Re-engage Gap"): "Margine di Riaggancio",
    ("*", "Range"): "Intervallo",
    ("*", "Maximum Guides"): "Numero Massimo di Guide",
    ("*", "Spacing"): "Spaziatura",
    ("*", "X"): "X",
    ("*", "Y"): "Y",
    ("*", "Z"): "Z",
    ("*", "Passive Guides"): "Guide Passive",
    ("*", "Feature Hints"): "Indicazioni Elementi",
    ("*", "Ticks"): "Tacche",
    ("*", "Extend to Viewport"): "Estendi alla Viewport",
    ("*", "Proximity Fade"): "Dissolvenza per Prossimità",
    ("Magnets", "Alignment Frame"): "Sistema di Allineamento",
    ("*", "Custom Frame Object"): "Oggetto di Riferimento Personalizzato",
    ("*", "Origin"): "Origine",
    ("*", "Pivot"): "Perno",
    ("*", "Centroid"): "Baricentro",
    ("*", "Face Centers"): "Centri delle Facce",
    ("*", "Bounding Box Corners"): "Angoli Casella Delimitazione",
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
        "In Modalità Precisione, vi si blocca durante il trascinamento"
    ),
    ("*", "Which gaps the Equal Spacing guides compare between objects"): (
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
    ("*", "Stretch edge guide lines across the 3D Viewport (alignment guides join the two objects)"): (
        "Estendi le linee guida degli spigoli attraverso la viewport 3D (le guide di allineamento uniscono i due oggetti)"
    ),
    ("*", "Fade guide opacity in as the cursor approaches the snap zone"): (
        "Aumenta gradualmente l’opacità delle guide "
        "quando il cursore si avvicina alla zona di aggancio"
    ),
    # ── Spacing metric enum ────────────────────────────────────────────────────
    ("Magnets", "Centers"): "Centri",
    ("Magnets", "Edges"): "Bordi",
    ("Magnets", "Both"): "Entrambi",
    ("*", "Distribute object centers evenly"): (
        "Distribuisci i centri degli oggetti in modo uniforme"
    ),
    ("*", "Distribute the visible gaps between bounding boxes"): (
        "Distribuisci gli spazi visibili tra le caselle di delimitazione"
    ),
    ("*", "Detect even spacing of centers and of edges"): (
        "Rileva spaziatura uniforme di centri e di bordi"
    ),
    # ── Alignment frame enum ───────────────────────────────────────────────────
    ("Magnets", "World"): "Mondo",
    ("Magnets", "Local"): "Locale",
    ("Magnets", "View"): "Vista",
    ("Magnets", "Parent"): "Genitore",
    ("Magnets", "Collection"): "Raccolta",
    ("Magnets", "Custom"): "Personalizzato",
    ("*", "Align to world X/Y/Z axes"): "Allinea agli assi X/Y/Z del mondo",
    ("*", "Align to the moving object's local axes"): (
        "Allinea agli assi locali dell’oggetto in movimento"
    ),
    ("*", "Align to the 3D Viewport axes"): "Allinea agli assi della viewport 3D",
    ("*", "Align to the parent object's local axes"): (
        "Allinea agli assi locali dell’oggetto genitore"
    ),
    ("*", "Align to a collection instance empty"): (
        "Allinea al vuoto di un’istanza di raccolta"
    ),
    ("*", "Align to a custom reference object"): (
        "Allinea a un oggetto di riferimento personalizzato"
    ),
    # ── Constraint families ────────────────────────────────────────────────────
    ("Magnets", "Alignment"): "Allineamento",
    ("Magnets", "Equal Spacing"): "Spaziatura Uguale",
    ("Magnets", "Equal Size"): "Dimensione Uguale",
    ("Magnets", "Midpoint"): "Punto Medio",
    ("Magnets", "Surface Contact"): "Contatto di Superficie",
    ("Magnets", "Sphere Tangency"): "Tangenza Sferica",
    ("Magnets", "Parallel"): "Parallelo",
    ("Magnets", "Collinear"): "Collineare",
    ("Magnets", "Coplanar"): "Coplanare",
    ("Magnets", "Concentric"): "Concentrico",
    ("Magnets", "Symmetry"): "Simmetria",
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
    ("*", "Detect and show Surface Contact markers"): (
        "Rileva e mostra i marcatori di contatto di superficie"
    ),
    ("*", "Detect and show Sphere Tangency markers"): (
        "Rileva e mostra i marcatori di tangenza sferica"
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
    ("Magnets", "Repeat Size"): (
        "Ripetizione Dimensione"
    ),
    ("*", "Detect and show Repeat Size markers"): (
        "Rileva e mostra i marcatori di ripetizione della dimensione"
    ),
    ("*", "Prioritize Nearby Objects"): (
        "Priorità agli Oggetti Vicini"
    ),
    ("*", "Ignore objects outside the view and limit distant ones to alignment guides near snapping. Faster in large scenes"): (
        "Ignora gli oggetti fuori dalla vista e limita quelli lontani alle guide di allineamento vicine all’aggancio. Più veloce nelle scene grandi"
    ),
    ("*", "Diagonal Guides"): (
        "Guide Diagonali"
    ),
    ("*", "Also offer Midpoint and Repeat Size guides between points that lie diagonally on an object, not only along the alignment axes"): (
        "Offri anche guide di punto medio e di ripetizione della dimensione tra punti in diagonale su un oggetto, non solo lungo gli assi di allineamento"
    ),
    ("*", "Depth Axis Cutoff"): (
        "Soglia Asse di Profondità"
    ),
    ("*", "Ignore guides and snaps along directions within this angle of the view direction, where a move into the screen is hard to see"): (
        "Ignora guide e agganci nelle direzioni entro questo angolo dalla direzione di vista, dove uno spostamento dentro lo schermo è difficile da vedere"
    ),
    # ── Preferences ────────────────────────────────────────────────────────────
    ("*", "Precision Mode"): "Modalità Precisione",
    ("*", "Debug Logging"): "Registro di Debug",
    ("*", "Passive Color"): "Colore Passivo",
    ("*", "Active Color"): "Colore Attivo",
    ("*", "Line Width"): "Spessore Linea",
    ("*", "Solid Lines"): "Linee Continue",
    ("*", "Snap Anchor Dot"): "Punto di Ancoraggio",
    ("*", "Dot Radius"): "Raggio del Punto",
    ("*", "Intersection Dot"): "Punto di Intersezione",
    ("*", "Snap Pulse"): "Impulso di Aggancio",
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
        "(Finestra ▸ Mostra/Nascondi Console di Sistema)"
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
        "Cedi all’Aggancio di Blender"
    ),
    ("*", "Skip the Magnets snap whenever Blender's own snapping is active for the transform, so the two never fight"): (
        "Salta l’aggancio di Magnets quando l’aggancio nativo di Blender è attivo per la trasformazione, così i due non entrano mai in conflitto"
    ),
    ("*", "Object whose axes define the alignment frame"): (
        "Oggetto i cui assi definiscono il sistema di allineamento"
    ),
    ("*", "Guides only, no snapping"): "Solo guide, senza aggancio",
    ("*", "Locks onto guides while dragging"): "Si blocca sulle guide durante il trascinamento",
    ("*", "Snaps when G/R/S is released"): "Aggancia al rilascio di G/R/S",
    ("*", "Blender snapping takes over"): "Prevale l’aggancio di Blender",
    ("*", "Blender Snap"): "Aggancio di Blender",
    ("*", "Yield"): "Cedi",
    # ── Header toggle, engaged colours, shortcut ──────────────────────────────
    ("*", "Header Toggle"): (
        "Pulsante nell’Intestazione"
    ),
    ("*", "Show the Magnets on/off button and settings popover in the 3D Viewport header"): (
        "Mostra il pulsante di attivazione di Magnets e il menu delle impostazioni nell’intestazione della viewport 3D"
    ),
    ("*", "Engaged Colors"): (
        "Colori Guide Attive"
    ),
    ("*", "How engaged guides are colored"): (
        "Come vengono colorate le guide attive"
    ),
    ("*", "Axis Colors"): (
        "Colori degli Assi"
    ),
    ("*", "Alignment labels use the theme's X/Y/Z axis colors; guide lines use the Active Color"): (
        "Le etichette di allineamento usano i colori degli assi X/Y/Z del tema; le linee guida il colore attivo"
    ),
    ("*", "Every engaged guide uses the Active Color"): (
        "Tutte le guide attive usano il colore attivo"
    ),
    ("*", "Shortcut"): (
        "Scorciatoia"
    ),
    ("Operator", "Toggle Magnets"): (
        "Attiva/Disattiva Magnets"
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
    ("*", "Tight tolerances for close work"): (
        "Tolleranze strette per il lavoro di precisione"
    ),
    ("*", "Default tolerances"): "Tolleranze predefinite",
    ("*", "Wide tolerances for blocking out"): (
        "Tolleranze ampie per l’abbozzo delle forme"
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
    ("Operator", "Magnets Move"): "Magnets: Muovi",
    ("Operator", "Magnets Rotate"): "Magnets: Ruota",
    ("Operator", "Magnets Scale"): "Magnets: Scala",
    ("Operator", "Magnets Extrude"): "Magnets: Estrudi",
    ("Operator", "Magnets Bevel"): "Magnets: Smussa",
    ("Operator", "Magnets Inset"): "Magnets: Incassa",
    ("Operator", "Magnets Knife"): "Magnets: Coltello",
    ("Operator", "Magnets Preset"): "Magnets: Preimpostazione",
    ("Operator", "Reset Magnets Options"): "Reimposta Opzioni Magnets",
    ("Operator", "Magnets: No-op"): "Magnets: No-op",
    # ── Operator descriptions ──────────────────────────────────────────────────
    ("*", "Move with Magnets geometric guides"): (
        "Muovi con le guide geometriche Magnets"
    ),
    ("*", "Rotate with Magnets geometric guides"): (
        "Ruota con le guide geometriche Magnets"
    ),
    ("*", "Scale with Magnets geometric guides"): (
        "Scala con le guide geometriche Magnets"
    ),
    ("*", "Extrude region then move with Magnets guides"): (
        "Estrudi la regione e poi muovi con le guide Magnets"
    ),
    ("*", "Bevel then adjust with Magnets guides"): (
        "Smussa e poi regola con le guide Magnets"
    ),
    ("*", "Inset faces then move with Magnets guides"): (
        "Incassa le facce e poi muovi con le guide Magnets"
    ),
    ("*", "Knife project cut then move with Magnets guides"): (
        "Proietta un taglio con il coltello e poi muovi con le guide Magnets"
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
