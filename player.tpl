﻿<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=0.75, maximum-scale=1.0, user-scalable=1">
<title>{{title}}</title>
<link href="static/css/bootstrap.min.css" rel="stylesheet">
<style>
/*** modified bootstrap style ***/
.glyphicon-film, .glyphicon-folder-close, .glyphicon-remove-circle, .glyphicon-file, .glyphicon-list-alt, .caret {
  font-size: 1.8em;
}
.glyphicon-remove-circle {
    color: grey;
}
.close {
  font-size: 2.5em;
  margin-right: 0.25em;
  margin-top: 0.05em;
}
.dropdown-menu {
  opacity: 0.75;
  min-width: 6em;
}
.breadcrumb {
  background: 0 0;
  margin: 0;
  font-size: 1.2em;
}
.table > tbody > tr > td {
  vertical-align: middle;
}
/*** modified bootstrap style ***/
html, body {
  /*height: 100%;*/
}
body {
  background-color: #F1F2F6; /* #DDD9DD #101010; */
  -webkit-user-select: none;
  -moz-user-select: none;
  user-select: none;
  font-family: AppleSDGothicNeo-Regular;
}
a {
  cursor: default;
}
div {
  text-align: center;
}
td:hover {
  background: #EEEEF3;
}
video {
  /*clear: both;*/
  display: block;
  margin: auto;
}
.filelist {
  min-width: 14em;
}
.filelist.other {
  color: grey;
}
#sidebar{
  opacity: 0;
  position: fixed;
  top: 40%;
}
#output {
  z-index: 99;
  font-size: 1.8em;
  pointer-events: none;
  border-radius: 0.2em;
  padding: 0.2em;
  opacity: 0.7;
  border: 1px solid #777777;
  box-shadow: 0.5em 0.5em 6em #AAAAAA inset;
  text-shadow: 0.1em 0.1em 0.4em #666;
}
#dialog {
  opacity: 0.8;
  box-shadow: 2px 2px 5px #333333;
  max-width: 100%;
}
#output, #dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  -webkit-transform: translate(-50%, -50%);
}
#mainframe {
  overflow: auto;
  min-height: 9em;
  min-width: 18em;
  width: 100%;
}
</style>
</head>
<body>
<div id="sidebar">
  <button id="history" type="button" class="btn btn-default">
    <i class="glyphicon glyphicon-list-alt"></i>
  </button>
</div>
<div id="dialog" style="display:none">
  <div class="bg-info">
  <button onClick="$('#dialog').hide();" type="button" class="close">&times;</button>
    <ul id="navtab" class="nav nav-tabs">
      <li class="active">
        <a href="#mainframe" data-toggle="tab" onclick="history('list')">
          <i class="glyphicon glyphicon-list"></i>History
        </a>
      </li>
      <li>
        <a href="#mainframe" data-toggle="tab" onclick="tabshow('/', 1)">
          <i class="glyphicon glyphicon-home"></i>Home dir
        </a>
      </li>
    </ul>
  </div>
  <div id="mainframe" class="tab-pane fade in bg-warning">
    <table class="table">
      <tbody id="list">
      </tbody>
    </table>
    
  </div>
  <div class="panel-footer">
    <button id="videosize" onClick="videosizetoggle()" type="button" class="btn btn-default">orign</button>
    <div id="rate" class="btn-group dropup">
      <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
        Rate<span class="caret"></span>
      </button>
      <ul class="dropdown-menu" role="menu">
        <li><a href="#" onclick="rate(0.5)">0.5X</a></li>
        <li><a href="#" onclick="rate(0.75)">0.75X</a></li>
        <li class="divider"/>
        <li><a href="#" onclick="rate(1)">1X</a></li>
        <li class="divider"/>
        <li><a href="#" onclick="rate(1.5)">1.5X</a></li>
        <li><a href="#" onclick="rate(2)">2X</a></li>
      </ul>
    </div>
    <button id="clear" type="button" class="btn btn-default">Clear History</button>
    <div class="btn-group dropup">
      <button type="button" class="btn btn-default" onClick="if(confirm('Suspend ?'))$.get('/suspend.php');">
        <i class="glyphicon glyphicon-off"></i>
      </button>
      <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
        <span class="caret"></span>
      </button>
      <ul class="dropdown-menu" role="menu">
        <li>
          <a onClick="if(confirm('Shutdown ?'))$.get('/shutdown.php');">
          <i class="glyphicon glyphicon-off"></i>shutdown</a>
        </li>
      </ul>
    </div>
  </div>
</div>
</body>
<script src="static/js/jquery-3.2.1.min.js"></script>
<script src="static/js/bootstrap.min.js"></script>
<script language="javascript">
var RANGE = 12; //minimum touch move range in px
var text="";
//var lastsavetime = 0;//in seconds
var lastplaytime = 0;//in seconds

$("#history").click(function () {
    if ($('#navtab li:eq(0)').attr('class') == 'active')
        history("list");
    $('#dialog').show();
});

window.onload = adapt;
$(window).resize(function () {
    adapt();
});
$(document).mousemove(function () {
    showsidebar();
});
if (("{{src}}"=="")) {
    history("list");
    $("#dialog").show();
    $("#videosize").hide();
    $('#rate').hide();
} else {
    $(document.body).append("<div><video poster controls preload='auto'>No video support!</video></div>");//preload meta
    $("video").attr("src", "{{src}}");
    $("video").on("error", function () {
        out("error");
    });
    $("video").on("loadeddata", function () { //auto load progress
        $("video").get(0).currentTime = Math.max({{progress}} - 0.5, 0);
        text = "Play from<br>";
    });
    $("video").on("seeking", function () { //show progress when changed
        out(text + format_time($("video").get(0).currentTime) + '/' + format_time($("video").get(0).duration));
        text = "";
    });
    $("video").on("timeupdate", function () { //auto save play progress
        lastplaytime = new Date().getTime(); //to dectect if video is playing
        if ($("video").get(0).readyState == 4 && $("video").get(0).currentTime < $("video").get(0).duration + 1) {
            //if (Math.abs($("video").get(0).currentTime - lastsavetime) > 3) {//save play progress in every 3 seconds
            if (Math.floor(Math.random() * 99) > 81) { //randomly save play progress
                //lastsavetime = $("video").get(0).currentTime;
                //dict={src:"{{src}}",time:$("video").get(0).currentTime,duration:"&duration=" + $("video").get(0).duration};
                $.get("?action=save&src={{src}}&time=" + $("video").get(0).currentTime + "&duration=" + $("video").get(0).duration, function (data, status, xhr) {
                    if (xhr.statusText != "OK")
                        out(xhr.statusText);
                    xhr = null;
                });
            }
        }
    });
    $("video").on("progress", function () { //show buffered
        var str = "";
        if (new Date().getTime() - lastplaytime > 1000) {
            for (i = 0, t = $("video").get(0).buffered.length; i < t; i++) {
                if ($("video").get(0).currentTime >= $("video").get(0).buffered.start(i) && $("video").get(0).currentTime <= $("video").get(0).buffered.end(i))
                    str = format_time($("video").get(0).buffered.start(i)) + "-" + format_time($("video").get(0).buffered.end(i)) + "<br>";
            };
            out(str + "<small>buffering...</small>");
        };
    });
};

function showsidebar() {
    //$("#sidebar").stop(true).show().fadeTo(300,0.65).delay(3000).fadeOut(800);
    $("#sidebar").show().fadeTo(500, 0.35).delay(9999).fadeOut(800);
}
function rate(x) {
    out(x + "X");
    $("video").get(0).playbackRate = x;
}
function format_time(time) {
    return Math.floor(time / 60) + ":" + (time % 60 / 100).toFixed(2).slice(-2);
}
function playward(time) {
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
function videosizetoggle() {
    if ($("#videosize").text() == "auto")
        adapt();
    else {
        $("#videosize").text("auto");
        if ($("video").get(0).width < $(window).width() && $("video").get(0).height < $(window).height()) {
            $("video").get(0).style.width = $("video").get(0).videoWidth + "px";
            $("video").get(0).style.height = $("video").get(0).videoHeight + "px";
        }
    }
}
function adapt() {
    $("#videosize").text("orign");
    $("#mainframe").css("max-height", ($(window).height() - 200) + "px");
    if ($(window).height() <= 480)
        $("#dialog").width("100%");
    else
        $("#dialog").width("auto");
    video_ratio = $("video").get(0).videoWidth / $("video").get(0).videoHeight;
    page_ratio = $(window).width() / $(window).height();
    if (page_ratio < video_ratio) {
        $("video").get(0).style.width = $(window).width() + "px";
        $("video").get(0).style.height = Math.floor($(window).width() / video_ratio) + "px";
    } else {
        $("video").get(0).style.width = Math.floor($(window).height() * video_ratio) + "px";
        $("video").get(0).style.height = $(window).height() + "px";
    }
}

function out(str) {
    if (str != "") {
        $("#output").remove();
        $(document.body).append("<div id='output'>" + str + "</div>");
        $("#output").fadeTo(250, 0.7).delay(1800).fadeOut(625);
    };
}
$(document).on('touchstart', function (e) {
    x0 = e.originalEvent.touches[0].screenX;
    y0 = e.originalEvent.touches[0].screenY;
});
/*
$(document).on('touchmove',function(e) {//test function
    x = e.changedTouches[0].screenX - x0;
    y = e.changedTouches[0].screenY - y0;
    if (Math.abs(y / x) < 0.25) {
        if (Math.abs(x) > RANGE) {
            $("video").get(0).muted = true;
            $("video").get(0).playbackRate = 9 * x / Math.abs(x);
            window.clearInterval(int);
            var int = setInterval("out(text+format_time($('video').get(0).currentTime)+ '/' + format_time($('video').get(0).duration))", 50);
       }
    }
});
*/
$(document).on('touchend', function (e) {
    x = e.changedTouches[0].screenX - x0;
    y = e.changedTouches[0].screenY - y0;
    //$("video").get(0).playbackRate = 1;
    //$("video").get(0).muted = false;
    //window.clearInterval(int);
    if (Math.abs(y / x) < 0.25) {
        if (Math.abs(x) > RANGE) {
            playward(Math.floor(x / 11));
        }
    } else
        showsidebar();
/*
    if (Math.abs(y / x) < 0.25) {
        if (x > RANGE)
            playward(Math.floor(x / 11));
        else if (x < -RANGE)
            playward(Math.floor(x / 11));
    } else
        showsidebar();
*/
});
$("#mainframe").on("click", ".dir", function (e) {
    tabshow(e.target.title, 1);
});
$("#mainframe").on("click", ".move", function (e) {
    if (confirm("Move " + e.target.title + " to old?"))
        tabshow("?action=move&src=" + e.target.title, 1);
});
$("#mainframe").on("click", ".del", function (e) {
    if (confirm("Clear " + e.target.title + "?"))
        history("del&src=" + e.target.title);
});
$("#clear").on("click", function () {
    if (confirm("Clear all history?"))
        history("clear");
});

function tabshow(str, n) {
    $("#list").load(encodeURI(str), function (responseTxt, status, xhr) {
        if (xhr.statusText == "OK") {
            $("#navtab li:eq(" + n + ") a").tab("show");
            if(n==0) {
                //$("#clear").show();
                history("list");
            }
            else
                $("#clear").hide();
            }
        else
            out(xhr.statusText);
    });
}
function history(str) {
    $.getJSON("?action=" + str, function (data, status, xhr) {
        if (xhr.statusText == "OK") {
            $("#navtab li:eq(0) a").tab("show");
            $("#clear").show();
            var html = "";
            $.each(data, function (i, n) {
                html += "<tr>" + "<td class='dir' title='" + n["path"] + "'>" +
                "<i class='glyphicon glyphicon-film' title='" + n["path"]
                 + "'></i></td><td class='filelist'>" + "<a href='?src="
                 + n["filename"] + "'>" + n["filename"] + "</a><br><small>"
                 + n["latest_date"] + " | " + format_time(n["time"]) + "/"
                 + format_time(n["duration"])
                 + "</small></td><td class='del' title='" + n["filename"]
                 + "'><i class='glyphicon glyphicon-remove-circle' title='"
                 + n["filename"] + "'></i>" + "</td></tr>";
            });
            $('#list').empty();
            $('#list').append(html);
        } else
            out(xhr.statusText);
    });
    }
</script>
</html>