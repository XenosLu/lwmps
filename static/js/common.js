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
            dlna_on: false,
            dlnashow: false,
            history_show: true,
            history: [],
            filelist: [],
        },
        methods: {
            test: function (obj) {
                console.log("test " + obj);
            },
            play: function (obj) {
                if (window.document.location.pathname == "/dlna")
                    get("/dlna/load/" + obj);
                else
                    window.location.href = "/wp/play/" + obj;
            },
            remove: function (obj) {
                if (confirm("Clear history of " + obj + "?"))
                    history("/hist/rm/" + obj.replace(/\?/g, "%3F")); //?to%3F #to%23
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


var RANGE = 12; //minimum touch move range in px
var hide_sidebar = 0;

window.onload = adapt;
window.onresize = adapt;
var isiOS = !!navigator.userAgent.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
if (!isiOS)
    $(document).mousemove(showSidebar);

check_dlna_state();

function showSidebar() {
    $("#sidebar").show();
    clearTimeout(hide_sidebar);
    hide_sidebar = setTimeout('$("#sidebar").hide()', 3000);
}

//buttons
$("#clear").click(function () {
    if (confirm("Clear all history?"))
        history("/hist/clear");
});

// Dialog open/close toggle buttons
//$("#history").click(toggleDialog);
//$(".close").click(toggleDialog);

//table buttons
$("#tabFrame").on("click", ".folder", function () {
    filelist("/fs/ls/" + this.title + "/");
}).on("click", ".move", function () {
    if (confirm("Move " + this.title + " to .old?")) {
        filelist("/fs/move/" + this.title);
    }
}).on("click", ".remove", function () {
    if (confirm("Clear history of " + this.title + "?"))
        history("/hist/rm/" + this.title.replace(/\?/g, "%3F"));  //?to%3F #to%23
}).on("click", ".mp4", function () {
    if (window.document.location.pathname == "/dlna")
        get("/dlna/load/" + this.title);
    else
        window.location.href = "/wp/play/" + this.title;
}).on("click", ".video", function () {
    if (window.document.location.pathname == "/dlna")
        get("/dlna/load/" + this.title);
});

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
 * Show Dialog
 *
 * @method showDialog
 * to be delete
 */
function showDialog() {
    if ($("#navtab li:eq(0)").attr("class") == "active")
        history("/hist/ls");
    $("#history").addClass("active");
    $("#dialog").show(250);
}

/**
 * Toggle Dialog open/close
 *
 * @method toggleDialog
 */
function toggleDialog() {
    if ($("#history").hasClass("active")) {
        $("#history").removeClass("active");
        $("#dialog").hide(250);
    } else {
        if ($("#navtab li:eq(0)").attr("class") == "active")
            history("/hist/ls");
        $("#history").addClass("active");
        $("#dialog").show(250);
    }
}

/**
 * Auto adjust video size and dialog hieght
 *
 * @method adapt
 */
function adapt() {
    $("#tabFrame").css("max-height", ($(window).height() - 240) + "px");
    if ($("video").length == 1) {
        $("#videosize").text("orign");
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

function renderFilelist(data) {
    window.commonView.history_show = false;
    window.commonView.filelist = data.filesystem;
    /*
    if ($("#navtab li:eq(1)").attr("class") != "active")
        $("#navtab li:eq(1) a").tab("show");
    $("#clear").hide();
    var html = "";
    var icon = {
        "folder": "folder-close",
        "mp4": "film",
        "video": "film",
        "other": "file"
    };
    $.each(data["filesystem"], function (i, n) {
        var size = "";
        if (n["size"])
            size = "<br><small>" + n["size"] + "</small>";
        var td = new Array(3);
        td[0] = '<td><i class="glyphicon glyphicon-' + icon[n["type"]] + '"></i></td>';
        td[1] = '<td class="filelist ' + n["type"] + '" title="' + n["path"] + '">' + n["filename"] + size + "</td>";
        td[2] = '<td class="move" title="' + n["path"] + '">' + '<i class="glyphicon glyphicon-remove-circle"></i></td>';
        html += "<tr>" + td.join("") + "</tr>";
    });
    $("#list").empty().append(html);
    */
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
        success: renderFilelist,
        error: function (xhr) {
            out(xhr.statusText);
        }
    });
}

function renderHistory(data) {
    window.commonView.history_show = true;
    window.commonView.history = data.history;
    /*
    if (!$("#navtab li:eq(0)").hasClass("active"))
        $("#navtab li:eq(0) a").tab("show");
    $("#clear").show();
    var html = "";
    
    $.each(data["history"], function (i, n) {
        var mediaType = "";
        if (n["exist"]) {
            mediaType = "video";
            if ((n["filename"]).lastIndexOf('.mp4') > 0)
                mediaType = "mp4";
        }
        var td = new Array();
        td[0] = '<td class="folder" title="' + n["path"] + '">' + '<i class="glyphicon glyphicon-folder-close"></i></td>';
        td[1] = '<td><i class="glyphicon glyphicon-film"></i></td>';
        td[2] = '<td class="filelist ' + mediaType + '" title="' + n["filename"] + '">' + n["filename"] + "<br><small>" + n["latest_date"] + " | " + secondToTime(n["position"]) + "/" + secondToTime(n["duration"]) + "</small></td>";
        td[3] = '<td class="remove" title="' + n["filename"] + '">' + '<i class="glyphicon glyphicon-remove-circle"></i>' + "</td>";
        //td[4] = '<td class="next" title="' + n["filename"] + '"><i class="glyphicon glyphicon-step-forward"></i></td>';
        html += "<tr>" + td.join("") + "</tr>";
    });
    $('#list').empty().append(html);*/
}

/**
 * Render history list box from ajax
 *
 * @method history
 * @param {String} str
 */
function history(str) {
    $.ajax({
        url: encodeURI(str),
        dataType: "json",
        timeout: 1999,
        type: "get",
        success: renderHistory,
        error: function (xhr) {
            out(xhr.statusText);
        }
    });
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

function check_dlna_state() {
    $.ajax({
        url: "/dlna/info",
        dataType: "json",
        timeout: 999,
        type: "GET",
        success: function (data) {
            window.commonView.dlna_on = !$.isEmptyObject(data);
            /*
            if ($.isEmptyObject(data)) {
                $("#dlna_toggle").removeClass("btn-success");
            } else {
                $("#dlna_toggle").addClass("btn-success");
            }
            */
        },
        error: function (xhr, err) {
            console.log('get dlna/info error')
        }
    });
}
