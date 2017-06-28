﻿<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=0.8, maximum-scale=1.0, user-scalable=1">
    <title>{{title}}</title>
    <link href="/static/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/css/player.css" rel="stylesheet">
    <style>
#position-bar {
    background-color: #A0D468;
    margin-top: 1.5em;
    margin-bottom: 1.5em;
    width: 84%;
    height: 2.4em;
}
#position-bar::-webkit-slider-thumb{
    -webkit-appearance: none;
    height: 5.2em;
    width: 3.3em;
    padding: 1.5em;
    background-clip: content-box;
    background-color: #F1F2F6;
    border: None;
    /* box-shadow: inset 0px 0px 5px 1px #A0D468; */
}
#volume-bar::-webkit-slider-thumb:active{
    /* background: grey; */
}
#volume-bar {
    background-color: #F0AD4E;
    width: 16em;
    height: 1.5em;
    margin-top: 3.5em;
}
#volume-bar::-webkit-slider-thumb{
    -webkit-appearance: none;
    height: 3.2em;
    width: 3.8em;
    padding: 1em;
    background-clip: content-box;
    background-color: #F1F2F6;
    border: None;
    /* box-shadow: inset 0px 0px 5px 1px #F0AD4E; */
}
#src {
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
}
#position {
    margin-top: 3em;
}
    </style>
  </head>
  <body>
    <div class="col-xs-12 col-sm-6 col-md-5" id="dlna">
      <h2 id="src"></h2>
      <button type="button" class="btn btn-success btn-lg glyphicon glyphicon-play" onclick="$.get('/dlnaplay')">
      <!-- play -->
      </button>
      <button type="button" class="btn btn-warning btn-lg glyphicon glyphicon-pause" onclick="$.get('/dlnapause')">
      <!-- pause -->
      </button>
      <button type="button" class="btn btn-danger btn-lg glyphicon glyphicon-stop" onclick="$.get('/dlnastop')">
      <!-- stop -->
      </button>
      <div class="btn-group dropdown">
        <button type="button" class="btn btn-info btn-lg dropdown-toggle glyphicon glyphicon-chevron-down" data-toggle="dropdown">
        <!-- seek -->
          <!-- <span class="caret"></span> -->
        </button>
        <ul class="dropdown-menu" role="menu">
          <li><a href="#" onclick="$.get('/dlnaseek/00:00:15')">00:15</a></li>
          <li><a href="#" onclick="$.get('/dlnaseek/00:00:30')">00:30</a></li>
          <li><a href="#" onclick="$.get('/dlnaseek/00:01:00')">01:00</a></li>
          <li class="divider"></li>
          <li><a href="#" onclick="$.get('/dlnaseek/00:01:30')">01:30</a></li>
        </ul>
      </div>
        <h3 id="position"></h3>
        <input type="range" id="position-bar" min="0" max="600">
          <span class="col-xs-3 col-sm-3 col-md-2" id="position-min">00:00:00</span>
          <span class="col-xs-3 col-sm-3 col-md-2 col-xs-offset-6 col-sm-offset-6 col-md-offset-8" id="position-max">00:10:00</span>
        <input type="range" id="volume-bar" min="0" value="12" max="100">
    </div>
    <div id="sidebar">
      <button id="history" type="button" class="btn btn-default">
        <i class="glyphicon glyphicon-list-alt"></i>
      </button>
    </div>
    <div id="dialog" class="col-xs-12 col-sm-6 col-md-4">
      <div id="panel">
        <div class="bg-info panel-title">
          <button onClick="$('#dialog').hide(250);" type="button" class="close">&times;</button>
          <ul id="navtab" class="nav nav-tabs">
            <li class="active">
              <a href="#tabFrame" data-toggle="tab" onclick="history('/list')">
                <i class="glyphicon glyphicon-list"></i>History
              </a>
            </li>
            <li>
              <a href="#tabFrame" data-toggle="tab" onclick="filelist('/fs/')">
                <i class="glyphicon glyphicon-home"></i>Home dir
              </a>
            </li>
          </ul>
        </div>
        <div id="tabFrame" class="tab-pane fade in">
          <table class="table-striped table-responsive table-condensed">
            <tbody id="list">
            </tbody>
          </table>
        </div>
        <div class="panel-footer">
          <button id="videosize" type="button" class="btn btn-default">orign</button>
          <div id="rate" class="btn-group dropup">
            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
              Rate<span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li><a href="#" onclick="rate(0.5)">0.5X</a></li>
              <li><a href="#" onclick="rate(0.75)">0.75X</a></li>
              <li class="divider"></li>
              <li><a href="#" onclick="rate(1)">1X</a></li>
              <li class="divider"></li>
              <li><a href="#" onclick="rate(1.5)">1.5X</a></li>
              <li><a href="#" onclick="rate(2)">2X</a></li>
            </ul>
          </div>
          <button id="clear" type="button" class="btn btn-default">Clear History</button>
          <div class="btn-group dropup">
            <button type="button" class="btn btn-default" onClick="if(confirm('Suspend ?'))$.post('/suspend');">
              <i class="glyphicon glyphicon-off"></i>
            </button>
            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li>
                <a onClick="if(confirm('Shutdown ?'))$.post('/shutdown');">
                <i class="glyphicon glyphicon-off"></i>shutdown</a>
              </li>
              <li>
                <a onClick="if(confirm('Restart ?'))$.post('/restart');">
                <i class="glyphicon glyphicon-off"></i>restart</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </body>
  <script src="/static/js/jquery-3.2.1.min.js"></script>
  <script src="/static/js/bootstrap.min.js"></script>
  <script language="javascript">
var RANGE = 12;  //minimum touch move range in px
var text="";
var lastplaytime = 0;  //in seconds

window.onload = adapt;
$(window).resize(adapt);
$(document).mousemove(showSidebar);
function get_dlna_position(){
    $.get("/dlnainfo",function(data){
        //max(0,min(current-300,total-600))
        //min(mini+600,total)
        reltime = timeToSecond(data["RelTime"]);
        duration = timeToSecond(data["TrackDuration"]);
        min = Math.max(Math.min(reltime - 300, duration - 600), 0);
        max = Math.min(min + 600, duration);
        $("#position-bar").attr("min", min);
        $("#position-bar").attr("max", max);
        $("#position-bar").val(reltime);
        $("#position-min").text(secondToTime(min));
        $("#position-max").text(secondToTime(max));
        $('#position').text(data["RelTime"] + "/" + data["TrackDuration"]);
        $('#src').text(decodeURI(data["TrackURI"]));
    });
}
if ("{{mode}}" == "index") {
    history("/list");
    $("#dialog").show(250);
} else if ("{{mode}}" == "dlna") {
    get_dlna_position();
    $("#dlna").show(250);
    setInterval("get_dlna_position()",1500);
    $("#position-bar").on("change", function() {
        $.get("/dlnaseek/" + secondToTime($(this).val()));
    }).on("input", function() {
        out(secondToTime($(this).val()));
    });
    $("#volume-bar").on("change",function() {
        $.get("/dlnavolume/" + $(this).val());
    }).on("input", function() {
        out($(this).val());
    });
} else if ("{{mode}}" == "player") {
    $("#videosize").show();
    $("#rate").show();
    $(document.body).append("<video poster controls preload='meta'>No video support!</video>");
    $("video").attr("src", "/video/{{src}}").on("error", function () {
        out("error");
    }).on("loadeddata", function () {  //auto load position
        this.currentTime = Math.max({{position}} - 0.5, 0);
        text = "<small>Play from</small><br>";
    }).on("seeking", function () {  //show position when changed
        out(text + secondToTime(this.currentTime) + '/' + secondToTime(this.duration));
        text = "";
    }).on("timeupdate", function () {  //auto save play position
        lastplaytime = new Date().getTime();  //to detect if video is playing
        if (this.readyState == 4 && Math.floor(Math.random() * 99) > 80) {  //randomly save play position
            $.ajax({
                url: "/save/{{src}}",
                data: {
                    position: this.currentTime,
                    duration: this.duration
                },
                timeout: 999,
                type: "POST",
                error: function (xhr) {
                    out("save: " + xhr.statusText);
                }
            });
        }
    }).on("progress", function () {  //show buffered
        var str = "";
        if (new Date().getTime() - lastplaytime > 1000) {
            for (i = 0, t = this.buffered.length; i < t; i++) {
                if (this.currentTime >= this.buffered.start(i) && this.currentTime <= this.buffered.end(i))
                    str = secondToTime(this.buffered.start(i)) + "-" + secondToTime(this.buffered.end(i)) + "<br>";
            }
            out(str + "<small>buffering...</small>");
        }
    });
}
function showSidebar() {
    $("#sidebar").show(600).delay(9999).hide(300);
}
function rate(x) {
    out(x + "X");
    $("video").get(0).playbackRate = x;
}
function secondToTime(time) {
    return ("0" + Math.floor(time / 3600)).slice(-2) + ":" + ("0" + Math.floor(time %3600 / 60)).slice(-2) + ":" + (time % 60 / 100).toFixed(2).slice(-2);
}
function timeToSecond(time) {
    t = String(time).split(":");
    return parseInt(t[0]) * 3600 + parseInt(t[1]) * 60 + parseInt(t[2]);
}
function adapt() {
    $("#videosize").text("orign");
    $("#tabFrame").css("max-height", ($(window).height() - 240) + "px");
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
$(document).on('touchend', function (e) {
    x = e.changedTouches[0].screenX - x0;
    y = e.changedTouches[0].screenY - y0;
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
$("#history").click(function () {
    if ($('#navtab li:eq(0)').attr('class') == 'active')
        history("/list");
    $('#dialog').show(250);
});
$("#videosize").click(function () {
    if ($(this).text() == "auto")
        adapt();
    else {
        $(this).text("auto");
        if ($("video").get(0).width < $(window).width() && $("video").get(0).height < $(window).height()) {
            $("video").get(0).style.width = $("video").get(0).videoWidth + "px";
            $("video").get(0).style.height = $("video").get(0).videoHeight + "px";
        }
    }
});
$("#clear").click(function () {
    if (confirm("Clear all history?"))
        history("/clear");
});
$("#tabFrame").on("click", ".folder", function () {
    filelist("/fs" + this.title + "/");
}).on("click", ".move", function () {
    if (confirm("Move " + this.title + " to old?")) {
        filelist("/move/" + this.title);
    }
}).on("click", ".remove", function () {
    if (confirm("Clear " + this.title + "?"))
        history("/remove/" + this.title);
}).on("click", ".mp4", function () {
    window.location.href = "/play/" + this.title;
}).on("click", ".dlna", function () {
    window.location.href = "/dlna/" + this.title;
});
function filelist(str) {
    $.ajax({
            url: encodeURI(str),
            dataType: "json",
            timeout : 999,
            type: "get",
            success: function (data) {
                if ($('#navtab li:eq(1)').attr('class') != 'active')
                    $("#navtab li:eq(1) a").tab("show");
                $("#clear").hide();
                var html = "";
                var icon = {"folder": "folder-close", "mp4": "film", "mkv": "film", "other": "file"};
                $.each(data, function (i, n) {
                    size = "";
                    if(n["size"])
                        size = "<br><small>" + n["size"] +"</small>";
                    dlna = "";
                    if(icon[n["type"]]=="film")
                        dlna = " class='dlna' title='" + n["path"] + "'";
                    html += "<tr>" +
                              "<td" + dlna + "><i class='glyphicon glyphicon-" + icon[n["type"]] + "'></i></td>" +
                              "<td class='filelist " + n["type"] + "' title='" + n["path"] + "'>" + n["filename"] + size + "</td>" +
                              "<td class='move' title='" + n["path"] + "'>" +
                                "<i class='glyphicon glyphicon-remove-circle'></i>" +
                              "</td>" +
                            "</tr>"
                });
                $('#list').empty().append(html);
            },
            error: function(xhr){
                out(xhr.statusText);
            }
    });
}
function history(str) {
    $.ajax({
            url: encodeURI(str),
            dataType: "json",
            timeout : 999,
            type: "get",
            success: function (data) {
                if ($('#navtab li:eq(0)').attr('class') != 'active')
                    $("#navtab li:eq(0) a").tab("show");
                $("#clear").show();
                var html = "";
                $.each(data, function (i, n) {
                    html += "<tr><td class='folder' title='/" + n["path"] + "'>" +
                                "<i class='glyphicon glyphicon-folder-close'></i>" +
                              "</td>" +
                              "<td class='dlna' title='" + n["filename"] + "'>" +
                                "<i class='glyphicon glyphicon-film'></i>" +
                              "</td>" +
                              "<td class='filelist mp4' title='" + n["filename"] + "'>" + n["filename"] + 
                                "<br><small>" + n["latest_date"] + " | " + 
                                secondToTime(n["position"]) + "/" + secondToTime(n["duration"]) + "</small>" + 
                              "</td>" + 
                              "<td class='remove' title='" + n["filename"] + "'>" +
                                "<i class='glyphicon glyphicon-remove-circle'></i>" + 
                              "</td></tr>";
                });
                $('#list').empty().append(html);
            },
            error: function(xhr){
                out(xhr.statusText);
            }
    });
}
  </script>
</html>