#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from functools import cmp_to_key

import psutil
from core.utils import *
from core.webengine import BrowserBuffer
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor


class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.panel_background_color = QColor(self.theme_background_color).darker(110).name()

        self.load_index_html(__file__)

    def init_app(self):
        self.buffer_widget.eval_js_function('''initProcesslistColor''', self.theme_background_color, self.theme_foreground_color)
        self.buffer_widget.eval_js_function('''initPanelColor''', self.panel_background_color, self.theme_foreground_color)

        self.update_process_info()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_process_info)
        self.timer.start(1000)

    @interactive
    def update_theme(self):
        super().update_theme()
        self.panel_background_color = QColor(self.theme_background_color).darker(110).name()
        self.buffer_widget.eval_js_function('''initProcesslistColor''', self.theme_background_color, self.theme_foreground_color)
        self.buffer_widget.eval_js_function('''initPanelColor''', self.panel_background_color, self.theme_foreground_color)

    @PostGui()
    def update_process_info(self):
        infos = []

        for proc in psutil.process_iter(['cpu_percent', 'memory_info', 'pid', 'name', 'username', 'cmdline']):
            info = proc.info
            memory_info = info["memory_info"]
            if memory_info is None:
                continue
            memory_number = memory_info.rss
            info["memory_number"] = memory_number
            info["memory"] = self.format_memory(memory_number)
            info["cmdline"] = " ".join(info["cmdline"]) if info["cmdline"] is not None else ""
            infos.append(proc.info)

        infos.sort(key=cmp_to_key(self.process_compare), reverse=True)

        self.buffer_widget.eval_js_function('''updateProcessInfo''', infos)

        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        cpu_percents = psutil.cpu_percent(percpu=True)
        cpu_count = psutil.cpu_count()
        panel_info = {
            "cpu": {
                "count": cpu_count,
                "percent": cpu_percent,
                "percents": cpu_percents
            },
            "memory": {
                "total": self.format_memory(mem.total),
                "used": self.format_memory(mem.used),
                "percent": mem.percent
            }
        }

        self.buffer_widget.eval_js_function('''updatePanelInfo''', panel_info)

    def process_compare(self, a, b):
        if a["cpu_percent"] < b["cpu_percent"]:
            return -1
        elif a["cpu_percent"] > b["cpu_percent"]:
            return 1
        else:
            if a["memory_number"] < b["memory_number"]:
                return -1
            elif a["memory_number"] > b["memory_number"]:
                return 1
            else:
                return 0

    def format_memory(self, memory):
        if memory < 1024:
            return str(memory) + "B"
        elif memory > 1024 * 1024 * 1024:
            return "{:.1f}".format(memory / 1024 / 1024 / 1024) + "GB"
        elif memory > 1024 * 1024:
            return "{:.1f}".format(memory / 1024 / 1024) + "MB"
        else:
            return "{:.1f}".format(memory / 1024) + "KB"

    def destroy_buffer(self):
        self.timer.stop()

        super().destroy_buffer()
