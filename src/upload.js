const myButton = document.createElement('button');
myButton.textContent = 'Upload';
myButton.className = 'upload';
console.log("started");


myButton.onclick = function(e) {
  let evtTgt = e.target;
  console.log("TODO attempt upload");
  var myHeaders = new Headers();

  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    redirect: 'follow'
  };

  fetch("http://loopservice.briancohn.com/update_obs/?token=f8992e21-a350-40a5-986f-5221412bdad8&obs=0.0", requestOptions)
    .then(response => response.text())
    .then(result => console.log(result))
    .catch(error => console.log('error', error));
}