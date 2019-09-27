// ==UserScript==
// @name PickTrueBrowser
// @namespace Violentmonkey Scripts
// @match *://www.artstation.com/*
// @grant GM_xmlhttpRequest
// @require https://cdn.bootcss.com/axios/0.19.0/axios.min.js
// @run-at          context-menu
// ==/UserScript==

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
  // alert("请确保已经启动了PickTrue客户端。将要解析当前用户的所有图集并将下载地址发送PickTrue下载器，确认后将立即开始。");
  let proxy = RequestProxy();
  proxy.getTask();
}

function setUpContextMenu(entryFn) {
  var menu = document.body.appendChild(document.createElement("menu"));
  var html = document.documentElement;
  if (html.hasAttribute("contextmenu")) {
    // We don't want to override web page context menu if any
    var contextmenu = $("#" + html.getAttribute("contextmenu"));
    contextmenu.appendChild(menu); // Append to web page context menu
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

setUpContextMenu(entry);
