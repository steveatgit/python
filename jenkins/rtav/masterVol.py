import ctypes
import comtypes
import sounddevice

from ctypes import (
    POINTER as _POINTER,
    HRESULT as _HRESULT,
    c_float as _c_float,
)

from ctypes.wintypes import (
    BOOL as _BOOL,
    DWORD as _DWORD,
)

from comtypes import (
    GUID as _GUID,
    COMMETHOD as _COMMETHOD,
    STDMETHOD as _STDMETHOD,
)

MMDeviceApiLib = _GUID(
    '{2FDAAFA3-7523-4F66-9957-9D5E7FE698F6}')

IID_IAudioEndpointVolume = _GUID(
    '{5CDF2C82-841E-4546-9722-0CF74078229A}')
IID_IMMDevice = _GUID(
    '{D666063F-1587-4E43-81F1-B948E807363F}')
IID_IMMDeviceCollection = _GUID(
    '{0BD7A1BE-7A1A-44DB-8397-CC5392387B5E}')
IID_IMMDeviceEnumerator = _GUID(
    '{A95664D2-9614-4F35-A746-DE8DB63617E6}')

CLSID_MMDeviceEnumerator = _GUID(
    '{BCDE0395-E52F-467C-8E3D-C4579291692E}')

    
class IAudioEndpointVolume(comtypes.IUnknown):
    _iid_ = IID_IAudioEndpointVolume
    _methods_ = (
        _STDMETHOD(_HRESULT,
            'RegisterControlChangeNotify', []),
        _STDMETHOD(_HRESULT,
            'UnregisterControlChangeNotify', []),
        _STDMETHOD(_HRESULT,
            'GetChannelCount', []),
        _COMMETHOD([], _HRESULT,
            'SetMasterVolumeLevel',
            (['in'], _c_float, 'fLevelDB'),
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'SetMasterVolumeLevelScalar',
            (['in'], _c_float, 'fLevelDB'),
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'GetMasterVolumeLevel',
            (['out','retval'], _POINTER(ctypes.c_float), 'pfLevelDB')),
        _COMMETHOD([], _HRESULT,
            'GetMasterVolumeLevelScalar',
            (['out','retval'], _POINTER(_c_float), 'pfLevelDB')),
        _COMMETHOD([], _HRESULT,
            'SetChannelVolumeLevel',
            (['in'], _DWORD, 'nChannel'),
            (['in'], _c_float, 'fLevelDB'),
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'SetChannelVolumeLevelScalar',
            (['in'], _DWORD, 'nChannel'),
            (['in'], _c_float, 'fLevelDB'),
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'GetChannelVolumeLevel',
            (['in'], _DWORD, 'nChannel'),
            (['out','retval'], _POINTER(_c_float), 'pfLevelDB')),
        _COMMETHOD([], _HRESULT,
            'GetChannelVolumeLevelScalar',
            (['in'], _DWORD, 'nChannel'),
            (['out','retval'], _POINTER(_c_float), 'pfLevelDB')),
        _COMMETHOD([], _HRESULT,
            'SetMute',
            (['in'], _BOOL, 'bMute'),
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'GetMute',
            (['out','retval'], _POINTER(_BOOL), 'pbMute')),
        _COMMETHOD([], _HRESULT,
            'GetVolumeStepInfo',
            (['out','retval'], _POINTER(_c_float), 'pnStep'),
            (['out','retval'], _POINTER(_c_float), 'pnStepCount')),
        _COMMETHOD([], _HRESULT,
            'VolumeStepUp',
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'VolumeStepDown',
            (['in'], _POINTER(_GUID), 'pguidEventContext')),
        _COMMETHOD([], _HRESULT,
            'QueryHardwareSupport',
            (['out','retval'], _POINTER(_DWORD), 'pdwHardwareSupportMask')),
        _COMMETHOD([], _HRESULT,
            'GetVolumeRange',
            (['out','retval'], _POINTER(_c_float), 'pfMin'),
            (['out','retval'], _POINTER(_c_float), 'pfMax'),
            (['out','retval'], _POINTER(_c_float), 'pfIncr')))

            
class IMMDevice(comtypes.IUnknown):
    _iid_ = IID_IMMDevice
    _methods_ = (
        _COMMETHOD([], _HRESULT,
            'Activate',
            (['in'], _POINTER(_GUID), 'iid'),
            (['in'], _DWORD, 'dwClsCtx'),
            (['in'], _POINTER(_DWORD), 'pActivationParams'),
            (['out','retval'],
             _POINTER(_POINTER(IAudioEndpointVolume)), 'ppInterface')),
        _STDMETHOD(_HRESULT,
            'OpenPropertyStore', []),
        _STDMETHOD(_HRESULT,
            'GetId', []),
        _STDMETHOD(_HRESULT,
            'GetState', []))

            
class IMMDeviceCollection(comtypes.IUnknown):
    _iid_ = IID_IMMDeviceCollection

    
class IMMDeviceEnumerator(comtypes.IUnknown):
    _iid_ = IID_IMMDeviceEnumerator
    _methods_ = (
        _COMMETHOD([], _HRESULT,
            'EnumAudioEndpoints',
            (['in'], _DWORD, 'dataFlow'),
            (['in'], _DWORD, 'dwStateMask'),
            (['out','retval'],
             _POINTER(_POINTER(IMMDeviceCollection)), 'ppDevices')),
        _COMMETHOD([], _HRESULT,
            'GetDefaultAudioEndpoint',
            (['in'], _DWORD, 'dataFlow'),
            (['in'], _DWORD, 'role'),
            (['out','retval'],
             _POINTER(_POINTER(IMMDevice)), 'ppDevices')))


def _get_default_endpoint_volume():
    enumerator = comtypes.CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    comtypes.CLSCTX_INPROC_SERVER)
    endpoint = enumerator.GetDefaultAudioEndpoint(0, 1)
    return endpoint.Activate(IID_IAudioEndpointVolume,
                             comtypes.CLSCTX_INPROC_SERVER,
                             None)

                             
def get_volume_range():
    comtypes.CoInitialize()
    try:
        endpoint_volume = _get_default_endpoint_volume()
        return endpoint_volume.GetVolumeRange()
    finally:
        comtypes.CoUninitialize()

        
def get_master_volume_level():
    comtypes.CoInitialize()
    try:
        endpoint_volume = _get_default_endpoint_volume()
        return endpoint_volume.GetMasterVolumeLevel()
    finally:
        comtypes.CoUninitialize()

        
def set_master_volume_level(level_db):
    comtypes.CoInitialize()
    try:
        endpoint_volume = _get_default_endpoint_volume()
        endpoint_volume.SetMasterVolumeLevel(level_db, None)
    finally:
        comtypes.CoUninitialize()


def virtualAudioEnable():
    devices = sounddevice.query_devices()
    for device in devices:
        if device['name'] == 'Speakers (VMware Virtual Audio ':
            exit(1)
    exit(0)

   
if __name__ == '__main__':
    virtualAudioEnable()
