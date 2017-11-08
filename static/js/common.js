var RANGE = 12;  //minimum touch move range in px
var text = "";  //temp output text


window.onload = adapt;
window.onresize = adapt;
//$(window).resize(adapt);
$(document).mousemove(showSidebar);

$("#history").click(showDialog);

$("#clear").click(function () {
    if (confirm("Clear all history?"))
        history("/clear");
});

//dialog close button
$(".close").click(function () {
    $("#dialog").hide(250);
});

//table buttons
$("#tabFrame").on("click", ".folder", function () {
    filelist("/fs" + this.title + "/");
}).on("click", ".move", function () {
    if (confirm("Move " + this.title + " to old?")) {
        filelist("/move/" + this.title);
    }
}).on("click", ".remove", function () {
    if (confirm("Clear " + escape(this.title) + "?"))
        history("/remove/" + escape(this.title));
}).on("click", ".mp4", function () {
    if (window.document.location.pathname == "/dlna")
        dlnaLoad(this.title);
    else
        window.location.href = "/play/" + this.title;
}).on("click", ".video", function () {
    if (window.document.location.pathname == "/dlna")
        dlnaLoad(this.title);
}).on("click", ".dlna", function () {
    dlnaLoad(this.title);
});

/**
 * Load media through DLNA
 *
 * @method dlnaLoad
 * @param {String} media
 */
function dlnaLoad(media) {
    $.get("/dlnaload/" + media, function () {
        out("Loaded.");
    });
}

function showSidebar() {
    //$("#sidebar").show(600).delay(9999).hide(300);
}

/**
 * Show Dialog
 *
 * @method showDialog
 */
function showDialog() {
    if ($("#navtab li:eq(0)").attr("class") == "active")
        history("/list");
    $("#dialog").show(250);
}

/**
 * Auto adjust video size and dialog hieght
 *
 * @method adapt
 */
function adapt() {
    $("#videosize").text("orign");
    $("#tabFrame").css("max-height", ($(window).height() - 240) + "px");
    if (!isNaN($("video").get(0).duration)) {
    // if (!isNaN($("video").get(0))) {
    // if (!isNaN($("video"))) {
        var video_ratio = $("video").get(0).videoWidth / $("video").get(0).videoHeight;
        var page_ratio = $(window).width() / $(window).height();
        if (page_ratio < video_ratio) {
            $("video").get(0).style.width = $(window).width() + "px";
            $("video").get(0).style.height = Math.floor($(window).width() / video_ratio) + "px";
        } else {
            $("video").get(0).style.width = Math.floor($(window).height() * video_ratio) + "px";
            $("video").get(0).style.height = $(window).height() + "px";
        }
    }
}

$(document).on("touchstart", function (e) {
    var x0 = e.originalEvent.touches[0].screenX;
    var y0 = e.originalEvent.touches[0].screenY;
});
$(document).on("touchmove", function (e) {
    var x = e.changedTouches[0].screenX - x0;
    var y = e.changedTouches[0].screenY - y0;
    if (Math.abs(y / x) < 0.25) {
        if (Math.abs(x) > RANGE) {
            time = Math.floor(x / 11);
            //out(time);
            if (!isNaN($("video").get(0).duration)) {
                if (time > 0) {
                    time = Math.min(60, time);
                } else if (time < 0) {
                    time = Math.max(-60, time);
                }
            }
        }
    }
});
$(document).on("touchend", function (e) {
    var x = e.changedTouches[0].screenX - x0;
    var y = e.changedTouches[0].screenY - y0;
    if (Math.abs(y / x) < 0.25) {
        if (Math.abs(x) > RANGE) {
            time = Math.floor(x / 11);
            if (!isNaN($("video").get(0).duration)) {
                if (time > 0) {
                    time = Math.min(60, time);
                    text = time + "S>><br>";
                } else if (time < 0) {
                    time = Math.max(-60, time);
                    text = "<<" + -time + "S<br>";
                }
                $("video").get(0).currentTime += time;
            }
        }
    } else
        showSidebar();
});

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
            $.each(data, function (i, n) {
                var size = "";
                if (n["size"])
                    size = "<br><small>" + n["size"] + "</small>";
                var dlna = "";
                if (icon[n["type"]] === "film")
                    dlna = ' class="dlna" title="' + n["path"] + '"';
                var download_link = "";
                if(icon[n["type"]]==="film")
                    download_link = '<a href="/video/' + n["path"] + '" class="glyphicon glyphicon-download-alt"></a>';                
                var td = new Array(4);
                td[0] = "<td" + dlna + '><i class="glyphicon glyphicon-' + icon[n["type"]] + '"></i></td>';
                td[1] = "<td>" + download_link + "</td>";
                td[2] = '<td class="filelist ' + n["type"] + '" title="' + n["path"] + '">' + n["filename"] + size + "</td>";
                td[3] = '<td class="move" title="' + n["path"] + '">' +'<i class="glyphicon glyphicon-remove-circle"></i></td>';
                html += "<tr>" + td.join("") + "</tr>";
            });
            $("#list").empty().append(html);
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
function history(str) {
    $.ajax({
        url: encodeURI(str),
        dataType: "json",
        timeout: 1999,
        type: "get",
        success: function (data) {
            if ($("#navtab li:eq(0)").attr("class") != "active")
                $("#navtab li:eq(0) a").tab("show");
            $("#clear").show();
            var html = "";
            $.each(data, function (i, n) {
                var mediaType;
                if ((n["filename"]).lastIndexOf('.mp4') > 0)
                    mediaType = "mp4";
                else
                    mediaType = "video";
                html += '<tr><td class="folder" title="/' + n["path"] + '">' +
                '<i class="glyphicon glyphicon-folder-close"></i>' +
                "</td>" +
                '<td class="dlna" title="' + n["filename"] + '">' +
                '<i class="glyphicon glyphicon-film"></i>' +
                "</td>" +
                '<td class="filelist '+ mediaType + '" title="' + n["filename"] + '">' + n["filename"] +
                "<br><small>" + n["latest_date"] + " | " +
                secondToTime(n["position"]) + "/" + secondToTime(n["duration"]) + "</small>" +
                "</td>" +
                '<td class="remove" title="' + n["filename"] + '">' +
                '<i class="glyphicon glyphicon-remove-circle"></i>' +
                "</td></tr>";
            });
            $('#list').empty().append(html);
        },
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
        $(document.body).append("<div id='output'>" + text + "</div>");
        $("#output").fadeTo(250, 0.7).delay(1800).fadeOut(625);
    };
}
