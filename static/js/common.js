"use strict";
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
 * Calculator offset value
 *
 * @method offset_value
 * @param {Integer} current, value, max
 * @return {Float}
 */
function offset_value(current, value, max) {
    var relduration;
    if (value < current)
        relduration = current;
    else
        relduration = max - current;
    var s = Math.sin((value - current) / relduration * 1.5707963267948966192313216916);
    return Math.round(current + Math.abs(Math.pow(s, 3)) * (value - current));
}

function vueTouch(el, type, binding) {
    this.el = el;
    this.type = type;
    this.binding = binding;
    var hammertime = new Hammer(this.el);
    hammertime.on(this.type, this.binding.value);
    hammertime.get('swipe').set({
        velocity: 0.01
    });
};

Vue.directive("tap", {
    bind: function (el, binding) {
        new vueTouch(el, "tap", binding);
    }
});

Vue.directive("press", {
    bind: function (el, binding) {
        new vueTouch(el, "press", binding);
    }
});

Vue.directive("pan", {
    bind: function (el, binding) {
        new vueTouch(el, "panleft panright", binding);
    }
});

Vue.directive("swipe", {
    bind: function (el, binding) {
        new vueTouch(el, "swipeleft swiperight", binding);
    }
});

Vue.component('x-transition-fade', {
    functional: true,
    render: function (createElement, context) {
        var data = {
            on: {
                enter: function (el, done) {
                    Velocity(el, 'stop');
                    Velocity(el, {
                        opacity: [0.75, 0]
                    }, {
                        duration: 170,
                        complete: done
                    });
                },
                leave: function (el, done) {
                    Velocity(el, 'stop');
                    Velocity(el, {
                        opacity: 0
                    }, {
                        duration: 600,
                        complete: done
                    });
                }
            }
        }
        return createElement('transition', data, context.children)
    }
})
