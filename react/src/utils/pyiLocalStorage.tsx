const pyiLocalStorage = {
  globalParams: {
    // url info
    API_URL: getApiUrl(), //"http://localhost:8000",
    IMAGE_URL: getApiUrl() + "/images", // "http://localhost:8000/images",
    PUBLIC_URL: getPublicUrl() + "/static/",

    // open screen
    OPEN_SCREEN_KEY_NAME: "OPEN_SCREEN",
    ACTION_COMMAND: "__CMD",

    //  sub screen
    SUB_SCREEN_KEY_NAME: "SUB_SCREEN_NAME",

    // rsa info
    RSA_PUBLIC_KEY: "RSA_PUBLIC_KEY",
    RSA_PRIVATE_KEY: "RSA_PRIVATE_KEY",

    // component info
    TREE_TYPE: "tree",
    SEARCH_TYPE: "search",
    SIMPLE_TYPE: "fields",
    TABLE_TYPE: "table",
    TABLE_TYPE_RESULT: "resultTable",
    ICON_BAR: "iconBar",
    VIEWER: "viewer",
    IFRAME: "iframe",
    HTML: "html",
    SITE_PLAN: "sitePlan",
    TABLE_PRIMARY_KEY: "__PK_",
    TABLE_ROW_ID: "__KEY_",
    TABLE_ROW_STATUS: "__STT_",
    SELECTABLE_TABLE_ROW_STATUS: "__SLT_",
    PLUGIN_ACTIVE_STATUS: "__CRR_",

    // field type
    FIELD_TYPE_LABEL: "label",
    FIELD_TYPE_TEXT_BOX:'textbox',
    FIELD_TYPE_TEXTAREA:'textarea',
    FIELD_TYPE_PASSWORD:'password',
    FIELD_TYPE_DATE_BOX:'datebox',
    FIELD_TYPE_COMBO_BOX: "combobox",
    FIELD_TYPE_LIST_BOX: "listbox",
    FIELD_TYPE_ADVANCED_COMBOBOX: "advancedcombobox",
    FIELD_TYPE_ADVANCED_SELECTION: "advancedselection",
    FIELD_TYPE_CHECK_BOX: "checkbox",
    FIELD_TYPE_BUTTON: "button",
    FIELD_TYPE_ICON_AND_TEXT: "iconandtext",
    FIELD_TYPE_FILE: "file",
    FIELD_TYPE_PLUGIN: "plugin",
    FIELD_TYPE_HTML: "html",

    // dialog type
    DIALOG_TYPE_NORMAL: "normal",
    DIALOG_TYPE_UPLOAD: "upload",
    DIALOG_TYPE_HOME_INBOX: "homeInbox",

    // button type
    BTN_TYPE_NORMAL: "normal",
    BTN_TYPE_UPLOAD_DIALOG: "uploadDialog",
    BTN_TYPE_UPLOAD_BUTTON: "uploadButton",
    BTN_TYPE_DOWNLOAD: "download",

    // button type in table
    TABLE_BTN_TYPE_NORMAL: "normal",
    TABLE_BTN_TYPE_DIALOG: "dialog",
    TABLE_BTN_TYPE_SWITCH: "switch",
    TABLE_BTN_TYPE_PDF: "pdf",
    TABLE_BTN_TYPE_UPLOAD: "uploadDialog",
    TABLE_BTN_TYPE_DOWNLOAD: "download",

    // selection mode
    SELECTION_MODE_SINGLE: "single",
    SELECTION_MODE_MULTIPLE: "multiple",

    // pagetype
    CLIENT_PAGING: "client",
    SERVER_PAGING: "server",

    // cookie info
    // menu
    COOKIE_MENU_ID: "PYI_USER_SELECTED_MENU_ID",
    COOKIE_MENU_ACTION: "PYI_USER_SELECTED_MENU_ACTION",
    // for system help
    COOKIE_SYS_SUPPORT_SESSION: "__SYS_SUPPORT_SESSION__",
    SCREEN_FIELD_GROUP_DATA: "fgData",
    SCREEN_FIELD_GROUP_DATA_STYLE: "fgDataStyle",

    PAGE_MAX_ROWS: 1000,

    HTTP_TYPE_GET: "GET",
    HTTP_TYPE_POST: "POST",
    HTTP_TYPE_DELETE: "DELETE",
    HTTP_TYPE_POST_NO_HEADER: "POST_NO_HEADER",
    HTTP_TYPE_DOWNLOAD: "DOWNLOAD",

    // How to manipulate the secondary menu to display the tertiary menu.
    // Values: click/hover. Default to click.
    SUBMENU_DISPLAY_MODE: "click",
  },

  // cookie info
  setCurrentUser: (userName: string) => {
    if (!userName) return
    window.localStorage.setItem("currentUser", userName)
  },
  getCurrentUser: () => {
    return window.localStorage.getItem("currentUser")
  },
  setToken: (token: string) => {
    if (!token) return
    if (typeof token !== "string") {
      token = JSON.stringify(token)
    }
    window.localStorage.setItem("token", token)
  },
  getToken: () => {
    return window.localStorage.getItem("token")
  },
  setSysMsgs: (sysMsg: Array<Object>) => {
    if (!sysMsg) return
    var sysMsgStr = pyiLocalStorage.getSysMsgs()
    var sysMsgArr
    if (sysMsgStr === null || sysMsgStr === "null") {
      sysMsgArr = []
    } else {
      sysMsgArr = JSON.parse(sysMsgStr)
    }
    sysMsgArr.push(sysMsg)

    const screenID = getScreenIDByUrl()
    window.localStorage.setItem(screenID + "_sysMsgs", JSON.stringify(sysMsgArr))
  },
  getSysMsgs: () => {
    const screenID = getScreenIDByUrl()
    return window.localStorage.getItem(screenID + "_sysMsgs")
  },
  clearSysMsgs: () => {
    const screenID = getScreenIDByUrl()
    window.localStorage.setItem(screenID + "_sysMsgs", null)
  },
  clearStore: () => {
    window.localStorage.clear()
  },
}
export default pyiLocalStorage

function getApiUrl() {
  let href = window.location.href
  let items = href.split("/")
  let hostPort = items[2].split(":")
  let host = hostPort[0]
  let port = "80"
  if (hostPort.length > 1) {
    port = hostPort[1]
  }
  if (port === "3000") {
    port = "8000" // for developing
  }
  return items[0] + "//" + host + (port === "80" ? "" : ":" + port)
}

function getPublicUrl() {
  return window.location.origin
}

function getScreenIDByUrl() {
  const href = window.location.href
  const parts = href.split('?');
  const screenID = parts[0].split('/').pop()
  return screenID
}