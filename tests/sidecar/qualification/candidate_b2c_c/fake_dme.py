# -*- coding: utf-8 -*-
"""B2C-C execution-layer: minimal, contract-driven fake DME/control-group
object model. Every method here exists ONLY because a specific frozen
production call site (cataloged in `production_execution_layer.py`'s
module docstring) requires it -- no speculative SFM emulation.

Interception design (governing prompt Section 3: prefer mutation-
boundary interception over full-engine emulation): every mutation-
capable NATIVE METHOD on `FakeDmeControlGroup` (SetVisible,
SetSelectable, SetSnappable, SetGroupColor, CreateControlGroup,
AddChild, RemoveChild, AddControl, SetName) records ONE canonical
intent to a shared, ordered `MutationLog` AND performs the state change
-- this is the single choke point every real mutation flows through,
whether reached via one of the 7 extracted Python wrapper functions
(`set_visible`, `add_control_to_group`, ...) or via a RAW native call
with no wrapper at all (`parent.RemoveChild`/`parent.AddChild` inside
`production_reorder_children_by_master`). The extracted wrapper
functions themselves are never modified or wrapped -- only the fake
native objects they call are instrumented.

Identity model: every element gets a permanent integer handle at
construction (`GetHandle()`), never reassigned by rename/reparent/
recolor -- matching the frozen code's own `handle(obj) != old_handle`
invariant checks (e.g. `rename_group`, `production_reorder_children_
by_master`).

`AddControl` enforces EXCLUSIVE membership (removes the control from
its current group, if any, before adding it to the new one) via a
shared `MutationLog.control_owner` registry keyed by handle -- this is
a documented assumption, not an invented one: `production_generic_
composer`'s own postcondition checks require `after["duplicate_
memberships"]` to be empty, and no code path anywhere calls a
"RemoveControl"-equivalent before `AddControl`, so exclusivity must be
a real native-side guarantee of `AddControl` itself.

`GetAttribute(name)` is implemented uniformly as `getattr(self, name,
None)` -- every DME-visible attribute name used anywhere in the
extraction (`children`, `controls`, `visible`, `selectable`,
`snappable`, `groupColor`, `scene`, `rootControlGroup`, `animationSet`,
`animSetList`, `elementList`, `hiddenGroups`) is a REAL Python instance
attribute, so `arr()`/`attr()`/`scalar()` (from `production_plan_
layer.py`, reused unmodified) resolve correctly through BOTH the
`GetAttribute` path and the `getattr` fallback path at once, guaranteed
consistent because they read the exact same storage.
"""


class MutationLog(object):
    def __init__(self):
        self.entries = []
        self._sequence = 0
        self.control_owner = {}  # control_handle -> owning FakeDmeControlGroup

    def record(self, operation, target=None, control=None, source_path=None,
               destination_path=None, sibling_index=None, metadata=None, reason=None):
        self._sequence += 1
        self.entries.append({
            "sequence": self._sequence,
            "operation": operation,
            "target": target,
            "control": control,
            "source_path": source_path,
            "destination_path": destination_path,
            "sibling_index": sibling_index,
            "metadata": metadata,
            "reason": reason,
        })


class _HandleAllocator(object):
    def __init__(self):
        self._next = 1

    def allocate(self):
        h = self._next
        self._next += 1
        return h


class FakeColor(object):
    """Stand-in for `vs.Color(r, g, b, a)` -- the ONE `vs.` reference in
    the entire execution layer (inside `set_group_color`). Exposes the
    exact attribute surface `group_color_rgba`'s `_component_value`
    helper reads (`.r`/`.g`/`.b`/`.a`, plain ints, never callables)."""

    def __init__(self, r, g, b, a):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        self.a = int(a)

    def __repr__(self):
        return "FakeColor(%d,%d,%d,%d)" % (self.r, self.g, self.b, self.a)


class FakeVsModule(object):
    """Installed as `ns["vs"] = FakeVsModule()` before `set_group_color`
    is ever called -- the extracted source does `vs.Color(r, g, b, a)`
    unmodified."""
    Color = staticmethod(lambda r, g, b, a: FakeColor(r, g, b, a))


class FakeDmeControl(object):
    def __init__(self, handles, name, control_type=u"DmeTransformControl"):
        self._handle = handles.allocate()
        self.name = name
        self._type_string = control_type

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.name

    def SetName(self, value):
        self.name = value

    def GetTypeString(self):
        return self._type_string

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)

    def FirstAttribute(self):
        return None

    def __repr__(self):
        return "FakeDmeControl(%r, handle=%d)" % (self.name, self._handle)


class FakeDmeControlGroup(object):
    def __init__(self, handles, mlog, name):
        self._handle = handles.allocate()
        self._handles = handles
        self._mlog = mlog
        self.name = name
        self._type_string = u"DmeControlGroup"
        self.children = []
        self.controls = []
        self.visible = True
        self.selectable = True
        self.snappable = True
        self.groupColor = FakeColor(255, 255, 255, 255)
        self._parent = None

    # --- identity / generic element protocol -------------------------
    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.name

    def SetName(self, value):
        self.name = value
        self._mlog.record("rename_group", target=self._handle, destination_path=value)

    def GetTypeString(self):
        return self._type_string

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)

    def FirstAttribute(self):
        return None  # groups are never graph-walked via reachable() in this scope

    # --- visibility / selectability / snappability / color ------------
    def IsVisible(self):
        return self.visible

    def SetVisible(self, value):
        self.visible = bool(value)
        self._mlog.record("set_visible", target=self._handle, metadata={"visible": bool(value)})

    def IsSelectable(self):
        return self.selectable

    def SetSelectable(self, value):
        self.selectable = bool(value)
        self._mlog.record("set_selectable", target=self._handle, metadata={"selectable": bool(value)})

    def IsSnappable(self):
        return self.snappable

    def SetSnappable(self, value):
        self.snappable = bool(value)
        self._mlog.record("set_snappable", target=self._handle, metadata={"snappable": bool(value)})

    def GroupColor(self):
        return self.groupColor

    def SetGroupColor(self, color, unused_flag):
        self.groupColor = color
        self._mlog.record("set_group_color", target=self._handle,
                           metadata={"rgba": [color.r, color.g, color.b, color.a]})

    # --- structural mutation -------------------------------------------
    def CreateControlGroup(self, technical_name):
        group = FakeDmeControlGroup(self._handles, self._mlog, technical_name)
        # Matches the real contract create_independent_group relies on:
        # `root.CreateControlGroup(name)` attaches the new group as a
        # child of ROOT directly -- the caller only separately calls
        # `parent.AddChild(group)` when parent is NOT root. `AddChild`
        # (below) is EXCLUSIVE-reparenting (like `AddControl` is for
        # controls), so calling it afterward correctly MOVES the group
        # from root to the real target parent rather than duplicating
        # it under both -- this was a real bug found and fixed during
        # this qualification round (a naive non-reparenting `AddChild`
        # produced a group duplicated under both root and its intended
        # parent, later caught by `production_generic_composer`'s own
        # `duplicate_invariant`/`destination` postcondition checks --
        # see the B2C-C execution-layer report's "bugs found and fixed
        # in the fake model itself" section).
        self.children.append(group)
        group._parent = self
        self._mlog.record("create_control_group", target=group._handle,
                           destination_path=technical_name, reason="created under root")
        return group

    def AddChild(self, group):
        if group._parent is not None and group._parent is not self:
            group._parent.children.remove(group)
        if group not in self.children:
            self.children.append(group)
        group._parent = self
        self._mlog.record("add_child", target=group._handle, destination_path=self.name)

    def RemoveChild(self, group):
        self.children.remove(group)
        if group._parent is self:
            group._parent = None
        self._mlog.record("remove_child", target=group._handle, source_path=self.name)

    def AddControl(self, control):
        control_handle = control.GetHandle()
        owner = self._mlog.control_owner.get(control_handle)
        source_path = owner.name if owner is not None else None
        if owner is not None and owner is not self:
            owner.controls.remove(control)
        if control not in self.controls:
            self.controls.append(control)
        self._mlog.control_owner[control_handle] = self
        self._mlog.record("add_control_to_group", control=control.GetName(),
                           source_path=source_path, destination_path=self.name)

    def __repr__(self):
        return "FakeDmeControlGroup(%r, handle=%d)" % (self.name, self._handle)


class FakeDmeRigAnimSetElements(object):
    """`arr(rig, "animSetList")` rows -- `typ(rec) == 'DmeRigAnimSetElements'`,
    `scalar(rec, 'animationSet')` returns the linked aset. This is the
    REGISTRY object `discover_rig_context` calls `registry` -- it (not
    the rig itself) is where `arr(registry, "elementList")` (owned
    control elements) and `arr(registry, "hiddenGroups")` are read from,
    confirmed by direct reading of `discover_rig_context`'s real source."""

    def __init__(self, handles, animation_set, owned_controls, hidden_groups=None):
        self._handle = handles.allocate()
        self._type_string = u"DmeRigAnimSetElements"
        self.animationSet = animation_set
        self.elementList = list(owned_controls)
        self.hiddenGroups = list(hidden_groups or [])

    def GetHandle(self):
        return self._handle

    def GetTypeString(self):
        return self._type_string

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)


class FakeDmeRig(object):
    def __init__(self, handles, name, animation_set, owned_controls, hidden_groups=None):
        self._handle = handles.allocate()
        self.name = name
        self._type_string = u"DmeRig"
        self._animation_set = animation_set
        self.animSetList = [FakeDmeRigAnimSetElements(handles, animation_set, owned_controls, hidden_groups)]

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.name

    def GetTypeString(self):
        return self._type_string

    def HasAnimationSet(self, aset):
        return aset is self._animation_set

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)


class FakeDmeAnimationSet(object):
    def __init__(self, handles, name, root_control_group, controls):
        self._handle = handles.allocate()
        self.name = name
        self._type_string = u"DmeAnimationSet"
        self.rootControlGroup = root_control_group
        self.controls = list(controls)

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.name

    def GetTypeString(self):
        return self._type_string

    def GetRootControlGroup(self):
        return self.rootControlGroup

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)


class FakeDmeScene(object):
    """`reachable(scene)` walks this via `element_ref_pairs`/
    `FirstAttribute`/`NextAttribute` looking for `DmeRig`-typed
    elements. We give `FakeDmeScene` a REAL, minimal element/element-
    array attribute-iteration protocol (the only object in this model
    that needs one, since it is the only `reachable()` entry point)."""

    def __init__(self, handles, rigs):
        self._handle = handles.allocate()
        self._type_string = u"DmeScene"
        self.rigs = list(rigs)

    def GetHandle(self):
        return self._handle

    def GetTypeString(self):
        return self._type_string

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)

    def FirstAttribute(self):
        return _SceneRigsAttribute(self.rigs) if self.rigs else None

    def NextAttribute_after_rigs(self):
        return None


class _SceneRigsAttribute(object):
    """The ONE synthetic "element_array" attribute `FakeDmeScene`
    exposes via `FirstAttribute()`, named "rigs", typed "element_array"
    -- exactly what `element_ref_pairs` expects to find `DmeRig`
    elements through."""

    def __init__(self, rigs):
        self._rigs = rigs

    def GetName(self):
        return u"rigs"

    def GetTypeString(self):
        return u"element_array"

    def Count(self):
        return len(self._rigs)

    def __getitem__(self, i):
        return self._rigs[i]

    def NextAttribute(self):
        return None


class FakeShot(object):
    def __init__(self, handles, name, scene):
        self._handle = handles.allocate()
        self.name = name
        self._type_string = u"DmeShot"
        self.scene = scene

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.name

    def GetTypeString(self):
        return self._type_string

    def HasAttribute(self, attr_name):
        return hasattr(self, attr_name)

    def GetAttribute(self, attr_name):
        return getattr(self, attr_name, None)


def build_world(group_spec, control_specs, rig_status="SUPPORTED_ACTIVE_RIG",
                 hidden_groups=None, shot_name=u"shot1", aset_name=u"aset1"):
    """Builds one complete fake world (shot -> scene -> rig(s)/registry
    -> aset -> root control-group tree with nested groups/controls) from
    the SAME declarative `group_spec`/`control_specs` shape `fixture_
    builder.build_snapshot` already uses for the decision layer -- so
    the SAME 10 scenario definitions can drive both layers without
    re-authoring fixtures. Returns (shot, aset, root, mlog, handles,
    groups_by_path, controls_by_name)."""
    handles = _HandleAllocator()
    mlog = MutationLog()

    root = FakeDmeControlGroup(handles, mlog, u"<ROOT>")
    groups_by_path = {u"<ROOT>": root}

    def ensure_group(path):
        if path in groups_by_path:
            return groups_by_path[path]
        if u"/" in path:
            parent_path, leaf = path.rsplit(u"/", 1)
        else:
            parent_path, leaf = u"<ROOT>", path
        parent = ensure_group(parent_path)
        group = FakeDmeControlGroup(handles, mlog, leaf)
        parent.children.append(group)
        group._parent = parent
        groups_by_path[path] = group
        return group

    for path in sorted(group_spec.keys(), key=lambda p: (p.count(u"/"), p)):
        if path == u"<ROOT>":
            root.visible = bool(group_spec[path]["visible"])
            continue
        g = ensure_group(path)
        g.visible = bool(group_spec[path]["visible"])

    controls_by_name = {}
    owned_controls = []
    for spec in control_specs:
        c = FakeDmeControl(handles, spec["name"], spec.get("type", u"DmeTransformControl"))
        controls_by_name[spec["name"]] = c
        group = groups_by_path[spec["path"]]
        group.controls.append(c)
        mlog.control_owner[c.GetHandle()] = group
        if spec.get("owned", False):
            owned_controls.append(c)

    aset = FakeDmeAnimationSet(handles, aset_name, root, list(controls_by_name.values()))

    rigs = []
    if rig_status == "SUPPORTED_ACTIVE_RIG":
        rig = FakeDmeRig(handles, u"rig1", aset, owned_controls, hidden_groups=hidden_groups)
        rigs.append(rig)
    scene = FakeDmeScene(handles, rigs)
    shot = FakeShot(handles, shot_name, scene)

    return shot, aset, root, mlog, handles, groups_by_path, controls_by_name
