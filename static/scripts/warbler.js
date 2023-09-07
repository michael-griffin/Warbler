"use strict";

let submit

async function toggleLike(evt) {
  evt.preventDefault();
  const $msgId = $(evt.target).attr('id').split('-')[1]
  const url = evt.target.action
  //console.log(evt.action);
  submit = evt;
  //let resp = await fetch(url, method="POST")
  // let resp = await fetch(`/messages/${$msgId}/toggle-like`, {method:"POST"});
  let resp = await fetch(url, {
    method: "POST",
    headers: {"Content-Type" : "application/json"}
  });
  let data = await resp.json();
  console.log(data);

}

const $message = $('#messages')

$message.on("submit", toggleLike)