import {
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Canvas,
  useThree,
} from "@react-three/fiber";

import Avatar from "./Avatar";
import Room from "./Room";


// ============================================================
// CÂMARA FIXA
// ============================================================

function CameraSetup() {
  const { camera } = useThree();

  useEffect(() => {

    camera.position.set(
      0,
      1,
      3.5
    );

    camera.lookAt(
      0,
      1,
      -0.4
    );

    camera.updateProjectionMatrix();

  }, [camera]);

  return null;
}


// ============================================================
// APP
// ============================================================

function App() {

  const socketRef =
    useRef(null);

  const reconnectTimerRef =
    useRef(null);

  const manualCloseRef =
    useRef(false);

  const listeningRequestRef =
    useRef(false);


  const [
    connected,
    setConnected,
  ] = useState(false);


  const [
    avatarState,
    setAvatarState,
  ] = useState("idle");


  const [
    expression,
    setExpression,
  ] = useState("neutral");


  const [
    speech,
    setSpeech,
  ] = useState(null);


  const [
    userText,
    setUserText,
  ] = useState("");


  const [
    assistantText,
    setAssistantText,
  ] = useState("");


  const [
    error,
    setError,
  ] = useState("");


  // ==========================================================
  // WEBSOCKET
  // ==========================================================

  useEffect(() => {

    manualCloseRef.current = false;


    function connect() {

      if (
        socketRef.current &&
        (
          socketRef.current.readyState === WebSocket.OPEN ||
          socketRef.current.readyState === WebSocket.CONNECTING
        )
      ) {
        return;
      }


      console.log(
        "A ligar WebSocket..."
      );


      const socket =
        new WebSocket(
          "ws://127.0.0.1:8000/ws/avatar"
        );


      socketRef.current =
        socket;


      // ------------------------------------------------------
      // OPEN
      // ------------------------------------------------------

      socket.onopen = () => {

        console.log(
          "WebSocket ligado."
        );


        setConnected(true);

        setError("");


        socket.send(
          JSON.stringify({
            type: "avatar_ready",
          })
        );

      };


      // ------------------------------------------------------
      // MESSAGE
      // ------------------------------------------------------

      socket.onmessage = (
        event
      ) => {

        let message;


        try {

          message =
            JSON.parse(
              event.data
            );

        }

        catch (parseError) {

          console.error(
            "Mensagem inválida:",
            event.data,
            parseError
          );

          return;
        }


        console.log(
          "WS:",
          message
        );


        // ====================================================
        // STATE
        // ====================================================

        if (
          message.type === "state"
        ) {

          setAvatarState(
            message.value
          );


          if (
            message.value === "idle"
          ) {

            listeningRequestRef.current =
              false;

          }


          return;
        }


        // ====================================================
        // USER TEXT
        // ====================================================

        if (
          message.type === "user_text"
        ) {

          setUserText(
            message.text || ""
          );

          return;
        }


        // ====================================================
        // RESPONSE
        // ====================================================

        if (
          message.type === "response"
        ) {

          setAssistantText(
            message.text || ""
          );


          if (
            message.emotion
          ) {

            setExpression(
              message.emotion
            );

          }


          return;
        }


        // ====================================================
        // SPEECH
        // ====================================================

        if (
          message.type === "speech"
        ) {

          setAvatarState(
            "speaking"
          );


          if (
            message.emotion
          ) {

            setExpression(
              message.emotion
            );

          }


          setSpeech({

            id:
              Date.now(),

            audioUrl:
              message.audio,

            mouthCues:
              message.mouthCues || [],

            duration:
              message.duration || 0,

            text:
              message.text || "",

          });


          return;
        }


        // ====================================================
        // BUSY
        // ====================================================

        if (
          message.type === "busy"
        ) {

          console.log(
            "Backend ocupado."
          );

          return;
        }


        // ====================================================
        // ERROR
        // ====================================================

        if (
          message.type === "error"
        ) {

          listeningRequestRef.current =
            false;

          setAvatarState(
            "idle"
          );

          setError(
            message.message
            ||
            "Erro desconhecido."
          );

          return;
        }

      };


      // ------------------------------------------------------
      // ERROR
      // ------------------------------------------------------

      socket.onerror = (
        websocketError
      ) => {

        console.error(
          "Erro WebSocket:",
          websocketError
        );

      };


      // ------------------------------------------------------
      // CLOSE
      // ------------------------------------------------------

      socket.onclose = () => {

        console.log(
          "WebSocket desligado."
        );


        setConnected(false);

        listeningRequestRef.current =
          false;

        socketRef.current =
          null;


        if (
          !manualCloseRef.current
        ) {

          reconnectTimerRef.current =
            setTimeout(
              connect,
              2000
            );

        }

      };

    }


    connect();


    return () => {

      manualCloseRef.current =
        true;


      if (
        reconnectTimerRef.current
      ) {

        clearTimeout(
          reconnectTimerRef.current
        );

      }


      if (
        socketRef.current
      ) {

        socketRef.current.close();

      }


      socketRef.current =
        null;

    };

  }, []);


  // ==========================================================
  // COMEÇAR A OUVIR
  // ==========================================================

  function startListening() {

    const socket =
      socketRef.current;


    if (
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      return;
    }


    if (
      avatarState !== "idle"
    ) {
      return;
    }


    if (
      listeningRequestRef.current
    ) {
      return;
    }


    listeningRequestRef.current =
      true;


    setAvatarState(
      "listening"
    );


    setUserText("");

    setAssistantText("");

    setError("");


    const requestId =
      crypto.randomUUID();


    console.log(
      "Pedido de escuta:",
      requestId
    );


    socket.send(
      JSON.stringify({
        type: "start_listening",
        requestId,
      })
    );

  }


  // ==========================================================
  // ÁUDIO TERMINOU
  // ==========================================================

  const handleSpeechEnd =
    useCallback(
      () => {

        /*
         * MUDA LOCALMENTE DE IMEDIATO.
         *
         * Não esperamos pela resposta
         * do backend.
         */

        setAvatarState(
          "idle"
        );


        setExpression(
          "neutral"
        );


        listeningRequestRef.current =
          false;


        const socket =
          socketRef.current;


        if (
          socket &&
          socket.readyState === WebSocket.OPEN
        ) {

          socket.send(
            JSON.stringify({
              type: "speech_ended",
            })
          );

        }

      },
      []
    );


  // ==========================================================
  // LABEL
  // ==========================================================

  const stateLabels = {

    idle:
      "Pronta",

    listening:
      "A ouvir...",

    thinking:
      "A pensar...",

    speaking:
      "A falar...",

  };


  const stateLabel =
    stateLabels[
      avatarState
    ]
    ||
    avatarState;


  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <div className="app">

      <Canvas

        className="scene"

        camera={{
          fov: 35,
          near: 0.1,
          far: 100,
        }}

        gl={{
          antialias: true,
        }}

      >

        <CameraSetup />


        <ambientLight
          intensity={0.7}
        />


        <directionalLight
          position={[
            4,
            6,
            4
          ]}
          intensity={1.5}
        />


        <pointLight
          position={[
            -3.2,
            2.2,
            -1.5
          ]}
          intensity={4}
          distance={5}
        />


        <Suspense
          fallback={null}
        >

          <Room />


          <Avatar

            expression={
              expression
            }

            speech={
              speech
            }

            state={
              avatarState
            }

            onSpeechEnd={
              handleSpeechEnd
            }

          />

        </Suspense>

      </Canvas>


      {/* STATUS */}

      <div className="status">

        <span
          className={
            connected
              ? "status-dot online"
              : "status-dot"
          }
        />


        {
          connected
            ? stateLabel
            : "Desligada"
        }

      </div>


      {/* CONVERSA */}

      <div className="conversation">

        {
          userText &&
          (
            <div className="user-text">

              {userText}

            </div>
          )
        }


        {
          assistantText &&
          (
            <div className="assistant-text">

              {assistantText}

            </div>
          )
        }

      </div>


      {/* MICROFONE */}

      <button

        className={
          `mic-button ${avatarState}`
        }

        onClick={
          startListening
        }

        disabled={
          !connected
          ||
          avatarState !== "idle"
          ||
          listeningRequestRef.current
        }

        title="Falar com Baghdad"

      >

        🎙️

      </button>


      {
        error &&
        (
          <div className="error-message">

            {error}

          </div>
        )
      }

    </div>

  );

}


export default App;