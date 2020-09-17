# -*- coding: utf-8 -*-

import json
import wx
from data import Country, Region, GetRegions, GetRegionById

class CountryEditor(wx.Dialog):
    def __init__(self, parent, countries):
        wx.Dialog.__init__(self, parent,
                           id=wx.ID_ANY,
                           title=_("Country Editor"),
                           pos=wx.DefaultPosition,
                           size=wx.Size(510,350),
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.gui_init()
        self.country_list = countries
        self.panel_editing.Disable()
        self.btn_remove.Disable()
        self.btn_add.Disable()
        self.colours = {"red": wx.Colour(255,200,200,255),
                        "dark": wx.Colour(200,230,200,255),
                        "light": wx.Colour(255,255,255,255)}

        # {region obj: item on tree}
        self.regions = {}

        # {contry obj: item on tree}
        self.countries = {}

    def getCountriesList(self):
        return [c for c in self.countries.keys()]

    def onInit(self, event):
        self.SetMinSize(self.GetSize())
        # add a root item, will be invisible because wxTR_HIDE_ROOT
        self.root = self.tree_countries.AddRoot("Region")
        # load regions
        for r in GetRegions():
            tree_item = self.tree_countries.AppendItem(self.root, r.name)
            self.tree_countries.SetItemData(tree_item, r)
            self.regions[r] = tree_item
            self.cmb_region.Append(r.name, r)
        self._sortTree()

        # setup countries if any
        if len(self.country_list) > 0:
            whatToDo = []
            for c in self.country_list:
                rGUI = self.regions[c.region]
                whatToDo.append([rGUI, c])
            self._buildCountriesTree(whatToDo)



    def onLoadCountries(self, event):
        file_name = self._callFileDialog(_("Open File"),
                                         wx.FD_OPEN |
                                         wx.FD_FILE_MUST_EXIST)
        if file_name is None:
            return

        with open(file_name, 'r') as data_file:
            try:
                data = json.load(data_file)
            except:
                wx.MessageBox(_("File is corrupt"
                                " or invalid JSON"),
                              _('Fail to read the file'),
                              wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
                return

            to_include = []
            for v in data.values():
                name = v['name']
                seeder = v['seeder']
                region_id = v['region']
                win_chance = v['win_chance']
                region = GetRegionById(region_id)
                if region is None:
                    wx.MessageBox(
                        _("Region '{region}' of Country '{country}' don't exist").format(
                            region=region_id, country=name),
                        _('Invalid Region'),
                        wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
                    return

                tree_item = self.regions[region]
                c = Country(name, region, seeder, win_chance)
                to_include.append([tree_item, c])
        self._buildCountriesTree(to_include)

    def onSaveCountries(self, event):
        duplicated = self._anyDuplicatedCountry()
        if duplicated:
            wx.MessageBox(
                _('Country name should be unique! Duplicated "{name}"').
                format(name=duplicated),
                _('Non unique Country'),
                wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
            return

        fileName = self._callFileDialog(_("Save As"),
                                        wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if fileName is None:
            return

        with open(fileName, 'w+') as outfile:
            to_save = {c.name: c.exportAsJSONObject()
                       for c in self.getCountriesList()}
            json.dump(to_save, outfile, indent=4)

    def onAddCountry(self, event):
        region_item = self.tree_countries.GetSelection()
        region_data = self.tree_countries.GetItemData(region_item)

        # if the selected item is a country, get the region
        if isinstance(region_data, Country):
            region_item = self.tree_countries.GetItemParent(region_item)
            region_data = self.tree_countries.GetItemData(region_item)

        # create a new country and append in the GUI
        c = Country(u"", region_data)
        new_item = self.tree_countries.AppendItem(region_item, c.name)

        self._syncTreeData(new_item, c)
        self._updateRegionCounter()
        self.tree_countries.SelectItem(new_item)
        self.txt_country.SetFocus()
        self.sld_winchance.SetValue(c.win_chance)

    def onRemoveCountry(self, event):
        item = self.tree_countries.GetSelection()
        data = self.tree_countries.GetItemData(item)
        if isinstance(data, Country):
            region = self.tree_countries.GetItemParent(item)
            self.tree_countries.SelectItem(region)
            self.tree_countries.Delete(item)
            self.countries.pop(data)
        self._updateColors()  # update colors to 'fix' possible old duplicates
        self._updateRegionCounter()

    def onCountrySelection(self, event):
        item = event.GetItem()  # get the selection
        s = self.tree_countries.GetItemData(item)  # get the selection Data

        # Region clicked -> disable country editing
        if isinstance(s, Region):
            self.panel_editing.Disable()
            self.btn_remove.Disable()
            self.btn_add.Enable()

        # Country clicked -> load values and enable controls
        elif isinstance(s, Country):
            self.cmb_region.SetValue(s.region.name)
            self.txt_country.SetValue(s.name)
            self.chk_seeder.SetValue(s.seeder)
            self.sld_winchance.SetValue(s.win_chance)
            self.panel_editing.Enable()
            self.btn_remove.Enable()
            self.btn_add.Enable()

    def onName(self, event):
        new_name = self.txt_country.GetValue()

        cGUI = self.tree_countries.GetSelection()  # get the selected item (country item)
        c = self.tree_countries.GetItemData(cGUI)  # get the data (country object)

        self.tree_countries.SetItemText(cGUI, new_name)  # update text on GUI
        c.name = new_name  # update text on data

        rGUI = self.tree_countries.GetItemParent(cGUI)  # get the region item
        self.tree_countries.SortChildren(rGUI)  # sort the region items

        self._updateColors()  # check country names and update gui color

    # update the country region in the tree when region get updated
    def onRegion(self, event):
        pos = self.cmb_region.GetCurrentSelection()
        region = self.cmb_region.GetClientData(pos)
        region_tree_item = self.regions[region]

        old_item = self.tree_countries.GetSelection()
        country = self.tree_countries.GetItemData(old_item)

        country.region = region
        new_item = self.tree_countries.AppendItem(region_tree_item,
                                                  country.name)
        self._syncTreeData(new_item, country)

        self.tree_countries.Delete(old_item)
        self.tree_countries.SortChildren(region_tree_item)
        self.tree_countries.SelectItem(new_item)

    def onWinChance(self, event):
        country_gui = self.tree_countries.GetSelection()
        country = self.tree_countries.GetItemData(country_gui)
        country.win_chance = self.sld_winchance.GetValue()

    def onSeed(self, event):
        item = self.tree_countries.GetSelection()
        c = self.tree_countries.GetItemData(item)
        c.seeder = not c.seeder
        self._updateColors()

    def onClose(self, event):
        duplicated = self._anyDuplicatedCountry()
        if duplicated:
            dlg = wx.MessageDialog(
                self,
                _('Country "{name}" not unique, quit without save?').format(
                    name=duplicated),
                _("Exit"),
                wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_NO:
                return
            dlg.Destroy()
            self.EndModal(wx.ID_CANCEL)
        else:
            self.EndModal(wx.ID_OK)
        self.tree_countries.DeleteAllItems()
        self.Destroy()

    def _anyDuplicatedCountry(self):
        dup = self._getDuplicateCountries()
        if len(dup) > 0:
            return dup.pop()
        else:
            return False

    def _sortTree(self):
        for region_item in self.regions.values():
            self.tree_countries.SortChildren(region_item)
        self.tree_countries.SortChildren(self.root)

    def _getDuplicateCountries(self):
        seen = set()
        duplicates = set()
        for c in self.countries.keys():
            if c.name not in seen:
                seen.add(c.name)
            else:
                duplicates.add(c.name)
        return duplicates

    # update every country item color
    def _updateColors(self):
        duplicates = self._getDuplicateCountries()

        for c, gui_item in self.countries.items():
            if c.name in duplicates:
                index = "red"
            else:
                if c.seeder:
                    index = "dark"
                else:
                    index = "light"
            self.tree_countries.SetItemBackgroundColour(gui_item,
                                                        self.colours[index])

    # update the counter in region titles
    def _updateRegionCounter(self):
        for r, tree_item in self.regions.items():
            count = self.tree_countries.GetChildrenCount(tree_item)
            if count > 0:
                self.tree_countries.SetItemText(tree_item,
                                                "{name} ({i})".format(
                                                    name=r.name, i=count))
            else:
                self.tree_countries.SetItemText(tree_item, "{name}".format(
                    name=r.name))

    # list of actions to fill the region nodes
    # to_do is a list of (region gui/tree node, country)
    # it add each country on the given region
    def _buildCountriesTree(self, to_do):
        # delete all countries references & gui nodes
        self.countries.clear()
        for region_item in self.regions.values():
            self.tree_countries.DeleteChildren(region_item)

        # fill the tree
        for region_item, country in to_do:
            new_item = self.tree_countries.AppendItem(region_item,
                                                      country.name)
            self._syncTreeData(new_item, country)

        # update the tree
        self._sortTree()
        self._updateColors()
        self._updateRegionCounter()

    # create references gui <-> data to fast access
    def _syncTreeData(self, gui_item, country):
        self.tree_countries.SetItemData(gui_item, country)
        self.countries[country] = gui_item

    def _callFileDialog(self, text, flags):
        file_dialog = wx.FileDialog(self, text, "", "",
                                    "JSON file (*.json)|*.json", flags)
        loaded = file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()

        if loaded != wx.ID_OK:
            return None
        else:
            return file_path

    def gui_init(self):
        text_load = _("Load from File")
        text_save = _("Save to File")
        text_add = _("Add Country")
        text_remove = _("Remove Country")
        text_name = _("Name :")
        text_country = _("Country")
        text_region = _("Region :")
        text_select = _("Select a Region")
        text_seeder = _("Can be a seeder")
        text_winchance = _("Win \nChance (%)")

        self.SetSizeHints(wx.Size(-1,-1), wx.DefaultSize)

        self.tree_countries = wx.TreeCtrl(self, wx.ID_ANY, wx.DefaultPosition,
                                          wx.Size(-1,-1),
                                          wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        self.btn_load = wx.Button(self, wx.ID_ANY,
                                  text_load,
                                  wx.DefaultPosition, wx.DefaultSize, 0)
        self.btn_save = wx.Button(self, wx.ID_ANY,
                                  text_save,
                                  wx.DefaultPosition, wx.DefaultSize, 0)
        staticline = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition,
                                   wx.DefaultSize, wx.LI_HORIZONTAL)
        self.btn_add = wx.Button(self, wx.ID_ANY,
                                 text_add,
                                 wx.DefaultPosition, wx.DefaultSize, 0)
        self.btn_remove = wx.Button(self, wx.ID_ANY,
                                    text_remove,
                                    wx.DefaultPosition, wx.DefaultSize, 0)
        self.panel_editing = wx.Panel(self, wx.ID_ANY,
                                      wx.DefaultPosition,
                                      wx.DefaultSize,
                                      wx.STATIC_BORDER)
        sizer_editing = wx.StaticBoxSizer(wx.StaticBox(self.panel_editing,
                                                       wx.ID_ANY,
                                                       text_country),
                                          wx.VERTICAL)
        label_name = wx.StaticText(sizer_editing.GetStaticBox(),
                                   wx.ID_ANY,
                                   text_name,
                                   wx.DefaultPosition,
                                   wx.DefaultSize, 0)
        label_region = wx.StaticText(sizer_editing.GetStaticBox(),
                                     wx.ID_ANY,
                                     text_region,
                                     wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        label_winchance = wx.StaticText(sizer_editing.GetStaticBox(),
                                        wx.ID_ANY,
                                        text_winchance,
                                        wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        label_name.Wrap(-1)
        label_region.Wrap(-1)
        label_winchance.Wrap(-1)
        self.txt_country = wx.TextCtrl(sizer_editing.GetStaticBox(),
                                       wx.ID_ANY,
                                       wx.EmptyString,
                                       wx.DefaultPosition,
                                       wx.DefaultSize,
                                       wx.TE_RICH)
        region_choices = []
        self.cmb_region = wx.ComboBox(sizer_editing.GetStaticBox(),
                                      wx.ID_ANY,
                                      text_select,
                                      wx.DefaultPosition,
                                      wx.DefaultSize,
                                      region_choices,
                                      wx.CB_READONLY)
        self.chk_seeder = wx.CheckBox(sizer_editing.GetStaticBox(),
                                      wx.ID_ANY,
                                      text_seeder,
                                      wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        self.sld_winchance = wx.Slider(sizer_editing.GetStaticBox(),
                                       wx.ID_ANY,
                                       50, 1, 100,
                                       wx.DefaultPosition,
                                       wx.DefaultSize,
                                       wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.sld_winchance.SetMinSize(wx.Size(100,-1))

        sizer_name = wx.BoxSizer(wx.HORIZONTAL)
        sizer_name.Add(label_name, 0, wx.ALL, 5)
        sizer_name.Add(self.txt_country, 1, wx.ALL, 0)

        sizer_region = wx.BoxSizer(wx.HORIZONTAL)
        sizer_region.Add(label_region, 0, wx.ALL, 5)
        sizer_region.Add(self.cmb_region, 1, wx.ALL, 0)

        sizer_winchance = wx.BoxSizer(wx.HORIZONTAL)
        sizer_winchance.Add(label_winchance, 0, wx.ALL, 5)
        sizer_winchance.Add(self.sld_winchance, 1, wx.ALL|wx.EXPAND, 4)

        sizer_editing.Add(sizer_name, 1, wx.EXPAND, 5)
        sizer_editing.Add(sizer_region, 1, wx.EXPAND, 5)
        sizer_editing.Add(self.chk_seeder, 0, wx.ALL, 5)
        sizer_editing.Add(sizer_winchance, 1, wx.EXPAND, 5)

        self.panel_editing.SetSizer(sizer_editing)
        self.panel_editing.Layout()
        sizer_editing.Fit(self.panel_editing)

        sizer_addremove = wx.BoxSizer(wx.HORIZONTAL)
        sizer_addremove.Add(self.btn_add, 0, wx.ALL, 5)
        sizer_addremove.Add(self.btn_remove, 0, wx.ALL, 5)

        sizer_tree = wx.GridSizer(1, 1, 0, 0)
        sizer_tree.Add(self.tree_countries, 0, wx.ALL|wx.EXPAND, 5)

        sizer_ctrl = wx.BoxSizer(wx.VERTICAL)
        sizer_ctrl.Add(self.btn_load, 0, wx.ALL|wx.EXPAND, 5)
        sizer_ctrl.Add(self.btn_save, 0, wx.ALL|wx.EXPAND, 5)
        sizer_ctrl.Add(staticline, 0, wx.EXPAND|wx.ALL, 5)
        sizer_ctrl.Add(sizer_addremove, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        sizer_ctrl.Add(self.panel_editing, 1, wx.EXPAND |wx.ALL, 5)

        sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(sizer_tree, 1, wx.EXPAND, 5)
        sizer_main.Add(sizer_ctrl, 0, 0, 5)

        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_INIT_DIALOG, self.onInit)
        self.tree_countries.Bind(wx.EVT_TREE_SEL_CHANGED,
                                 self.onCountrySelection)
        self.btn_load.Bind(wx.EVT_BUTTON, self.onLoadCountries)
        self.btn_save.Bind(wx.EVT_BUTTON, self.onSaveCountries)
        self.btn_add.Bind(wx.EVT_BUTTON, self.onAddCountry)
        self.btn_remove.Bind(wx.EVT_BUTTON, self.onRemoveCountry)
        self.txt_country.Bind(wx.EVT_TEXT, self.onName)
        self.cmb_region.Bind(wx.EVT_COMBOBOX, self.onRegion)
        self.chk_seeder.Bind(wx.EVT_CHECKBOX, self.onSeed)
        self.sld_winchance.Bind(wx.EVT_SCROLL, self.onWinChance)

