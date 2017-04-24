# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from future import standard_library

from builtins import str
from copy import copy
from traceback import print_exc

from ..datatype.init import ProgressInfo, ProgressType
from .plugin import PluginThread

standard_library.install_aliases()


class AddonThread(PluginThread):
    """
    Thread for addons.
    """
    __slots__ = ['_progress', 'active', 'args', 'func', 'kwargs']

    def __init__(self, manager, func, args, kwargs):
        """
        Constructor.
        """
        PluginThread.__init__(self, manager)

        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.active = []
        self._progress = None

    def start(self):
        self.manager.add_thread(self)
        PluginThread.start(self)
        
    def get_active_files(self):
        return self.active

    def get_progress(self):
        """
        Progress of the thread.
        """
        if not self.active:
            return None
        active = self.active[0]
        return ProgressInfo(active.pluginname, active.name, active.get_status_name(), 0,
                            self._progress, 100, self.owner, ProgressType.Addon)

    def add_active(self, file):
        """
        Adds a file to active list and thus will be displayed on overview.
        """
        if file not in self.active:
            self.active.append(file)

    def finish_file(self, file):
        if file in self.active:
            self.active.remove(file)

        file.finish_if_done()

    def run(self):  # TODO: approach via func_code
        try:
            try:
                self.kwargs['thread'] = self
                self.func(*self.args, **self.kwargs)
            except TypeError as e:
                # dirty method to filter out exceptions
                if "unexpected keyword argument 'thread'" not in e.args[0]:
                    raise

                del self.kwargs['thread']
                self.func(*self.args, **self.kwargs)
        except Exception as e:
            if hasattr(self.func, "im_self"):
                addon = self.func.__self__
                addon.log_error(_("An Error occurred"), str(e))
                if self.manager.pyload.debug:
                    print_exc()
                    # self.debug_report(addon.__name__, plugin=addon)

        finally:
            local = copy(self.active)
            for x in local:
                self.funcinish_file(x)

            self.funcinished()
