## Get Screen Definition From Database

First system need to get all the page definitions from the database.

    
    
    def _getScreenDefinitionFromDB(self, name) -> ScreenDefinition:
        dfn = None
        if "." in name:
            name = name.split(".")[1]
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=name).order_by("-rev").first()
        if screenRc:
            dfn = {}
            dfn['viewAPIRev'] = screenRc.api_version
            dfn['viewID'] = screenRc.screen_sn
            dfn['viewTitle'] = screenRc.screen_title
            dfn['viewDesc'] = screenRc.screen_dsc
            dfn['layoutType'] = screenRc.layout_type
            dfn['layoutParams'] = screenRc.layout_params
            dfn['viewName'] = screenRc.class_nm
            dfn['editable'] = screenRc.editable
            # YL, 2024-02-28, Bugfix for auto refresh - start
            if isNotNullBlank(screenRc.auto_refresh_interval):
                dfn['autoRefresh'] = str(screenRc.auto_refresh_interval)
                if isNotNullBlank(screenRc.auto_refresh_action):
                    dfn['autoRefresh'] = dfn['autoRefresh'] + ";" + screenRc.auto_refresh_action
            # YL, 2024-02-28 - end
    
            # Recordset
            dfn['recordsetTable'] = []
            recordsetRcs = ikModels.ScreenRecordset.objects.filter(screen=screenRc).order_by("id")
            for rc in recordsetRcs:
                data = []
                data.append(rc.recordset_nm)
                data.append(rc.sql_fields)
                data.append(rc.sql_models)
                data.append(rc.sql_where)
                data.append(rc.sql_order)
                data.append(rc.sql_limit)
                # data.append('') # old page size(no use)
                # data.append('') # old ReadOnly(no use)
                data.append(rc.rmk)
                dfn['recordsetTable'].append(data)
    
            # Field Groups
            dfn['fieldGroupTable'] = []
            fieldGroupRcs = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc).order_by("seq")
            for rc in fieldGroupRcs:
                data = []
                data.append(rc.fg_nm)
                data.append(rc.fg_type.type_nm if rc.fg_type else None)
                data.append(rc.caption)
                data.append(rc.recordset.recordset_nm if rc.recordset else None)
                data.append(rc.deletable)
                data.append(rc.editable)
                data.append(rc.insertable)
                data.append(rc.highlight_row)
                data.append(rc.selection_mode)
                data.append(rc.cols)
                # data.append(rc.sort_new_rows)
                data.append(rc.data_page_type)
                data.append(rc.data_page_size)
                data.append(rc.outer_layout_params)
                data.append(rc.inner_layout_type)
                data.append(rc.inner_layout_params)
                data.append(rc.html)
                data.append(rc.additional_props)
                data.append(rc.rmk)
                dfn['fieldGroupTable'].append(data)
    
            # Fields
            dfn['fieldTable'] = []
            fieldRcs = ikModels.ScreenField.objects.filter(screen=screenRc).order_by("seq")
            lastFgNm = None
            for rc in fieldRcs:
                data = []
                fgNm = rc.field_group.fg_nm if rc.field_group else None
                data.append(fgNm)
                # data.append(fgNm if lastFgNm != fgNm else None)
                # lastFgNm = fgNm
    
                data.append(rc.field_nm)
                data.append(rc.caption)
                data.append(rc.tooltip)
                data.append(rc.visible)
                data.append(rc.editable)
                data.append(rc.db_unique)
                data.append(rc.db_required)
                data.append(rc.widget.widget_nm if rc.widget else None)
                data.append(rc.widget_parameters)
                data.append(rc.db_field)
                data.append(rc.event_handler)
                data.append(rc.styles)
                data.append(rc.rmk)
                dfn['fieldTable'].append(data)
    
            # Sub Screen
            dfn['subScreenTable'] = []
            dfnRcs = ikModels.ScreenDfn.objects.filter(screen=screenRc)
            for rc in dfnRcs:
                data = []
                data.append(rc.sub_screen_nm)
                data.append(rc.field_group_nms)
                dfn['subScreenTable'].append(data)
    
            # Field Group Links
            dfn['fieldGroupLinkTable'] = []
            fgLinkRcs = ikModels.ScreenFgLink.objects.filter(screen=screenRc).order_by("field_group__seq")
            for rc in fgLinkRcs:
                data = []
                data.append(rc.field_group.fg_nm if rc.field_group else None)
                data.append(rc.parent_field_group.fg_nm if rc.parent_field_group else None)
                data.append(rc.parent_key)
                data.append(rc.local_key)
                data.append(rc.rmk)
                dfn['fieldGroupLinkTable'].append(data)
    
            # Table Header and Footer
            dfn['headerFooterTable'] = []
            fgHeaderFooterRcs = ikModels.ScreenFgHeaderFooter.objects.filter(screen=screenRc).order_by("field_group__seq", "field__seq")
            for rc in fgHeaderFooterRcs:
                data = []
                data.append(rc.field_group.fg_nm if rc.field_group else None)
                data.append(rc.field.field_nm if rc.field else None)
                data.append(rc.header_level1)
                data.append(rc.header_level2)
                data.append(rc.header_level3)
                data.append(rc.footer)
                data.append(rc.rmk)
                dfn['headerFooterTable'].append(data)
        if dfn is None:
            logger.debug('getScreenDefinitionFromDB(%s) from database is empty.' % name)
            return None
    
        return dfn
    

## Get Screen

Then page definition is organized to be saved using the back-end Screen class.

    
    
    def getScreen(self, screenName: str, subScreenNm=None, globalRequestUrlParameters: dict = None) -> Screen:
        '''
            screenName (str): screen's name
            globalRequestUrlParameters (dict, optional):  add parameters to all request urls (e.g. get data request, button action ...)
        '''
        global DNF_Summary
        # screenDfn = self.__getScreenDefinition(screenName)
        screenDfn = ikuiCache.getPageDefinitionFromCache(screenName)
        if isNullBlank(screenDfn):
            screenDfn = self._getScreenDefinitionFromDB(screenName)  # YL.ikyo, 2023-04-18 get screen from database
            ikuiCache.setPageDefinitionCache(screenName, screenDfn)
        dfn = copy.deepcopy(screenDfn)
    
        if dfn is None:
            logger.error('getScreenDefinition(%s).data=None' % screenName)
            return None
    
        screen = Screen(screenDefinition=dfn)
        # 1. screen information
        screen.apiVersion = dfn['viewAPIRev']
        screen.id = dfn['viewID']
        screen.title = dfn['viewTitle']
        screen.description = dfn['viewDesc']
        screen.layoutType = dfn['layoutType']
        screen.layoutParams = dfn['layoutParams']
        screen.className = dfn['viewName']
        # YL.ikyo, 2023-04-20 - start
        # screen.editable = ('yes' == dfn.get('editable', '').lower())
        screen.editable = self.__toBool(dfn.get('editable'))
        # YL.ikyo, 2023-04-20 - end
    
        autoRefreshInterval, autoRefreshAction = self.__getScreenAutoRefreshInfo(dfn.get('autoRefresh', None))
        screen.autoRefreshInterval = autoRefreshInterval
        screen.autoRefreshAction = ikHttpUtils.setQueryParameter(autoRefreshAction, globalRequestUrlParameters)
    
        # 2. Recordset
        for recordsetRecord in dfn['recordsetTable']:
            srs = ScreenRecordSet()
            srs.name = recordsetRecord[0]
            srs.queryFields = recordsetRecord[1]
            srs.modelNames = recordsetRecord[2]
            srs.queryWhere = recordsetRecord[3]
            srs.queryOrder = recordsetRecord[4]
            srs.queryLimit = None if recordsetRecord[5] is None else int(recordsetRecord[5])
            # YL.ikyo, 2023-04-20 from database no use - start
            # srs.queryPageSize = recordsetRecord[6]
            # srs.readOnly = recordsetRecord[7] is not None and 'yes' == recordsetRecord[7].lower()
            # YL.ikyo, 2023-04-20 - end
            screen.recordsets.append(srs)
    
        # 3. FieldGroups
        # for fgName, fgType, caption, recordsetName, deletable, editable, insertable, selectable, cols, pageType, pageSize in dfn['fieldGroupTable']: # old from excel
        subScreenTable = dfn['subScreenTable']
        displayFgs = None  # None:  default display all field group, []: have not subScreen, [xxx]: the field group display in sub screen
        if subScreenNm is None:
            subScreenNm = MAIN_SCREEN_NAME
        for i in subScreenTable:
            if i[0].strip().lower() == subScreenNm.strip().lower():
                displayFgs = [item.strip() for item in i[1].split(',')]
        if displayFgs is None and subScreenNm is not None and subScreenNm.strip().lower() != MAIN_SCREEN_NAME.lower():
            displayFgs = []
        screen.subScreenName = subScreenNm
    
        for fgName, fgType, caption, recordsetName, deletable, editable, insertable, highlightRow, selectionMode, cols, pageType, \
                pageSize, outerLayoutParams, innerLayoutType, innerLayoutParams, html, additionalProps, rmk in dfn['fieldGroupTable']:  # from database
            if displayFgs is not None and fgName not in displayFgs:
                continue
            sfg = ScreenFieldGroup(parent=screen)
            sfg.name = fgName
            sfg.groupType = getScreenFieldGroupType(fgType)
            sfg.caption = caption
            sfg.recordSetName = recordsetName
            sfg.deletable = self.__toBool(deletable)
            sfg.editable = self.__toBool(editable)
            sfg.insertable = self.__toBool(insertable)
            sfg.highlightRow = self.__toBool(highlightRow)
            sfg.selectionMode = getScreenFieldGroupSelectionMode(selectionMode)
            sfg.cols = None if cols is None else int(cols)
            sfg.pageType = getScreenFieldGroupDataPageType(pageType)
            sfg.pageSize = None if isNullBlank(pageSize) else pageSize
            sfg.outerLayoutParams = outerLayoutParams
            sfg.innerLayoutType = innerLayoutType
            sfg.innerLayoutParams = innerLayoutParams
            sfg.html = html
            sfg.additionalProps = None if isNullBlank(additionalProps) else self.parseWidgetPrams(additionalProps)
            sfg.beforeDisplayAdapter = None  # a javascript function for react
    
            DNF_Summary.addGroupType(screenName, sfg.groupType)
    
            if isTableFieldGroup(fgType) or isDetailFieldGroup(fgType):
                if isNullBlank(sfg.beforeDisplayAdapter):
                    sfg.beforeDisplayAdapter = None
                if fgType == SCREEN_FIELD_TYPE_RESULT_TABLE:
                    # sfg.editable = False
                    sfg.insertable = False
                    sfg.deletable = False
                    sfg.selectionMode = getScreenFieldGroupSelectionMode(selectionMode)
                elif fgType == SCREEN_FIELD_TYPE_FIELDS:
                    sfg.beforeDisplayAdapter = None
                elif fgType == SCREEN_FIELD_TYPE_SEARCH:
                    sfg.insertable = None
                    sfg.deletable = None
                    sfg.beforeDisplayAdapter = None
            screen.fieldGroups.append(sfg)
    
        currentFieldGroupName = None
        for fieldDfn in dfn['fieldTable']:
            fieldGroupName, name, caption, tooltip, visible, editable, unique, required, widget, widgetPrms, dataField, eventHandler, style, rmk = fieldDfn
            if displayFgs is not None and fieldGroupName not in displayFgs:
                continue
            if currentFieldGroupName is None or not isNullBlank(fieldGroupName) and fieldGroupName != currentFieldGroupName:
                currentFieldGroupName = fieldGroupName
            sfg = screen.getFieldGroup(currentFieldGroupName)
            if sfg is None:
                raise IkValidateException('Field group [%s] is not found in screen [%s].' % (currentFieldGroupName, screen.id))
            field = ScreenField(parent=sfg)
            sfg.fields.append(field)
    
            eventHandlerUrl, eventHandlerPrms = self.__getEventHandler(screen, eventHandler)
            if isNullBlank(widget):
                if sfg.groupType == SCREEN_FIELD_TYPE_ICON_BAR:
                    widget = SCREEN_FIELD_WIDGET_ICON_AND_TEXT
                else:
                    widget = SCREEN_FIELD_WIDGET_LABEL
    
            field.name = _getSceenFieldName(name, dataField if isNotNullBlank(dataField) else eventHandlerUrl, fieldGroupName)
            field.caption = caption
            field.tooltip = tooltip
            field.widget = getScreenFieldWidget(widget)
            field.editable = self.__toBool(editable, default=True)
            # field.visible = not self.__toBool(visible, default=False) # YL.ikyo, 2023-04-20 old from excel
            field.visible = self.__toBool(visible, default=True)  # YL.ikyo, 2023-04-20 from data database(visible)
            field.required = self.__toBool(None, default=False)  # TODO: reference to recordset
            field.dataField = dataField
            # field.dataKeyField = dataKeyField # XH, 2023-04-20 old from excel
            field.unique = unique
            field.required = required
            field.eventHandler = ikHttpUtils.setQueryParameter(eventHandlerUrl, globalRequestUrlParameters)
            field.eventHandlerParameter = eventHandlerPrms
            field.style = self.__getStylePrms(style)
            # field is an input parameter, then put this line at the end.
            # TODO:....
            field.widgetParameter = self.__getWidgetPramsOnly(widgetPrms)
    
            DNF_Summary.addFieldWidget(screenName, field.widget)
            DNF_Summary.addFieldWidgetParameters(screenName + ' -> ' + str(widget), widgetPrms)
            DNF_Summary.addFieldEventHandler(screenName, field.eventHandler)
    
            if isTableFieldGroup(sfg.groupType) or isDetailFieldGroup(sfg.groupType):
                if isNullBlank(field.widget):
                    field.widget = SCREEN_FIELD_WIDGET_LABEL
                if field.widget == SCREEN_FIELD_WIDGET_LABEL:
                    field.editable = False
                # TODO:
            elif sfg.groupType == SCREEN_FIELD_TYPE_ICON_BAR:
                if isNullBlank(field.widget):
                    field.widget = SCREEN_FIELD_WIDGET_ICON_AND_TEXT
                # TODO:
        for sfg in screen.fieldGroups:
            if sfg.groupType == SCREEN_FIELD_TYPE_RESULT_TABLE and sfg.editable:
                # result table add edit field
                sfg.fields.append(self.__getResultTableEditButtonField(sfg))
    
        # 4. FieldGroupLinks
        fieldGroupLinkTable = dfn.get('fieldGroupLinkTable', None)
        if fieldGroupLinkTable is not None and len(fieldGroupLinkTable) > 0:
            # TODO
            # for fieldGropName, parentFieldGroupName, parentKey, localKeyin fieldGroupLinkTable: # rmk
            for fieldGropName, parentFieldGroupName, parentKey, localKey, rmk in fieldGroupLinkTable:  # rmk
                if isNullBlank(fieldGropName) and isNullBlank(parentKey) and isNullBlank(localKey):
                    continue  # ignore the blank row
                # 1) check the field group is exists or not
                fieldGroup = screen.getFieldGroup(fieldGropName)
                if fieldGroup is None:
                    raise IkValidateException(
                        'Field group [%s] is not found in Field Group Link table. Please check screen [%s].' % (fieldGropName, screen.id))
                parentFieldGroup = screen.getFieldGroup(parentFieldGroupName)
                if parentFieldGroup is None:
                    raise IkValidateException(
                        'Field group [%s] is not found in Field Group Link table. Please check screen [%s].' % (parentFieldGroupName, screen.id))
                # 2) check the parent field gorup is exists or not
                # 2) check the parent key and local key
                if isNullBlank(parentKey) and isNullBlank(localKey):
                    raise IkValidateException(
                        'Parent Key and Local Key are mandatory in Field Group Link table: Field group [%s], screen [%s].' % (fieldGropName, screen.id))
                # screen.getFieldGroupRecordSet()
                fgl = FieldGroupLink(parentFieldGroup, parentKey, localKey)
                fieldGroup.fieldGroupLink = fgl
                screen.fieldGroupLinks[fieldGropName] = fgl
    
        # 5. table header / footers
        headerFooterTable = dfn.get('headerFooterTable', None)
        if headerFooterTable is not None and len(headerFooterTable) > 0:
            tableFgNames = []
            for fg in screen.fieldGroups:
                if fg.isTable():
                    tableFgNames.append(fg.name)
    
            lastFgName = None
            hfMap = {}  # header footer table detail map
            rowIndex = -1
            for row in headerFooterTable:
                fgName = row[0]
                if displayFgs is not None and fgName not in displayFgs:
                    continue
                if len(tableFgNames) == 0:
                    raise IkValidateException(
                        'No table field group found in current screen. Please check screen: [%s] sub screen: [%s].' % (screen.id, screen.subScreenName))
                if isNullBlank(fgName):
                    fgName = lastFgName
                    rowIndex += 1
                else:
                    lastFgName = fgName
                    rowIndex = 0
                if not isNullBlank(fgName) and fgName not in tableFgNames:
                    raise IkValidateException(
                        'Field Group [%s] is not found in FieldGroups table in [Table Header and Footer for inline tables]. Please check screen [%s].' % (fgName, screen.id))
                if isNullBlank(fgName):
                    raise IkValidateException(
                        'Field Group Name is mandatory in [Table Header and Footer for inline tables]. Please check screen [%s].' % (screen.id))
                tableHf = hfMap.get(fgName, None)
                if tableHf is None:  # new table
                    tableHf = TableHeaderFooter()
                    hfMap[fgName] = tableHf
    
                tableFieldNames = screen.getFieldGroup(fgName).getFieldNames()
                fieldName = row[1]
                if isNullBlank(fieldName):
                    fieldName = tableFieldNames[rowIndex]
    
                tableHfRow = TableHeaderFooterRow(fieldName)
                # # The first two columns are 'fg_nm' and 'field_nm', with several columns in the middle as 'header', the second-to-last column as 'footer', and the last column as 'rmk' (rmk is not used for now).
                for i in range(2, len(row) - 2):
                    tableHfRow.headers.append(convertStr2Json(row[i], defaultKey="text"))
                tableHfRow.footer = convertStr2Json(row[-2], defaultKey="text")
                tableHf.fields.append(tableHfRow)
            # validate total fields for each table
            for fgName, tableHf in hfMap.items():
                totalFields = len(tableHf.fields)
                fg = screen.getFieldGroup(fgName)
                totalFgFields = len(fg.fields)
                if totalFields == totalFgFields:
                    # the field name in header-footer table shoulbe the the same as defined in fields table for a field group
                    # if it's empty, then update it
                    for i in range(totalFgFields):
                        tableHfRowField = tableHf.fields[i]
                        fgFieldName = fg.fields[i].name
                        if tableHfRowField.fieldName != fgFieldName:
                            if isNullBlank(tableHfRowField.fieldName):
                                tableHfRowField.fieldName = fgFieldName
                            else:
                                raise IkValidateException('Field [%s] is incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (
                                    tableHfRowField.fieldName, fgName, screen.id))
                elif totalFields < totalFgFields:
                    # the field name is mandatory if total fields is not the same as total fields defined in fields table.
                    fgFieldNames = [field.name for field in fg.fields]
                    for i in range(len(tableHf.fields)):
                        tableHfRowField = tableHf.fields[i]
                        if tableHfRowField.fieldName not in fgFieldNames:
                            raise IkValidateException('Field [%s] is incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (
                                tableHfRowField.fieldName, fgName, screen.id))
                else:
                    raise IkValidateException(
                        'Total fields s incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (fgName, screen.id))
                # update field group's header and footer
                for fgField in fg.fields:
                    tableHfRow = tableHf.getField(fgField.name)
                    if tableHfRow is not None:
                        totalHeaderRows = tableHf.getTotalHeaderRows()
                        headerCaptions = tableHfRow.headers
                        if len(headerCaptions) > 0:
                            if not (len(headerCaptions) == 1 and isNullBlank(headerCaptions[0])):
                                fgField.caption = headerCaptions
                        footer = tableHfRow.footer
                        if not isNullBlank(footer):
                            fgField.footer = footer
        return screen  # end of getScreen
    

