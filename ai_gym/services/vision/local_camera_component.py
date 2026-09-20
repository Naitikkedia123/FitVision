import streamlit as st


# =========================================================
# Camera HTML
# =========================================================

_CAMERA_HTML = """
<div id="fitvision-camera-shell">

    <video
        id="fitvision-camera"
        autoplay
        muted
        playsinline>
    </video>

    <canvas
        id="fitvision-overlay">
    </canvas>

    <div id="fitvision-camera-status">
        STARTING CAMERA
    </div>

    <div id="fitvision-camera-error">
    </div>

</div>
"""


# =========================================================
# Camera CSS
# =========================================================

_CAMERA_CSS = """
#fitvision-camera-shell {
    position: relative;

    width: 100%;
    max-width: 760px;

    margin: 0 auto;

    overflow: hidden;

    border-radius: 18px;

    background: #050505;

    aspect-ratio: 4 / 3;
}

#fitvision-camera,
#fitvision-overlay {
    position: absolute;

    inset: 0;

    width: 100%;
    height: 100%;

    display: block;

    object-fit: cover;

    transform: scaleX(-1);
}

#fitvision-camera {
    z-index: 1;

    background: #050505;
}

#fitvision-overlay {
    z-index: 2;

    background: transparent;

    pointer-events: none;
}

#fitvision-overlay {
    pointer-events: none;
}

#fitvision-camera-status {
    position: absolute;

    top: 14px;
    left: 14px;

    z-index: 10;

    padding: 8px 12px;

    border-radius: 999px;

    background: rgba(0, 0, 0, 0.65);

    color: white;

    font-family:
        Inter,
        Arial,
        sans-serif;

    font-size: 12px;

    letter-spacing: 0.04em;
}

#fitvision-camera-error {
    position: absolute;

    left: 14px;
    right: 14px;
    bottom: 14px;

    z-index: 10;

    display: none;

    padding: 10px 12px;

    border-radius: 10px;

    background: rgba(80, 0, 0, 0.85);

    color: #ffb4b4;

    font-family:
        Inter,
        Arial,
        sans-serif;

    font-size: 12px;
}
"""


# =========================================================
# Browser-side MediaPipe
# =========================================================

_CAMERA_JS = """
import {
    FilesetResolver,
    PoseLandmarker,
    DrawingUtils,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/+esm";


export default function(component) {

    const {
        parentElement,
        setStateValue,
        data,
    } = component;


    const video =
        parentElement.querySelector(
            "#fitvision-camera"
        );


    const overlay =
        parentElement.querySelector(
            "#fitvision-overlay"
        );


    const status =
        parentElement.querySelector(
            "#fitvision-camera-status"
        );


    const errorBox =
        parentElement.querySelector(
            "#fitvision-camera-error"
        );


    const ctx =
        overlay.getContext(
            "2d"
        );


    let stream = null;

    let poseLandmarker = null;

    let drawingUtils = null;

    let running = false;

    let cameraReady = false;

    let modelReady = false;

    let lastInferenceTime = 0;

    let inferenceIntervalMs = 250;

    let lastBackendSendTime = 0;

    const backendSendIntervalMs = 500;

    let pendingLandmarkFrames = [];

    // =====================================================
    // Immediate camera stop
    // =====================================================

    function stopCameraImmediately() {

        running = false;
        cameraReady = false;

        pendingLandmarkFrames = [];

        if (video) {
            video.pause();
            video.srcObject = null;
        }

        if (stream) {
            stream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

            stream = null;
        }

        clearOverlay();
    }


    function handleTrainerEndClick(event) {

        const path =
            typeof event.composedPath === "function"
                ? event.composedPath()
                : [];

        const button =
            path.find(
                element =>
                    element &&
                    element.tagName === "BUTTON"
            );

        if (!button) {
            return;
        }

        const label =
            (
                button.innerText ||
                button.textContent ||
                ""
            )
                .trim()
                .toUpperCase();

        if (
            label === "END WORKOUT" ||
            label === "END WARM-UP"
        ) {
            stopCameraImmediately();
        }
    }


    document.addEventListener(
        "click",
        handleTrainerEndClick,
        true
    );


    // =====================================================
    // MediaPipe assets
    // =====================================================

    const WASM_URL =
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";


    const MODEL_URL =
        "https://storage.googleapis.com/mediapipe-models/" +
        "pose_landmarker/pose_landmarker_lite/" +
        "float16/1/pose_landmarker_lite.task";


    // =====================================================
    // Helpers
    // =====================================================

    function setStatus(message) {

        status.textContent =
            message;
    }


    function showError(message) {

        console.error(
            "FitVision camera:",
            message
        );


        errorBox.style.display =
            "block";

        errorBox.textContent =
            message;

        setStatus(
            "CAMERA ERROR"
        );


        setStateValue(
            "packet",
            {
                camera_active: false,
                pose_detected: false,
                landmarks: null,
                error: String(message),
            }
        );
    }


    function resizeOverlay() {

        if (
            !video.videoWidth ||
            !video.videoHeight
        ) {
            return;
        }


        if (
            overlay.width !==
            video.videoWidth
        ) {

            overlay.width =
                video.videoWidth;
        }


        if (
            overlay.height !==
            video.videoHeight
        ) {

            overlay.height =
                video.videoHeight;
        }
    }


    function clearOverlay() {

        resizeOverlay();

        ctx.clearRect(
            0,
            0,
            overlay.width,
            overlay.height
        );
    }


    function drawPose(landmarks) {

        resizeOverlay();

        ctx.clearRect(
            0,
            0,
            overlay.width,
            overlay.height
        );


        if (
            !landmarks ||
            !landmarks.length
        ) {
            return;
        }


        if (!drawingUtils) {

            drawingUtils =
                new DrawingUtils(
                    ctx
                );
        }


        drawingUtils.drawConnectors(
            landmarks,

            PoseLandmarker.POSE_CONNECTIONS,

            {
                color:
                    "#00ff88",

                lineWidth:
                    4,
            }
        );


        drawingUtils.drawLandmarks(
            landmarks,

            {
                radius:
                    4,

                color:
                    "#3b82f6",

                fillColor:
                    "#3b82f6",
            }
        );
    }


    function serializeLandmarks(
        landmarks
    ) {

        return landmarks.map(
            landmark => ({

                x: Number(
                    landmark.x || 0
                ),

                y: Number(
                    landmark.y || 0
                ),

                z: Number(
                    landmark.z || 0
                ),

                visibility: Number(
                    landmark.visibility ??
                    0
                ),

                presence: Number(
                    landmark.presence ??
                    0
                ),
            })
        );
    }


    function sendPacket() {

        const now =
            performance.now();

        if (
            now - lastBackendSendTime <
            backendSendIntervalMs
        ) {
            return;
        }

        lastBackendSendTime =
            now;

        const frames =
            pendingLandmarkFrames;

        pendingLandmarkFrames = [];

        setStateValue(
            "packet",
            {
                camera_active:
                    cameraReady,

                landmark_frames:
                    frames,

                timestamp_ms:
                    now,
            }
        );
    }


    // =====================================================
    // Camera
    // =====================================================

    async function initializeCamera() {

        setStatus(
            "REQUESTING CAMERA"
        );


        stream =
            await navigator
                .mediaDevices
                .getUserMedia({

                    video: {

                        width: {
                            ideal: 640,
                            max: 640,
                        },

                        height: {
                            ideal: 480,
                            max: 480,
                        },

                        frameRate: {
                            ideal: 30,
                            max: 30,
                        },

                        facingMode:
                            "user",
                    },

                    audio: false,
                });


        video.srcObject =
            stream;


        await video.play();


        cameraReady =
            true;


        setStateValue(
            "packet",
            {
                camera_active: true,
                landmark_frames: [],
            }
        );
    }


    // =====================================================
    // MediaPipe initialization
    // =====================================================

    async function initializePose() {

        setStatus(
            "LOADING AI"
        );


        const vision =
            await FilesetResolver
                .forVisionTasks(
                    WASM_URL
                );


        try {

            poseLandmarker =
                await PoseLandmarker
                    .createFromOptions(
                        vision,
                        {

                            baseOptions: {

                                modelAssetPath:
                                    MODEL_URL,

                                delegate:
                                    "GPU",
                            },

                            runningMode:
                                "VIDEO",

                            numPoses:
                                1,

                            minPoseDetectionConfidence:
                                0.7,

                            minPosePresenceConfidence:
                                0.7,

                            minTrackingConfidence:
                                0.7,

                            outputSegmentationMasks:
                                false,
                        }
                    );


        } catch (gpuError) {

            console.warn(
                "GPU delegate failed. Falling back to CPU.",
                gpuError
            );


            poseLandmarker =
                await PoseLandmarker
                    .createFromOptions(
                        vision,
                        {

                            baseOptions: {

                                modelAssetPath:
                                    MODEL_URL,

                                delegate:
                                    "CPU",
                            },

                            runningMode:
                                "VIDEO",

                            numPoses:
                                1,

                            minPoseDetectionConfidence:
                                0.7,

                            minPosePresenceConfidence:
                                0.7,

                            minTrackingConfidence:
                                0.7,

                            outputSegmentationMasks:
                                false,
                        }
                    );
        }


        modelReady =
            true;
    }


    // =====================================================
    // Inference loop
    // =====================================================

    function processFrame(
        timestamp
    ) {

        if (!running) {
            return;
        }


        const enoughTimePassed =
            (
                timestamp -
                lastInferenceTime
            ) >=
            inferenceIntervalMs;


        if (
            cameraReady &&
            modelReady &&
            video.readyState >= 2 &&
            enoughTimePassed
        ) {

            lastInferenceTime =
                timestamp;


            try {

                const result =
                    poseLandmarker
                        .detectForVideo(
                            video,
                            timestamp
                        );


                let landmarks =
                    null;


                if (
                    result &&
                    result.landmarks &&
                    result.landmarks.length
                ) {

                    landmarks =
                        result.landmarks[0];
                }


                drawPose(
                    landmarks
                );

                pendingLandmarkFrames.push({

                    landmarks:
                        landmarks
                            ? serializeLandmarks(
                                landmarks
                            )
                            : null,

                    timestamp_ms:
                        timestamp,

                });

                sendPacket();


            } catch (error) {

                console.error(
                    "Pose inference error:",
                    error
                );
            }
        }


        requestAnimationFrame(
            processFrame
        );
    }


    // =====================================================
    // Start
    // =====================================================

    async function start() {

        try {

            if (data) {

                inferenceIntervalMs =
                    Number(
                        data.inference_interval_ms ||
                        250
                    );
            }


            await initializeCamera();

            await initializePose();


            running =
                true;


            setStatus(
                "AI GYM LIVE"
            );


            requestAnimationFrame(
                processFrame
            );


        } catch (error) {

            showError(
                error?.message ||
                String(error)
            );
        }
    }


    // =====================================================
    // Start once
    // =====================================================

    start();


    // =====================================================
    // Cleanup
    // =====================================================

    return () => {

        document.removeEventListener(
            "click",
            handleTrainerEndClick,
            true
        );

        stopCameraImmediately();
    };
}
"""


# =========================================================
# Register Components v2
# =========================================================

_fitvision_camera = st.components.v2.component(
    name="fitvision_local_camera_v2",
    html=_CAMERA_HTML,
    css=_CAMERA_CSS,
    js=_CAMERA_JS,
    isolate_styles=True,
)


# =========================================================
# Public API
# =========================================================

def render_local_camera(
    *,
    exercise_type: str,
    key: str,
    inference_interval_ms: int = 250,
):

    result = _fitvision_camera(
        key=key,

        data={
            "exercise_type": exercise_type,
            "inference_interval_ms": (
                inference_interval_ms
            ),
        },

        default={
            "packet": {
                "camera_active": False,
                "pose_detected": False,
                "landmarks": None,
            }
        },

        on_packet_change=lambda: None,
    )


    packet = getattr(
        result,
        "packet",
        None,
    )


    return packet