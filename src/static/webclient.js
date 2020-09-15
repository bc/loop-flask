const obs_val = document.getElementById("obs_val");
const obs_time = document.getElementById("obs_time");

const cpu_val = document.getElementById("cpu_val");
const cpu_time = document.getElementById("cpu_time");
const cpu_title_element = document.getElementById("cpu_title");

function get_token_from_param() {
    var url = new URL(window.location);
    var token = url.searchParams.get("token");
    return token;
}
let _userdata = {
    OBS: [],
    CPU: []
}
 function milliseconds_to_human_readable(s) {
    // TIP: to find current time in milliseconds, use:
    // var  current_time_milliseconds = new Date().getTime();

    function numberEnding(number) {
        return (number > 1) ? 's' : '';
    }

    var temp = Math.floor(s);
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


function b_handle(d) {
    function update_local_model(observation_type, observation) {
        const when = new Date(observation["unixtime"]*1000);

        if (observation_type=="CPU"){
            const v = {x: when, y: observation.value, name: observation.name}
            update_CPU_view(v);
            _userdata[observation_type].push(v);
        } else if (observation_type=="OBS"){
            const v = {x: when, y: observation.value}
            update_OBS_view(v)
            _userdata[observation_type].push(v);
        } else{
            throw Error("unacceptable input observation type")
        }
        try {
        console.log(`OBSlen:${_userdata.OBS.length}\nCPUlen:${_userdata.CPU.length}`)
        } catch (e) {
            debugger;
        }

    }

    var response = JSON.parse(d);
    // base case
    if (_userdata.CPU.length == 0){
        update_local_model("CPU", response["CPU"]);
        return 0;
    }

    function push_if_it_is_a_new_value(observation_type, observation) {
        const new_time = new Date(observation["unixtime"] * 1000)
        const is_newer = _userdata[observation_type][_userdata[observation_type].length - 1]["x"] - new_time > 0
        if (is_newer) {
            update_local_model(observation_type, observation);
        }
    }
    function save_into_local_if_novel(observation_type, observation) {
        if (_userdata[observation_type].length == 0) {
            update_local_model(observation_type, observation);
        } else {
            push_if_it_is_a_new_value(observation_type, observation);
        }
    }
    save_into_local_if_novel("OBS", response["OBS"]);
    save_into_local_if_novel("CPU", response["CPU"]);
}
function update_observation(input_token, obs_str){
        var requestOptions = {
            method: 'POST',
            redirect: 'follow'
        };
        console.log(obs_str + "is the str");
var endpt = `/update_obs/?token=${input_token}&obs=${obs_str}`;
    console.log(endpt);
        fetch(endpt, requestOptions)
            .then(response => response.text())
            .then(result => console.log(result))
            .catch(error => console.log('error', error));
    }


function update_cpu(input_token, cpu_value){
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({"name":"WebClient Manual Entry","cpu":cpu_value});

        var requestOptions = {
          method: 'POST',
          headers: myHeaders,
          body: raw,
          redirect: 'follow'
        };

        fetch(`update_cpu/?token=${input_token}`, requestOptions)
          .then(response => response.text())
          .then(result => console.log(result))
          .catch(error => console.log('error', error));
}

const mock_post_update_obs_button = document.getElementsByClassName("post_obs_onclick");
Array.from(mock_post_update_obs_button).map(function(x){
    x.onclick = function() {
    update_observation(get_token_from_param(), x.innerText)
}})

const mock_post_update_cpu_button = document.getElementsByClassName("post_cpu_onclick");
Array.from(mock_post_update_cpu_button).map(function(x){
    x.onclick = function() {
    update_cpu(get_token_from_param(), x.innerText)
}})


function update_CPU_view(cpu_observation) {
    cpu_val.innerText = `${cpu_observation.y.toFixed(2)}`
    cpu_title_element.innerText = `${cpu_observation.name}: Current CPU Use`
    cpu_time.innerText = `Updated ${milliseconds_to_human_readable(((Date.now() / 1000) - cpu_observation.x))} ago`;
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

function update_OBS_view(observation) {
    obs_val.innerText = `${observation.y.toFixed(2)}`;
    obs_time.innerText = `Updated ${milliseconds_to_human_readable((Date.now() / 1000) - observation.x)} ago`;
}

function GET_data(token) {
var requestOptions = {
  method: 'GET',
  redirect: 'follow'
};
var listen_response_code;
fetch(`/listen/?token=${get_token_from_param()}`, requestOptions)
  .then(function(response){
      if (response.status != 200){
          alert("Sorry! Your token is invalid, please make a new one")
          return;
      }
      return response.text()
  })
  .then(result => b_handle(result))
  .catch(error => console.log('error', error));
}

const myToken = getQueryVariable("token")
if (!myToken) {
    alert("Retry after adding ?token=X at the end with your URL request. Replace X with your token.")
} else {
    window.setInterval(function() {
            GET_data(myToken);
            get_predicate_from_server("predicate_check_serverside");
            get_contactinfo_from_server('contactinfo_check_serverside');
        }
    ,2000)
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


function get_predicate_from_server(status_icon_id){
    var requestOptions = {
  method: 'GET',
  redirect: 'follow'
};
var target_element = document.getElementById(status_icon_id);
fetch(`/get_predicates/?token=${get_token_from_param()}`, requestOptions)
  .then(response => response.text())
  .then(function(result){
      if (result == "[]"){
          target_element.style = "background-color: grey;";
          target_element.innerText = "No active predicates enabled";
      } else {
          target_element.style = "background-color: green";
          target_element.innerText = `Predicate enabled: ${result}`;
      }
  })
  .catch(error => console.log('error', error));
}

function get_contactinfo_from_server(status_icon_id) {
    var response_status;
    var requestOptions = {
        method: 'GET',
        redirect: 'follow'
    };
    var target_element = document.getElementById(status_icon_id);

    fetch(`/get_contactinfo/?token=${get_token_from_param()}`, requestOptions)
        .then(function(response){
            response_status = response.status;
        return response.text()})
        .then(function(result){
      if (response_status == 401){
          target_element.style = "background-color: grey;";
          target_element.innerText = "Missing contact info";
      } else if (response_status == 200){
          target_element.style = "background-color: green";
          target_element.innerText = `Contact Info Enabled: ${result}`;
      } else{
          target_element.style = "background-color: black";
          target_element.innerText = `Unknown response err for contact info`;
      }
  })
        .catch(error => console.log('error', error));
}

//Generate Code Snippets
const client_cpu_link = `${window.location.protocol}//${window.location.host}/static/client_cpu.py`
const myrand = Math.random().toString();
const cpu_bash_command = `curl -L -H 'Cache-Control: no-cache' ${client_cpu_link} > /tmp/cpu_runner_${myrand}.py && python3 /tmp/cpu_runner_${myrand}.py ${window.location.protocol}//${window.location.host} ${get_token_from_param()}`;
document.getElementById("bash_cpu_code_snippet").innerText = cpu_bash_command
const curl_command_obs = `curl --location --request POST '${window.location.protocol}//${window.location.host}/update_obs/?token=${token}&obs=0.22'`;
document.getElementById("curl_obs_code_snippet").innerText = curl_command_obs
document.getElementById("matlab_obs_code_snippet").innerText = `system("${curl_command_obs} &");`
document.getElementById("python_obs_code_snippet").innerText = `import requests;print(requests.request("POST","${window.location.protocol}//${window.location.host}/update_obs/?token=${token}&obs=%s"%val, headers={}, data = {}).text.encode('utf8'))`

// var ctx = document.getElementById('myChart').getContext('2d');
// var myLineChart = new Chart(ctx, {
//     type: 'line',
//     data: [{
//     x: 10,
//     y: 20
// }, {
//     x: 15,
//     y: 10
// }],
//     options:
// });