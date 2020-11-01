//extracts form elements into js dictionary
const formToJSON = elements => [].reduce.call(elements, (data, element) => {
    data[element.name] = element.value;
    return data;
}, {});

function predicate_form_into_statement(val_dict) {

    var sentences = []
    sentences.push(`${"predicate_form_obs"}${val_dict["predicate_form_obs_comparator"]}${val_dict["predicate_form_obs_val"]}`);
    sentences.push(`${"predicate_form_cpu"}${val_dict["predicate_form_cpu_comparator"]}${val_dict["predicate_form_cpu_val"]}`);
    return sentences.join(";");
}

const SetPredicateStatus = {
    INIT: 0,
    WAITING_ON_POST: 1,
    POST_SUCCESS: 2,
    POST_FAIL: 3
};
Object.freeze(SetPredicateStatus);

//status should be from SetPredicateStatus
function show_predicate_post_status(button_id, status, custom_text = "") {
    button = document.getElementById(button_id)
    if (status == SetPredicateStatus.INIT) {
        button.style = "background-color: #FFF; color:#000";
    } else if (status == SetPredicateStatus.WAITING_ON_POST) {
        button.style = "background-color: orange;";
    } else if (status == SetPredicateStatus.POST_FAIL) {
        button.style = "background-color: grey;";
        button.innerText = `POST failed. Make sure your token is correct and internet is connected: ${custom_text}`
        button.disabled = true;
    } else if (status == SetPredicateStatus.POST_SUCCESS) {
        button.style = "background-color: green;";
    } else {
        console.log('not a valid SetPredicateStatus input')
    }
}

function show_raw_predicate(predicate_sentence, predicate_raw_id) {
    document.getElementById(predicate_raw_id).innerText = predicate_sentence;
}

var predicate_response;

//predicate raw_id is the output target PRE
function post_set_predicate(predicate_sentence, button_id, predicate_raw_id) {
    var requestOptions = {
        method: 'POST',
        redirect: 'follow'
    };
    console.log(predicate_sentence + "=input");
    show_predicate_post_status(button_id, SetPredicateStatus.WAITING_ON_POST);
    show_raw_predicate(predicate_sentence, predicate_raw_id)
    fetch(`/set_predicates/?token=${get_token_from_param()}&predicate=${predicate_sentence}`, requestOptions)
        .then(response => {
            predicate_response = response.text();
            console.log(predicate_response)
            show_predicate_post_status(button_id, SetPredicateStatus.POST_SUCCESS);
        })
        .catch(error => {
            console.log(error)
            show_predicate_post_status(button_id, SetPredicateStatus.POST_FAIL, error.toString());
        });
}

function gen_and_send_predicate(form_id, button_id, predicate_raw_id) {
    const form_elements = formToJSON(document.getElementById(form_id))
    const statement = predicate_form_into_statement(form_elements);
    if (statement == ""){
        alert("you have to check at least 1 of the boxes to set up the ping");
    } else{
        post_set_predicate(statement, button_id, predicate_raw_id);
    }
}

function post_contactinfo(contact_number, document_id_for_status) {
    var requestOptions = {
        method: 'POST',
        redirect: 'follow'
    };
    const status_object = document.getElementById(document_id_for_status)
    var response_status;
    contact_number = contact_number.trim();
    //if they entered nothing or non numbers, err out
    if(contact_number == ""){
        alert("You gave a blank phone number");
        status_object.style = "background-color: yellow;"
        return;
        //if it's not a pure number
    } else if (/^\d+$/.test(contact_number)==false){
        alert("No symbols please, try again with only digits")
        status_object.style = "background-color: yellow;"
        return;
    }
    fetch(`/set_contactinfo/?token=${get_token_from_param()}&contact_number=${contact_number}`, requestOptions)
        .then(function(response){
            response_status = response.status;
            if (response_status != 200){
                status_object.style = "background-color: red;"
                alert("phone number provided is messed up. Make sure it's just numbers and has the country code at the beginning.")
                return;
            }
            return response.text();
        })
        .then(function(result){
            if (response_status == 200){
                status_object.style = "background-color: green;"
            }
        }
        )
        .catch(error => {
            status_object.style = "background-color: black;"
            alert('error\n' + error)
        })
        }