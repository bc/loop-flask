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
    function update_local_model(observation_type, observation, local_data_target) {
        const when = new Date(observation["unixtime"]*1000);

        if (observation_type=="CPU"){
            const v = {x: when, y: observation.value, name: observation.name}
            update_CPU_view(v);
            local_data_target[observation_type].push(v);
        } else if (observation_type=="OBS"){
            const v = {x: when, y: observation.value}
            update_OBS_view(v)
            var priorlen = local_data_target["OBS"].length
            local_data_target[observation_type].push(v);
        } else{
            throw Error("unacceptable input observation type")
        }
        try {
        // console.log(`OBSlen:${local_data_target.OBS.length}\nCPUlen:${local_data_target.CPU.length}`)
        } catch (e) {
            debugger;
        }

    }


    function push_if_it_is_a_new_value(observation_type, observation,local_data_target) {
        const new_time = new Date(observation["unixtime"] * 1000)
        const latest_time_in_array = local_data_target[observation_type][local_data_target[observation_type].length - 1]["x"]

        if (new_time - latest_time_in_array  > 0) {
            update_local_model(observation_type, observation, local_data_target=local_data_target);
        }
    }
    function save_into_local_if_novel(observation_type, observation, local_data_target) {
        // base case, append if array is empty
        if (_userdata[observation_type].length == 0) {
            update_local_model(observation_type, observation, local_data_target=local_data_target);
        } else {
            push_if_it_is_a_new_value(observation_type, observation,local_data_target=local_data_target);
        }
    }
    var response = JSON.parse(d);
    save_into_local_if_novel("OBS", response["OBS"], local_data_target=_userdata);
    save_into_local_if_novel("CPU", response["CPU"], local_data_target=_userdata);
}
function update_observation(input_token, obs_str){
        var requestOptions = {
            method: 'POST',
            redirect: 'follow'
        };

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
    ,800)
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
    var contact_info_input = document.getElementById("discord_id_input")
    fetch(`/get_contactinfo?token=${get_token_from_param()}`, requestOptions)
        .then(function(response){
            response_status = response.status;
        return response.text()})
        .then(function(result){
      if (response_status != 200) {
          return;
      }
      if (result == '{"value": 0}'){
          target_element.style = "background-color: red;";
          target_element.innerText = "Missing contact info";
      } else{
          target_element.style = "background-color: green";
          var discord_id = JSON.parse(result).value
          target_element.innerText = `Discord ID is Set: ${discord_id}`;
          contact_info_input.value = discord_id;
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

var mychart_canvas = document.getElementById('myChart')
setInterval(function (){
    fetch(`/monotonic_obs_eta/?token=${get_token_from_param()}`, {
  method: 'GET',
  redirect: 'follow'
})
  .then(response => response.text())
  .then(result => {
      // console.log(result);
      if(result == "too few datapoints to predict"){

      } else{
          try{
        console.log(result)
        _userdata["modeling"] = JSON.parse(result);
          } catch (e) {
              debugger;
          }
      }
  })
  .catch(error => {console.log('error', error); });
},1000)


setInterval(function(){
    if (_userdata["modeling"] == null){

    } else if (_userdata["modeling"]["OBS"]["unixtimes"].length > 2){
        plotData(_userdata["modeling"]["OBS"]["unixtimes"], _userdata["modeling"]["OBS"]["values"], _userdata["modeling"]["predictions"],mychart_canvas)
    }
}, 2000)

const predictions_table_p = document.getElementById("predictions_table_p")


setInterval(function(){
    if (_userdata["modeling"] == null){

    } else if (_userdata["modeling"]["OBS"]["unixtimes"].length > 2){
        var pred = _userdata["modeling"]["predictions"]["unixtime_predicted"][20]
        var pred_timestamp = new Date(pred*1000).toLocaleTimeString('en-US')
        var ci_margin = _userdata["modeling"]["predictions"]["unixtime_upperbound"][20] - pred
        var margin = milliseconds_to_human_readable(ci_margin)
        var lower = _userdata["modeling"]["predictions"]["unixtime_lowerbound"][20]
        predictions_table_p.innerHTML = `Process finishes at <mark>${pred_timestamp}</mark>, plus or minus ${margin}, (95% confidence interval)`
    }
}, 2000)

function plotData(arrX, arrY,  predictions,Canvas){
    var ctx = Canvas.getContext('2d'), cW= Canvas.offsetWidth, cH= Canvas.offsetHeight
	ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.fillStyle="rgb(255,255,255)"
    ctx.fillRect(0,0,cW,cH)



    //axes and arrows
    ctx.strokeStyle='black'
    ctx.beginPath()
	ctx.lineTo(0.08*cW, 0.08*cH)
	ctx.lineTo(0.12*cW, 0.08*cH)
	ctx.moveTo(0.1*cW, 0.05*cH)
	ctx.lineTo(0.1*cW, 0.9*cH)
	ctx.lineTo(0.95*cW, 0.9*cH)

	ctx.moveTo(0.95*cW, 0.9*cH)

    ctx.stroke()

    ctx.translate(0.1*cW, 0.9*cH)
    ctx.scale(1,-1)
    ctx.stroke()
    const current_unixtime =  Date.now() / 1000
    var minX= Math.min.apply(null, arrX), minY= 0.0
    var maxX= current_unixtime, maxY= 1.15
    var wX=maxX-minX, wY=maxY-minY
    var gW=0.95*cW-0.1*cW, gH=0.9*cH-0.05*cH
    var facX=gW/wX, facY=gH/wY

    ctx.beginPath()
    ctx.fillStyle='blue'
    ctx.strokeStyle='black'
    ctx.lineWidth= 0.001*(cW+cH)
	var newX, newY
    //plot datapoints on screen
	for (var i in arrX){
		newX= (arrX[i]-minX)*facX
		newY= (arrY[i]-minY)*facY
    	if (i==0)
    		ctx.moveTo(newX,newY)
    	else
    		ctx.lineTo(newX,newY)
    }
	ctx.lineTo(current_unixtime,(arrX[i]-minX)*facX)
    ctx.stroke();
    ctx.closePath();
    //end basic datapoints

    //plot linear fit line
    ctx.beginPath()

    ctx.lineWidth= 0.002*(cW+cH)
	var newX_lm, newY_lm
    //plot datapoints on screen
    lm_X = predictions["unixtime_predicted"]
    lm_Y = predictions["values_to_infer"]
	for (var i in lm_X){
		newX_lm= (lm_X[i]-minX)*facX
		newY_lm= (lm_Y[i]-minY)*facY
    	if (i==0)
    		ctx.moveTo(newX_lm,newY_lm)
    	else
    		ctx.lineTo(newX_lm,newY_lm)
    }
	ctx.stroke();
	ctx.closePath();
    //end linear fit line


//


        //plot upper and lowerbound
    ctx.beginPath()

    ctx.lineWidth= 0.002*(cW+cH)
	var newX, newY
    //plot datapoints on screen
    lm_X_u = [...predictions["unixtime_upperbound"]]
    lm_Y_u = [...predictions["values_to_infer"]]

	//now plot lowerbound
        lm_X_l = [...predictions["unixtime_lowerbound"]]
    lm_Y_l = [...predictions["values_to_infer"]]

    x_ci = lm_X_u.concat(lm_X_l.reverse())
    y_ci = lm_Y_u.concat(lm_Y_l.reverse())
	for (var i in x_ci){
		newX= (x_ci[i]-minX)*facX
		newY= (y_ci[i]-minY)*facY
    	if (i==0)
    		ctx.moveTo(newX,newY)
    	else
    		ctx.lineTo(newX,newY)
    }
    ctx.globalAlpha = 0.15;
    ctx.closePath();
	ctx.strokeStyle='green'
    ctx.fillStyle = "red";
    ctx.fill();
    ctx.globalAlpha = 1.0;





        ctx.strokeStyle='pink'
    ctx.beginPath();
	ctx.lineTo(0.08*cW, 0.08*cH);


	ctx.scale(1,-1)
    ctx.fillStyle='darkblue'
 	ctx.textBaseline= 'middle'
	ctx.textAlign= 'center'
	var fntSize=8;
   	ctx.font= fntSize+"pt serif"

    ctx.beginPath()
    for (i=1;i<=5;i++){
    	ctx.moveTo(i*gW/6, 0.02*cH)
    	ctx.lineTo(i*gW/6, -0.02*cH)
	   	txtB= Math.round(current_unixtime - Math.round((i/6*wX+minX)*100)/100)
	   	txtBW=ctx.measureText(txtB).width
	    ctx.fillText("-" + txtB + "s", i*gW/6, 0.06*cH)

    	ctx.moveTo(0.02*cW, -i*gH/6)
    	ctx.lineTo(-0.02*cW, -i*gH/6)
	   	txtB= Math.round((i/6*wY+minY)*100)/100
	   	txtBW= ctx.measureText(txtB).width
	   	if (txtBW>0.06*cW) txtBW=0.06*cW
	    ctx.fillText(txtB, -0.06*cW, -i*gH/6, txtBW)
    }
    ctx.strokeStyle='purple'
    ctx.stroke()

    ctx.strokeStyle="yellow"
    ctx.beginPath()


}
