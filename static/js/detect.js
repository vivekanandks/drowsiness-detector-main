let camera_button = document.querySelector("#start-camera");
let video = document.querySelector("#video");
let click_button = document.querySelector("#click-photo");
let canvas = document.querySelector("#canvas");

let dps = [];
let alert = [];
let yawn_alert = [];

let audio = document.getElementById("drowsyAlert");
let audio1 = document.getElementById("yawnAlert");

let count = 0;
let yawn_count = 0;
let warning = 10;
let yawn_Counter = 0;

camera_button.addEventListener("click", async function () {
    let stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = stream;
});

click_button.addEventListener("click", function () {
    intervalID = setInterval(detectDrowsiness, 100);
});

var chart = new CanvasJS.Chart("chartContainer", {
    title: {
        text: "Eye Aspect Ratio Over Time"
    },
    data: [{ type: "line", dataPoints: dps }]
});

let xVal = 0;
let yVal = 0;

function detectDrowsiness() {
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    let image_data_url = canvas.toDataURL("image/jpeg");
    document.getElementById("image").value = image_data_url;

    $.ajax({
        type: "POST",
        url: "/submit-photo",
        data: { todo: $("#image").val() },
        success: function (data) {
            let ear = data.ear;
            let yawn = data.mar;
            alert.push(ear);
            yawn_alert.push(yawn);

            if (yawn_alert.length === 30) {
                yawn_alert.forEach(val => { if (val > 14) yawn_count++; });
                if (yawn_count > 20) {
                    audio1.play();
                    yawn_Counter++;
                }
                if (yawn_Counter > 3) clearInterval(intervalID);
                yawn_alert = [];
                yawn_count = 0;
            }

            if (alert.length === 20) {
                alert.forEach(val => { if (val <= 0.245) count++; });
                if (count >= warning) {
                    audio.play();
                    warning -= 2;
                }
                if (warning < 0) clearInterval(intervalID);
                alert = [];
                count = 0;
            }

            yVal = ear;
            dps.push({ x: xVal, y: yVal });
            xVal++;
            if (dps.length > 20) dps.shift();
            chart.render();
        }
    });
}
