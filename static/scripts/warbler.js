"use strict";

let submit

//https://stackoverflow.com/questions/60510765/flask-ajax-bad-request-the-csrf-token-is-missing

// var csrf_token = "{{ csrf_token() }}";

// $.ajaxSetup({
//     beforeSend: function(xhr, settings) {
//         if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
//             xhr.setRequestHeader("X-CSRFToken", csrf_token);
//         }
//     }
// });

async function toggleLike(evt) {
  evt.preventDefault();
  submit = evt;

  //TODO: csrf validation is tricky, leaving it for now.
  const url = evt.target.action

  let resp = await fetch(url, {
    method: "POST",
    headers: {"Accept": "application/json"}
  });
  let server_response = await resp.json();
  let $icon = $(evt.target).find('.bi');

  handleToggle(server_response, $icon);

}

function handleToggle(server_response, icon){
  if (server_response["status"] === "ok"){
    icon.toggleClass('bi-star-fill');
    icon.toggleClass('bi-star');
  }
}

const $message = $('#messages')

$message.on("submit", toggleLike)