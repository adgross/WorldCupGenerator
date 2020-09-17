# -*- coding: utf-8 -*-

import sys
import os
import wx
from data import GetRegions
from gen import SuperLeague, AllRandom
from ruleseditor import RulesEditor
from countryeditor import CountryEditor


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None,
                          id=wx.ID_ANY,
                          title=_("World Cup Generator"),
                          pos=wx.DefaultPosition,
                          size=wx.Size(827, 420),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.slots = []
        self.slots_seeders = []
        self.slots_non_seeders = []
        self.countries = []
        # countries in this list not change when generating a new world cup
        self.countries_freezed = []

        self.gui_init()
        self.setup_icon()
        self.SetMinSize(self.GetSize())
        self._UpdateGUI()

        # setup rules / default
        self.rules = {'SeedersOn': True, 'mins': {}, 'max': {}}
        for r in GetRegions():
            self.rules['mins'][r.id] = 0
            self.rules['max'][r.id] = 32
        self.cmb_method.SetSelection(1)



    def onClickFreeze(self, event):
        btn = event.GetEventObject()
        if btn.wcg_country is None:
            btn.SetValue(False)
        else:
            if btn.GetValue():
                self.countries_freezed.append(btn.wcg_country)
            else:
                self.countries_freezed.remove(btn.wcg_country)
        return

    def onGenerate(self, event):
        if len(self.countries) < 32:
            wx.MessageBox(_("Need at least 32 countries"
                            " to make a World Cup."),
                          _("Fail to Generate"),
                          wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
            return

        # check if we have enought seeders considering the rules
        # example: one region have 15 seeders while others have 0,
        #          if this region have a rule-limit of 7 teams,
        #          we will be missing 1 seeder
        if self.rules['SeedersOn']:
            seeders = [c for c in self.countries if c.seeder]
            if len(seeders) < 8:
                wx.MessageBox(_("Need at least 8 seeders."),
                              _("Impossible create a World Cup"),
                              wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
                return

            max_possible_seeders = sum(
                min(len([c for c in seeders if c.region == r]),
                    self.rules['max'][r.id])
                for r in GetRegions())

            if max_possible_seeders < 8:
                wx.MessageBox(
                    _("The minimun per region"
                      " do not ensure 8 seeders available."),
                    _("Impossíble create a World Cup"),
                    wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
                return

        cup_generator = {0: AllRandom, 1: SuperLeague}
        selection = self.cmb_method.GetSelection()
        method = cup_generator[selection](self.rules,
                                          self.countries,
                                          self.countries_freezed)

        # slot.GetValue)() tell if freezed
        if self.rules['SeedersOn']:
            needed_seeders = [
                s for s in self.slots_seeders
                if not s.GetValue()]
            needed_non_seeders = [
                s for s in self.slots_non_seeders
                if not s.GetValue()]
            seeder_choices = method.GetSelections(len(needed_seeders),
                                                  isSeeder=True)
            country_choices = method.GetSelections(len(needed_non_seeders))

            for slot in needed_seeders:
                c = seeder_choices.pop(0)
                slot.SetLabel(c.name)
                slot.wcg_country = c
            for slot in needed_non_seeders:
                c = country_choices.pop(0)
                slot.SetLabel(c.name)
                slot.wcg_country = c
        else:
            needed_slots = [s for s in self.slots if not s.GetValue()]
            choices = method.GetSelections(len(needed_slots))
            for slot in needed_slots:
                c = choices.pop(0)
                slot.SetLabel(c.name)
                slot.wcg_country = c

    def onCallCountryManager(self, event):
        ce = CountryEditor(self, self.countries)
        if ce.ShowModal() == wx.ID_OK:
            self.countries = ce.getCountriesList()

            # check if an old selected country is now removed
            for btn in self.slots:
                if btn.wcg_country not in self.countries:
                    btn.SetLabel(wx.EmptyString)
                    if btn.GetValue():
                        btn.SetValue(False)
                        self.countries_freezed.remove(btn.wcg_country)
                    btn.wcg_country = None
            self._UpdateGUI()

    def onCallRulesManager(self, event):
        re = RulesEditor(self, self.rules, self.countries)
        if re.ShowModal() == wx.ID_OK:
            self.rules = re.GetRules()

    # enable/disable buttons
    # should run when program starts and after country editor
    def _UpdateGUI(self):
        if len(self.countries) >= 32:
            self.btn_rules.Enable()
            self.btn_generate.Enable()
        else:
            self.btn_rules.Disable()
            self.btn_generate.Disable()

    def setup_icon(self):
        # if hasattr(sys, 'frozen') and sys.platform == 'win32':
        #     icon_name = sys.executable
        # elif not hasattr(sys, 'frozen'):
        start_path = os.path.dirname(os.path.realpath(__file__))
        icon_name = start_path + "/icons/app.svg"
        self.SetIcon(wx.Icon(icon_name, wx.BITMAP_TYPE_ICO))

    def gui_init(self):
        text_group = _("Group ")
        text_generate = _("Generate")
        text_cmb = _("Combo")
        text_country = _("Country Editor")
        text_rule = _("Rules Editor")
        method_choices = [_("All Random"), _("Super League")]

        self.SetSizeHints(wx.Size(-1, -1), wx.DefaultSize)

        pnl_main = wx.Panel(self, wx.ID_ANY,
                            wx.DefaultPosition, wx.DefaultSize,
                            wx.TAB_TRAVERSAL)

        sizer_grid = wx.GridSizer(2, 4, 0, 0)
        for group in 'ABCDEFGH':
            sizer_group = wx.BoxSizer(wx.VERTICAL)
            lbl_group = wx.StaticText(pnl_main, wx.ID_ANY,
                                      text_group + group,
                                      wx.DefaultPosition, wx.DefaultSize, 0)
            lbl_group.Wrap(-1)
            sizer_group.Add(lbl_group, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
            for i in range(0, 4):
                btn_team = wx.ToggleButton(pnl_main, wx.ID_ANY,
                                           wx.EmptyString,
                                           wx.DefaultPosition,
                                           wx.DefaultSize, 0)
                sizer_group.Add(btn_team, 0, wx.ALL | wx.EXPAND, 5)

                self.slots.append(btn_team)
                if i == 0:
                    self.slots_seeders.append(btn_team)
                else:
                    self.slots_non_seeders.append(btn_team)
                btn_team.Bind(wx.EVT_TOGGLEBUTTON, self.onClickFreeze)
                btn_team.wcg_country = None
            sizer_grid.Add(sizer_group, 1, wx.EXPAND, 5)


        self.btn_generate = wx.Button(pnl_main, wx.ID_ANY,
                                      text_generate,
                                      wx.DefaultPosition, wx.DefaultSize, 0)
        self.cmb_method = wx.ComboBox(pnl_main, wx.ID_ANY,
                                      text_cmb,
                                      wx.DefaultPosition, wx.DefaultSize,
                                      method_choices,
                                      wx.CB_READONLY)
        self.btn_countries = wx.Button(pnl_main, wx.ID_ANY,
                                       text_country,
                                       wx.DefaultPosition, wx.DefaultSize, 0)
        self.btn_rules = wx.Button(pnl_main, wx.ID_ANY,
                                   text_rule,
                                   wx.DefaultPosition, wx.DefaultSize, 0)
        staticline = wx.StaticLine(pnl_main, wx.ID_ANY,
                                   wx.DefaultPosition, wx.DefaultSize,
                                   wx.LI_HORIZONTAL)

        sizer_cmd = wx.BoxSizer(wx.VERTICAL)
        sizer_cmd.Add(self.btn_generate, 0, wx.ALL | wx.EXPAND, 5)
        sizer_cmd.Add(self.cmb_method, 0, wx.ALL | wx.EXPAND, 5)
        sizer_cmd.Add(staticline, 0, wx.EXPAND | wx.ALL, 5)
        sizer_cmd.Add(self.btn_countries, 0, wx.ALL | wx.EXPAND, 5)
        sizer_cmd.Add(self.btn_rules, 0, wx.ALL | wx.EXPAND, 5)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(sizer_grid, 1, wx.EXPAND, 5)
        sizer_top.Add(sizer_cmd, 0, wx.EXPAND, 5)

        pnl_main.SetSizer(sizer_top)
        pnl_main.Layout()
        sizer_top.Fit(pnl_main)

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(pnl_main, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre(wx.BOTH)

        self.btn_generate.Bind(wx.EVT_BUTTON, self.onGenerate)
        self.btn_countries.Bind(wx.EVT_BUTTON, self.onCallCountryManager)
        self.btn_rules.Bind(wx.EVT_BUTTON, self.onCallRulesManager)

