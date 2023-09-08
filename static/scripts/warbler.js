"use strict";

let submit

async function toggleLike(evt) {
  evt.preventDefault();
  //const $msgId = $(evt.target).attr('id').split('-')[1]
  const url = evt.target.action

  resp = await fetch(url, method="POST")
  submit = evt;
  console.log(evt.action);
}

const $message = $('#messages')

$message.on("submit", toggleLike)