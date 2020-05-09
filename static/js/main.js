'use strict';
var icon = {
    folder: "oi-folder",
    mp4: "oi-video",
    video: "oi-video",
    other: "oi-file"
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
            devMode: false, // develop mode switch
            allSelected: false,
            removeCheckboxList: [],
            moveCheckboxList: [],
            mode: '', // mode of player, switch between empty/DLNA/WebPlayer
            navCollapse: false, // navbar is collapse
            editMode: false,
            browserShow: false,
            historyShow: true, // ture if browser window is history, false if browser window is file list
            history: [], // updated by ajax
            filelist: [], // updated by ajax
            dlnaInfo: {}, // updated by websocket
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
            'dlnaInfo.CurrentDMR': function () {
                if (!this.wpMode) {
                    if (typeof(this.dlnaInfo.CurrentDMR) === "undefined")
                        this.mode = '';
                    else if(this.dlnaInfo.CurrentDMR.indexOf('小米AI音箱')===-1)
                        this.mode = 'DLNA';
                }
            },
            // editMode: function () {
                // this.allSelected = false;
                // this.removeCheckboxList = [];
            // },
            historyShow: function () {
                this.allSelected = false;
                // this.moveCheckboxList = [];
                // this.removeCheckboxList = [];
            },
            browserShow: function () {
                if (this.browserShow && this.historyShow)
                    this.showHistory();
                this.navCollapse = false;
                this.editMode = false;
            },
            'dlnaInfo.RelTime': function () {
                // console.log('reltime update');
                if (this.positionBarCanUpdate)
                    this.positionBarVal = timeToSecond(this.dlnaInfo.RelTime);
                // console.log(this.positionBarVal);
            },
            mode: function () {
                if (this.dlnaMode) {
                    window.document.title = "DMC - Light Media Player";
                } else if (this.wpMode) {
                    window.document.title = this.video.src + " - Light Media Player";
                    touchWebPlayer();
                } else
                    window.document.title = "Light Media Player";
            },
        },
        computed: {
            // dlnaOn: function () { // check if dlna dmr is exist
                // return typeof(this.dlnaInfo.CurrentDMR) !== "undefined" && this.dlnaInfo.CurrentDMR !== 'no DMR';
            // },
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
                    if (this.history[item].fullpath === window.appView.video.src)
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
            transitionBounceIn: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {
                    opacity: [1, 0],
                    // translateY: [0, -75],
                    transformOriginX: ["50%", "50%"],
                    transformOriginY: ["50%", "50%"],
                    scaleX: [1, .625],
                    scaleY: [1, .625],
                    translateZ: 0
                }, {
                    duration: 300,
                    complete: done
                });
            },
            transitionBounceOut: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {
                    opacity: [0, 1],
                    // translateY: -75,
                    transformOriginX: ["50%", "50%"],
                    transformOriginY: ["50%", "50%"],
                    scaleX: .5,
                    scaleY: .5,
                    translateZ: 0
                }, {
                    duration: 300,
                    complete: done
                });
            },
            transitionSlideUpBigIn: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {
                    opacity: [1, 0],
                    translateY: [0, 75],
                    translateZ: 0
                }, {
                    duration: 300,
                    complete: done
                });
            },
            transitionSlideDownBigOut: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {
                    opacity: [0, 1],
                    translateY: 75,
                    translateZ: 0
                }, {
                    duration: 300,
                    complete: done
                });
            },
           transitionPulse: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, 'callout.pulse', {
                    duration: 300,
                    complete: done
                });
            },
            removeSelected: function () {
                if (confirm('Remove ' + this.removeCheckboxList + '?')) {
                    this.removeCheckboxList.forEach(this.remove);
                    this.removeCheckboxList = [];
                    this.editMode = false;
                }
            },
            moveSelected: function () {
                if (confirm('Move ' + this.moveCheckboxList + ' to .old?')) {
                    this.moveCheckboxList.forEach(this.move);
                    this.moveCheckboxList = [];
                    this.editMode = false;
                }
            },
            historySelectAll: function () {
                if (this.allSelected) {
                    if (this.historyShow)
                        this.history.forEach((item) => {
                            this.removeCheckboxList.push(item.fullpath);
                        });
                    else
                        this.filelist.forEach((item) => {
                            this.moveCheckboxList.push(item.path);
                        });
                } else {
                    this.removeCheckboxList = [];
                    this.moveCheckboxList = [];
                }
            },
            volUp: function (obj) {
                server.dlna_vol('up').then(window.appView.out).catch(window.appView.out);
            },
            volDown: function (obj) {
                server.dlna_vol('down').then(window.appView.out).catch(window.appView.out);
            },
            pressOpen: function (obj) {
                var target = obj.target.tagName === 'TD' ? obj.target : obj.target.parentNode;
                this.open(target.getAttribute('data-target'), 'folder');
            },
            tapOpen: function (obj) {
                var target = obj.target.tagName === 'TD' ? obj.target : obj.target.parentNode;
                this.open(target.getAttribute('data-path'), target.getAttribute('data-type'));
            },
            showFixBar: function () { // show fix bar and then hide
				console.log('show nav')
                this.fixBar.show = true;
                if (this.fixBar.timerId) {
                    clearTimeout(this.fixBar.timerId);
                    this.fixBar.timerId = null;
                }
                this.fixBar.timerId = setTimeout(() => {
                        this.fixBar.show = false;
                    }, 3500);
            },
            out: function (str) {
                if (str !== '') {
                    if (this.output.timerId) {
                        clearTimeout(this.output.timerId);
                        this.output.timerId = null;
                    }
                    this.output.text = str;
                    this.output.show = true;
                    this.output.timerId = setTimeout(() => {
                            this.output.show = false;
                        }, 2100);
                }
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
                if (this.video.sizeBtnText === 'auto')
                    this.videoAdapt();
                else {
                    this.video.sizeBtnText = 'auto';
                    if (this.$refs.video.width < window.innerWidth && this.$refs.video.height < window.innerHeight) {
                        this.$refs.video.style.width = this.$refs.video.videoWidth + "px";
                        this.$refs.video.style.height = this.$refs.video.videoHeight + "px";
                    }
                }
            },
            historyCallBack: function (data) {
                this.history = data;
            },
            showHistory: function () {
                server.list_history().then(this.historyCallBack).catch(window.appView.out);
                this.historyShow = true;
            },
            fileSystemCallBack: function (data) {
                this.filelist = data;
            },
            remove: function (obj) {
                server.remove_history(obj).then(this.historyCallBack).catch(window.appView.out);
            },
            move: function (obj) {
                server.file_move(obj).then(this.fileSystemCallBack).catch(window.appView.out);
                if (this.historyShow)
                    this.showHistory();
            },
            open: function (obj, type) {
                switch (type) {
                case "folder":
                    this.historyShow = false;
                    server.file_list(obj).then(this.fileSystemCallBack).catch(window.appView.out);
                    break;
                case "mp4":
                    if (!this.dlnaMode)
                        this.playInWeb(obj);
                case "video":
                    if (this.dlnaMode)
                        server.dlna_load(obj, window.location.host).then(window.appView.out).catch(window.appView.out);
                    break;
                default:
                }
            },
            checkFileExist: function (obj) {
                for (var item in this.history) {
                    if (this.history[item].filename === obj)
                        return this.history[item].exist;
                }
                return true;
            },
            playInWeb: function (obj) {
                if (!this.checkFileExist(obj)) {
                    this.out(obj + ' not exist');
                    return;
                }
                this.video.src = obj;
                this.mode = "WebPlayer";
                this.browserShow = false;
            },
            setDmr: function (dmr) {
                server.dlna_set_dmr(dmr).then(() => {this.mode='DLNA';}).catch(window.appView.out);
            },
            positionSeek: function () {
                var position = secondToTime(offset_value(timeToSecond(this.dlnaInfo.RelTime), this.positionBarVal, this.positionBarMax));
                server.dlna_seek(position).then(window.appView.out).catch(window.appView.out);
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
            seek: function (position) {
              if (this.dlnaMode)
                  server.dlna_seek(secondToTime(position)).then(window.appView.out).catch(window.appView.out);
              else if (this.wpMode)
                  this.$refs.video.currentTime = position;
            },
            videosave: function () {
                this.video.lastplaytime = new Date().getTime(); //to detect if video is playing
                if (this.$refs.video.readyState === 4 && Math.floor(Math.random() * 99) > 70) //randomly save play position
                    server.save_history(this.video.src, this.$refs.video.currentTime, this.$refs.video.duration).catch(window.appView.out);
            },
			volumechange: function () {
				console.log(this.$refs.video.volume)
				localStorage.volume = this.$refs.video.volume;
			},
            videoload: function () {
                this.videoAdapt();
                this.out('adapt');
                this.$refs.video.currentTime = Math.max(this.wpPosition - 0.5, 0);
                this.output.smallText = "Play from";
				this.$refs.video.volume = localStorage.volume;
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
                    server.dlna_seek(secondToTime(newtime)).then(window.appView.out).catch(window.appView.out);
                    console.log('swipe');
                } else
                    console.log('pan');
            },
        },
        created: function () {
            window.onresize = this.videoAdapt;
            this.isIos = !!navigator.userAgent.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
            this.isIos = true;
            if (!this.isIos) {
                this.fixBar.show = false;
                document.onmousemove = this.showFixBar;
            }
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
                // if (now - lastTouchEnd <= 300) {
                if (now - lastTouchEnd <= 350) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
        },
        mounted: function () {
            this.$nextTick(function () {
                // window.appView.showHistory();
            });
        },
    });


function webSocketLink(options) {
    var ws = new ReconnectingWebSocket(options.url);
    ws.onmessage = function (evt) {
        var data = JSON.parse(evt.data);
        options.onmessage(data);
    }
    ws.onopen = options.onopen;
    ws.onclose = options.onclose;
    ws.onerror = options.onerror;
    return ws;
}

var methods = {};

var connApi = webSocketLink({
        url: 'ws://' + window.location.host + '/link',
        onmessage: function (data) {
            console.log(data);
            var errorCallback = window.appView.out;
            if (data.hasOwnProperty('jsonrpc')) {
                if (data.hasOwnProperty('result')) {
                    var callback = methods[data.id];
                    delete methods[data.id];
                    if (typeof(callback.resolve) === 'undefined')
                        callback.resolve = window.appView.out;
                    if (callback)
                        callback.resolve(data.result);
                } else
                    errorCallback(data.error);
            } else
                window.appView.dlnaInfo = data;
        },
        onclose: function () {
            Vue.set(window.appView.dlnaInfo, 'CurrentTransportState', 'disconnected');
            console.log('disconnected');
        },
        onopen: function () {
            window.appView.out('connected');
        }
    });
    

function jsonrpcWS(jsonData) {
    return new Promise(function (resolve, reject) {
        connApi.send(JSON.stringify(jsonData));
        methods[jsonData.id] = {resolve:resolve, reject:reject};
    });
}


//const server = JsonRpc(jsonrpcAxios('/api'));
var server = JsonRpc(jsonrpcWS);
