"""Per-scene Magnets options (N-panel). Preferences hold colors."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)

from .core.families import FAMILIES
from .core.frames import Frame
from .translations import CONTEXT


def _family_toggle_annotations() -> dict:
    ann = {}
    for fid, label in FAMILIES:
        ann[f"enable_{fid}"] = BoolProperty(
            name=label,
            description=f"Detect and show {label} markers",
            default=True,
        )
    return ann


_FRAME_ITEMS = [
    (Frame.WORLD.value, "World", "Align to world X/Y/Z axes"),
    (Frame.LOCAL.value, "Local", "Align to the moving object's local axes"),
    (Frame.VIEW.value, "View", "Align to the 3D Viewport axes"),
    (Frame.PARENT.value, "Parent", "Align to the parent object's local axes"),
    (Frame.COLLECTION.value, "Collection", "Align to a collection instance empty"),
    (Frame.CUSTOM.value, "Custom", "Align to a custom reference object"),
]


class MagnetsOptions(bpy.types.PropertyGroup):
    """Per-scene Magnets options property group."""
    enabled: BoolProperty(
        name="Magnets",
        description="Show geometric guides and snapping during transforms",
        default=True,
    )
    soft_snap: BoolProperty(
        name="Snap to Guides",
        description="Snap to the engaged guide when the transform is released. "
        "In Precision Mode, lock onto it while dragging",
        default=True,
    )
    defer_to_native_snap: BoolProperty(
        name="Yield to Blender Snapping",
        description="Skip the Magnets snap whenever Blender's own snapping is "
        "active for the transform, so the two never fight",
        default=True,
    )
    spacing_metric: EnumProperty(
        name="Even Spacing",
        description="Which gaps the Equal Spacing guides compare between objects",
        translation_context=CONTEXT,
        items=[
            ("center", "Centers", "Distribute object centers evenly"),
            ("edge", "Edges", "Distribute the visible gaps between bounding boxes"),
            ("both", "Both", "Detect even spacing of centers and of edges"),
        ],
        default="both",
    )
    angle_snap_increment: FloatProperty(
        name="Angle Snap",
        description="Snap rotation to this increment in degrees. 0 disables",
        default=15.0,
        min=0.0,
        max=90.0,
    )
    snap_tolerance_px: IntProperty(
        name="Snap Tolerance",
        description="Screen distance at which a guide engages",
        default=16,
        min=1,
        max=100,
        subtype="PIXEL",
    )
    snap_release_hysteresis_px: IntProperty(
        name="Break Distance",
        description="Extra distance beyond the snap tolerance before an "
        "engaged guide releases",
        default=40,
        min=0,
        max=120,
        subtype="PIXEL",
    )
    snap_reengage_margin_px: IntProperty(
        name="Re-engage Gap",
        description="Distance the cursor must leave the snap zone before a "
        "guide can engage again",
        default=12,
        min=0,
        max=60,
        subtype="PIXEL",
    )
    passive_range_px: IntProperty(
        name="Range",
        description="Screen distance within which guides appear",
        default=72,
        min=1,
        max=400,
        subtype="PIXEL",
    )
    max_guides: IntProperty(
        name="Maximum Guides",
        description="Largest number of guides shown at once",
        default=5,
        min=1,
        max=12,
    )
    nms_distance_px: IntProperty(
        name="Spacing",
        description="Minimum screen distance between shown guides",
        default=24,
        min=0,
        max=200,
        subtype="PIXEL",
    )
    snap_axis_x: BoolProperty(
        name="X",
        description="Allow snapping to align on the X axis",
        default=True,
    )
    snap_axis_y: BoolProperty(
        name="Y",
        description="Allow snapping to align on the Y axis",
        default=True,
    )
    snap_axis_z: BoolProperty(
        name="Z",
        description="Allow snapping to align on the Z axis",
        default=True,
    )
    show_passive_guides: BoolProperty(
        name="Passive Guides",
        description="Show guides before they engage",
        default=True,
    )
    show_feature_hints: BoolProperty(
        name="Feature Hints",
        description="Show the reference feature next to each guide",
        default=True,
    )
    show_guide_ticks: BoolProperty(
        name="Ticks",
        description="Show tick marks at guide reference points",
        default=True,
    )
    extend_guides_to_viewport: BoolProperty(
        name="Extend to Viewport",
        description="Stretch guide lines across the 3D Viewport",
        default=True,
    )
    alignment_frame: EnumProperty(
        name="Alignment Frame",
        items=_FRAME_ITEMS,
        translation_context=CONTEXT,
        default=Frame.WORLD.value,
    )
    custom_frame_object: PointerProperty(
        name="Custom Frame Object",
        description="Object whose axes define the alignment frame",
        type=bpy.types.Object,
    )
    align_use_origin: BoolProperty(name="Origin", default=True)
    align_use_pivot: BoolProperty(name="Pivot", default=True)
    align_use_centroid: BoolProperty(name="Centroid", default=True)
    align_use_face_centers: BoolProperty(name="Face Centers", default=True)
    align_use_corners: BoolProperty(name="Bounding Box Corners", default=True)

    __annotations__.update(_family_toggle_annotations())


def get_options(context) -> MagnetsOptions:
    """Return the scene MagnetsOptions property group."""
    return context.scene.magnets


def enabled_families(options) -> set[str]:
    """Set of currently enabled constraint family ids."""
    from .core.families import FAMILY_IDS

    return {fid for fid in FAMILY_IDS if getattr(options, f"enable_{fid}", True)}


def enabled_snap_axes(options) -> set[str]:
    """Set of enabled alignment axes (X/Y/Z)."""
    axes = set()
    if getattr(options, "snap_axis_x", True):
        axes.add("X")
    if getattr(options, "snap_axis_y", True):
        axes.add("Y")
    if getattr(options, "snap_axis_z", True):
        axes.add("Z")
    return axes


def active_frame(options) -> Frame:
    """Active Frame enum from options."""
    return Frame(options.alignment_frame)


def extract_options(options) -> dict:
    """Keyword args for feature extraction from options."""
    return {
        "use_origin": options.align_use_origin,
        "use_pivot": options.align_use_pivot,
        "use_centroid": options.align_use_centroid,
        "use_face_centers": options.align_use_face_centers,
        "use_corners": options.align_use_corners,
        "use_edges": True,
        "use_face_planes": True,
        "use_axes": True,
        "use_bbox": True,
        "use_circles": True,
    }


def custom_frame_object(context, options):
    """Return the custom reference object, if configured."""
    obj = options.custom_frame_object
    if obj is None or context.view_layer.objects.get(obj.name) is None:
        return None
    return obj


classes = (MagnetsOptions,)


def register():
    """Register Blender classes / handlers for this module."""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.magnets = PointerProperty(type=MagnetsOptions)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    del bpy.types.Scene.magnets
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
