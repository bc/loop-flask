function sample_data() {
    return {
        "CPU": {
            "name": "Finder",
            "percent": Math.random() * 100,
            "unixtime": Date.now() / 1000
        },
        "OBS": {
            "unixtime": Date.now() / 1000,
            "value": Math.random()
        }
    }
}

function handle(result_json) {
    datalist.unshift(result_json);
    update_rawconsole();
    update_live_progress(result_json["OBS"]);
    update_live_proc(result_json["CPU"]);
}

const observationPercentage = document.getElementById("percentage")
const obsTime = document.getElementById("obsTime")

const procPercentage = document.getElementById("procPercentage")
const procTime = document.getElementById("procTime")

function millisecondsToStr(milliseconds) {
    // TIP: to find current time in milliseconds, use:
    // var  current_time_milliseconds = new Date().getTime();

    function numberEnding(number) {
        return (number > 1) ? 's' : '';
    }

    var temp = Math.floor(milliseconds / 1000);
    var years = Math.floor(temp / 31536000);
    if (years) {
        return years + ' year' + numberEnding(years);
    }
    //TODO: Months! Maybe weeks?
    var days = Math.floor((temp %= 31536000) / 86400);
    if (days) {
        return days + ' day' + numberEnding(days);
    }
    var hours = Math.floor((temp %= 86400) / 3600);
    if (hours) {
        return hours + ' hour' + numberEnding(hours);
    }
    var minutes = Math.floor((temp %= 3600) / 60);
    if (minutes) {
        return minutes + ' minute' + numberEnding(minutes);
    }
    var seconds = temp % 60;
    if (seconds) {
        return seconds + ' second' + numberEnding(seconds);
    }
    return 'less than a second'; //'just now' //or other string you like;
}

function update_live_proc(proc) {
    procPercentage.innerText = `${proc.percent}%`
    cpu_title_element.innerText = `${proc.name}: Current CPU Use`
    procTime.innerText = `Updated ${((Date.now() / 1000) - proc.unixtime).toFixed(2)}s ago`;
}

function delta_time_human_readable(unix_seconds) {
    var elapsed_str = millisecondsToStr(((Date.now() / 1000) - unix_seconds).toFixed(2));
    return elapsed_str;
}

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return pair[1];
        }
    }
    alert('Query Variable ' + variable + ' not found');
}

function update_live_progress(observation) {
    observationPercentage.innerText = `${observation.value * 100}%`;
    var elapsed_str = delta_time_human_readable(observation.unixtime);
    obsTime.innerText = `Updated ${elapsed_str} ago`;
}

function GET_data(token) {
    var settings = {
        //TODO handle cors correctly
        "url": `/listen/?token=${token}`,
        "method": "GET",
        "timeout": 0,
    };

    $.ajax(settings).done(function (response) {
        handle(response);
    });
}

let datalist = [];
const console_element = document.getElementById("jsonRaw");
const cpu_title_element = document.getElementById("cpu_title");

function update_rawconsole() {
    console_element.innerText = JSON.stringify(datalist, undefined, 4);
}

var myToken = getQueryVariable("token")
if (!myToken) {
    alert("Retry after adding ?token=X at the end with your URL request. Replace X with your token.")
} else {
    window.setInterval(() => GET_data(myToken), 1000);
    console.log("invoked");
}
