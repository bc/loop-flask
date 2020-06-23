//extracts form elements into js dictionary
const formToJSON = elements => [].reduce.call(elements, (data, element) => {
    data[element.name] = element.value;
    return data;
}, {});
//returns dictionary of the form elements as key value pairs
function get_form_elements(form_id) {
    var elements = formToJSON(document.getElementById(form_id));
    return elements
}
function predicate_form_into_statement(val_dict){
    const variables = ["predicate_form_obs","predicate_form_cpu"]
    var arr = variables.map(x=>val_dict[`${x}_enabled`])
    const indices = arr.reduce(
        (out, bool, index) => bool ? out.concat(index) : out,
        []
    )
    var sentences = []
    for (let i = 0; i < indices.length; i++) {
        var varname = variables[i];
        var comparator = val_dict[varname + "_comparator"];
        var trigger_val = val_dict[varname+"_val"];
        sentences.push(`${varname}${comparator}${trigger_val}`);
    }
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
function show_predicate_post_status(button_id, status, custom_text=""){
    button = document.getElementById(button_id)
    if (status == SetPredicateStatus.INIT){
        button.style = "background-color: #FFF; color:#000";
    } else if(status == SetPredicateStatus.WAITING_ON_POST){
        button.style = "background-color: orange;";
    } else if(status == SetPredicateStatus.POST_FAIL){
        button.style = "background-color: grey;";
        button.innerText = `POST failed. Make sure your token is correct and internet is connected: ${custom_text}`
        button.disabled = true;
    } else if (status == SetPredicateStatus.POST_SUCCESS){
        button.style = "background-color: green;";
    } else{
        console.log('not a valid SetPredicateStatus input')
    }
}

function show_raw_predicate(predicate_sentence,predicate_raw_id){
    document.getElementById(predicate_raw_id).innerText = predicate_sentence;
}
function post_set_predicate(predicate_sentence, button_id, predicate_raw_id){
    var requestOptions = {
        method: 'POST',
        redirect: 'follow'
    };
    console.log(predicate_sentence + "=input");
    show_predicate_post_status(button_id,SetPredicateStatus.WAITING_ON_POST);
    show_raw_predicate(predicate_sentence,predicate_raw_id)
    fetch(`/set_predicates/?token=${get_token_from_param()}&predicate=${predicate_sentence}`, requestOptions)
        .then(response => {
            response.text();
            show_predicate_post_status(button_id,SetPredicateStatus.POST_SUCCESS);
        })
        .catch(error => {
            show_predicate_post_status(button_id,SetPredicateStatus.POST_FAIL, error.toString());
        });
}
function gen_and_send_predicate(form_id,button_id, predicate_raw_id){
    post_set_predicate(predicate_form_into_statement(get_form_elements(form_id)), button_id, predicate_raw_id)
}