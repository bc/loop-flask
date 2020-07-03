const obs_val = document.getElementById("obs_val");
const obs_time = document.getElementById("obs_time");

const cpu_val = document.getElementById("cpu_val");
const cpu_time = document.getElementById("cpu_time");
cpu_title_element = document.getElementById("cpu_title");

function get_token_from_param() {
    var url = new URL(window.location);
    var token = url.searchParams.get("token");
    return token;
}

function b_handle(d) {
    var response = JSON.parse(d);
    datalist.unshift(response);
    update_live_progress(response["OBS"]);
    update_live_cpu(response["CPU"]);
}


const update_observation = function(obs_str){
        var requestOptions = {
            method: 'POST',
            redirect: 'follow'
        };
        console.log(obs_str + "is the str");
var endpt = `/update_obs/?token=${get_token_from_param()}&obs=${obs_str}`;
    console.log(endpt);
        fetch(endpt, requestOptions)
            .then(response => response.text())
            .then(result => console.log(result))
            .catch(error => console.log('error', error));
    };

const mock_post_update_button = document.getElementsByClassName("post_obs_onclick");
Array.from(mock_post_update_button).map(function(x){
    x.onclick = function() {
    update_observation(x.innerText)
}})


function milliseconds_to_human_readable(s) {
    // TIP: to find current time in milliseconds, use:
    // var  current_time_milliseconds = new Date().getTime();

    function numberEnding(number) {
        return (number > 1) ? 's' : '';
    }

    var temp = Math.floor(s );
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

function update_live_cpu(proc) {
    cpu_val.innerText = `${proc.value.toFixed(2)}`
    cpu_title_element.innerText = `${proc.name}: Current CPU Use`
    cpu_time.innerText = `Updated ${milliseconds_to_human_readable(((Date.now() / 1000) - proc.unixtime))} ago`;
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
    obs_val.innerText = `${observation.value.toFixed(2)}`;
    obs_time.innerText = `Updated ${milliseconds_to_human_readable((Date.now() / 1000) - observation.unixtime)} ago`;
}

function GET_data(token) {
var requestOptions = {
  method: 'GET',
  redirect: 'follow'
};
var listen_response_code;
fetch(`/listen/?token=${get_token_from_param()}`, requestOptions)
  .then(function(response){
      response_status = response.status;
      if (response_status != 200){
          alert("Sorry! Your token is invalid, please make a new one")
          return;
      }
      return response.text()
  })
  .then(result => b_handle(result))
  .catch(error => console.log('error', error));
}

let datalist = [];

var myToken = getQueryVariable("token")
if (!myToken) {
    alert("Retry after adding ?token=X at the end with your URL request. Replace X with your token.")
} else {
    window.setInterval(() => GET_data(myToken), 1000);
    console.log("invoked");
}


function set_contactinfo(token, user_cell_formatted){
    var requestOptions = {
   method: 'POST',
   redirect: 'follow'
};

fetch(`${window.location.protocol}//${window.location.host}/set_contactinfo/?token=${get_token_from_param()}&cell=${user_cell_formatted}`, requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
}