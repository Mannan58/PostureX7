let video = document.getElementById("video");
let stream;

async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
}

function stopCamera() {
    let tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
}