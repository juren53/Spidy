/****************************************************************************
**
** Copyright (C) 2016 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the examples of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/

"use strict";

var QWebChannelMessageTypes = {
    signal: 1,
    propertyUpdate: 2,
    init: 3,
    idle: 4,
    debug: 5,
    invokeMethod: 6,
    connectToSignal: 7,
    disconnectFromSignal: 8,
    setProperty: 9,
    response: 10,
};

var QWebChannel = function(transport, initCallback)
{
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("The QWebChannel expects a transport object with a send function and onmessage callback property." +
                      " Given is: transport: " + typeof(transport) + ", transport.send: " + typeof(transport.send));
        return;
    }

    var channel = this;
    this.transport = transport;

    this.send = function(data)
    {
        if (typeof(data) !== "string") {
            data = JSON.stringify(data);
        }
        channel.transport.send(data);
    };

    this.transport.onmessage = function(message)
    {
        var data = message.data;
        if (typeof data === "string") {
            data = JSON.parse(data);
        }
        switch (data.type) {
            case QWebChannelMessageTypes.signal:
                channel.handleSignal(data);
                break;
            case QWebChannelMessageTypes.response:
                channel.handleResponse(data);
                break;
            case QWebChannelMessageTypes.propertyUpdate:
                channel.handlePropertyUpdate(data);
                break;
            case QWebChannelMessageTypes.init:
                channel.handleInit(data);
                break;
            default:
                console.error("invalid message received:", message.data);
                break;
        }
    };

    this.execCallbacks = {};
    this.execId = 0;
    this.exec = function(data, callback)
    {
        if (!callback) {
            // if no callback is given, send directly
            channel.send(data);
            return;
        }
        if (channel.execId === Number.MAX_VALUE) {
            // wrap
            channel.execId = Number.MIN_VALUE;
        }
        if (data.hasOwnProperty("id")) {
            console.error("Cannot exec message with property id: " + JSON.stringify(data));
            return;
        }
        data.id = channel.execId++;
        channel.execCallbacks[data.id] = callback;
        channel.send(data);
    };

    this.objects = {};

    this.handleSignal = function(message)
    {
        var object = channel.objects[message.object];
        if (object) {
            object.signalEmitted(message.signal, message.args);
        } else {
            console.warn("Unhandled signal: " + message.object + "::" + message.signal);
        }
    };

    this.handleResponse = function(message)
    {
        if (!message.hasOwnProperty("id")) {
            console.error("Invalid response message received: ", JSON.stringify(message));
            return;
        }
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    };

    this.handlePropertyUpdate = function(message)
    {
        for (var i in message.data) {
            var data = message.data[i];
            var object = channel.objects[data.object];
            if (object) {
                object.propertyUpdate(data.signals, data.properties);
            } else {
                console.warn("Unhandled property update: " + data.object + "::" + data.signal);
            }
        }
        channel.exec({type: QWebChannelMessageTypes.idle});
    };

    this.handleInit = function(message)
    {
        for (var objectName in message.data) {
            var object = message.data[objectName];
            var objectId = object.__id__;
            let objectWrapper = new QObject(objectId, objectName, object, channel);
            channel.objects[objectId] = objectWrapper;
        }

        // now unwrap properties, which might reference other registered objects
        for (var objectId in channel.objects) {
            channel.objects[objectId].unwrapProperties();
        }

        if (initCallback) {
            initCallback(channel);
        }

        channel.exec({type: QWebChannelMessageTypes.idle});
    };

    this.debug = function(message)
    {
        channel.send({type: QWebChannelMessageTypes.debug, data: message});
    };

    channel.exec({type: QWebChannelMessageTypes.init}, function(data) {
        channel.handleInit(data);
    });
};

function QObject(id, objectName, initialProperties, webChannel)
{
    this.__id__ = id;
    this.__objectName__ = objectName;
    this.__propertyCache__ = {};
    this.__signalHandlers__ = {};
    this.__unwrappedProperties__ = false;
    this.__webChannel__ = webChannel;

    this.propertyUpdate = function(signals, propertyMap)
    {
        // update property cache
        for (var propertyName in propertyMap) {
            var propertyValue = propertyMap[propertyName];
            this.__propertyCache__[propertyName] = propertyValue;
        }

        // emit all newly connected signals
        for (var signalName in signals) {
            var signalHandlers = this.__signalHandlers__[signalName];
            if (signalHandlers) {
                var args = signals[signalName];
                for (var i = 0; i < signalHandlers.length; ++i) {
                    signalHandlers[i].apply(this, args);
                }
            }
        }
    };

    this.signalEmitted = function(signalName, signalArgs)
    {
        var handlers = this.__signalHandlers__[signalName];
        if (handlers) {
            for (var i = 0; i < handlers.length; ++i) {
                handlers[i].apply(this, signalArgs);
            }
        }
    };

    this.unwrapProperties = function()
    {
        if (this.__unwrappedProperties__)
            return;
        this.__unwrappedProperties__ = true;

        for (var propertyName in this.__propertyCache__) {
            this.__propertyCache__[propertyName] = this.unwrapValue(propertyName, this.__propertyCache__[propertyName]);
        }
    };

    this.unwrapValue = function(propertyName, value)
    {
        if (typeof value !== "object" || value === null)
            return value;

        if (value.hasOwnProperty("__objectId__")) {
            return webChannel.objects[value.__objectId__];
        } else if (value.hasOwnProperty("__array__")) {
            var unwrappedArray = [];
            for (var i = 0; i < value.__array__.length; ++i) {
                unwrappedArray.push(this.unwrapValue(propertyName + "[" + i + "]", value.__array__[i]));
            }
            return unwrappedArray;
        } else if (value.hasOwnProperty("__object__")) {
            var unwrappedObject = {};
            for (var i in value.__object__) {
                unwrappedObject[i] = this.unwrapValue(propertyName + "." + i, value.__object__[i]);
            }
            return unwrappedObject;
        }
        return value;
    };

    // ------------------ Methods and properties

    this.connectToSignal = function(signalName, signalFunction)
    {
        var signalHandlers = this.__signalHandlers__[signalName];
        if (!signalHandlers) {
            signalHandlers = [];
            this.__signalHandlers__[signalName] = signalHandlers;

            // add the callback to the Qt object
            var msg = {
                type: QWebChannelMessageTypes.connectToSignal,
                object: this.__id__,
                signal: signalName
            };
            webChannel.send(msg);
        }
        signalHandlers.push(signalFunction);
    };

    this.disconnectFromSignal = function(signalName, signalFunction)
    {
        var signalHandlers = this.__signalHandlers__[signalName];
        if (signalHandlers) {
            var idx = signalHandlers.indexOf(signalFunction);
            if (idx !== -1) {
                signalHandlers.splice(idx, 1);
            }
            if (signalHandlers.length === 0) {
                var msg = {
                    type: QWebChannelMessageTypes.disconnectFromSignal,
                    object: this.__id__,
                    signal: signalName
                };
                webChannel.send(msg);
                delete this.__signalHandlers__[signalName];
            }
        }
    };

    // initialize property cache with current values
    // properties will be available as normal JS properties
    for (var propertyName in initialProperties) {
        if (propertyName === "__id__" || propertyName === "__objectName__")
            continue;
        var propertyValue = initialProperties[propertyName];
        this.__propertyCache__[propertyName] = propertyValue;
    }

    // setup property update handler using the meta-info
    var thisobject = this;
    for (var propertyName in initialProperties) {
        if (propertyName === "__id__" || propertyName === "__objectName__")
            continue;
        setupProperty(propertyName);
    }

    function setupProperty(propertyName)
    {
        // property accessor for cached values
        Object.defineProperty(thisobject, propertyName, {
            get: function() { return thisobject.__propertyCache__[propertyName]; },
            set: function(value) { 
                if (value === undefined) {
                    console.warn("Property setter for " + propertyName + " called with undefined value!");
                    return;
                }
                thisobject.__propertyCache__[propertyName] = value;
                var valueToSend = value;
                
                var msg = {
                    type: QWebChannelMessageTypes.setProperty,
                    object: thisobject.__id__,
                    property: propertyName,
                    value: valueToSend
                };
                webChannel.send(msg);
            }
        });
    }

    // handle methods via invokeMethod
    var invokables = initialProperties.__invokables__;
    if (invokables) {
        for (var i = 0; i < invokables.length; ++i) {
            var methodName = invokables[i];
            setupMethod(methodName);
        }
    }

    function setupMethod(methodName)
    {
        var thisobject = webChannel.objects[id];
        thisobject[methodName] = function() {
            var args = [];
            var callback;
            for (var i = 0; i < arguments.length; ++i) {
                if (typeof arguments[i] === "function")
                    callback = arguments[i];
                else
                    args.push(arguments[i]);
            }

            var msg = {
                type: QWebChannelMessageTypes.invokeMethod,
                object: id,
                method: methodName,
                args: args
            };
            if (callback) {
                var replyHandler = function(response) {
                    callback(response);
                };
                msg.id = webChannel.execId;
                webChannel.execCallbacks[msg.id] = replyHandler;
                webChannel.execId += 1;
            }
            webChannel.send(msg);
        };
    }

    // connects a Qt signal to a JavaScript function
    this.connect = function(signalName, callback) {
        this.connectToSignal(signalName, callback);
    };

    // disconnects a Qt signal from a JavaScript function
    this.disconnect = function(signalName, callback) {
        this.disconnectFromSignal(signalName, callback);
    };
};

