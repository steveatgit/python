/*jslint sloppy: true, vars: true, white: true, nomen: true, browser: true  */
/*global phantom, console, require, QUnit */

/*
A phantomjs QUnit test runner with support for JUnit, TAP, and pretty
console output.
*/

(function() {
    'use strict';

    var args = require('system').args;

    // Takes up to 4 args
    // 1. URL
    // 2. Output Format: (junit, tap, console (default))
    // 3. Verbosity (1: Show all assertions (default), 0: Show only test results)
    // 4. The errorcode to use for the phantomjs process if tests fail (Defaults to 1).

    var url = args[1];
    var output = "console";
    var verbose = true;
    var errorcode = 1;
    var usecolor = true;
    if (args.length > 2) {
        output = args[2];
        if (args.length > 3) {
            verbose = (args[3] === '1');
            if (args.length > 4) {
                errorcode = parseInt(args[4], 10);
                if (args.length > 5) {
                    usecolor = (args[5] === '1');
                }
            }
        }
    }


    var COLORS = {
        'pass': 90,
        'fail': 31,
        'bright pass': 92,
        'bright fail': 91,
        'bright yellow': 93,
        'pending': 36,
        'suite': 0,
        'error title': 0,
        'error message': 31,
        'error stack': 90,
        'checkmark': 32,
        'fast': 90,
        'medium': 33,
        'slow': 31,
        'green': 32,
        'light': 90,
        'diff gutter': 90,
        'diff added': 42,
        'diff removed': 41
    };

    function color(type, str) {
        if (!usecolor) {
            return str;
        }
        return '\u001b[' + COLORS[type] + 'm' + str + '\u001b[0m';
    }



    /*
    JUnit XML output for QUnit tests compatible with PhantomJS 1.3
    https://gist.github.com/1363104
    */
    var JUnitPlugin = (function () {
        var module, moduleStart, testStart, testCases = [],
            current_test_assertions = [], JUnitPlugin = {};

        JUnitPlugin.begin = function() {
            // That does not work when invoked in PhantomJS
            require("system").stderr.write('<?xml version="1.0" encoding="UTF-8"?>\n');
            require("system").stderr.write('<testsuites>\n');
        };

        JUnitPlugin.moduleStart = function(context) {
            moduleStart = new Date();
            module = context.name;
            testCases = [];
        };

        JUnitPlugin.moduleDone = function(context) {
            // context = { name, failed, passed, total }
            var i, l, xml = '\t<testsuite name="' + context.name + '" time="' + (new Date() - moduleStart) / 1000 + '"';
            if (testCases.length) {
                xml += '>\n';
                for (i = 0, l = testCases.length; i < l; i+=1) {
                    xml += testCases[i];
                }
                xml += '\t</testsuite>\n';
            } else {
                xml += '/>\n';
            }
            require("system").stderr.write(xml);
        };

        JUnitPlugin.testStart = function() {
            testStart = new Date();
        };

        JUnitPlugin.testDone = function(result) {
            // result = { name, failed, passed, total }
            var i, xml = '\t\t<testcase name="' + module + ':' + result.name + '" time="' + (new Date() - testStart) / 1000 + '"';
            if (result.failed) {
                xml += '>\n';
                for (i = 0; i < current_test_assertions.length; i+=1) {
                    xml += "\t\t\t" + current_test_assertions[i];
                }
                xml += '\t\t</testcase>\n';
            } else {
                xml += '/>\n';
            }
            current_test_assertions = [];
            testCases.push(xml);
        };

        JUnitPlugin.log = function(details) {
            //details = { result , actual, expected, message }
            if (details.result) {
                return;
            }
            var message = details.message || "";
            if (details.expected) {
                if (message) {
                    message += ", ";
                }
                message = "Expected: " + details.expected + ", Actual: " + details.actual;
            }
            var xml = '<failure type="failed" message="' + message + '"/>\n';

            current_test_assertions.push(xml);
        };

        JUnitPlugin.done = function(result) {
            require("system").stderr.write('</testsuites>');
            return result.failed > 0 ? 1 : 0;
        };

        return JUnitPlugin;
    }());


    var ConsolePlugin = (function () {
        var begin, module, moduleStart, testStart, testCases = [],
            current_test_assertions = [], plugin = {};
        var testDetails = {
            passed: 0,
            failed: 0,
            total: 0
        };

        plugin.begin = function() {
            // That does not work when invoked in PhantomJS
            begin = new Date();
            console.log('Tests Started');
            console.log('');
        };

        plugin.moduleStart = function(context) {
            moduleStart = new Date();
            module = context.name;
            testCases = [];
            console.log(module);
            console.log('');
        };

        plugin.moduleDone = function(details) {
            var runtime = (new Date() - moduleStart) / 1000;
            console.log('');
        };

        plugin.testStart = function(details) {
            testStart = new Date();
            if (verbose) {
                console.log('     ' + details.name);
            }
        };

        plugin.testDone = function(details) {
            var runtime = (new Date() - testStart) / 1000;
            if (details.failed) {
                testDetails.failed += 1;
            } else {
                testDetails.passed += 1;
            }
            testDetails.total += 1;
            if (!verbose) {
                console.log('    ' + (details.failed ?  color('fail', '× ') : color('checkmark', '✔ ')) + color(details.failed ? 'fail' : 'pass', details.name + ' (' + runtime + 's)')); 
            }
        };

        plugin.log = function(details) {
            var runtime = (new Date() - testStart) / 1000;
            if (verbose) {
                console.log('        ' + (details.result ?  color('checkmark', '✓ ') : color('fail', '☓ ')) + color(details.result ? 'pass' : 'fail', (details.message || details.name) + ' (' + runtime + 's)')); 
            }

            if (details.result) {
                return;
            }
            var message = details.message || "";
            if (details.expected) {
                if (message) {
                    message += ", ";
                }
                message = "expected: " + details.expected + ", but was: " + details.actual;
            }

            current_test_assertions.push({
                module: module,
                name: details.name,
                message: message,
                source: details.source
            });
        };

        plugin.done = function(details) {
            // That does not work when invoked in PhantomJS
            testDetails.runtime = details.runtime;
            details = (verbose ? details : testDetails);

            // TODO: Traceback summary.
            if (details.failed) {
                var i;
                for (i = 0; i < current_test_assertions.length; i += 1) {
                    var err = current_test_assertions[i];
                    console.log('======================================================================');
                    console.log('FAIL: ' + color('error title', err.name) + '(' + err.module + ')');
                    console.log('----------------------------------------------------------------------');
                    console.log(color('error message', err.message));
                    if (err.source) {
                        console.log(color('error stack', err.source));
                    }
                }
            }

            console.log('----------------------------------------------------------------------');
            console.log('Ran ' + details.total + ' tests in ' + (details.runtime / 1000) + ' secs');
            console.log('');
            if (details.failed) {
                console.log(color('bright fail', 'FAILED') + ' (failures=' + details.failed + ')');
            } else {
                console.log(color('bright pass', 'OK'));
            }
        };

        return plugin;
    }());

    //-----------------------------------------

    var OUTPUT_FORMATS = {
        'junit': JUnitPlugin,
        'console': ConsolePlugin
    };



    var OutputPlugin = OUTPUT_FORMATS[output];
    if (!OutputPlugin) {
        console.error('Bad output format: ' + output);
        phantom.exit(1);
    }


    var page = require('webpage').create();

    function setupCallbacks() {
        window.document.addEventListener('DOMContentLoaded', function() {
            // Setup Error Handling
            var qunit_error = window.onerror;
            window.onerror = function ( error, filePath, linerNr ) {
                qunit_error(error, filePath, linerNr);
                if (typeof window.callPhantom === 'function') {
                    window.callPhantom({
                        'name': 'Window.error',
                        'error': error,
                        'filePath': filePath,
                        'linerNr': linerNr
                    });
                }
            };

            var callback = function(name) {
                return function(details) {
                    if (typeof window.callPhantom === 'function') {
                        window.callPhantom({
                            'name': 'QUnit.' + name,
                            'details': details
                        });
                    }
                };
            };

            var i, callbacks = [
                'begin', 'done', 'log',
                'moduleStart', 'moduleDone',
                'testStart', 'testDone'
            ];
            for (i=0; i<callbacks.length;i+=1) {
                QUnit[callbacks[i]](callback(callbacks[i]));
            }

        }, false);
    }


    // Route `console.log()` calls from within the Page context to the main Phantom context (i.e. current `this`)
    page.onConsoleMessage = function(msg) {
        console.log(msg);
    };

    page.onInitialized = function() {
        page.evaluate(setupCallbacks);
    };

    page.onCallback = function(message) {
        var result,
            failed;

        if (message) {
            if (message.name === 'Window.error') {
                phantom.exit(1);
            } else {
                var msgs = message.name.split(".");
                if (msgs[0] === "QUnit") {

                    var cb = OutputPlugin[msgs[1]];
                    if (cb) {
                        cb(message.details);
                    }

                    if (msgs[1] === 'done') {
                        result = message.data;
                        failed = !result || result.failed;

                        phantom.exit(failed ? errorcode : 0);
                    }
                }
            }
        }
    };

    page.open(url, function(status) {
        if (status !== 'success') {
            console.error('Unable to access network: ' + status);
            phantom.exit(1);
        } else {
            // Cannot do this verification with the 'DOMContentLoaded' handler because it
            // will be too late to attach it if a page does not have any script tags.
            var qunitMissing = page.evaluate(function() { return (typeof QUnit === 'undefined' || !QUnit); });
            if (qunitMissing) {
                console.error('The `QUnit` object is not present on this page.');
                phantom.exit(1);
            }

            // Do nothing... the callback mechanism will handle everything!
        }
    });

    page.onError = function(msg, trace) {
        console.error(color('error message', msg));
        trace.forEach(function(item) {
            console.error(color('error stack', '  ' + item.file + ':' + item.line));
        });
        console.error('');
        phantom.exit(1);
    };
}());
