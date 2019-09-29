// ==UserScript==
// @name PickTrueBrowser
// @author winkidney@gmail.com
// @version 0.0.1
// @namespace tools
// @description A tool to get meta info form ArtStation within browser to provide downloading service.
// @match *://www.artstation.com/*
// @grant GM_xmlhttpRequest
// @require https://code.jquery.com/jquery-1.12.4.min.js
// @run-at context-menu
// @updateURL https://github.com/winkidney/PickTrue/raw/master/artstation.user.js
// ==/UserScript==
let utils = {
  isFirefox: function () {
    return (navigator.userAgent.indexOf("Firefox") !== -1)
  },
  isChrome: function () {
    return (navigator.userAgent.indexOf("Chrome") !== -1)
  }
};

let logger = {
  info: function(...args) {
    console.log("[PickTrue]: ", ...args);
  }
};

let Artstation = function () {
  function _parseUserId(rawUrl) {
    var urlArray = rawUrl.split("/");
    var userId = urlArray[urlArray.length - 1];
    return userId;
  }

  function fetchUrl(url, callback) {
    logger.info("Fetching url:", url);
    return $.get(url, callback);
  }

  function _getUrl(userId, page) {
    return "https://www.artstation.com/users/" + userId + "/projects.json?page=" + page;
  }

  return {
    getPage: _getUrl,
    fetchUrl: fetchUrl,
  }
};

let RequestProxy = function () {
  let client = Artstation();

  function submitTask(respData, callback) {
    logger.info("Submit response:", respData);
    let request_data = JSON.stringify(respData);
    let details = {
      url: "http://localhost:2333/tasks/submit/",
      data: request_data,
      method: "POST",
      onloadend: function (data) {
        logger.info("Submit response done: ", data);
        callback()
      },
    };
    return GM_xmlhttpRequest(details);
  }
  function getTask() {
    let details = {
      url: "http://localhost:2333/tasks/",
      method: "GET",
      onloadend: function (resp) {
        logger.info("Get task: ", resp);
        let data = JSON.parse(resp.responseText);
        if (data.length <= 0){
          return getTask()
        } else {
          client.fetchUrl(
            data[0],
            function (respData) {
              submitTask(respData, getTask)
            },
          )
        }
      },
    };
    return GM_xmlhttpRequest(details);
  }
  return {
    getTask: getTask,
    submitTask: submitTask,
  };
};

function entry() {
  alert("请确保已经启动了PickTrue客户端。将要解析当前用户的所有图集并将下载地址发送PickTrue下载器，确认后将立即开始。");
  let proxy = RequestProxy();
  proxy.getTask();
}

function _setUpContextMenuFirefox(entryFn) {
  var menu = document.body.appendChild(document.createElement("menu"));
  var html = document.documentElement;
  if (html.hasAttribute("contextmenu")) {
    // We don't want to override web page context menu if any
    var contextmenu = $("#" + html.getAttribute("contextmenu"));
    contextmenu[0].appendChild(menu); // Append to web page context menu
  } else {
    html.setAttribute("contextmenu", "userscript-picktrue-context-menu");
  }

  menu.outerHTML = '<menu id="userscript-picktrue-context-menu"\
                          type="context">\
                      <menuitem id="userscript-picktrue-menuitem"\
                                label="发送相册到PickTrue并下载">\
                      </menuitem>\
                    </menu>';

  if ("contextMenu" in html && "HTMLMenuItemElement" in window) {
    var menuitem = $("#userscript-picktrue-menuitem")[0];
    menuitem.addEventListener("click", entryFn, false);
  }
}

function _setUpContextMenuChrome(entryFn) {
  $(document).on("contextmenu", function (e) {
    if (e.ctrlKey){
      entryFn()
    }
  });
}

function setUpContextMenu(entryFn) {
  if (utils.isFirefox()) {
    _setUpContextMenuFirefox(entryFn);
  } else if (utils.isChrome()) {
    _setUpContextMenuChrome(entryFn);
  } else {
    alert("Unsupported browser " + navigator.userAgent);
  }
}

setUpContextMenu(entry);
