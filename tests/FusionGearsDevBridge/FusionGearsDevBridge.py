"""Development bridge: runs request.py dropped into tests/bridge inside Fusion.

Only for local testing of FusionGears. Stop it in Scripts and Add-Ins when done.
The request is executed with `app` and `adsk` available; stdout and errors go to
response.txt next to it. bridge_log.txt records start-up and failures.
"""
import adsk.core
import contextlib
import io
import os
import threading
import traceback

BRIDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bridge')
EVENT_ID = 'FusionGearsDevBridgeEvent'

_app = None
_handlers = []
_stop = threading.Event()
_busy = threading.Event()


def _log(msg):
    try:
        os.makedirs(BRIDGE, exist_ok=True)
        with open(os.path.join(BRIDGE, 'bridge_log.txt'), 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass


_log('module imported')


class _Handler(adsk.core.CustomEventHandler):
    def notify(self, args):
        req = os.path.join(BRIDGE, 'request.py')
        out = io.StringIO()
        try:
            with open(req, encoding='utf-8') as f:
                code = f.read()
            os.remove(req)
            with contextlib.redirect_stdout(out):
                exec(compile(code, req, 'exec'), {'adsk': adsk, 'app': _app, '__name__': '__bridge__'})
        except Exception:
            out.write('\nERROR\n' + traceback.format_exc())
        finally:
            with open(os.path.join(BRIDGE, 'response.txt'), 'w', encoding='utf-8') as f:
                f.write(out.getvalue() + '\n<<END>>\n')
            _busy.clear()


def _poll():
    while not _stop.wait(1.0):
        try:
            if not _busy.is_set() and os.path.exists(os.path.join(BRIDGE, 'request.py')):
                _busy.set()
                _app.fireCustomEvent(EVENT_ID, '')
        except Exception:
            _log('poll failed\n' + traceback.format_exc())
            _busy.clear()


def _start():
    global _app
    _app = adsk.core.Application.get()
    os.makedirs(BRIDGE, exist_ok=True)
    try:
        _app.unregisterCustomEvent(EVENT_ID)
    except Exception:
        pass
    ev = _app.registerCustomEvent(EVENT_ID)
    h = _Handler()
    ev.add(h)
    _handlers.append(h)
    _stop.clear()
    threading.Thread(target=_poll, daemon=True).start()
    _log('started')


def run(context):
    try:
        _start()
    except Exception:
        _log('run failed\n' + traceback.format_exc())
        adsk.core.Application.get().userInterface.messageBox(
            'FusionGearsDevBridge: ошибка запуска\n' + traceback.format_exc())


def stop(context):
    _stop.set()
    try:
        _app.unregisterCustomEvent(EVENT_ID)
    except Exception:
        pass
    _handlers.clear()
    _log('stopped')
