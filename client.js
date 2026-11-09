
const socket = new WebSocket("ws://localhost:8765");
const log = document.getElementById("log");
const input = document.getElementById("input");

function append(text) {
log.textContent += text + "\n";
}

socket.onopen = () => append("connected");

socket.onmessage = (event) => {
  append(event.data);
};

socket.onclose = () => append("disconnected");

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    socket.send(input.value);
    input.value = "";
  }
});
