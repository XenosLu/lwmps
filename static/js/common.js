"use strict";
var icon = {
    "folder": "oi oi-folder",
    "mp4": "oi oi-video",
    "video": "oi oi-video",
    "other": "oi oi-file"
};

window.commonView = new Vue({
        delimiters: ['${', '}'],
        el: '#v-common',
        data: {
            icon: icon,
            swipeState: 0,
            uiState: {
                modalShow: false,
                dlnaOn: false,
                dlnaShow: false,
                historyShow: true,
                rateMenu: false,
                fixBarShow: true,
                videoBtnText: 'origin',
            },
            history: [],
            filelist: [],
        },
        methods: {
            test: function (obj) {
                console.log("test " + obj);
            },
            showModal: function () {
                this.uiState.modalShow = true;
                if (this.uiState.historyShow)
                    this.showHistory();
            },
            showHistory: function () {
                getHistory("/hist/ls");
            },
            showFs: function (path) {
                filelist(path);
            },
            clearHistory: function () { // clear history button
                if (confirm("Clear all history?"))
                    getHistory("/hist/clear");
            },
            play: function (obj) {
                if (window.document.location.pathname == "/dlna")
                    get("/dlna/load/" + obj);
                else
                    window.location.href = "/wp/play/" + obj;
            },
            remove: function (obj) {
                if (confirm("Clear history of " + obj + "?"))
                    getHistory("/hist/rm/" + obj.replace(/\?/g, "%3F")); //?to%3F #to%23
            },
            move: function (obj) {
                if (confirm("Move " + obj + " to .old?")) {
                    filelist("/fs/move/" + obj);
                }
            },
            open: function (obj, type) {
                switch (type) {
                case "folder":
                    filelist("/fs/ls/" + obj + "/");
                    break;
                case "mp4":
                    if (window.document.location.pathname == "/dlna")
                        get("/dlna/load/" + obj);
                    else
                        window.location.href = "/wp/play/" + obj;
                    break;
                case "video":
                    if (window.document.location.pathname == "/dlna")
                        get("/dlna/load/" + obj);
                    break;
                default:
                }
            },
        },
    });

var hammertimeModal = new Hammer(document.getElementById("ModalTouch"));

hammertimeModal.on("swipeleft", function (ev) {
    window.commonView.swipeState -= 1;
    if (window.commonView.swipeState < -1)
        window.commonView.swipeState = -1;
});
hammertimeModal.on("swiperight", function (ev) {
    window.commonView.swipeState += 1;
    if (window.commonView.swipeState > 1)
        window.commonView.swipeState = 1;
});
hammertimeModal.add( new Hammer.Press({time: 1000 }) )
hammertimeModal.on("press", function (ev) {
    out("press");
    var target;
    if(ev.target.tagName=='TD')
        target = ev.target;
    else
        target = ev.target.parentNode;
    // console.log(target);
    if(target.hasAttribute("data-target"))
        window.commonView.open(target.getAttribute('data-target'), 'folder')
    console.log(target.getAttribute('data-target'));
});

var RANGE = 12; //minimum touch move range in px
var hide_sidebar = 0;

window.onload = adapt;
window.onresize = adapt;
var isiOS = !!navigator.userAgent.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
if (!isiOS) {
    window.commonView.uiState.fixBarShow = false;
    $(document).mousemove(showSidebar);
}
check_dlna_state();

function showSidebar() {
    window.commonView.uiState.fixBarShow = true;
    clearTimeout(hide_sidebar);
    hide_sidebar = setTimeout('window.commonView.uiState.fixBarShow = false;', 3000);
}

//window.commonView.showModal();  // show modal at start


/**
 * Ajax get and out result
 *
 * @method get
 * @param {String} url
 */
function get(url) {
    console.log('get');
    $.get(url, out);
}

/**
 * Auto adjust video size
 *
 * @method adapt
 */
function adapt() {
    if ($("video").length == 1) {
        window.commonView.uiState.videoBtnText = "orign";
        var video_ratio = $("video").get(0).videoWidth / $("video").get(0).videoHeight;
        var page_ratio = $(window).width() / $(window).height();
        if (page_ratio < video_ratio) {
            var width = $(window).width() + "px";
            var height = Math.floor($(window).width() / video_ratio) + "px";
        } else {
            var width = Math.floor($(window).height() * video_ratio) + "px";
            var height = $(window).height() + "px";
        }
        $("video").get(0).style.width = width;
        $("video").get(0).style.height = height;
    }
}

/**
 * Render file list box from ajax
 *
 * @method filelist
 * @param {String} str
 */
function filelist(str) {
    $.ajax({
        url: encodeURI(str),
        dataType: "json",
        timeout: 1999,
        type: "get",
        success: function (data) {
            window.commonView.uiState.historyShow = false;
            window.commonView.filelist = data.filesystem;
        },
        error: function (xhr) {
            out(xhr.statusText);
        }
    });
}

/**
 * Render history list box from ajax
 *
 * @method history
 * @param {String} str
 */
function getHistory(str) {
    $.ajax({
        url: encodeURI(str),
        dataType: "json",
        timeout: 1999,
        type: "get",
        success: function (data) {
            window.commonView.uiState.historyShow = true;
            window.commonView.history = data.history;
        },
        error: function (xhr) {
            out(xhr.statusText);
        }
    });
}

function check_dlna_state() {
    $.ajax({
        url: "/dlna/info",
        dataType: "json",
        timeout: 999,
        type: "GET",
        success: function (data) {
            window.commonView.uiState.dlnaOn = !$.isEmptyObject(data);
        },
        error: function (xhr, err) {
            console.log('get dlna/info error')
        }
    });
}

/**
 * Made an output box to show some text notification
 *
 * @method out
 * @param {String} text
 */
function out(text) {
    if (text != "") {
        $("#output").remove();
        $(document.body).append('<div id="output">' + text + "</div>");
        $("#output").fadeTo(250, 0.7).delay(1800).fadeOut(625);
    };
}

/**
 * Convert Second to Time Format
 *
 * @method secondToTime
 * @param {Integer} time
 * @return {String}
 */
function secondToTime(time) {
    return ("0" + Math.floor(time / 3600)).slice(-2) + ":" +
    ("0" + Math.floor(time % 3600 / 60)).slice(-2) + ":" + (time % 60 / 100).toFixed(2).slice(-2);
}

/**
 * Convert Time format to seconds
 *
 * @method timeToSecond
 * @param {String} time
 * @return {Integer}
 */
function timeToSecond(time) {
    var t = String(time).split(":");
    return (parseInt(t[0]) * 3600 + parseInt(t[1]) * 60 + parseInt(t[2]));
}
