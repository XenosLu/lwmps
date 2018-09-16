"use strict";
var icon = {
    "folder": "oi-folder",
    "mp4": "oi-video",
    "video": "oi-video",
    "other": "oi-file"
};

//window.appView.showModal();  // show modal at start

/**
 * Ajax get and out result
 *
 * @method get
 * @param {String} url
 */
// function get(url) {
    // // $.get(url, out);
// }

/**
 * Render history list box from ajax
 *
 * @method history
 * @param {String} str
 */
function getHistory(str) {
    // $.ajax({
        // url: encodeURI(str),
        // dataType: "json",
        // timeout: 1999,
        // type: "get",
        // success: function (data) {
            // window.appView.uiState.historyShow = true;
            // window.appView.history = data.history;
        // },
        // error: function (xhr) {
            // window.appView.out(xhr.statusText);
        // }
    // });
    axios.get(encodeURI(str))
    .then(function (response) {
        window.appView.uiState.historyShow = true;
        window.appView.history = response.data.history;
    })
    .catch(function (error) {
        window.appView.out(error.response.statusText);
    });
}

/**
 * Made an output box to show some text notification
 *
 * @method out
 * @param {String} str
 */
// function out(str) {
    // window.appView.out(str);
// }

function dlnaTouch() {
    var hammertimeDlna = new Hammer(document.getElementById("DlnaTouch"));
    hammertimeDlna.on("panleft panright swipeleft swiperight", function (ev) {
        var newtime = window.appView.positionBarVal + ev.deltaX / 4;
        newtime = Math.max(newtime, 0);
        newtime = Math.min(newtime, window.appView.positionBarMax);
        window.appView.out(secondToTime(newtime));
        if (ev.type.indexOf("swipe") != -1)
            window.appView.get("/dlna/seek/" + secondToTime(newtime));
        // console.log(ev);
        // console.log(ev.type);
    });
}

function dlnalink() {
    var ws = new WebSocket("ws://" + window.location.host + "/link");
    ws.onmessage = function (e) {
        var data = JSON.parse(e.data);
        console.log(data);
        // if (window.appView.positionBarCanUpdate && data.hasOwnProperty('RelTime')) {
            // window.appView.positionBarVal = timeToSecond(data.RelTime);
        // }
        window.appView.dlnaInfo = data;
    }
    ws.onclose = function () {
        window.appView.dlnaInfo.CurrentTransportState = 'disconnected';
    };
    ws.onerror = function () {
        console.log('error');
    };
    ws.check = function () {
        if (this.readyState == 3)
            ws_link = dlnalink();
    };
    return ws;
}

function modalTouch() {
    var hammertimeModal = new Hammer(document.getElementById("ModalTouch"));

    hammertimeModal.on("swipeleft", function (ev) {
        window.appView.swipeState -= 1;
        if (window.appView.swipeState < -1)
            window.appView.swipeState = -1;
    });
    hammertimeModal.on("swiperight", function (ev) {
        window.appView.swipeState += 1;
        if (window.appView.swipeState > 0)
            window.appView.swipeState = 0;
    });
    // var press = new Hammer.Press({time: 500});
    // press.requireFailure(new Hammer.Tap());
    // hammertimeModal.add(press);
    hammertimeModal.on("press", function (ev) {
        var target = ev.target.tagName == 'TD' ? ev.target : ev.target.parentNode;
        if (target.hasAttribute("data-target"))
            window.appView.open(target.getAttribute('data-target'), 'folder');
        console.log(target.getAttribute('data-target'));
    });
    hammertimeModal.on("tap", function (ev) {
        var target = ev.target.tagName == 'TD' ? ev.target : ev.target.parentNode;
        if (target.hasAttribute("data-type"))
            window.appView.open(target.getAttribute('data-path'), target.getAttribute('data-type'));
        console.log(target.getAttribute('data-target'));
    });
}

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
}

window.appView = new Vue({
        delimiters: ['${', '}'],
        el: '#v-common',
        data: {
            video: {
                lastplaytime: 0,
                sizeBtnText: 'origin',
                src: '', // web player source
            },
            icon: icon,
            swipeState: 0, // modal touch state
            mode: '', // mode of player, switch between empty/DLNA/WebPlayer
            uiState: {
                modalShow: false, // true if the modal is show
                historyShow: true, // ture if modal is history, false if modal content is file list
            },
            history: [], // updated by ajax
            filelist: [], // updated by ajax
            positionBarCanUpdate: true, //dlna position bar
            positionBarVal: 0,
            dlnaInfo: { // updated by websocket
                CurrentDMR: 'no DMR',
                CurrentTransportState: '',
                TrackURI: '',
            },
            fixBar: {
                show: true,
                timerId: null,
            },
            output: {
                text: '',
                smallText: '',
                show: false,
                timerId: null,
            },
            isIos: null,
        },
        watch: {
            'dlnaInfo.RelTime': function () {
                console.log('reltime update');
                if (this.positionBarCanUpdate)
                    this.positionBarVal = timeToSecond(this.dlnaInfo.RelTime);
                console.log(this.positionBarVal);
            }
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
                if(this.dlnaInfo.hasOwnProperty('TrackDuration'))
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
            test: function (obj) {
                console.log("test " + obj);
                this.out('test');
            },
            showFixBar: function () {
                this.fixBar.show = true;
                if (this.fixBar.timerId) {
                    clearTimeout(this.fixBar.timerId);
                    this.fixBar.timerId = null;
                }
                this.fixBar.timerId = setTimeout(function () {
                        window.appView.fixBar.show = false;
                    }, 3000);
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
                Velocity(el, {translateX: '-50%', translateY: '-50%'}, {duration: 0});
                Velocity(el, {opacity: 0.8}, {duration: 250});
            },
            outFadeOut: function (el, done) {
                Velocity(el, 'stop');
                Velocity(el, {opacity: 0}, {duration: 600});
            },
            out_old: function (str) {
                if (str !== "") {
                    this.output.text = str;
                    var el = this.$refs.output;
                    Velocity(el, 'stop');
                Velocity(el, {translateX: '-50%', translateY: '-50%'}, {duration: 0});
                    Velocity(el, {opacity: 0.8}, {duration: 250});
                    Velocity(el, {opacity: 0}, {delay: 1800, duration: 625});
                }
            },
            dlnaToogle: function () {
                this.mode = this.mode !== '' ? '' : 'DLNA';
                localStorage.mode = this.mode;
            },
            videoAdapt: function () {
                if (this.wpMode) {
                    this.video.sizeBtnText = "orign";
                    var video_ratio = this.$refs.video.videoWidth / this.$refs.video.videoHeight;
                    var page_ratio = window.innerWidth / window.innerHeight;
                    if (page_ratio < video_ratio) {
                        var width = window.innerWidth + "px";
                        var height = Math.floor(window.innerWidth / video_ratio) + "px";
                    } else {
                        var width = Math.floor(window.innerHeight * video_ratio) + "px";
                        var height = window.innerHeight + "px";
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
                this.uiState.modalShow = true;
                if (this.uiState.historyShow)
                    this.showHistory();
            },
            showHistory: function () {
                getHistory("/hist/ls");
            },
            showFs: function (path) {
                axios.get(encodeURI(path))
                .then(function (response) {
                        window.appView.uiState.historyShow = false;
                        window.appView.filelist = response.data.filesystem;
                })
                .catch(function (error) {
                    // console.log(error.response);
                    window.appView.out(error.response.statusText);
                });
                
                // $.ajax({
                    // url: encodeURI(path),
                    // dataType: "json",
                    // timeout: 1999,
                    // type: "get",
                    // success: function (data) {
                        // window.appView.uiState.historyShow = false;
                        // window.appView.filelist = data.filesystem;
                    // },
                    // error: function (xhr) {
                        // window.appView.out(xhr.statusText);
                    // }
                // });
            },
            clearHistory: function () { // clear history button
                if (confirm("Clear all history?"))
                    getHistory("/hist/clear");
            },
            remove: function (obj) {
                if (confirm("Clear history of " + obj + "?"))
                    getHistory("/hist/rm/" + obj.replace(/\?/g, "%3F")); //?to%3F #to%23
            },
            move: function (obj) {
                if (confirm("Move " + obj + " to .old?")) {
                    this.showFs("/fs/move/" + obj);
                }
            },
            open: function (obj, type) {
                switch (type) {
                case "folder":
                    this.showFs("/fs/ls/" + obj + "/");
                    break;
                case "mp4":
                    if (!this.dlnaMode) {
                        this.playInWeb(obj);
                    }
                case "video":
                    if (this.dlnaMode)
                        this.get("/dlna/load/" + obj);
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
                this.uiState.modalShow = false;
            },
            setDmr: function (dmr) {
                this.get("/dlna/setdmr/" + dmr);
            },
            positionSeek: function () {
                this.get("/dlna/seek/" + secondToTime(offset_value(timeToSecond(this.dlnaInfo.RelTime), this.positionBarVal, this.positionBarMax)));
                this.positionBarCanUpdate = true;
            },
            positionShow: function () {
                this.out(secondToTime(offset_value(timeToSecond(this.dlnaInfo.RelTime), this.positionBarVal, this.positionBarMax)));
                this.positionBarCanUpdate = false;
            },
            get: function (url) {
                axios.get(url).then(function (response) {
                    window.appView.out(response.data);
                })
            },
            rate: function (ratex) {
                this.out(ratex + 'X');
                this.$refs.video.playbackRate = ratex;
            },
            videosave: function () {
                this.video.lastplaytime = new Date().getTime(); //to detect if video is playing
                if (this.$refs.video.readyState == 4 && Math.floor(Math.random() * 99) > 70) { //randomly save play position
                    axios.post('/wp/save/' + this.video.src, {
                        position: this.$refs.video.currentTime,
                        duration: this.$refs.video.duration
                    }).catch(function (error) {
                        window.appView.out(error.response.statusText);
                    });
                    // $.ajax({
                        // url: "/wp/save/" + this.video.src,
                        // data: {
                            // position: this.$refs.video.currentTime,
                            // duration: this.$refs.video.duration
                        // },
                        // timeout: 999,
                        // type: "POST",
                        // error: function (xhr) {
                            // this.out("save: " + xhr.statusText);
                        // }
                    // });
                }
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
        },
        updated: function () {
            this.$nextTick(function () {
                if (this.dlnaMode) {
                    window.document.title = "DMC - Light Media Player";
                    dlnaTouch();
                } else if (this.wpMode) {
                    window.document.title = this.video.src + " - Light Media Player";
                    if (this.isIos)
                        touchWebPlayer();
                } else
                    window.document.title = "Light Media Player";
            })
        },
        created: function () {
            if (typeof(localStorage.mode) !== "undefined")
                this.mode = localStorage.mode;
            window.onresize = this.videoAdapt;
            this.isIos = !!navigator.userAgent.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
            if (!this.isIos) {
                this.fixBar.show = false;
                document.onmousemove = this.showFixBar;
            }
            axios.defaults.timeout = 1999;
        },
    });

var ws_link = dlnalink();
setInterval("ws_link.check()", 1200);
modalTouch();
