"use strict";
var icon = {
    "folder": "oi-folder",
    "mp4": "oi-video",
    "video": "oi-video",
    "other": "oi-file"
};

function touchWebPlayer() {
    var hammertimeVideo = new Hammer(document);
    hammertimeVideo.on("panleft panright swipeleft swiperight", function (ev) {
        var deltaTime = ev.deltaX / 4;
        if (ev.type.indexOf("swipe") != -1)
            window.appView.$refs.video.currentTime += deltaTime;
        else
            window.appView.out(secondToTime(window.appView.$refs.video.currentTime + deltaTime));
        console.log(ev);
        console.log(ev.type);
    });
    hammertimeVideo.get('swipe').set({
        velocity: 0.01
    });
}

window.appView = new Vue({
        delimiters: ['${', '}'],
        el: '#v-main',
        data: {
            mode: '', // mode of player, switch between empty/DLNA/WebPlayer
            navCollapse: false, // navbar is collapse
            devMode: true, // develop mode
            editMode: false,
            browserShow: false,
            historyShow: true, // ture if browser window is history, false if browser window is file list
            history: [], // updated by ajax
            filelist: [], // updated by ajax
            dlnaInfo: { // updated by websocket
                CurrentDMR: 'no DMR',
                CurrentTransportState: '',
                TrackURI: '',
            },
            positionBarCanUpdate: true, //dlna position bar
            positionBarVal: 0,
            fixBar: {
                show: true,
                timerId: null,
            },
            video: {
                lastplaytime: 0,
                sizeBtnText: 'origin',
                src: '', // web player source
            },
            output: {
                text: '',
                smallText: '', // consider to declared
                show: false,
                timerId: null,
            },
            isIos: null,
            icon: icon,
        },
        watch: {
            browserShow: function () {
                this.navCollapse = false;
                if (!this.browserShow)
                    this.editMode = false;
            },
            'dlnaInfo.RelTime': function () {
                console.log('reltime update');
                if (this.positionBarCanUpdate)
                    this.positionBarVal = timeToSecond(this.dlnaInfo.RelTime);
                console.log(this.positionBarVal);
            },
            mode: function () {
                if (this.dlnaMode) {
                    window.document.title = "DMC - Light Media Player";
                } else if (this.wpMode) {
                    window.document.title = this.video.src + " - Light Media Player";
                    // if (this.isIos)
                    touchWebPlayer();
                } else
                    window.document.title = "Light Media Player";
            },
        },
        computed: {
            dlnaOn: function () { // check if dlna dmr is exist
                return this.dlnaInfo.CurrentDMR !== 'no DMR';
            },
            dlnaMode: function () { // check if in dlna mode
                return this.mode === 'DLNA';
            },
            wpMode: function () { // check if in web player mode
                return this.mode === 'WebPlayer';
            },
            positionBarMax: function () {
                if (this.dlnaInfo.hasOwnProperty('TrackDuration'))
                    return timeToSecond(this.dlnaInfo.TrackDuration);
                return 0;
            },
            wpPosition: function () {
                for (var item in this.history) {
                    if (this.history[item].filename == window.appView.video.src)
                        return this.history[item].position;
                }
                return 0;
            }
        },
        methods: {
            test: function (obj, obj2) {
                // console.log("test " + obj);
                // this.out('test' + obj);
            },
            volUp: function (obj) {
                server.dlna_vol(['up']);
            },
            volDown: function (obj) {
                server.dlna_vol(['down']);
            },
            pressOpen: function (obj) {
                var target = obj.target.tagName == 'TD' ? obj.target : obj.target.parentNode;
                this.open(target.getAttribute('data-target'), 'folder');
            },
            tapOpen: function (obj) {
                var target = obj.target.tagName == 'TD' ? obj.target : obj.target.parentNode;
                this.open(target.getAttribute('data-path'), target.getAttribute('data-type'));
            },
            showFixBar: function () { // show fix bar and then hide
                this.fixBar.show = true;
                if (this.fixBar.timerId) {
                    clearTimeout(this.fixBar.timerId);
                    this.fixBar.timerId = null;
                }
                this.fixBar.timerId = setTimeout(function () {
                        window.appView.fixBar.show = false;
                    }, 3500);
            },
            out: function (str) {
                if (str !== "") {
                    if (this.output.timerId) {
                        clearTimeout(this.output.timerId);
                        this.output.timerId = null;
                    }
                    this.output.text = str;
                    this.output.show = true;
                    this.output.timerId = setTimeout(function () {
                            window.appView.output.show = false;
                        }, 2100);
                }
            },
            outFadeIn: function (el, done) {
                Velocity(el, 'stop');
                // Velocity(el, {opacity: 0.8}, {duration: 180});
                Velocity(el, {opacity: 0.75}, {duration: 170});
            },
            outFadeOut: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {opacity: 0}, {duration: 600});
            },
            dlnaToogle: function () {
                this.mode = this.mode !== '' ? '' : 'DLNA';
                localStorage.mode = this.mode;
            },
            videoAdapt: function () {
                if (this.wpMode) {
                    var wHeight = window.innerHeight;
                    this.video.sizeBtnText = "orign";
                    var video_ratio = this.$refs.video.videoWidth / this.$refs.video.videoHeight;
                    var page_ratio = window.innerWidth / wHeight;
                    if (page_ratio < video_ratio) {
                        var width = window.innerWidth + "px";
                        var height = Math.floor(window.innerWidth / video_ratio) + "px";
                    } else {
                        var width = Math.floor(wHeight * video_ratio) + "px";
                        var height = wHeight + "px";
                    }
                    this.$refs.video.style.width = width;
                    this.$refs.video.style.height = height;
                }
            },
            videoSizeToggle: function () {
                if (this.video.sizeBtnText == 'auto')
                    this.videoAdapt();
                else {
                    this.video.sizeBtnText = 'auto';
                    if (this.$refs.video.width < window.innerWidth && this.$refs.video.height < window.innerHeight) {
                        this.$refs.video.style.width = this.$refs.video.videoWidth + "px";
                        this.$refs.video.style.height = this.$refs.video.videoHeight + "px";
                    }
                }
            },
            showModal: function () {
                this.browserShow = !this.browserShow;
                if (this.browserShow && this.historyShow)
                    this.showHistory();
            },
            historyCallBack: function (data) {
                this.historyShow = true;
                this.history = data;
                // this.history = data.history;
            },
            showHistory: function () {
                server.list_history({}, this.historyCallBack);
            },
            fileSystemCallBack: function (data) {
                this.historyShow = false;
                // this.filelist = data.filesystem;
                this.filelist = data;
            },
            clearHistory: function () { // clear history button
                if (confirm("Clear all history?"))
                    server.clear_history({}, this.historyCallBack);
            },
            remove: function (obj) {
                server.remove_history({src: obj}, this.historyCallBack);
            },
            move: function (obj) {
                server.file_move({src: obj}, this.fileSystemCallBack);
            },
            open: function (obj, type) {
                switch (type) {
                case "folder":
                    server.file_list({path: obj}, this.fileSystemCallBack);
                    break;
                case "mp4":
                    if (!this.dlnaMode) 
                        this.playInWeb(obj);
                case "video":
                    if (this.dlnaMode)
                        server.dlna_load({src: obj, host: window.location.host});
                    break;
                default:
                }
            },
            checkFileExist: function (obj) {
                for (var item in this.history) {
                    if (this.history[item].filename == obj)
                        return this.history[item].exist;
                }
                return true;
            },
            playInWeb: function (obj) {
                console.log(obj);
                if (!this.checkFileExist(obj)) {
                    this.out(obj + ' not exist');
                    return;
                }
                this.video.src = obj;
                this.mode = "WebPlayer";
                this.browserShow = false;
            },
            setDmr: function (dmr) {
                server.dlna_set_dmr({dmr: dmr});
            },
            positionSeek: function () {
                var position = secondToTime(offset_value(timeToSecond(this.dlnaInfo.RelTime), this.positionBarVal, this.positionBarMax));
                server.dlna_seek({position: position});
                this.positionBarCanUpdate = true;
            },
            positionShow: function () {
                this.out(secondToTime(offset_value(timeToSecond(this.dlnaInfo.RelTime), this.positionBarVal, this.positionBarMax)));
                this.positionBarCanUpdate = false;
            },
            rate: function (ratex) {
                this.out(ratex + 'X');
                this.$refs.video.playbackRate = ratex;
            },
            videosave: function () {
                this.video.lastplaytime = new Date().getTime(); //to detect if video is playing
                if (this.$refs.video.readyState == 4 && Math.floor(Math.random() * 99) > 70) //randomly save play position
                    server.save_history({
                        src: this.video.src,
                        position: this.$refs.video.currentTime,
                        duration: this.$refs.video.duration,
                    }, null);
            },
            videoload: function () {
                this.videoAdapt();
                this.out('adpat');
                this.$refs.video.currentTime = Math.max(this.wpPosition - 0.5, 0);
                this.output.smallText = "Play from";
            },
            videoseek: function () { //show position when changed
                this.out(secondToTime(this.$refs.video.currentTime) + '/' + secondToTime(this.$refs.video.duration));
                this.output.smallText = "";
            },
            videoerror: function () {
                this.out("error");
            },
            videoprogress: function () { //show buffered when hanged
                var str = "";
                if (new Date().getTime() - this.video.lastplaytime > 1000) {
                    for (var i = 0, t = this.$refs.video.buffered.length; i < t; i++) {
                        if (this.$refs.video.currentTime >= this.$refs.video.buffered.start(i) && this.$refs.video.currentTime <= this.$refs.video.buffered.end(i)) {
                            str = secondToTime(this.$refs.video.buffered.start(i)) + "-" + secondToTime(this.$refs.video.buffered.end(i));
                            break;
                        }
                    }
                    this.out(str + " buffering...");
                }
            },
            dlnaTouch: function (obj) {
                var newtime = this.positionBarVal + obj.deltaX / 4;
                newtime = Math.max(newtime, 0);
                newtime = Math.min(newtime, this.positionBarMax);
                this.out(secondToTime(newtime));
                if (obj.type.indexOf("swipe") != -1) {
                    server.dlna_seek({position: secondToTime(newtime)});
                    console.log('swipe');
                } else
                    console.log('pan');
            },
        },
        created: function () {
            if (typeof(localStorage.mode) !== "undefined")
                this.mode = localStorage.mode;
            window.onresize = this.videoAdapt;
            this.isIos = !!navigator.userAgent.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
            this.isIos = true;
            if (!this.isIos) {
                this.fixBar.show = false;
                document.onmousemove = this.showFixBar;
            };
            axios.defaults.timeout = 1999;
            // prevent double click for IOS
            document.addEventListener('touchstart', function (event) {
                if (event.touches.length > 1) {
                    event.preventDefault();
                }
            });
            var lastTouchEnd = 0;
            document.addEventListener('touchend', function (event) {
                var now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                };
                lastTouchEnd = now;
            }, false);
        },
        mounted: function () {
            this.$nextTick(function () {
                // console.log('mounted');
                window.appView.showHistory();
            });
        },
    });

function dlnalink() {
    var ws = new WebSocket("ws://" + window.location.host + "/link");
    ws.onmessage = function (e) {
        var data = JSON.parse(e.data);
        console.log(data);
        window.appView.dlnaInfo = data;
    }
    ws.onclose = function () {
        window.appView.dlnaInfo.CurrentTransportState = 'disconnected';
    };
    ws.onerror = function () {
        console.log('connection lost');
    };
    ws.check = function () {
        if (this.readyState == 3)
            ws_link = dlnalink();
    };
    return ws;
}

function dlnalink2() {
    var ws = new WebSocket("ws://" + window.location.host + "/wsapi");
    ws.onmessage = function (e) {
        var data = JSON.parse(e.data);
        console.log(data);
        var callback = window.appView.out;
        var errorCallback = window.appView.out;
        if (data.hasOwnProperty('result'))
            callback(data.result);
        else
            errorCallback(data.error);
    }
    ws.onclose = function () {

    };
    ws.onerror = function () {
        console.log('connection lost');
    };
    ws.check = function () {
        if (this.readyState == 3)
            ws_link2 = dlnalink2();
    };
    return ws;
}
var ws_link2 = dlnalink2();

function JsonRpc2() {
    return new Proxy(function () {}, {
        get: function (target, method, receiver) {
            return function (params, callback) {
                // if (typeof(callback) == "undefined")
                    // callback = options.callback;
                var json_data = {
                    jsonrpc: '2.0',
                    method: method,
                    params: params,
                    id: Math.floor(Math.random() * 9999)
                };
                ws_link2.send(JSON.stringify(json_data));
            };
        }
    });
}

var ws_link = dlnalink();
setInterval("ws_link.check()", 1200);

// var server = JsonRpc2();
var server = JsonRpc({
        url: '/api',
        callback: window.appView.out
    });
