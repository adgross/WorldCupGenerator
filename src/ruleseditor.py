# -*- coding: utf-8 -*-

from collections import Counter
import wx
from data import GetRegions


class RulesEditor(wx.Dialog):
    def __init__(self, parent, rules, countries):
        wx.Dialog.__init__(self, parent,
                           id=wx.ID_ANY,
                           title=wx.EmptyString,
                           pos=wx.DefaultPosition,
                           size=wx.Size(500,360),
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.rules = rules
        self.gui_init()
        self.countriesPerRegion = Counter([c.region.id for c in countries])

    def GetRules(self):
        for region, s in self.sliders.items():
            slider, *ignored = s
            self.rules['mins'][region] = slider.GetValue()
            self.rules['max'][region] = self._nSlotsRegionCanUse(region)
        self.rules['SeedersOn'] = self.chk_seeder.GetValue()
        return self.rules

    def onInit(self, event):
        for region, s in self.sliders.items():
            slider, *ignored = s
            slider.SetValue(self.rules['mins'][region])
        self.chk_seeder.SetValue(self.rules['SeedersOn'])
        self._UpdateSliders()

    def onSlide(self, event):
        self._UpdateSliders()

    def onSave(self, event):
        self.EndModal(wx.ID_OK)

    def onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def _UpdateSliders(self):
        for region_id, slider_block in self.sliders.items():
            slider, text = slider_block
            free_slots = self._nSlotsRegionCanUse(region_id)
            maximun = min(free_slots, self.countriesPerRegion[region_id])
            if maximun == 0:
                slider.Disable()
                maximun = 1
            else:
                slider.Enable()
            slider.SetMax(maximun)
            text.SetLabel(str(slider.GetValue()))

    def _nSlotsRegionCanUse(self, id):
        sum_minimun = 0
        for region_id, slider_block in self.sliders.items():
            if region_id != id:
                slider, text = slider_block
                sum_minimun += slider.GetValue()
        return 32 - sum_minimun

    def gui_init(self):
        text_seeder = _(" Seeder in the group's first slot")
        text_sliders_header = _(" Minimun number of contries per region")

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.chk_seeder = wx.CheckBox(self, wx.ID_ANY,
                                     text_seeder,
                                     wx.DefaultPosition, wx.DefaultSize, 0)

        sizer_sliders = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY,
                                                       text_sliders_header,
                                                       style=wx.ALIGN_LEFT),
                                          wx.VERTICAL)
        self.sliders = {}
        for r in GetRegions():
            b_sizer = wx.BoxSizer(wx.HORIZONTAL)
            static_text = wx.StaticText(sizer_sliders.GetStaticBox(), wx.ID_ANY,
                                        r.name,
                                        wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT)
            static_text.Wrap(-1)
            sizer_sliders.Add(b_sizer, 1, wx.ALIGN_RIGHT, 0)
            slider_label = wx.StaticText(sizer_sliders.GetStaticBox(), wx.ID_ANY,
                                         "00",
                                         wx.DefaultPosition, wx.DefaultSize, 0)
            slider = wx.Slider(sizer_sliders.GetStaticBox(), wx.ID_ANY,
                               0, 0, 32,
                               wx.DefaultPosition,
                               wx.Size(150,24),
                               wx.SL_MIN_MAX_LABELS)
            slider.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            slider.Bind(wx.EVT_SCROLL, self.onSlide)
            b_sizer.Add(static_text, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            b_sizer.Add(slider, 0, wx.ALL, 5)
            b_sizer.Add(slider_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            self.sliders[r.id] = [slider, slider_label]

        btn_save = wx.Button(self, wx.ID_ANY,
                             _("Save"),
                             wx.DefaultPosition, wx.DefaultSize, 0)
        btn_cancel = wx.Button(self, wx.ID_ANY,
                               _("Cancel"),
                               wx.DefaultPosition, wx.DefaultSize, 0)

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(btn_save, 0, wx.ALL, 5)
        sizer_buttons.Add(btn_cancel, 0, wx.ALL, 5)

        sizer_top = wx.BoxSizer(wx.VERTICAL)
        sizer_top.Add(self.chk_seeder, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer_top.Add(sizer_sliders, 0, wx.EXPAND, 5)

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(sizer_top, 1, wx.EXPAND, 5)
        sizer_main.Add(sizer_buttons, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_INIT_DIALOG, self.onInit)
        btn_save.Bind(wx.EVT_BUTTON, self.onSave)
        btn_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

