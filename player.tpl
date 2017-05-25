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
  font-size: 1.75em;
}
.glyphicon-remove-circle {
    color: gray;
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
  font-size: 1.3em;
}
/*** modified bootstrap style ***/
html, body {
  height: 100%
}
body {
  background-color: #F1F2F6; /* #DDD9DD #101010; */
  cursor: default;
  -webkit-user-select: none;
  -moz-user-select: none;
  user-select: none;
  font-family: AppleSDGothicNeo-Regular;
}
/*
article {
  left: 0%;
}
*/
div {
  text-align: center;
}
video {
  clear: both;
  display: block;
  margin: auto;
}
a {
  cursor: default;
}
input {
  height: 3em;
}
.filelist {
  min-width: 14em;
}
.filelist.other {
  color: grey;
}
/*
@keyframes slide {
  0% {left:-8%}
  9% {left:0%}
  75% {left:0%}
  100% {left:-9%}
}
@-webkit-keyframes slide {
  0% {left:-8%}
  9% {left:0%}
  75% {left:0%}
  100% {left:-9%}
}
#sidebar.sliding {
  left: 0%;
  -webkit-transform: translateX(0%);
  -webkit-animation-name: slide;
  -webkit-animation-duration: 5.5s;
  -webkit-animation-iteration-count: 1;
  -webkit-animation-delay: 0s;
  animation-name: slide;
  animation-duration: 5.5s;
  animation-iteration-count: 1;
  animation-delay: 0s;
}
*/
#sidebar{
  opacity: 0;
  position: fixed;
  top: 40%;
}
#sidebar.outside {
  /*left: -25%*/
}
#output {
  z-index: 99;
  font-size: 1.8em;
  pointer-events: none;
  border-radius: 0.2em;
  padding: 0.2em;
  opacity: 0.4;
  border: 1px solid #777777;
  box-shadow: 0.5em 0.5em 6em #AAAAAA inset;
  text-shadow: 0.1em 0.1em 0.4em #666;
}
#dialog {
  opacity: 0.8;
  box-shadow: 2px 2px 5px #333333;
  max-width: 100%;
  /* background-color: #CCCCCC; */
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
  min-width: 10em;
  width: 100%;
}
</style>
</head>
<body>
<div>
  <video src="{{src}}" onprogress="showBuff()" onerror="out('error')" onseeking="showProgress()" ontimeupdate="saveprogress()" onloadeddata="loadprogress()" poster controls preload="meta">No video support!</video>
</div>
<!-- <div id="sidebar" class="outside"> -->
<div id="sidebar">
  <button onClick="if($('#navtab li:eq(0)').attr('class')=='active')tabshow('?action=list', 0);$('#dialog').show();" type="button" class="btn btn-default"><i class="glyphicon glyphicon-list-alt"></i></button>
</div>
<div id="dialog" style="display:none">
  <div class="bg-info">
  <button onClick="$('#dialog').hide();" type="button" class="close">&times;</button> <!-- &#10060; -->
    <ul id="navtab" class="nav nav-tabs">
      <li class="active">
        <a href="#mainframe" data-toggle="tab" onclick="tabshow('?action=list', 0)"><i class="glyphicon glyphicon-list"></i>History</a>
      </li>
      <li>
        <a href="#mainframe" data-toggle="tab" onclick="tabshow('/', 1)"><i class="glyphicon glyphicon-home"></i>Home dir</a>
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
    <!-- <button type="button" class="btn btn-default" onClick="if(confirm('Suspend ?'))$.get('/suspend.php');"> -->
      <!-- <i class="glyphicon glyphicon-off"></i> -->
    <!-- </button> -->
    <div class="btn-group dropup">
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
    <div class="btn-group dropup">
      <button type="button" class="btn btn-default" onClick="if(confirm('Suspend ?'))$.get('/suspend.php');"><i class="glyphicon glyphicon-off"></i></button>
      <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
        <span class="caret"></span>
      </button>
      <ul class="dropdown-menu" role="menu">
        <li><a onClick="if(confirm('Shutdown ?'))$.get('/shutdown.php');"><i class="glyphicon glyphicon-off"></i>shutdown</a></li>
      </ul>
    </div>
  </div>
</div>
</body>
<script src="static/js/jquery-3.2.1.min.js"></script>
<script src="static/js/bootstrap.min.js"></script>
<script language="javascript">
var range = 12; //minimum touch move range in pxs
var text="";
var lastsavetime = 0;//in seconds
var lastplaytime = 0;//in seconds
var video = document.getElementsByTagName("video");//$("video")
window.addEventListener("load", onload, false);
window.addEventListener("resize", adapt, false);
window.addEventListener("mousemove", showsidebar, false);

function onload() {
    adapt();
    //document.addEventListener("touchstart", touch, false);
    //document.addEventListener("touchend", touch, false);
}

$(document).on('touchstart',function(e) {
    x0 = e.originalEvent.touches[0].screenX;
    y0 = e.originalEvent.touches[0].screenY;
});
$(document).on('touchend',function(e) {
    x = event.changedTouches[0].screenX - x0;
    y = event.changedTouches[0].screenY - y0;

    if (Math.abs(y / x) < 0.25) {
        if (x > range)
            playward(Math.floor(x / 11));
        else if (x < -range)
            playward(Math.floor(x / 11));
    } else
        showsidebar();
});

if (isNaN({{src}})) {
    $("video").remove();
    tabshow("?action=list", 0);
    $("#dialog").show();
} else
    out(2);

$("#mainframe").on("click",".dir", function(e) {
    tabshow(e.target.title, 1);
});
$("#mainframe").on("click",".move", function(e) {
    if (confirm("Move " + e.target.title + " to old?"))
        tabshow("?action=move&src=" + e.target.title, 1);
});
$("#mainframe").on("click",".del", function(e) {
    if (confirm("Clear " + e.target.title + "?"))
        tabshow("?action=del&src=" + e.target.title, 0);
});
$("#mainframe").on("click","#clear", function() {
    if (confirm("Clear all history?"))
        tabshow("?action=clear", 0);
});
/*
function touch(event) {
    var event = event || window.event;
    switch (event.type) {
    case "touchstart":
        x0 = event.touches[0].clientX;
        y0 = event.touches[0].clientY;
        break;
    case "touchend":
        x = event.changedTouches[0].clientX - x0;
        y = event.changedTouches[0].clientY - y0;

        if (Math.abs(y / x) < 0.25) {
            if (x > range)
                playward(Math.floor(x / 11));
            else if (x < -range)
                playward(Math.floor(x / 11));
        } else
            showsidebar();
        break;
    }
}
*/
function out(str) {
    if (str=="")
        return;
    $("#output").remove();
    $(document.body).append("<div id='output'>" + str + "</div>");
    $("#output").fadeTo(250,0.7).delay(1625).fadeOut(625);
}
function showsidebar() {
    //$("#sidebar").removeClass("outside");
    //$("#sidebar").show().animate({left:"0"},500).delay(3250).animate({left:"-10%"},1250);
    //$("#sidebar").stop(true).show().fadeTo(300,0.65).delay(3000).fadeOut(800);
    //$("#sidebar").show().fadeTo(300,0.3).delay(3200).fadeOut(800);
    $("#sidebar").show().fadeTo(500,0.35).delay(9999).fadeOut(800);
    //$("#sidebar").addClass("outside");
    ////////////////////////////////////////////////////////////////
    //var sidebar = document.getElementById("sidebar");
    //sidebar.className = "sliding";
    //sidebar.addEventListener("animationend", resetsidebar);
    //sidebar.addEventListener("webkitAnimationEnd", resetsidebar);
}
/*
function resetsidebar() {
    $("#sidebar").attr("class", "outside");
}
*/
function rate(x) {
    out(x + "X");
    video[0].playbackRate = x;
}
function format_time(time) {
    return Math.floor(time / 60) + ":" + (time % 60 / 100).toFixed(2).slice(-2);
}
function playward(time) {
    if (!isNaN(video[0].duration)) {
        if (time > 0) {
            time=Math.min(60,time);
            text=time + "S>><br>";
        }
        else if (time < 0) {
            time=Math.max(-60,time);
            text="<<" + -time + "S<br>";
        }
        video[0].currentTime += time;
    }
}
function loadprogress() {
    video[0].currentTime = Math.max({{progress}} - 0.5, 0);
    text="Start from<br>";
}
function showProgress() {
    out(text+format_time(video[0].currentTime)+ '/' + format_time(video[0].duration));
    text="";
}
function saveprogress() {
    lastplaytime = new Date().getTime();
    if (video[0].readyState == 4 && video[0].currentTime < video[0].duration + 1) {
        if (Math.abs(video[0].currentTime - lastsavetime) > 3)//save play progress in every 3 seconds
        {
            lastsavetime = video[0].currentTime;
            $.get("?action=save&src={{src}}&time=" + video[0].currentTime + "&duration=" + video[0].duration ,function(data, status, xhr) {
                if(xhr.statusText!="OK")
                    out(xhr.statusText);
            });
        }
    }
}
function videosizetoggle() {
    if ($("#videosize").text()=="auto")
        adapt();
    else {
        $("#videosize").text("auto");
        if (video[0].width < document.body.clientWidth && video[0].height < document.body.clientHeight) {
            video[0].style.width = video[0].videoWidth + "px";
            video[0].style.height = video[0].videoHeight + "px";
        }
    }
}
function adapt() {
    $("#videosize").text("orign");
    //out($(window).height() +"|"+ $(document).height() +"|"+ $(document.body).height()  +"|"+  $(document.body).outerHeight(true));
    $("#mainframe").css("max-height", ($(document.body).height() - 240) + "px");
    if ($(document.body).height() <= 480)
        $("#dialog").width("100%");
    else
        $("#dialog").width("auto");
    video_ratio = video[0].videoWidth / video[0].videoHeight;
    page_ratio = document.body.clientWidth / document.body.clientHeight;
    if (page_ratio < video_ratio) {
        video[0].style.width = document.body.clientWidth + "px";
        video[0].style.height = Math.floor(document.body.clientWidth / video_ratio) + "px";
    } else {
        video[0].style.width = Math.floor($(document.body).height() * video_ratio) + "px";
        video[0].style.height = document.body.clientHeight + "px";
    }
}
function showBuff() {
    var str="";
    for(i = 0, t = video[0].buffered.length; i < t; i++)
    {
        if (video[0].currentTime >= video[0].buffered.start(i) && video[0].currentTime <= video[0].buffered.end(i))
            str += format_time(video[0].buffered.start(i)) + "-" + format_time(video[0].buffered.end(i)) + "<br>";
    }
    if (new Date().getTime() - lastplaytime > 1000)
        out(str + "<small>buffering...</small>");
}
function tabshow(str, n) {
    $("#list").load(encodeURI(str), function(responseTxt, status, xhr) {
        if (xhr.statusText=="OK")
            $("#navtab li:eq(" + n + ") a").tab("show");
        else
            out(xhr.statusText);
    });
}
</script>
</html>