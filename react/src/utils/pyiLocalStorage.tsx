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

    // dialog type
    DIALOG_TYPE_NORMAL: "normal",
    DIALOG_TYPE_HTML: "html",
    DIALOG_TYPE_UPLOAD: "upload",
    DIALOG_TYPE_HOME_INBOX: "homeInbox",

    // button type
    BTN_TYPE_NORMAL: "normal",
    BTN_TYPE_UPLOAD: "upload",
    BTN_TYPE_DOWNLOAD: "download",

    // button type in table
    TABLE_BTN_TYPE_NORMAL: "normal",
    TABLE_BTN_TYPE_DIALOG: "dialog",
    TABLE_BTN_TYPE_SWITCH: "switch",
    TABLE_BTN_TYPE_PDF: "pdf",
    TABLE_BTN_TYPE_UPLOAD: "upload",
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
    SUBMENU_DISPLAY_MODE: 'click'
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
    window.localStorage.setItem("sysMsgs", JSON.stringify(sysMsgArr))
  },
  getSysMsgs: () => {
    return window.localStorage.getItem("sysMsgs")
  },
  clearSysMsgs: () => {
    window.localStorage.setItem("sysMsgs", null)
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
