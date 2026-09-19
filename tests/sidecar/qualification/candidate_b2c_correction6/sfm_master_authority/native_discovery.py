# -*- coding: utf-8 -*-
"""Real ifm.dll-loaded-module discovery -- reproduces, verbatim in
technique, production `Rebuild_Control_Groups_Normalizer.get_loaded_ifm_module()`
/ `get_loaded_module_path()` (GetModuleHandleW + GetModuleFileNameW).

Used ONLY by the SFM runtime identity probe (this module requires ifm.dll
to already be loaded in the current process, i.e. requires actually
running inside SFM). Offline tests never call this module -- they inject
a fixture ifm.dll path directly into `resolver.resolve_effective_master()`
instead.
"""
import ctypes
import os


class NativeModuleNotLoaded(Exception):
    pass


def get_loaded_ifm_dll_path():
    kernel32 = ctypes.windll.kernel32

    get_module_handle = kernel32.GetModuleHandleW
    get_module_handle.argtypes = [ctypes.c_wchar_p]
    get_module_handle.restype = ctypes.c_void_p

    base = get_module_handle(u"ifm.dll")
    if not base:
        raise NativeModuleNotLoaded("ifm.dll is not loaded in this process.")

    get_module_filename = kernel32.GetModuleFileNameW
    get_module_filename.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    get_module_filename.restype = ctypes.c_uint

    buffer_size = 32768
    buf = ctypes.create_unicode_buffer(buffer_size)
    count = get_module_filename(ctypes.c_void_p(base), buf, buffer_size)
    if count == 0:
        raise NativeModuleNotLoaded("GetModuleFileNameW failed for ifm.dll.")
    if count >= buffer_size:
        raise NativeModuleNotLoaded("loaded ifm.dll path exceeded buffer.")
    return os.path.abspath(buf.value)
