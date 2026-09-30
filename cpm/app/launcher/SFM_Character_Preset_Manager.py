# -*- coding: ascii -*-
# SFM Character Preset Manager -- Scripts-menu launcher (CPM R15).
#
# RUN TYPE: MAINMENU. Deployed as
# <SFM game>/usermod/scripts/sfm/mainmenu/ChadChan3D/SFM_Character_Preset_Manager.py.
#
# SFM runs every Scripts-menu script in one shared, process-lifetime namespace.
# This launcher therefore defines no application code there. It loads the CPM
# implementation, deployed outside the entire scripts/sfm discovery tree at
# <SFM game>/usermod/scripts/ChadChan3D_CPM/SFM_Character_Preset_Manager.py,
# exactly once per SFM process into the private module chadchan3d_cpm_app, and
# asks that module to open or reuse its window.
#
# Module lifecycle: ABSENT -> LOADING -> READY. READY is permanent until SFM
# exits: the module is never reloaded, replaced or deleted. If the installed
# implementation bytes change, launches are refused until SFM is restarted.
#
# The launcher keeps its imports and working state local, adds nothing to
# sys.path, connects no Python callback to Qt, and deletes its own function
# before returning. Its one retained object is the reusable launch notice.
#
# (Comments, not a docstring: a module docstring would rebind __doc__ in
# SFM's shared Scripts-menu namespace.)


def _chadchan3d_cpm_launcher_v1():
    import hashlib
    import os
    import sys
    import traceback
    import types

    module_key = "chadchan3d_cpm_app"
    loader_marker = "cpm-private-loader-v1"
    notice_attr = "_chadchan3d_cpm_launch_notice_v1"
    notice_name = "chadchan3d_cpm_launch_notice_v1"

    copy_restart = (
        "Character Preset Manager could not start in this SFM session. "
        "Restart SFM to use it."
    )
    copy_changed = (
        "Character Preset Manager was updated on disk after it started in this "
        "SFM session. Restart SFM to use the updated version."
    )
    copy_unreadable = (
        "Character Preset Manager is not installed correctly: its application "
        "file could not be read. Reinstall it, then open it again."
    )
    copy_load_failed = (
        "Character Preset Manager could not load. Check the installation, "
        "then open it again."
    )
    copy_start_failed = (
        "Character Preset Manager could not open. Restart SFM to use it again."
    )

    def console(sys_module, text):
        try:
            sys_module.stdout.write("[ChadChan3D CPM launcher] %s\n" % (text,))
        except Exception:
            pass

    def read_bytes(path):
        handle = None
        try:
            handle = open(path, "rb")
            return handle.read()
        except Exception:
            return None
        finally:
            if handle is not None:
                try:
                    handle.close()
                except Exception:
                    pass

    def notice(console_fn, sys_module, attr, object_name, text):
        """Show the one retained, parentless, non-modal launch notice.

        No Python callback, timer, provider or window reference is attached,
        no nested event loop is entered, and nothing is shown or queued while
        any modal dialog is active. A foreign or malformed notice slot is left
        untouched."""
        try:
            from PySide import QtCore
            from PySide import QtGui
        except Exception as exc:
            console_fn(sys_module, "notice unavailable (%r): %s" % (exc, text))
            return "no-qt"
        try:
            app = QtGui.QApplication.instance()
            if app is None:
                console_fn(sys_module, "notice unavailable (no QApplication): %s" % (text,))
                return "no-qapplication"
            try:
                modal = app.activeModalWidget()
            except Exception:
                console_fn(sys_module, "notice suppressed (modal state unknown): %s" % (text,))
                return "suppressed-modal-unknown"
            if modal is not None:
                console_fn(sys_module, "notice suppressed (a modal dialog is active): %s" % (text,))
                return "suppressed-modal"
            box = getattr(app, attr, None)
            if box is None:
                box = QtGui.QMessageBox()
                box.setObjectName(object_name)
                box.setWindowTitle("SFM Character Preset Manager")
                box.setIcon(QtGui.QMessageBox.Information)
                box.setStandardButtons(QtGui.QMessageBox.Ok)
                box.setModal(False)
                box.setWindowModality(QtCore.Qt.NonModal)
                box.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
                box.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
                setattr(app, attr, box)
            else:
                try:
                    from PySide import shiboken
                    valid = bool(shiboken.isValid(box))
                except Exception:
                    valid = False
                if not (
                    valid
                    and isinstance(box, QtGui.QMessageBox)
                    and box.objectName() == object_name
                ):
                    console_fn(sys_module, "notice slot foreign or malformed; left untouched: %s" % (text,))
                    return "slot-foreign"
            box.setText(text)
            box.show()
            box.raise_()
            return "shown"
        except Exception as exc:
            console_fn(sys_module, "notice failed (%r): %s" % (exc, text))
            return "failed"

    def classify(entry, types_module, key, marker, impl_path):
        """('ready', sha) | ('loading', None) | (refusal, detail)."""
        try:
            if not isinstance(entry, types_module.ModuleType):
                return ("foreign", "type=%s" % (type(entry).__name__,))
            namespace = entry.__dict__
            if namespace.get("__name__") != key:
                return ("foreign", "name=%r" % (namespace.get("__name__"),))
            if namespace.get("__chadchan3d_cpm_loader__") != marker:
                return ("incompatible", "loader=%r" % (namespace.get("__chadchan3d_cpm_loader__"),))
            if namespace.get("__file__") != impl_path:
                return ("wrong-origin", "file=%r" % (namespace.get("__file__"),))
            build = namespace.get("__chadchan3d_cpm_build_sha256__")
            if not (isinstance(build, str) and len(build) == 64):
                return ("malformed", "build=%r" % (build,))
            state = namespace.get("__chadchan3d_cpm_state__")
            if state == "loading":
                return ("loading", None)
            if state != "ready":
                return ("malformed", "state=%r" % (state,))
            if not (callable(namespace.get("StartProdTool"))
                    and callable(namespace.get("prod_r15_launcher_refusal"))):
                return ("malformed", "entry points missing")
            return ("ready", build)
        except Exception as exc:
            return ("malformed", "%r" % (exc,))

    impl_path = os.path.normpath(os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(sys.executable)),
        "usermod", "scripts", "ChadChan3D_CPM", "SFM_Character_Preset_Manager.py",
    )))

    if module_key in sys.modules:
        status, detail = classify(sys.modules.get(module_key), types, module_key, loader_marker, impl_path)
        if status != "ready":
            # LOADING, foreign, incompatible or malformed: never touched.
            console(sys, "outcome=refused code=module-%s detail=%s" % (status, detail))
            notice(console, sys, notice_attr, notice_name, copy_restart)
            return
        module = sys.modules[module_key]
        source_bytes = read_bytes(impl_path)
        if source_bytes is None:
            code, text = "installed-unreadable", copy_unreadable
        elif hashlib.sha256(source_bytes).hexdigest() != detail:
            code, text = "installed-build-changed", copy_changed
        else:
            code, text = None, None
        source_bytes = None
        if code is not None:
            # The loaded module and any open window keep running; no reload.
            try:
                module.prod_r15_launcher_refusal(code, impl_path)
            except Exception:
                pass
            console(sys, "outcome=refused code=%s" % (code,))
            notice(console, sys, notice_attr, notice_name, text)
            return
    else:
        source_bytes = read_bytes(impl_path)
        if source_bytes is None:
            console(sys, "outcome=refused code=installed-unreadable path=%s" % (impl_path,))
            notice(console, sys, notice_attr, notice_name, copy_unreadable)
            return
        module = types.ModuleType(str(module_key))
        module.__file__ = impl_path
        module.__chadchan3d_cpm_loader__ = loader_marker
        module.__chadchan3d_cpm_build_sha256__ = hashlib.sha256(source_bytes).hexdigest()
        module.__chadchan3d_cpm_state__ = "loading"
        sys.modules[module_key] = module
        try:
            # The same buffer that was hashed; no inherited future flags.
            # eval() runs the exec-mode code object with the module dict as
            # both globals and locals (portable across Python 2.7 and 3).
            code_object = compile(source_bytes, impl_path, "exec", 0, True)
            source_bytes = None
            eval(code_object, module.__dict__, module.__dict__)
            code_object = None
            if sys.modules.get(module_key) is not module:
                raise RuntimeError("private module registration changed during loading")
            if not (module.__dict__.get("__chadchan3d_cpm_state__") == "loading"
                    and callable(module.__dict__.get("StartProdTool"))
                    and callable(module.__dict__.get("prod_r15_launcher_refusal"))):
                raise RuntimeError("private module initialization is incomplete")
            module.__chadchan3d_cpm_state__ = "ready"
        except BaseException as exc:
            # Pre-READY failure: remove only the entry this attempt created,
            # and only while it is still that exact module.
            removed = False
            try:
                if sys.modules.get(module_key) is module:
                    del sys.modules[module_key]
                    removed = True
            except Exception:
                pass
            diagnostics = traceback.format_exc()
            module = None
            source_bytes = None
            code_object = None
            if not isinstance(exc, Exception):
                raise
            exc = None
            try:
                sys.exc_clear()
            except AttributeError:
                pass
            console(sys, "outcome=failed code=load-failed entry_removed=%r\n%s" % (removed, diagnostics))
            notice(console, sys, notice_attr, notice_name, copy_load_failed)
            return

    try:
        result = module.StartProdTool()
    except BaseException as exc:
        diagnostics = traceback.format_exc()
        if not isinstance(exc, Exception):
            raise
        exc = None
        try:
            sys.exc_clear()
        except AttributeError:
            pass
        result = {"outcome": "failed", "code": "startup-raised", "notice": copy_start_failed}
        console(sys, "startup raised\n%s" % (diagnostics,))
    module = None
    if not isinstance(result, dict):
        result = {"outcome": "failed", "code": "startup-result-malformed", "notice": copy_start_failed}
    console(sys, "outcome=%s code=%s" % (result.get("outcome"), result.get("code")))
    if result.get("notice"):
        notice(console, sys, notice_attr, notice_name, result.get("notice"))


try:
    _chadchan3d_cpm_launcher_v1()
finally:
    try:
        del _chadchan3d_cpm_launcher_v1
    except NameError:
        pass
